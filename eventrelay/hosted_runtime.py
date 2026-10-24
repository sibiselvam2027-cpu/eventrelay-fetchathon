"""Agentverse-hosted runtime: attach protocols to the platform-provided agent.

No Agent is constructed or run here. Every invocation restores persistent state
from ctx.storage, performs synchronous mutations, checkpoints, and only then
awaits network sends. Deploy the coordinator as a single sequential writer.
Timer changes are visible through ASI status polling; unsolicited ASI delivery
across conversation sessions is deliberately not assumed.
"""

import json
import os
import re
import time
from urllib.parse import urlsplit

from uagents import Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement, ChatMessage, TextContent, chat_protocol_spec,
)
from eventrelay.asi import ASIError, extract_intent_async
from eventrelay.fetch_agents import (
    IssueOffer, VendorCommand, VendorDecision, _actor, _chat_message, _staff_command,
)
from eventrelay.hosted_state import open_hosted_service
from eventrelay.router import EVENT


ROLES = {"coordinator", "hospitality", "audio", "facilities", "housekeeping"}
STAFF = {"hospitality": {"staff_arun", "staff_neha"}, "audio": {"staff_ravi", "staff_sara"},
         "facilities": {"staff_vikram", "staff_pooja"}, "housekeeping": {"staff_meena", "staff_kiran"}}
CATEGORY = {"hospitality": "drinking_water", "audio": "audio", "facilities": "power", "housekeeping": "cleanup"}
TRANSPORT_KEY = "eventrelay.transport.v1"


def _setting(ctx, name, default=""):
    secrets = getattr(ctx, "secrets", None)
    value = secrets.get(name) if secrets is not None and hasattr(secrets, "get") else None
    return value if value is not None else os.environ.get(name, default)


def _prepare(ctx):
    # Hosted secrets remain in memory. They are never put in storage, source,
    # model messages, cards or logs. The existing ASI client reads this key.
    for name in ("ASI1_API_KEY", "ASI1_BASE_URL", "ASI1_MODEL", "EVENTRELAY_DEMO_MODE"):
        value = _setting(ctx, name)
        if value:
            os.environ[name] = str(value)


def _mapping(ctx, name):
    raw = _setting(ctx, name, "{}")
    value = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(value, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in value.items()):
        raise ValueError(f"{name} must be a JSON string-to-string mapping.")
    return value


def _addresses(ctx, agent, role):
    values = {name: str(_setting(ctx, f"EVENTRELAY_{name.upper()}_ADDRESS")) for name in ROLES}
    values[role] = agent.address
    return values


class HostedTransport:
    """Per-invocation transport state, explicitly saved to Agentverse storage."""

    def __init__(self, storage):
        self.storage = storage
        raw = storage.get(TRANSPORT_KEY)
        self.state = json.loads(raw) if isinstance(raw, str) else json.loads(json.dumps(raw or {}))
        for key in ("origins", "offers", "inbox"):
            self.state.setdefault(key, {})

    def save(self):
        self.storage.set(TRANSPORT_KEY, self.state)

    def capture(self, response, actor, recipient, session, addresses):
        issues = ([response["issue"]] if response.get("issue") else []) + response.get("issues", [])
        for issue in issues:
            if actor and recipient and issue.get("reporter_id") == actor:
                self.state["origins"].setdefault(issue["issue_id"], {
                    "actor": actor, "recipient": recipient, "session": str(session)})
        for value in response.get("offers", []):
            offer = IssueOffer(**value)
            canonical = offer.dict()
            old = self.state["offers"].get(offer.offer_id)
            address = addresses.get(offer.vendor_group, "")
            if old:
                if old["offer"] != canonical:
                    raise ValueError("An existing offer cannot change identity.")
                if old["expected_sender"] and address and old["expected_sender"] != address:
                    raise ValueError("An existing offer cannot change vendor identity.")
                if not old["expected_sender"]:
                    old["expected_sender"] = address
            else:
                self.state["offers"][offer.offer_id] = {
                    "offer": canonical, "expected_sender": address,
                    "processed": False, "sent_at": 0}

    def claim(self, offers, now=None):
        timestamp = time.time() if now is None else now
        messages = []
        for value in offers:
            row = self.state["offers"].get(value["offer_id"])
            if not row or row["processed"] or not row["expected_sender"]:
                continue
            if row["sent_at"] and timestamp - row["sent_at"] < 5:
                continue
            row["sent_at"] = timestamp
            messages.append((row["expected_sender"], IssueOffer(**row["offer"])))
        return messages

    def match(self, sender, decision):
        row = self.state["offers"].get(decision.offer_id)
        if not row or row["processed"] or row["expected_sender"] != sender:
            return None
        offer = row["offer"]
        if (offer["issue_id"], offer["staff_id"], offer["version"]) != (
                decision.issue_id, decision.staff_id, decision.version):
            return None
        return row

    def command_origin(self, sender, command):
        for row in self.state["offers"].values():
            offer = row["offer"]
            if (row["expected_sender"] == sender and offer["issue_id"] == command.issue_id
                    and offer["staff_id"] == command.staff_id):
                return self.state["origins"].get(command.issue_id) or {"recipient": "", "session": ""}
        return None

    def receive(self, offer):
        old = self.state["inbox"].get(offer.offer_id)
        if old and old != offer.dict():
            raise ValueError("A received offer cannot change identity.")
        self.state["inbox"][offer.offer_id] = offer.dict()

    def latest(self, staff_id, issue_id):
        candidates = [row for row in self.state["inbox"].values()
                      if row["staff_id"] == staff_id and row["issue_id"] == issue_id]
        return IssueOffer(**max(candidates, key=lambda item: item["version"])) if candidates else None


def _finish(session, transport, response, actor, recipient, chat_session, addresses):
    """No awaits: save outbox/origin and domain snapshot before any delivery."""
    transport.capture(response, actor, recipient, chat_session, addresses)
    outgoing = transport.claim(response.get("offers", []))
    transport.save()
    session.checkpoint()
    return outgoing


async def _deliver(ctx, response, outgoing, recipient=None):
    if recipient:
        await ctx.send(recipient, _chat_message(response))
    for destination, offer in outgoing:
        await ctx.send(destination, offer)


def attach(agent, role):
    """Attach EventRelay to an Agentverse-provided `agent`; never call run()."""
    if role not in ROLES:
        raise ValueError("Unknown hosted EventRelay role.")
    def stage(label):
        logger = getattr(agent, "logger", None) or getattr(agent, "_logger", None)
        if logger is not None:
            logger.info("EventRelay attach: " + label)
        else:
            print("EventRelay attach: " + label)
    stage("01 creating chat protocol")
    chat = Protocol(spec=chat_protocol_spec)
    stage("02 creating operations protocol")
    operations = Protocol(name="EventRelayOffers", version="1.0.0")

    @chat.on_message(ChatAcknowledgement)
    async def acknowledge(ctx: Context, sender: str, msg: ChatAcknowledgement):
        pass

    stage("03 acknowledgement handler registered")

    @chat.on_message(ChatMessage)
    async def receive_chat(ctx: Context, sender: str, msg: ChatMessage):
        await ctx.send(sender, ChatAcknowledgement(acknowledged_msg_id=msg.msg_id))
        text = "\n".join(block.text for block in msg.content if isinstance(block, TextContent)).strip()
        if not text:
            return
        try:
            _prepare(ctx)
            addresses = _addresses(ctx, agent, role)
            staff_senders = _mapping(ctx, "EVENTRELAY_STAFF_SENDERS")
            if role != "coordinator":
                staff_id = staff_senders.get(sender)
                if staff_id not in STAFF[role]:
                    await ctx.send(sender, _chat_message({"text": "This chat is not an authenticated crew identity. Report the issue through EventRelay Coordinator."}))
                    return
                command = _staff_command(text)
                transport = HostedTransport(ctx.storage)
                offer = transport.latest(staff_id, command["issue_id"])
                if not offer:
                    raise ValueError("No matching offer was received for this crew identity.")
                if not addresses["coordinator"]:
                    raise ValueError("The hosted coordinator address is not configured.")
                if command["action"] in {"accept", "decline"}:
                    result = VendorDecision(offer_id=offer.offer_id, issue_id=offer.issue_id,
                                            staff_id=staff_id, decision=command["action"], version=offer.version)
                else:
                    result = VendorCommand(issue_id=offer.issue_id, staff_id=staff_id,
                                           action=command["action"], version=command["expected_version"],
                                           evidence=command["evidence"])
                transport.save()
                await ctx.send(addresses["coordinator"], result)
                await ctx.send(sender, _chat_message({"text": "Your crew response was forwarded for issue-state validation."}))
                return
            organizers = {value.strip() for value in str(_setting(ctx, "EVENTRELAY_ORGANIZER_SENDERS")).split(",") if value.strip()}
            actor = _actor(sender, ctx.session, staff_senders, organizers)
            try:
                parsed = json.loads(text)
            except ValueError:
                parsed = None
            intent = parsed if isinstance(parsed, dict) else None
            explicit = re.fullmatch(r"(?:help|roster|tick)|(?:status|accept|decline|start|done|confirm|reopen)(?:\s+ER-[0-9A-F]{8}(?:\s+.*)?)?", text, re.IGNORECASE)
            live = bool(os.environ.get("ASI1_API_KEY", "").strip())
            if intent is None and not explicit and live:
                base = urlsplit(os.environ.get("ASI1_BASE_URL", "https://api.asi1.ai/v1"))
                ctx.logger.info(f"ASI1 configuration: base_host={base.hostname}; base_path={base.path}; key_present=True; hosted_sdk={bool(os.environ.get('ASI1_BASE_URL'))}")
                context_session = open_hosted_service(ctx.storage)
                try:
                    context = context_session.service.context(actor)
                finally:
                    context_session.close()
                intent = await extract_intent_async(text, context)
            # Reload AFTER the LLM await so no stale snapshot can overwrite a
            # staff response or timer mutation that happened during reasoning.
            session = open_hosted_service(ctx.storage)
            try:
                response = session.service.handle(actor, text, intent=intent, request_id=str(msg.msg_id))
                if not live and intent is None:
                    response = {**response, "text": "[Offline command parser; ASI1 is not connected] " + response.get("text", "")}
                transport = HostedTransport(ctx.storage)
                outgoing = _finish(session, transport, response, actor, sender, ctx.session, addresses)
            finally:
                session.close()
            await _deliver(ctx, response, outgoing, sender)
        except ASIError:
            if role != "coordinator":
                await ctx.send(sender, _chat_message({"text": "The AI service is unavailable. Use the coordinator's guided report form."}))
                return
            recovery = open_hosted_service(ctx.storage)
            try:
                response = recovery.service.guided_report(actor, text, request_id=str(msg.msg_id))
                recovery.checkpoint()
            finally:
                recovery.close()
            # This response has a fresh form, never an issue or staff offer.
            await ctx.send(sender, _chat_message(response))
        except ValueError as exc:
            await ctx.send(sender, _chat_message({"text": str(exc)}))
        except Exception as exc:
            ctx.logger.error(f"Hosted event step failed ({type(exc).__name__})")
            await ctx.send(sender, _chat_message({"text": "This event step could not complete. Check status and retry; delivery alone has not accepted or closed an issue."}))

    stage("04 chat handler registered")
    if role == "coordinator":
        @operations.on_message(VendorDecision)
        async def receive_decision(ctx: Context, sender: str, msg: VendorDecision):
            _prepare(ctx)
            transport = HostedTransport(ctx.storage)
            row = transport.match(sender, msg)
            if not row or (msg.simulated and _setting(ctx, "EVENTRELAY_DEMO_MODE", "0") != "1"):
                ctx.logger.warning("Rejected stale or untrusted hosted staff response.")
                return
            session = open_hosted_service(ctx.storage)
            try:
                response = session.service.staff_response(msg.issue_id, msg.staff_id, msg.decision, msg.version)
                transport.state["offers"][msg.offer_id]["processed"] = True
                if msg.simulated:
                    response = {**response, "text": "[Simulated staff response] " + response.get("text", "")}
                outgoing = _finish(session, transport, response, None, None, ctx.session, _addresses(ctx, agent, role))
                origin = transport.state["origins"].get(msg.issue_id)
            finally:
                session.close()
            recipient = origin["recipient"] if origin and origin["session"] == str(ctx.session) else None
            await _deliver(ctx, response, outgoing, recipient)

        stage("05 vendor decision handler registered")
        @operations.on_message(VendorCommand)
        async def receive_progress(ctx: Context, sender: str, msg: VendorCommand):
            _prepare(ctx)
            transport = HostedTransport(ctx.storage)
            origin = transport.command_origin(sender, msg)
            if not origin:
                ctx.logger.warning("Rejected progress without a trusted staff offer.")
                return
            session = open_hosted_service(ctx.storage)
            try:
                intent = {"action": msg.action, "issue_id": msg.issue_id,
                          "expected_version": msg.version, "evidence": msg.evidence}
                response = session.service.handle(msg.staff_id, json.dumps(intent), intent=intent)
                outgoing = _finish(session, transport, response, None, None, ctx.session, _addresses(ctx, agent, role))
            finally:
                session.close()
            recipient = origin["recipient"] if origin["session"] == str(ctx.session) else None
            await _deliver(ctx, response, outgoing, recipient)

        stage("06 progress handler registered")
        @agent.on_interval(period=5.0)
        async def sweep(ctx: Context):
            _prepare(ctx)
            session = open_hosted_service(ctx.storage)
            try:
                session.store.tick(EVENT)
                response = {"offers": session.service.pending_offers()}
                transport = HostedTransport(ctx.storage)
                outgoing = _finish(session, transport, response, None, None, ctx.session, _addresses(ctx, agent, role))
            finally:
                session.close()
            await _deliver(ctx, response, outgoing)
    else:
        @operations.on_message(IssueOffer)
        async def receive_offer(ctx: Context, sender: str, msg: IssueOffer):
            _prepare(ctx)
            coordinator = _addresses(ctx, agent, role)["coordinator"]
            if (not coordinator or sender != coordinator or msg.vendor_group != role
                    or msg.category != CATEGORY[role] or msg.staff_id not in STAFF[role]):
                ctx.logger.warning("Rejected an offer outside the hosted vendor's authority.")
                return
            transport = HostedTransport(ctx.storage)
            transport.receive(msg)
            transport.save()
            decision = _mapping(ctx, "EVENTRELAY_DEMO_DECISIONS").get(msg.staff_id)
            if _setting(ctx, "EVENTRELAY_DEMO_MODE", "0") == "1" and decision in {"accept", "decline"}:
                await ctx.send(sender, VendorDecision(offer_id=msg.offer_id, issue_id=msg.issue_id,
                                                      staff_id=msg.staff_id, decision=decision,
                                                      version=msg.version, simulated=True))

    stage("07 including chat protocol")
    agent.include(chat, publish_manifest=True)
    stage("08 including operations protocol")
    agent.include(operations, publish_manifest=True)
    stage("09 attached successfully")
    return agent
