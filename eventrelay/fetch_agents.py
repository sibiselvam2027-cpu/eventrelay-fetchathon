"""Five real uAgents for event reports and explicitly acknowledged staff offers.

Transport delivery never counts as a staff acceptance. Automated decisions are
available only in explicitly labelled demo mode with a configured staff choice.
"""

import argparse
import asyncio
from contextlib import contextmanager
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import sqlite3
import time
from typing import Literal

from uagents import Agent, Context, Model, Protocol
from uagents.dispatch import dispatcher
from uagents.resolver import RulesBasedResolver
from uagents_core.registration import AgentRegistrationPolicy
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement, ChatMessage, MetadataContent, TextContent, chat_protocol_spec,
)
from eventrelay.asi import ASIError


class IssueOffer(Model):
    offer_id: str
    issue_id: str
    staff_id: str
    category: str
    summary: str
    location: str
    version: int
    vendor_group: Literal["hospitality", "audio", "facilities", "housekeeping"]


class VendorDecision(Model):
    offer_id: str
    issue_id: str
    staff_id: str
    decision: Literal["accept", "decline"]
    version: int
    simulated: bool = False


class VendorCommand(Model):
    issue_id: str
    staff_id: str
    action: Literal["start", "done"]
    version: int
    evidence: str = ""


class _LocalRegistration(AgentRegistrationPolicy):
    """Explicit local-test mode does not register agents on a public network."""

    async def register(self, agent_identifier, identity, protocols, endpoints, metadata=None):
        return None


class OfferTransport:
    """Durable expected-sender binding for replies and their original ASI route."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS transport_offers (
                offer_id TEXT PRIMARY KEY, payload TEXT NOT NULL,
                expected_sender TEXT NOT NULL, recipient TEXT NOT NULL,
                actor TEXT NOT NULL, processed INTEGER NOT NULL DEFAULT 0,
                sent_at REAL NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS vendor_inbox (
                role TEXT NOT NULL, offer_id TEXT NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY(role,offer_id)
            );
            CREATE TABLE IF NOT EXISTS issue_origins (
                issue_id TEXT PRIMARY KEY, recipient TEXT NOT NULL, actor TEXT NOT NULL
            );
            """)
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(transport_offers)")}
            if "sent_at" not in columns:
                conn.execute("ALTER TABLE transport_offers ADD COLUMN sent_at REAL NOT NULL DEFAULT 0")

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def remember_origin(self, issue_id: str, recipient: str, actor: str) -> None:
        with self._connection() as conn:
            conn.execute("INSERT OR IGNORE INTO issue_origins(issue_id,recipient,actor) VALUES(?,?,?)",
                         (issue_id, recipient, actor))

    def origin(self, issue_id: str) -> dict | None:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM issue_origins WHERE issue_id=?", (issue_id,)).fetchone()
        return dict(row) if row else None

    def record(self, offer: IssueOffer, expected_sender: str, recipient: str, actor: str) -> None:
        payload = json.dumps(offer.dict(), sort_keys=True)
        with self._connection() as conn:
            existing = conn.execute("SELECT * FROM transport_offers WHERE offer_id=?", (offer.offer_id,)).fetchone()
            if existing:
                if (existing["payload"], existing["expected_sender"]) != (payload, expected_sender):
                    raise ValueError("An existing offer cannot change its transport identity.")
                if not existing["recipient"] and recipient:
                    conn.execute("UPDATE transport_offers SET recipient=?,actor=? WHERE offer_id=?",
                                 (recipient, actor, offer.offer_id))
                return
            conn.execute("INSERT INTO transport_offers(offer_id,payload,expected_sender,recipient,actor) VALUES(?,?,?,?,?)",
                         (offer.offer_id, payload, expected_sender, recipient, actor))

    def match(self, sender: str, decision: VendorDecision) -> dict | None:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM transport_offers WHERE offer_id=?", (decision.offer_id,)).fetchone()
        if not row or row["processed"] or row["expected_sender"] != sender:
            return None
        offer = json.loads(row["payload"])
        if (offer["issue_id"], offer["staff_id"], offer["version"]) != (
                decision.issue_id, decision.staff_id, decision.version):
            return None
        return dict(row)

    def processed(self, offer_id: str) -> None:
        with self._connection() as conn:
            conn.execute("UPDATE transport_offers SET processed=1 WHERE offer_id=?", (offer_id,))

    def claim_dispatch(self, offer_id: str, now: float | None = None) -> bool:
        """Send once, then retry unresolved offers at most once every five seconds."""
        timestamp = time.time() if now is None else now
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT processed,sent_at FROM transport_offers WHERE offer_id=?", (offer_id,)).fetchone()
            if not row or row["processed"] or (row["sent_at"] and timestamp - row["sent_at"] < 5):
                return False
            conn.execute("UPDATE transport_offers SET sent_at=? WHERE offer_id=?", (timestamp, offer_id))
        return True

    def command_route(self, sender: str, command: VendorCommand) -> dict | None:
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM transport_offers WHERE expected_sender=? ORDER BY rowid DESC", (sender,)).fetchall()
        for row in rows:
            offer = json.loads(row["payload"])
            if offer["issue_id"] == command.issue_id and offer["staff_id"] == command.staff_id:
                return dict(row)
        return None

    def receive(self, role: str, offer: IssueOffer) -> None:
        payload = json.dumps(offer.dict(), sort_keys=True)
        with self._connection() as conn:
            row = conn.execute("SELECT payload FROM vendor_inbox WHERE role=? AND offer_id=?", (role, offer.offer_id)).fetchone()
            if row and row["payload"] != payload:
                raise ValueError("An existing vendor offer cannot be overwritten.")
            conn.execute("INSERT OR IGNORE INTO vendor_inbox(role,offer_id,payload) VALUES(?,?,?)", (role, offer.offer_id, payload))

    def latest(self, role: str, staff_id: str, issue_id: str) -> IssueOffer | None:
        with self._connection() as conn:
            rows = conn.execute("SELECT payload FROM vendor_inbox WHERE role=? ORDER BY rowid DESC", (role,)).fetchall()
        for row in rows:
            data = json.loads(row["payload"])
            if data["staff_id"] == staff_id and data["issue_id"] == issue_id:
                return IssueOffer(**data)
        return None


def _json_setting(name: str) -> dict:
    try:
        value = json.loads(os.environ.get(name, "{}"))
    except ValueError:
        raise RuntimeError(f"{name} must be a JSON object.") from None
    if not isinstance(value, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in value.items()):
        raise RuntimeError(f"{name} must map strings to strings.")
    return value


def _actor(sender: str, session, staff_senders: dict[str, str], organizer_senders: set[str]) -> str:
    if sender in organizer_senders:
        return "organizer_demo"
    if sender in staff_senders:
        return staff_senders[sender]
    digest = hashlib.sha256(f"{sender}:{session}".encode()).hexdigest()[:16]
    return f"reporter_{digest}"


def _chat_message(response: dict) -> ChatMessage:
    content = [TextContent(type="text", text=str(response.get("text", "Event status updated.")))]
    card = response.get("card")
    if card:
        kind = card.get("kind")
        payload = json.dumps(card.get("payload"), separators=(",", ":"))
        if kind in {"form", "carousel", "detail", "review", "custom"} and len(payload.encode()) <= 64_000:
            content.append(MetadataContent(type="metadata", metadata={
                "card_protocol_version": "1", "requires_card_interaction": "true",
                "card_kind": kind, "card_payload": payload,
            }))
    return ChatMessage(content=content)


async def _resolve(value):
    return await value if inspect.isawaitable(value) else value


def _staff_command(text: str) -> dict:
    """Read direct staff JSON or compact commands; identity never comes from text."""
    try:
        data = json.loads(text)
    except ValueError:
        match = re.fullmatch(r"(accept|decline|start|done)\s+(\S+)(?:\s+(.+))?", text.strip(), re.IGNORECASE)
        if not match:
            raise ValueError("Use accept ISSUE_ID, decline ISSUE_ID, start ISSUE_ID or done ISSUE_ID evidence.") from None
        data = {"action": match.group(1).lower(), "issue_id": match.group(2), "evidence": match.group(3) or ""}
    if not isinstance(data, dict) or data.get("action") not in {"accept", "decline", "start", "done"}:
        raise ValueError("Only staff acceptance and progress commands are supported here.")
    issue_id = data.get("issue_id")
    if not isinstance(issue_id, str) or not issue_id or len(issue_id) > 100:
        raise ValueError("Include the exact issue ID from the offer.")
    version = data.get("expected_version")
    if data["action"] in {"start", "done"} and (type(version) is not int or version < 1):
        raise ValueError("For progress, send JSON with action, issue_id and the latest expected_version from the issue status.")
    return {"action": data["action"], "issue_id": issue_id, "expected_version": version,
            "evidence": str(data.get("evidence", ""))[:1000]}


def _build_agents(master_seed: str) -> dict[str, Agent]:
    descriptions = {
        "coordinator": "EventRelay: report event problems, clarify location, route staff offers, track acceptance, escalation and reporter-confirmed closure inside ASI:One.",
        "hospitality": "EventRelay hospitality service: receive drinking-water offers and relay authorized staff decisions; delivery acknowledgements are never acceptance.",
        "audio": "EventRelay audio service: receive microphone, speaker and projector offers and relay authorized staff acceptance and progress.",
        "facilities": "EventRelay facilities service: receive power and electrical issue offers and relay authorized staff acceptance and progress.",
        "housekeeping": "EventRelay housekeeping service: receive cleanup offers and relay authorized staff acceptance and progress.",
    }
    local = os.environ.get("EVENTRELAY_LOCAL_MODE", "0") == "1"
    rules = _json_setting("EVENTRELAY_LOCAL_ROUTES") if local else {}
    resolver = RulesBasedResolver(rules) if local else None
    result = {}
    for role, port in (("coordinator", 8101), ("hospitality", 8102), ("audio", 8103), ("facilities", 8104), ("housekeeping", 8105)):
        seed = hashlib.sha256(f"{master_seed}:{role}".encode()).hexdigest()
        actual_port = int(os.environ.get(f"EVENTRELAY_{role.upper()}_PORT", str(port)))
        result[role] = Agent(name=f"EventRelay {role.title()}", seed=seed,
                             port=actual_port,
                             mailbox=not local, publish_agent_details=not local,
                             endpoint=[f"http://127.0.0.1:{actual_port}/submit"] if local else None,
                             resolve=resolver,
                             registration_policy=_LocalRegistration() if local else None,
                             description=descriptions[role],
                             handle=os.environ.get(f"EVENTRELAY_{role.upper()}_HANDLE") or None)
        if local:
            rules[result[role].address] = f"http://127.0.0.1:{actual_port}/submit"
    return result


def _remove_unused_agents(role: str, agents: dict[str, Agent]) -> None:
    """Keep only this process's running agent in the SDK's local dispatcher.

    Agent construction registers a local sink immediately. Leaving the other
    identities registered makes Context.send queue messages at their unrun
    objects instead of resolving the actual HTTP endpoint or mailbox.
    """
    for name, item in agents.items():
        if name != role and isinstance(item, Agent) and dispatcher.contains(item.address):
            dispatcher.unregister(item.address, item)


def configure(role: str, agents: dict[str, Agent], service=None):
    """Attach protocols without starting agents or modifying external accounts."""
    agent = agents[role]
    _remove_unused_agents(role, agents)
    addresses = {name: item.address for name, item in agents.items()}
    staff_senders = _json_setting("EVENTRELAY_STAFF_SENDERS")
    organizer_senders = {s.strip() for s in os.environ.get("EVENTRELAY_ORGANIZER_SENDERS", "").split(",") if s.strip()}
    decisions = _json_setting("EVENTRELAY_DEMO_DECISIONS")
    if any(value not in {"accept", "decline"} for value in decisions.values()):
        raise RuntimeError("EVENTRELAY_DEMO_DECISIONS values must be accept or decline.")
    demo = os.environ.get("EVENTRELAY_DEMO_MODE", "0") == "1"
    from eventrelay.settings import local_path
    transport = OfferTransport(local_path("EVENTRELAY_TRANSPORT_DB", "data/transport.db"))
    if role == "coordinator" and service is None:
        from eventrelay.store import EventStore
        from eventrelay.router import ConversationService
        store = EventStore(local_path("EVENTRELAY_DB", "data/eventrelay.db"))
        if demo:
            store.seed_demo()
        service = ConversationService(local_path("EVENTRELAY_STATE_DB", "data/conversations.db"), store)
    chat = Protocol(spec=chat_protocol_spec)
    operations = Protocol(name="EventRelayOffers", version="1.0.0")
    response_lock = asyncio.Lock()

    async def send_response(ctx: Context, recipient: str | None, actor: str | None, response: dict):
        if recipient:
            await ctx.send(recipient, _chat_message(response))
        issues = ([response["issue"]] if response.get("issue") else []) + response.get("issues", [])
        for issue in issues:
            if recipient and actor and issue.get("reporter_id") == actor:
                transport.remember_origin(issue["issue_id"], recipient, actor)
        for data in response.get("offers", []):
            offer = IssueOffer(**data)
            vendor = addresses[offer.vendor_group]
            origin = transport.origin(offer.issue_id) or {"recipient": "", "actor": ""}
            transport.record(offer, vendor, origin["recipient"], origin["actor"])
            if transport.claim_dispatch(offer.offer_id):
                await ctx.send(vendor, offer)

    @agent.on_event("startup")
    async def startup(ctx: Context):
        ctx.logger.info(f"EventRelay {role} running at {agent.address}")
        if os.environ.get("EVENTRELAY_LOCAL_MODE", "0") == "1":
            ctx.logger.info("LOCAL transport test: Agentverse registration and ASI discovery are disabled.")
        ctx.logger.info("DEMO staff decisions enabled." if demo else "Staff offers require an authenticated explicit response.")

    if role == "coordinator":
        @agent.on_interval(period=2.0)
        async def sweep_offers(ctx: Context):
            try:
                from eventrelay.router import EVENT
                await _resolve(service.store.tick(EVENT))
                offers = await _resolve(service.pending_offers())
                # Timer checks update persistent issue state and dispatch offers.
                # Reporter-facing timer changes are shown by their next status
                # request; this does not claim verified unsolicited ASI push.
                await send_response(ctx, None, None, {"offers": offers})
            except Exception as exc:
                ctx.logger.error(f"Follow-up sweep failed ({type(exc).__name__})")

    @chat.on_message(ChatAcknowledgement)
    async def ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
        pass

    @chat.on_message(ChatMessage)
    async def receive_chat(ctx: Context, sender: str, msg: ChatMessage):
        await ctx.send(sender, ChatAcknowledgement(acknowledged_msg_id=msg.msg_id))
        text = "\n".join(block.text for block in msg.content if isinstance(block, TextContent)).strip()
        if not text:
            return
        try:
            if role == "coordinator":
                actor = _actor(sender, ctx.session, staff_senders, organizer_senders)
                try:
                    direct = json.loads(text)
                except ValueError:
                    direct = None
                explicit = re.fullmatch(r"(?:help|roster|tick)|(?:status|accept|decline|start|done|confirm|reopen)(?:\s+ER-[0-9A-F]{8}(?:\s+.*)?)?", text, re.IGNORECASE)
                intent = direct if isinstance(direct, dict) else None
                live_key = bool(os.environ.get("ASI1_API_KEY", "").strip())
                if intent is None and not explicit and live_key:
                    from eventrelay.asi import extract_intent_async
                    intent = await extract_intent_async(text, service.context(actor))
                response = await _resolve(service.handle(actor, text, intent=intent, request_id=str(msg.msg_id)))
                if not live_key and intent is None:
                    response = {**response, "text": "[Offline command parser; ASI1 is not connected] " + response.get("text", "")}
                await send_response(ctx, sender, actor, response)
                return
            staff_id = staff_senders.get(sender)
            if not staff_id:
                await ctx.send(sender, _chat_message({"text": (
                    f"EventRelay {role} receives staff offers. This chat is not registered "
                    "as a staff identity. Report issues through EventRelay Coordinator."
                )}))
                return
            command = _staff_command(text)
            offer = transport.latest(role, staff_id, command["issue_id"])
            if not offer:
                raise ValueError("No offer for this staff identity and issue was received here.")
            if command["action"] in {"accept", "decline"}:
                message = VendorDecision(offer_id=offer.offer_id, issue_id=offer.issue_id,
                                         staff_id=staff_id, decision=command["action"], version=offer.version)
            else:
                message = VendorCommand(issue_id=offer.issue_id, staff_id=staff_id,
                                        action=command["action"], version=command["expected_version"],
                                        evidence=command["evidence"])
            await ctx.send(addresses["coordinator"], message)
            await ctx.send(sender, _chat_message({"text": "Your staff response was forwarded for issue-state validation."}))
        except ASIError as exc:
            await ctx.send(sender, _chat_message({"text": str(exc)}))
        except ValueError as exc:
            await ctx.send(sender, _chat_message({"text": str(exc)}))
        except Exception as exc:
            ctx.logger.error(f"Event chat step failed ({type(exc).__name__})")
            await ctx.send(sender, _chat_message({"text": "This event step could not complete. Check status and retry; delivery alone has not accepted or closed the issue."}))

    if role == "coordinator":
        @operations.on_message(VendorDecision)
        async def staff_decision(ctx: Context, sender: str, msg: VendorDecision):
            async with response_lock:
                route = transport.match(sender, msg)
                if not route or (msg.simulated and not demo):
                    ctx.logger.warning("Rejected untrusted, stale or mismatched staff decision.")
                    return
                response = await _resolve(service.staff_response(msg.issue_id, msg.staff_id, msg.decision, msg.version))
                transport.processed(msg.offer_id)
                if msg.simulated:
                    response = {**response, "text": "[Simulated staff response] " + response.get("text", "")}
                await send_response(ctx, route["recipient"] or None, route["actor"] or None, response)

        @operations.on_message(VendorCommand)
        async def staff_progress(ctx: Context, sender: str, msg: VendorCommand):
            route = transport.command_route(sender, msg)
            if not route:
                ctx.logger.warning("Rejected progress from an unexpected vendor or staff identity.")
                return
            # The worker's authenticated staff identity, not a supplied actor in
            # prose, determines who may change the issue's current state.
            intent = {"action": msg.action, "issue_id": msg.issue_id,
                      "evidence": msg.evidence, "expected_version": msg.version}
            response = await _resolve(service.handle(msg.staff_id, json.dumps(intent), intent=intent))
            await send_response(ctx, route["recipient"] or None, route["actor"] or None, response)

    else:
        @operations.on_message(IssueOffer)
        async def vendor_offer(ctx: Context, sender: str, msg: IssueOffer):
            if sender != addresses["coordinator"] or msg.vendor_group != role:
                ctx.logger.warning("Rejected an offer from an unexpected coordinator or vendor group.")
                return
            transport.receive(role, msg)
            ctx.logger.info(f"Offer {msg.offer_id} received for {msg.staff_id}; awaiting explicit staff decision.")
            decision = decisions.get(msg.staff_id) if demo else None
            if decision:
                # This is an explicitly configured simulator decision, not an
                # inference from transport success or an unlabelled real person.
                await ctx.send(sender, VendorDecision(offer_id=msg.offer_id, issue_id=msg.issue_id,
                                                      staff_id=msg.staff_id, decision=decision,
                                                      version=msg.version, simulated=True))

    agent.include(chat, publish_manifest=True)
    agent.include(operations, publish_manifest=True)
    return agent


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EventRelay agents independently")
    parser.add_argument("role", choices=("coordinator", "hospitality", "audio", "facilities", "housekeeping", "addresses"))
    args = parser.parse_args()
    from eventrelay.settings import load_environment
    load_environment()
    seed = os.environ.get("EVENTRELAY_AGENT_SEED", "").strip()
    if len(seed) < 20:
        raise SystemExit("Set a private EVENTRELAY_AGENT_SEED of at least 20 characters in .env.")
    agents = _build_agents(seed)
    if args.role == "addresses":
        print(json.dumps({name: item.address for name, item in agents.items()}, indent=2))
        return
    configure(args.role, agents).run()


if __name__ == "__main__":
    main()
