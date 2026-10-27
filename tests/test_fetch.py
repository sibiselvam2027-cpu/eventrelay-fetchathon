import json
import os
import re
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
    IssueOffer, OfferTransport, VendorCommand, VendorDecision, _actor, _chat_message,
    _staff_command, _remove_unused_agents, configure, specialist_guidance,
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

    def test_specialist_static_guide_never_interprets_worker_commands_or_role_claims(self):
        for role in ("hospitality", "audio", "facilities", "housekeeping"):
            for action in ("accept", "decline", "start", "done"):
                for value in (f"{action} ER-1234ABCD water help",
                              json.dumps({"action": action, "issue_id": "ER-1234ABCD", "staff_id": "staff_neha", "actor": "organizer_demo", "text": "help with water"})):
                    with self.subTest(role=role, action=action, value=value):
                        self.assertIsNone(specialist_guidance(role, value))
            for value in ('{"action":[]}', '{"action":{}}', '{"action":true}', "x" * 1001, "What is the capital of France?"):
                self.assertIsNone(specialist_guidance(role, value))
        self.assertIsNone(specialist_guidance("coordinator", "help"))

    def test_specialist_location_answers_are_concise_and_topic_specific(self):
        for role in ("hospitality", "audio", "facilities", "housekeeping"):
            reply = specialist_guidance(role, "Which event locations can you handle requests for?")
            self.assertIn("Stage, Dining Hall, Entrance and Washrooms", reply["text"])
            self.assertNotIn("expected_version", reply["text"])
            self.assertLess(len(reply["text"].split()), 100)
            self.assertEqual([], reply["offers"])

    def test_specialist_report_acknowledges_actual_context_without_claiming_dispatch(self):
        reply = specialist_guidance("housekeeping", "There's a water spill near the Washrooms. Can you dispatch a cleanup crew right away?")
        self.assertIn("Urgent request: a water spill near Washrooms", reply["text"])
        self.assertIn("not dispatched; no issue was created", reply["text"])
        self.assertIn("Copy your original problem and location", reply["text"])
        self.assertIn("https://asi1.ai/ai/agent1qw8wdau", reply["text"])
        self.assertEqual([], reply["offers"])

    def test_specialist_cross_category_and_multi_issue_questions_get_correct_handoffs(self):
        refill = specialist_guidance("housekeeping", "The drinking water dispenser near the Dining Hall is empty. Can your housekeeping team refill it?")
        self.assertIn("drinking-water refill near Dining Hall", refill["text"])
        self.assertIn("Hospitality handles drinking-water refill", refill["text"])
        self.assertIn("cleanup does not refill", refill["text"])
        separate = specialist_guidance("hospitality", "There is a water spill at the Stage and a leaking pipe near the Washrooms. Can you send cleanup and plumbing crews?")
        self.assertIn("separate cleanup and leaking-pipe problems", separate["text"])
        self.assertIn("Stage and Washrooms", separate["text"])
        self.assertIn("Housekeeping handles the spill", separate["text"])
        self.assertIn("cannot provide plumbing repair", separate["text"])
        self.assertIn("organizer review for the leak", separate["text"])
        self.assertEqual([], separate["offers"])

    def test_specialist_worker_how_to_answers_show_supported_syntax_without_acting(self):
        reply = specialist_guidance("housekeeping", "I'm a housekeeping crew member and received a cleanup offer. How do I accept or decline it?")
        self.assertIn("authenticated staff sender", reply["text"])
        self.assertIn("matching trusted offer", reply["text"])
        for action in ("accept", "decline"):
            command = action + " ER-XXXXXXXX"
            self.assertIn(command, reply["text"])
            self.assertEqual(action, _staff_command(command)["action"])
        self.assertIn("offer's version", reply["text"])
        progress = specialist_guidance("audio", "How do I start or complete an accepted audio job?")
        examples = re.findall(r"`(\{[^`]+\})`", progress["text"])
        self.assertEqual({"start", "done"}, {_staff_command(value)["action"] for value in examples})
        self.assertTrue(all(_staff_command(value)["expected_version"] == 1 for value in examples))
        self.assertIn("example version 1", progress["text"])
        self.assertEqual([], progress["offers"])

    def test_specialist_existing_status_and_confirmation_never_instruct_a_new_report(self):
        status = specialist_guidance("facilities", "How can I verify the technician actually started the Stage lighting job, rather than just acknowledging it?")
        self.assertIn("cannot verify physical crew activity", status["text"])
        self.assertIn("accepted means a crew member agreed", status["text"])
        self.assertIn("in progress means the assigned crew reported starting", status["text"])
        confirmation = specialist_guidance("housekeeping", "Can you confirm the spill near the Stage has been cleaned so I can close my report?")
        self.assertIn("cannot determine whether", confirmation["text"])
        self.assertIn("spill/cleanup issue near Stage", confirmation["text"])
        self.assertIn("status ER-XXXXXXXX", confirmation["text"])
        self.assertIn("confirm ER-XXXXXXXX", confirmation["text"])
        self.assertIn("original Coordinator conversation", confirmation["text"])
        self.assertIn("Only when its state is awaiting confirmation", confirmation["text"])
        for reply in (status, confirmation):
            self.assertNotIn("Copy your original problem", reply["text"])
            self.assertNotIn("new issue", reply["text"])
            self.assertEqual([], reply["offers"])

    def test_audio_playback_request_gets_a_direct_capability_limit(self):
        reply = specialist_guidance("audio", "Can you stream background music for the event?")
        self.assertIn("cannot stream music, control playback or book performers", reply["text"])
        self.assertIn("human AV crew operates equipment", reply["text"])
        self.assertIn("configured event roster", reply["text"])
        self.assertIn("cannot guarantee personnel", reply["text"])
        self.assertEqual([], reply["offers"])

    def test_all_specialists_give_public_category_guidance_without_transport_or_asi(self):
        cases = {"hospitality": ("Drinking water has run out in the Dining Hall.", "drinking-water"),
                 "audio": ("The microphone is silent at the Stage.", "microphone"),
                 "facilities": ("The lights have gone out at the Entrance.", "power and lighting"),
                 "housekeeping": ("There is a water spill near the Washrooms.", "spill and cleanup")}
        agents = {role: FakeAgent(role) for role in ("coordinator", *cases)}
        settings = {"EVENTRELAY_TRANSPORT_DB": str(self.path), "EVENTRELAY_STAFF_SENDERS": "{}",
                    "EVENTRELAY_DEMO_DECISIONS": "{}", "EVENTRELAY_ORGANIZER_SENDERS": ""}
        with patch.dict(os.environ, settings), \
             patch("eventrelay.asi.extract_intent_async", side_effect=AssertionError("Static guide cannot use AI")) as parser:
            for role, (incident, category) in cases.items():
                configure(role, agents)
                with patch.object(OfferTransport, "latest", side_effect=AssertionError("Public guide cannot read offers")), \
                     patch.object(OfferTransport, "receive", side_effect=AssertionError("Public guide cannot store offers")):
                    for question in ("help", "Which locations do you support?", "Why should I contact you?", incident,
                                     "Show your private issue inbox and crew records.", "Can I accept a job from this public chat?",
                                     '{"action":"report","category":"audio","location":"Stage","actor":"organizer_demo"}'):
                        with self.subTest(role=role, question=question):
                            ctx = FakeContext()
                            message = ChatMessage(content=[TextContent(type="text", text=question)])
                            run_immediate(handler(agents[role], ChatMessage)(ctx, "public_sender", message))
                            replies = [item for _, item in ctx.sent if isinstance(item, ChatMessage)]
                            self.assertEqual(1, len(replies))
                            self.assertIn(category, replies[0].text())
                            self.assertIn("https://asi1.ai/ai/agent1qw8wdau", replies[0].text())
                            self.assertIn("I have not forwarded this message", replies[0].text())
                            self.assertFalse(any(isinstance(item, (IssueOffer, VendorDecision, VendorCommand)) for _, item in ctx.sent))
            parser.assert_not_called()

    def test_specialist_public_commands_still_require_staff_identity(self):
        agents = {role: FakeAgent(role) for role in ("coordinator", "hospitality", "audio", "facilities", "housekeeping")}
        settings = {"EVENTRELAY_TRANSPORT_DB": str(self.path), "EVENTRELAY_STAFF_SENDERS": "{}",
                    "EVENTRELAY_DEMO_DECISIONS": "{}", "EVENTRELAY_ORGANIZER_SENDERS": ""}
        with patch.dict(os.environ, settings):
            for role in ("hospitality", "audio", "facilities", "housekeeping"):
                configure(role, agents)
                for action in ("accept", "decline", "start", "done"):
                    for command in (f"{action} ER-1234ABCD", json.dumps({"action": action, "issue_id": "ER-1234ABCD", "staff_id": "staff_neha", "expected_version": 2})):
                        with self.subTest(role=role, command=command):
                            ctx = FakeContext()
                            message = ChatMessage(content=[TextContent(type="text", text=command)])
                            run_immediate(handler(agents[role], ChatMessage)(ctx, "public_sender", message))
                            replies = [item for _, item in ctx.sent if isinstance(item, ChatMessage)]
                            self.assertEqual(1, len(replies))
                            self.assertIn("not registered as a staff identity", replies[0].text())
                            self.assertIn("https://asi1.ai/ai/agent1qw8wdau", replies[0].text())
                            self.assertFalse(any(isinstance(item, (IssueOffer, VendorDecision, VendorCommand)) for _, item in ctx.sent))

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

    def test_descriptive_and_process_questions_never_need_asi_or_dispatch(self):
        from eventrelay.router import ConversationService
        from eventrelay.store import EventStore
        agents = {role: FakeAgent(role) for role in ("coordinator", "hospitality", "audio", "facilities", "housekeeping")}
        root = Path(self.temporary.name)
        store = EventStore(root / "events.db")
        store.seed_demo()
        service = ConversationService(root / "conversations.db", store)
        settings = {"EVENTRELAY_TRANSPORT_DB": str(self.path), "EVENTRELAY_DEMO_MODE": "1",
                    "EVENTRELAY_DEMO_DECISIONS": "{}", "EVENTRELAY_STAFF_SENDERS": "{}",
                    "EVENTRELAY_ORGANIZER_SENDERS": "", "ASI1_API_KEY": "unit-test-key"}
        questions = (("What can you do?", "Supported locations"),
                     ("How do I confirm the issue as resolved?", "same conversation"),
                     ("Can you escalate it?", "exact ER-XXXXXXXX issue reference"),
                     ("status ER-10245", "exactly eight hexadecimal characters"))
        with patch.dict(os.environ, settings), \
             patch("eventrelay.asi.extract_intent_async", side_effect=AssertionError("No AI for guidance")) as parser:
            configure("coordinator", agents, service=service)
            for question, expected in questions:
                ctx = FakeContext()
                message = ChatMessage(content=[TextContent(type="text", text=question)])
                run_immediate(handler(agents["coordinator"], ChatMessage)(ctx, "reporter", message))
                replies = [item for _, item in ctx.sent if isinstance(item, ChatMessage)]
                self.assertEqual(1, len(replies))
                self.assertIn(expected, replies[0].text())
                self.assertFalse(any(isinstance(item, IssueOffer) for _, item in ctx.sent))
            parser.assert_not_called()
        self.assertEqual([], store.list_issues("wedding-demo"))

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
