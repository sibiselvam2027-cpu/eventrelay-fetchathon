import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from uagents_core.contrib.protocols.chat import ChatMessage, MetadataContent, TextContent
from uagents import Agent
from uagents.crypto import Identity
from uagents.dispatch import dispatcher
from eventrelay.fetch_agents import (
    IssueOffer, OfferTransport, VendorDecision, _actor, _chat_message,
    _staff_command, _remove_unused_agents, configure,
)


class FakeAgent:
    def __init__(self, role):
        self.address = f"agent_{role}"
        self.protocols = []

    def on_event(self, event):
        return lambda handler: handler

    def on_interval(self, **kwargs):
        return lambda handler: handler

    def include(self, protocol, **kwargs):
        self.protocols.append(protocol)


class FakeContext:
    def __init__(self):
        self.session = uuid4()
        self.logger = Mock()
        self.sent = []

    async def send(self, recipient, message):
        self.sent.append((recipient, message))


def handler(agent, model):
    digest = model.build_schema_digest(model)
    for protocol in agent.protocols:
        if digest in protocol.signed_message_handlers:
            return protocol.signed_message_handlers[digest]
    raise AssertionError("Handler not registered")


def run_immediate(coroutine):
    """In-memory test handlers do not need Windows' socket-based event loop."""
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    finally:
        coroutine.close()
    raise AssertionError("An in-memory test unexpectedly waited for external I/O")


class FetchTests(unittest.TestCase):
    def setUp(self):
        base = Path(os.environ.get("EVENTRELAY_TEST_TEMP", Path(__file__).resolve().parents[3] / "work" / "eventrelay-tests"))
        base.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "transport.db"
        self.offer = IssueOffer(offer_id="offer_1", issue_id="issue_1", staff_id="staff_neha",
                                category="drinking_water", summary="Water bottles needed",
                                location="Hall A", version=2, vendor_group="hospitality")

    def test_approval_identity_comes_from_transport(self):
        actor = _actor("public_sender", "session_1", {}, set())
        self.assertTrue(actor.startswith("reporter_"))
        self.assertNotEqual(actor, _actor("public_sender", "session_2", {}, set()))
        self.assertEqual(_actor("staff_sender", "s", {"staff_sender": "staff_neha"}, set()), "staff_neha")

    def test_nonrunning_agent_identities_do_not_capture_remote_messages(self):
        # Real SDK Agent objects and its real dispatcher, without constructing
        # a Windows socket event loop. Register the same sinks __init__ adds.
        agents = {}
        for role in ("coordinator", "hospitality", "audio", "facilities", "housekeeping"):
            agent = Agent.__new__(Agent)
            agent._identity = Identity.from_seed(f"eventrelay-dispatch-test-{role}", 0)
            agents[role] = agent
            dispatcher.register(agent.address, agent)
        try:
            self.assertTrue(all(dispatcher.contains(agent.address) for agent in agents.values()))
            _remove_unused_agents("coordinator", agents)
            self.assertTrue(dispatcher.contains(agents["coordinator"].address))
            self.assertTrue(all(not dispatcher.contains(agent.address)
                                for role, agent in agents.items() if role != "coordinator"))
        finally:
            for agent in agents.values():
                if dispatcher.contains(agent.address):
                    dispatcher.unregister(agent.address, agent)

    def test_native_card_metadata_has_sdk_required_string_values(self):
        message = _chat_message({"text": "Confirm resolution", "card": {"kind": "review", "payload": {
            "title": "Confirm", "approve_cta": {"label": "Fixed", "selection": {"action": "confirm", "issue_id": "issue_1"}}}}})
        metadata = next(block.metadata for block in message.content if isinstance(block, MetadataContent))
        self.assertTrue(all(isinstance(value, str) for value in metadata.values()))
        self.assertEqual(json.loads(metadata["card_payload"])["approve_cta"]["selection"]["issue_id"], "issue_1")

    def test_reply_must_match_vendor_issue_staff_and_version(self):
        store = OfferTransport(self.path)
        store.record(self.offer, "vendor_a", "reporter", "actor_1")
        decision = VendorDecision(offer_id="offer_1", issue_id="issue_1", staff_id="staff_neha", decision="accept", version=2)
        self.assertIsNone(store.match("attacker", decision))
        wrong_version = decision.copy(update={"version": 3})
        self.assertIsNone(store.match("vendor_a", wrong_version))
        self.assertIsNotNone(store.match("vendor_a", decision))
        store.processed("offer_1")
        self.assertIsNone(store.match("vendor_a", decision))

    def test_route_and_offer_identity_survive_restart(self):
        first = OfferTransport(self.path)
        first.record(self.offer, "vendor_a", "reporter", "actor_1")
        second = OfferTransport(self.path)
        decision = VendorDecision(offer_id="offer_1", issue_id="issue_1", staff_id="staff_neha", decision="decline", version=2)
        self.assertEqual(second.match("vendor_a", decision)["recipient"], "reporter")
        with self.assertRaises(ValueError):
            second.record(self.offer.copy(update={"staff_id": "staff_arun"}), "vendor_a", "reporter", "actor_1")

    def test_status_reader_cannot_replace_original_notification_route(self):
        store = OfferTransport(self.path)
        store.remember_origin("issue_1", "original_reporter", "reporter_1")
        store.remember_origin("issue_1", "staff_chat", "staff_neha")
        self.assertEqual(store.origin("issue_1")["recipient"], "original_reporter")
        store.record(self.offer, "vendor_a", "original_reporter", "reporter_1")
        store.record(self.offer, "vendor_a", "staff_chat", "staff_neha")
        decision = VendorDecision(offer_id="offer_1", issue_id="issue_1", staff_id="staff_neha", decision="accept", version=2)
        self.assertEqual(store.match("vendor_a", decision)["recipient"], "original_reporter")

    def test_outbox_deduplicates_and_retries_until_a_staff_decision(self):
        store = OfferTransport(self.path)
        store.record(self.offer, "vendor_a", "reporter", "reporter_1")
        self.assertTrue(store.claim_dispatch("offer_1", now=100))
        self.assertFalse(store.claim_dispatch("offer_1", now=101))
        self.assertTrue(OfferTransport(self.path).claim_dispatch("offer_1", now=106))
        store.processed("offer_1")
        self.assertFalse(store.claim_dispatch("offer_1", now=112))

    def test_backup_offer_keeps_reporter_route_after_staff_status(self):
        agents = {role: FakeAgent(role) for role in ("coordinator", "hospitality", "audio", "facilities", "housekeeping")}
        reporter_actor = _actor("original_reporter", "original_session", {}, set())
        service = Mock()
        issue = {"issue_id": "issue_1", "reporter_id": reporter_actor}
        service.handle.return_value = {"text": "Offered", "issue": issue, "offers": [self.offer.dict()]}
        settings = {"EVENTRELAY_TRANSPORT_DB": str(self.path), "EVENTRELAY_DEMO_MODE": "1",
                    "EVENTRELAY_DEMO_DECISIONS": "{}", "EVENTRELAY_STAFF_SENDERS": '{"staff_sender":"staff_neha"}',
                    "EVENTRELAY_ORGANIZER_SENDERS": "", "ASI1_API_KEY": ""}
        with patch.dict(os.environ, settings):
            configure("coordinator", agents, service=service)
            ctx = FakeContext()
            ctx.session = "original_session"
            message = ChatMessage(content=[TextContent(type="text", text='{"action":"report"}')])
            run_immediate(handler(agents["coordinator"], ChatMessage)(ctx, "original_reporter", message))
            backup = self.offer.copy(update={"offer_id": "offer_2", "staff_id": "staff_arun", "version": 3})
            service.handle.return_value = {"text": "Backup offered", "issue": issue, "offers": [backup.dict()]}
            staff_ctx = FakeContext()
            status = ChatMessage(content=[TextContent(type="text", text='{"action":"status","issue_id":"issue_1"}')])
            run_immediate(handler(agents["coordinator"], ChatMessage)(staff_ctx, "staff_sender", status))
        decision = VendorDecision(offer_id="offer_2", issue_id="issue_1", staff_id="staff_arun", decision="accept", version=3)
        route = OfferTransport(self.path).match(agents["hospitality"].address, decision)
        self.assertEqual(route["recipient"], "original_reporter")
        self.assertEqual(route["actor"], reporter_actor)

    def test_coordinator_uses_asi_for_natural_language_with_key(self):
        agents = {role: FakeAgent(role) for role in ("coordinator", "hospitality", "audio", "facilities", "housekeeping")}
        service = Mock()
        service.context.return_value = {"pending_report": None}
        service.handle.return_value = {"text": "Clarify the location", "offers": []}
        intent = {"action": "report", "category": "audio", "location": None}
        settings = {"EVENTRELAY_TRANSPORT_DB": str(self.path), "EVENTRELAY_DEMO_MODE": "1",
                    "EVENTRELAY_DEMO_DECISIONS": "{}", "EVENTRELAY_STAFF_SENDERS": "{}",
                    "EVENTRELAY_ORGANIZER_SENDERS": "", "ASI1_API_KEY": "unit-test-key"}
        with patch.dict(os.environ, settings), \
             patch("eventrelay.asi.extract_intent_async", new=AsyncMock(return_value=intent)) as parse:
            configure("coordinator", agents, service=service)
            ctx = FakeContext()
            message = ChatMessage(content=[TextContent(type="text", text="The microphone suddenly stopped working")])
            run_immediate(handler(agents["coordinator"], ChatMessage)(ctx, "reporter", message))
        parse.assert_awaited_once()
        self.assertEqual(service.handle.call_args.kwargs["intent"], intent)
        self.assertEqual(service.handle.call_args.kwargs["request_id"], str(message.msg_id))

    def test_card_json_preserves_version_and_clarification_id(self):
        agents = {role: FakeAgent(role) for role in ("coordinator", "hospitality", "audio", "facilities", "housekeeping")}
        service = Mock()
        service.handle.return_value = {"text": "Updated", "offers": []}
        selection = {"action": "report", "clarification_id": "request_abc", "version": 4, "category": "audio", "location": "Stage"}
        settings = {"EVENTRELAY_TRANSPORT_DB": str(self.path), "EVENTRELAY_DEMO_MODE": "1",
                    "EVENTRELAY_DEMO_DECISIONS": "{}", "EVENTRELAY_STAFF_SENDERS": "{}",
                    "EVENTRELAY_ORGANIZER_SENDERS": "", "ASI1_API_KEY": "unit-test-key"}
        with patch.dict(os.environ, settings), patch("eventrelay.asi.extract_intent_async", new=AsyncMock()) as parse:
            configure("coordinator", agents, service=service)
            ctx = FakeContext()
            message = ChatMessage(content=[TextContent(type="text", text=json.dumps(selection))])
            run_immediate(handler(agents["coordinator"], ChatMessage)(ctx, "reporter", message))
        parse.assert_not_awaited()
        self.assertEqual(service.handle.call_args.kwargs["intent"], selection)

    def _vendor(self, demo, decisions):
        agents = {role: FakeAgent(role) for role in ("coordinator", "hospitality", "audio", "facilities", "housekeeping")}
        settings = {"EVENTRELAY_TRANSPORT_DB": str(self.path), "EVENTRELAY_DEMO_MODE": demo,
                    "EVENTRELAY_DEMO_DECISIONS": json.dumps(decisions), "EVENTRELAY_STAFF_SENDERS": "{}",
                    "EVENTRELAY_ORGANIZER_SENDERS": ""}
        with patch.dict(os.environ, settings):
            configure("hospitality", agents)
        return agents

    def test_transport_receipt_does_not_accept_an_offer(self):
        agents = self._vendor("0", {"staff_neha": "accept"})
        ctx = FakeContext()
        run_immediate(handler(agents["hospitality"], IssueOffer)(ctx, agents["coordinator"].address, self.offer))
        self.assertEqual(ctx.sent, [])
        self.assertIsNotNone(OfferTransport(self.path).latest("hospitality", "staff_neha", "issue_1"))

    def test_demo_mode_alone_does_not_accept_an_offer(self):
        agents = self._vendor("1", {})
        ctx = FakeContext()
        run_immediate(handler(agents["hospitality"], IssueOffer)(ctx, agents["coordinator"].address, self.offer))
        self.assertEqual(ctx.sent, [])

    def test_explicit_demo_decision_is_labelled_simulated(self):
        agents = self._vendor("1", {"staff_neha": "accept"})
        ctx = FakeContext()
        run_immediate(handler(agents["hospitality"], IssueOffer)(ctx, agents["coordinator"].address, self.offer))
        self.assertEqual(len(ctx.sent), 1)
        self.assertIsInstance(ctx.sent[0][1], VendorDecision)
        self.assertTrue(ctx.sent[0][1].simulated)

    def test_untrusted_coordinator_cannot_inject_staff_offers(self):
        agents = self._vendor("1", {"staff_neha": "accept"})
        ctx = FakeContext()
        run_immediate(handler(agents["hospitality"], IssueOffer)(ctx, "attacker", self.offer))
        self.assertEqual(ctx.sent, [])
        self.assertIsNone(OfferTransport(self.path).latest("hospitality", "staff_neha", "issue_1"))

    def test_staff_payload_cannot_assign_itself_another_staff_identity(self):
        command = _staff_command('{"action":"accept","issue_id":"issue_1","staff_id":"organizer_demo"}')
        self.assertNotIn("staff_id", command)
        with self.assertRaises(ValueError):
            _staff_command("done issue_1")


if __name__ == "__main__":
    unittest.main()
