import asyncio
import json
import os
import unittest
from unittest.mock import Mock, patch

from uagents_core.contrib.protocols.chat import ChatMessage, TextContent
from eventrelay.fetch_agents import IssueOffer, VendorCommand, VendorDecision
from eventrelay.hosted_runtime import HostedTransport, TRANSPORT_KEY, attach, _finish, _send, _without_own_leading_mention
from eventrelay.hosted_state import HostedSession, HostedStateError, STORAGE_KEY, open_hosted_service
from eventrelay.asi import ASIError
from eventrelay.fetch_agents import _actor


class MemoryStorage:
    def __init__(self):
        self.values = {}

    def get(self, key):
        value = self.values.get(key)
        return json.loads(json.dumps(value)) if value is not None else None

    def set(self, key, value):
        self.values[key] = json.loads(json.dumps(value))


class HostAgent:
    def __init__(self, role):
        self.address = "agent_" + role
        self.protocols = []
        self.intervals = []

    def include(self, protocol, **kwargs):
        self.protocols.append(protocol)

    def on_interval(self, **kwargs):
        def register(callback):
            self.intervals.append(callback)
            return callback
        return register


class HostContext:
    def __init__(self, storage, session="original-session"):
        self.storage = storage
        self.session = session
        self.logger = Mock()
        self.sent = []
        self.network_timeouts = []

    async def send(self, recipient, message, timeout=30):
        self.network_timeouts.append(timeout)
        if isinstance(message, IssueOffer):
            # Checkpoint must already be durable when an offer leaves the agent.
            session = open_hosted_service(self.storage)
            try:
                issue = session.store.issue(message.issue_id)
                assert issue["version"] == message.version
                outbox = self.storage.get(TRANSPORT_KEY)
                assert outbox["offers"][message.offer_id]["sent_at"] > 0
            finally:
                session.close()
        self.sent.append((recipient, message))


def immediate(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as value:
        return value.value
    finally:
        coroutine.close()
    raise AssertionError("An in-memory hosted test unexpectedly awaited external I/O")


def callback(agent, model):
    digest = model.build_schema_digest(model)
    for protocol in agent.protocols:
        if digest in protocol.signed_message_handlers:
            return protocol.signed_message_handlers[digest]
    raise AssertionError("Missing protocol handler")


class HostedRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.settings = {"EVENTRELAY_DEMO_MODE": "1", "EVENTRELAY_STAFF_SENDERS": "{}",
                         "EVENTRELAY_ORGANIZER_SENDERS": "", "ASI1_API_KEY": "",
                         "EVENTRELAY_DEMO_DECISIONS": '{"staff_arun":"decline","staff_neha":"accept"}'}
        for role in ("coordinator", "hospitality", "audio", "facilities", "housekeeping"):
            self.settings[f"EVENTRELAY_{role.upper()}_ADDRESS"] = "agent_" + role
        self.environment = patch.dict(os.environ, self.settings)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        async def no_socket_timeout(awaitable, timeout):
            return await awaitable
        self.timeouts = patch("eventrelay.hosted_runtime._with_timeout", new=no_socket_timeout)
        self.timeouts.start()
        self.addCleanup(self.timeouts.stop)
        async def no_socket_gather(*awaitables):
            return [await item for item in awaitables]
        self.gather = patch("eventrelay.hosted_runtime.asyncio.gather", new=no_socket_gather)
        self.gather.start()
        self.addCleanup(self.gather.stop)

    def agent(self, role):
        return attach(HostAgent(role), role)

    def test_transport_noop_does_not_flush_cached_storage_and_real_changes_save_once(self):
        shared = {STORAGE_KEY: "accepted-v3"}
        class CachedStorage:
            def __init__(self):
                self.cache = dict(shared)
                self.writes = 0
            def get(self, key):
                return json.loads(json.dumps(self.cache.get(key)))
            def set(self, key, value):
                self.cache[key] = value
                shared.clear()
                shared.update(json.loads(json.dumps(self.cache)))
                self.writes += 1
        cached = CachedStorage()
        reader = HostedTransport(cached)
        shared[STORAGE_KEY] = "in-progress-v4"
        self.assertFalse(reader.save())
        self.assertEqual(0, cached.writes)
        self.assertEqual("in-progress-v4", shared[STORAGE_KEY])

        storage = MemoryStorage()
        transport = HostedTransport(storage)
        offer = IssueOffer(offer_id="o1", issue_id="ER-1234ABCD", staff_id="staff_ravi", category="audio",
                           summary="Mic silent", location="Stage", version=2, vendor_group="audio").dict()
        with patch.object(storage, "set", wraps=storage.set) as writes:
            self.assertFalse(transport.save())
            transport.capture({"offers": [offer]}, None, None, "session", {"audio": "agent_audio"})
            self.assertTrue(transport.save())
            self.assertFalse(transport.save())
            self.assertEqual(1, len(transport.claim([offer], now=100)))
            self.assertTrue(transport.save())
            self.assertEqual([], transport.claim([offer], now=101))
            self.assertFalse(transport.save())
            transport.state["offers"]["o1"]["processed"] = True
            self.assertTrue(transport.save())
            self.assertFalse(transport.save())
            self.assertEqual(3, writes.call_count)
        self.assertTrue(storage.get(TRANSPORT_KEY)["offers"]["o1"]["processed"])

    def test_transport_real_address_migration_is_saved_only_once(self):
        storage = MemoryStorage()
        storage.values[TRANSPORT_KEY] = {"origins": {"i1": {"recipient": "reporter\r"}}, "inbox": {},
            "offers": {"o1": {"expected_sender": "agent_audio\r\n", "recipient": "reporter\r", "processed": False}}}
        with patch.object(storage, "set", wraps=storage.set) as writes:
            transport = HostedTransport(storage)
            self.assertTrue(transport.save())
            self.assertFalse(transport.save())
            self.assertFalse(HostedTransport(storage).save())
            self.assertEqual(1, writes.call_count)
        self.assertEqual("agent_audio", storage.get(TRANSPORT_KEY)["offers"]["o1"]["expected_sender"])
        self.assertFalse(storage.get(TRANSPORT_KEY)["offers"]["o1"]["processed"])

    def test_rejected_chat_checkpoint_never_commits_outbox_or_uses_ai_fallback(self):
        storage = MemoryStorage()
        ctx = HostContext(storage)
        message = ChatMessage(content=[TextContent(type="text", text=json.dumps({
            "action": "report", "category": "audio", "location": "Stage", "summary": "Mic silent"}))])
        private = "PRIVATE-SNAPSHOT-CONTENT"
        with patch.object(HostedSession, "checkpoint", side_effect=HostedStateError("stale_snapshot", private)), \
             patch("eventrelay.hosted_runtime.extract_intent_async", side_effect=AssertionError("No fallback AI")), \
             patch.object(storage, "set", wraps=storage.set) as writes:
            immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", message))
            writes.assert_not_called()
        replies = [item.text() for _, item in ctx.sent if isinstance(item, ChatMessage)]
        self.assertEqual(1, len(replies))
        self.assertIn("Check status and retry", replies[0])
        self.assertNotIn("manual guided", replies[0])
        self.assertNotIn(private, replies[0])
        self.assertEqual({}, storage.values)
        self.assertFalse(any(isinstance(item, (IssueOffer, VendorDecision, VendorCommand)) for _, item in ctx.sent))
        self.assertNotIn(private, str(ctx.logger.method_calls))

    def test_rejected_vendor_checkpoint_preserves_processing_and_progress_state(self):
        storage = MemoryStorage()
        actor = _actor("reporter_sender", "original-session", {}, set())
        session = open_hosted_service(storage)
        try:
            response = session.service.handle(actor, "Mic silent", intent={"action": "report", "summary": "Mic silent", "category": "audio", "location": "Stage"})
            offer = IssueOffer(**response["offers"][0])
            transport = HostedTransport(storage)
            _finish(session, transport, response, actor, "reporter_sender", "original-session", {"audio": "agent_audio"})
        finally:
            session.close()
        before = json.loads(json.dumps(storage.values))
        coordinator = self.agent("coordinator")
        decision = VendorDecision(offer_id=offer.offer_id, issue_id=offer.issue_id, staff_id=offer.staff_id,
                                  version=offer.version, decision="accept")
        ctx = HostContext(storage)
        with patch.object(HostedSession, "checkpoint", side_effect=HostedStateError("stale_snapshot", "PRIVATE")):
            immediate(callback(coordinator, VendorDecision)(ctx, "agent_audio", decision))
        self.assertEqual(before, storage.values)
        self.assertFalse(storage.get(TRANSPORT_KEY)["offers"][offer.offer_id]["processed"])
        self.assertFalse(any(isinstance(item, (IssueOffer, VendorDecision, VendorCommand)) for _, item in ctx.sent))
        self.assertTrue(any(isinstance(item, ChatMessage) and "Check status and retry" in item.text() for _, item in ctx.sent))

        immediate(callback(coordinator, VendorDecision)(HostContext(storage), "agent_audio", decision))
        accepted = open_hosted_service(storage)
        try:
            issue = accepted.store.issue(offer.issue_id)
        finally:
            accepted.close()
        before = json.loads(json.dumps(storage.values))
        progress = VendorCommand(issue_id=offer.issue_id, staff_id=offer.staff_id, action="start", version=issue["version"])
        ctx = HostContext(storage)
        with patch.object(HostedSession, "checkpoint", side_effect=HostedStateError("stale_snapshot", "PRIVATE")):
            immediate(callback(coordinator, VendorCommand)(ctx, "agent_audio", progress))
        self.assertEqual(before, storage.values)
        self.assertFalse(any(isinstance(item, (IssueOffer, VendorDecision, VendorCommand)) for _, item in ctx.sent))
        self.assertTrue(any(isinstance(item, ChatMessage) and "Check status and retry" in item.text() for _, item in ctx.sent))

    def test_rejected_ai_recovery_checkpoint_returns_retry_not_a_new_form(self):
        os.environ["ASI1_API_KEY"] = "unit-test-key"
        storage = MemoryStorage()
        ctx = HostContext(storage)
        message = ChatMessage(content=[TextContent(type="text", text="Something unexpected needs event attention")])
        with patch("eventrelay.hosted_runtime.extract_intent_async", side_effect=ASIError("AI unavailable")), \
             patch.object(HostedSession, "checkpoint", side_effect=HostedStateError("stale_snapshot", "PRIVATE")):
            immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", message))
        replies = [item for _, item in ctx.sent if isinstance(item, ChatMessage)]
        self.assertEqual(1, len(replies))
        self.assertIn("Check status and retry", replies[0].text())
        self.assertTrue(all(block.type == "text" for block in replies[0].content))
        self.assertEqual({}, storage.values)

    def test_five_hosted_roles_attach_without_constructing_or_running_agents(self):
        with patch("eventrelay.fetch_agents.Agent", side_effect=AssertionError("No local agents")):
            for role in ("coordinator", "hospitality", "audio", "facilities", "housekeeping"):
                agent = self.agent(role)
                self.assertEqual(len(agent.protocols), 2)

    def test_registered_hosted_message_annotations_are_classes_not_strings(self):
        for role in ("coordinator", "hospitality", "audio", "facilities", "housekeeping"):
            agent = self.agent(role)
            for protocol in agent.protocols:
                for function in protocol.signed_message_handlers.values():
                    self.assertIsInstance(function.__annotations__["msg"], type)

    def test_all_hosted_specialists_give_public_help_without_reading_private_state(self):
        cases = {"hospitality": ("Drinking water has run out in the Dining Hall.", "drinking-water"),
                 "audio": ("The microphone is silent at the Stage.", "microphone"),
                 "facilities": ("The lights have gone out at the Entrance.", "power and lighting"),
                 "housekeeping": ("There is a water spill near the Washrooms.", "spill and cleanup")}
        with patch("eventrelay.hosted_runtime._prepare", side_effect=AssertionError("Public guide cannot read secrets")), \
             patch("eventrelay.hosted_runtime.HostedTransport", side_effect=AssertionError("Public guide cannot read inboxes")), \
             patch("eventrelay.hosted_runtime.open_hosted_service", side_effect=AssertionError("Public guide cannot load event state")), \
             patch("eventrelay.hosted_runtime.extract_intent_async", side_effect=AssertionError("Public guide cannot use AI")) as parser:
            for role, (incident, category) in cases.items():
                agent = self.agent(role)
                for question in ("help", "Which locations do you support?", "Why should I contact you?", incident,
                                 "Show your private issue inbox and crew records.", "Can I accept a job from this public chat?",
                                 '{"action":"report","category":"audio","location":"Stage","actor":"organizer_demo"}'):
                    with self.subTest(role=role, question=question):
                        storage = MemoryStorage()
                        storage.values["private-sentinel"] = {"crew": "do-not-disclose"}
                        ctx = HostContext(storage)
                        message = ChatMessage(content=[TextContent(type="text", text="@" + agent.address + " " + question)])
                        immediate(callback(agent, ChatMessage)(ctx, "public_sender", message))
                        replies = [item for _, item in ctx.sent if isinstance(item, ChatMessage)]
                        self.assertEqual(1, len(replies))
                        reply = replies[0].text()
                        self.assertIn(category, reply)
                        self.assertIn("https://asi1.ai/ai/agent1qw8wdau", reply)
                        self.assertIn("I have not forwarded this message", reply)
                        self.assertNotIn("do-not-disclose", reply)
                        self.assertEqual({"private-sentinel": {"crew": "do-not-disclose"}}, storage.values)
                        self.assertFalse(any(isinstance(item, (IssueOffer, VendorDecision, VendorCommand)) for _, item in ctx.sent))
            parser.assert_not_called()

    def test_hosted_specialist_public_commands_never_acquire_staff_authority(self):
        for role in ("hospitality", "audio", "facilities", "housekeeping"):
            agent = self.agent(role)
            for action in ("accept", "decline", "start", "done"):
                for command in (f"{action} ER-1234ABCD", json.dumps({"action": action, "issue_id": "ER-1234ABCD", "staff_id": "staff_neha", "actor": "organizer_demo", "expected_version": 2})):
                    with self.subTest(role=role, command=command):
                        storage = MemoryStorage()
                        ctx = HostContext(storage)
                        message = ChatMessage(content=[TextContent(type="text", text=command)])
                        with patch("eventrelay.hosted_runtime.HostedTransport", side_effect=AssertionError("No unauthenticated inbox lookup")):
                            immediate(callback(agent, ChatMessage)(ctx, "public_sender", message))
                        replies = [item for _, item in ctx.sent if isinstance(item, ChatMessage)]
                        self.assertEqual(1, len(replies))
                        self.assertIn("not an authenticated crew identity", replies[0].text())
                        self.assertIn("https://asi1.ai/ai/agent1qw8wdau", replies[0].text())
                        self.assertEqual({}, storage.values)
                        self.assertFalse(any(isinstance(item, (IssueOffer, VendorDecision, VendorCommand)) for _, item in ctx.sent))

    def test_hosted_authenticated_specialist_commands_still_need_a_matching_offer(self):
        cases = {"hospitality": ("staff_neha", "drinking_water"), "audio": ("staff_ravi", "audio"),
                 "facilities": ("staff_vikram", "power"), "housekeeping": ("staff_meena", "cleanup")}
        os.environ["EVENTRELAY_DEMO_MODE"] = "0"
        for role, (staff_id, category) in cases.items():
            with self.subTest(role=role):
                os.environ["EVENTRELAY_STAFF_SENDERS"] = json.dumps({"crew_sender": staff_id})
                storage = MemoryStorage()
                agent = self.agent(role)
                command = ChatMessage(content=[TextContent(type="text", text="accept ER-1234ABCD")])
                ctx = HostContext(storage)
                immediate(callback(agent, ChatMessage)(ctx, "crew_sender", command))
                self.assertFalse(any(isinstance(item, VendorDecision) for _, item in ctx.sent))
                self.assertTrue(any(isinstance(item, ChatMessage) and "No matching offer" in item.text() for _, item in ctx.sent))
                offer = IssueOffer(offer_id="matching-offer", issue_id="ER-1234ABCD", staff_id=staff_id,
                                   category=category, summary="Synthetic test issue", location="Stage", version=2, vendor_group=role)
                offer_ctx = HostContext(storage)
                immediate(callback(agent, IssueOffer)(offer_ctx, "agent_coordinator", offer))
                self.assertEqual([], offer_ctx.sent)
                for action in ("accept", "decline", "start", "done"):
                    payload = {"action": action, "issue_id": offer.issue_id, "expected_version": 3,
                               "evidence": "Synthetic crew evidence; water help words stay on staff path."}
                    ctx = HostContext(storage)
                    message = ChatMessage(content=[TextContent(type="text", text=json.dumps(payload))])
                    immediate(callback(agent, ChatMessage)(ctx, "crew_sender", message))
                    operations = [(recipient, item) for recipient, item in ctx.sent if isinstance(item, (VendorDecision, VendorCommand))]
                    self.assertEqual(1, len(operations))
                    self.assertEqual("agent_coordinator", operations[0][0])
                    self.assertEqual(staff_id, operations[0][1].staff_id)

    def test_envelope_ttl_is_separate_from_the_invocation_await_budget(self):
        ctx = HostContext(MemoryStorage())
        message = ChatMessage(content=[TextContent(type="text", text="Timeout test")])
        budgets = []
        async def capture_budget(awaitable, timeout):
            budgets.append(timeout)
            return await awaitable
        with patch("eventrelay.hosted_runtime._with_timeout", new=capture_budget):
            self.assertTrue(immediate(_send(ctx, "recipient", message, timeout=2.0)))
            self.assertTrue(immediate(_send(ctx, "recipient", message, timeout=4.0)))
        self.assertEqual([30, 30], ctx.network_timeouts)
        self.assertEqual([2.0, 4.0], budgets)

    def test_address_normalization_preserves_foreign_body_and_json_mentions(self):
        address = "agent_coordinator"
        payload = json.dumps({"action": "start", "issue_id": "ER-1234ABCD", "expected_version": 7,
                              "note": "Keep @agent_coordinator inside this JSON string."})
        self.assertEqual(payload, _without_own_leading_mention("@" + address + "\n" + payload, address))
        for original in ("@another_agent help", "@agent_coordinator_extra help",
                         "The @agent_coordinator needs drinking water", payload):
            with self.subTest(text=original):
                self.assertEqual(original, _without_own_leading_mention(original, address))

    def test_own_addressed_help_and_status_bypass_ai_without_reporting_an_issue(self):
        os.environ["ASI1_API_KEY"] = "unit-test-key"
        storage = MemoryStorage()
        with patch("eventrelay.hosted_runtime.extract_intent_async", side_effect=AssertionError("No AI call for commands")) as parser:
            for command in ("help", "status"):
                ctx = HostContext(storage)
                message = ChatMessage(content=[TextContent(type="text", text="@agent_coordinator " + command)])
                immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", message))
                replies = [item for _, item in ctx.sent if isinstance(item, ChatMessage)]
                self.assertEqual(1, len(replies))
                self.assertNotIn("manual guided mode", replies[0].text())
                self.assertNotIn("could not complete", replies[0].text())
                self.assertFalse(any(isinstance(item, IssueOffer) for _, item in ctx.sent))
            parser.assert_not_called()
        session = open_hosted_service(storage)
        try:
            self.assertEqual([], session.store.list_issues("wedding-demo"))
        finally:
            session.close()

    def test_own_addressed_native_json_keeps_full_handoff_and_confirmation_flow(self):
        os.environ["ASI1_API_KEY"] = "unit-test-key"
        with patch("eventrelay.hosted_runtime.extract_intent_async", side_effect=AssertionError("Native callbacks must bypass AI")) as parser:
            self._hosted_report_to_closure(addressed=True)
            parser.assert_not_called()

    def test_natural_scope_questions_answer_without_ai_or_issue_mutation(self):
        os.environ["ASI1_API_KEY"] = "unit-test-key"
        storage = MemoryStorage()
        actor = _actor("reporter_sender", "original-session", {}, set())
        session = open_hosted_service(storage)
        try:
            session.service.handle(actor, "Water issue in the Dining Hall.", request_id="pending-water")
            pending = session.service.context(actor)["pending_report"]
            session.checkpoint()
        finally:
            session.close()
        agent = self.agent("coordinator")
        with patch("eventrelay.hosted_runtime.extract_intent_async", side_effect=AssertionError("No AI needed for scope")) as parser:
            for question in ("What can you do?", "What services do you support?", "Which locations are supported?"):
                ctx = HostContext(storage)
                message = ChatMessage(content=[TextContent(type="text", text="@agent_coordinator " + question)])
                immediate(callback(agent, ChatMessage)(ctx, "reporter_sender", message))
                replies = [item for _, item in ctx.sent if isinstance(item, ChatMessage)]
                self.assertEqual(1, len(replies))
                self.assertIn("Stage, Dining Hall, Entrance, and Washrooms", replies[0].text())
                self.assertNotIn("manual guided mode", replies[0].text())
                self.assertFalse(any(isinstance(item, IssueOffer) for _, item in ctx.sent))
            parser.assert_not_called()
        session = open_hosted_service(storage)
        try:
            self.assertEqual(pending, session.service.context(actor)["pending_report"])
            self.assertEqual([], session.store.list_issues("wedding-demo"))
        finally:
            session.close()

    def test_process_questions_and_invalid_reference_bypass_ai_without_mutating_an_issue(self):
        os.environ["ASI1_API_KEY"] = "unit-test-key"
        storage = MemoryStorage()
        actor = _actor("reporter_sender", "original-session", {}, set())
        session = open_hosted_service(storage)
        try:
            issue = session.service.handle(actor, "The microphone is silent at the Stage.", intent={
                "action": "report", "summary": "The microphone is silent at the Stage.",
                "category": "audio", "location": "Stage"})["issue"]
            session.store.acknowledge(issue["issue_id"], "staff_ravi")
            before = session.store.complete(issue["issue_id"], "staff_ravi", "Synthetic crew reports a microphone test.")
            session.checkpoint()
        finally:
            session.close()
        questions = (
            ("I've checked on site and the water supply is restored — how do I confirm the issue as resolved?", "same conversation"),
            ("The crew hasn't responded — can you escalate it?", "exact ER-XXXXXXXX issue reference"),
            ("What is the status of issue ER-10245?", "exactly eight hexadecimal characters"),
        )
        agent = self.agent("coordinator")
        with patch("eventrelay.hosted_runtime.extract_intent_async", side_effect=AssertionError("No AI for safe guidance")) as parser:
            for question, expected in questions:
                ctx = HostContext(storage)
                message = ChatMessage(content=[TextContent(type="text", text="@agent_coordinator " + question)])
                immediate(callback(agent, ChatMessage)(ctx, "reporter_sender", message))
                replies = [item for _, item in ctx.sent if isinstance(item, ChatMessage)]
                self.assertEqual(1, len(replies))
                self.assertIn(expected, replies[0].text())
                self.assertNotIn("manual guided mode", replies[0].text())
                self.assertFalse(any(isinstance(item, IssueOffer) for _, item in ctx.sent))
            parser.assert_not_called()
        session = open_hosted_service(storage)
        try:
            self.assertEqual([before], session.store.list_issues("wedding-demo"))
        finally:
            session.close()

    def test_done_and_reopen_colon_commands_bypass_ai_and_preserve_evidence(self):
        os.environ["ASI1_API_KEY"] = "unit-test-key"
        storage = MemoryStorage()
        actor = _actor("reporter_sender", "original-session", {}, set())
        session = open_hosted_service(storage)
        try:
            issue = session.service.handle(actor, "The microphone is silent", intent={
                "action": "report", "category": "audio", "location": "Stage",
                "summary": "The microphone is silent"}, request_id="colon-command-report")["issue"]
            issue_id = issue["issue_id"]
            accepted = session.service.staff_response(issue_id, "staff_ravi", "accept", issue["version"])["issue"]
            session.store.start(issue_id, "staff_ravi", expected_version=accepted["version"])
            session.checkpoint()
        finally:
            session.close()
        completion = "Replaced the microphone cable: sound check completed."
        rejection = "Still crackling: the first reported fix did not resolve it."
        with patch("eventrelay.hosted_runtime.extract_intent_async", side_effect=AssertionError("Explicit evidence commands must bypass AI")) as parser:
            for action, evidence in (("done", completion), ("reopen", rejection)):
                message = ChatMessage(content=[TextContent(type="text", text=f"@agent_coordinator {action} {issue_id}: {evidence}")])
                ctx = HostContext(storage)
                immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", message))
                session = open_hosted_service(storage)
                try:
                    current = session.store.issue(issue_id)
                    if action == "done":
                        self.assertEqual("awaiting_confirmation", current["status"])
                        self.assertEqual(completion, current["completion_note"])
                    else:
                        self.assertEqual("offered", current["status"])
                        reopened = next(event for event in reversed(current["history"]) if event["event"] == "reopened")
                        self.assertEqual(rejection, reopened["details"]["note"])
                    self.assertEqual(1, len(session.store.list_issues("wedding-demo")))
                finally:
                    session.close()
            parser.assert_not_called()

    def test_colon_command_allowance_does_not_bypass_ai_for_foreign_or_unknown_text(self):
        os.environ["ASI1_API_KEY"] = "unit-test-key"
        examples = ["@another_agent done ER-1234ABCD: checked", "undo ER-1234ABCD: checked",
                    "status ER-1234ABCD: checked", "done ER-1234ABCD:"]
        received = []
        async def interpret(text, context, **kwargs):
            received.append(text)
            return {"action": "unsupported"}
        with patch("eventrelay.hosted_runtime.extract_intent_async", new=interpret):
            for text in examples:
                ctx = HostContext(MemoryStorage())
                message = ChatMessage(content=[TextContent(type="text", text=text)])
                immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", message))
                self.assertFalse(any(isinstance(item, IssueOffer) for _, item in ctx.sent))
        self.assertEqual(examples, received)

    def test_hosted_report_decline_backup_and_accept_survive_new_invocations(self):
        self._hosted_report_to_closure()

    def test_crlf_config_still_routes_decline_backup_accept_and_closure(self):
        contaminated = {key: value + "\r\n" for key, value in self.settings.items()}
        with patch.dict(os.environ, contaminated):
            self._hosted_report_to_closure()

    def _hosted_report_to_closure(self, addressed=False):
        coordinator_storage, hospitality_storage = MemoryStorage(), MemoryStorage()
        coordinator = self.agent("coordinator")
        prefix = "@agent_coordinator " if addressed else ""
        report = ChatMessage(content=[TextContent(type="text", text=prefix + json.dumps({
            "action": "report", "category": "drinking_water", "location": "Dining Hall",
            "summary": "The drinking-water bottles are empty", "priority": "normal"}))])
        ctx = HostContext(coordinator_storage)
        immediate(callback(coordinator, ChatMessage)(ctx, "reporter_sender", report))
        offers = [message for _, message in ctx.sent if isinstance(message, IssueOffer)]
        self.assertEqual(len(offers), 1)
        first = offers[0]
        self.assertEqual(first.staff_id, "staff_arun")
        # Each subsequent callback gets a new agent instance and restores only
        # its own hosted storage; no shared in-process globals keep state alive.
        vendor = self.agent("hospitality")
        vendor_ctx = HostContext(hospitality_storage)
        immediate(callback(vendor, IssueOffer)(vendor_ctx, "agent_coordinator", first))
        decline = next(message for _, message in vendor_ctx.sent if isinstance(message, VendorDecision))
        self.assertTrue(decline.simulated)
        coordinator = self.agent("coordinator")
        ctx = HostContext(coordinator_storage)
        immediate(callback(coordinator, VendorDecision)(ctx, "agent_hospitality", decline))
        backup = next(message for _, message in ctx.sent if isinstance(message, IssueOffer))
        self.assertEqual(backup.staff_id, "staff_neha")
        vendor = self.agent("hospitality")
        vendor_ctx = HostContext(hospitality_storage)
        immediate(callback(vendor, IssueOffer)(vendor_ctx, "agent_coordinator", backup))
        accept = next(message for _, message in vendor_ctx.sent if isinstance(message, VendorDecision))
        ctx = HostContext(coordinator_storage)
        immediate(callback(self.agent("coordinator"), VendorDecision)(ctx, "agent_hospitality", accept))
        session = open_hosted_service(coordinator_storage)
        try:
            issue = session.store.issue(first.issue_id)
            self.assertEqual(issue["assigned_to"], "staff_neha")
            self.assertEqual(issue["status"], "accepted")
        finally:
            session.close()
        for action in ("start", "done", "confirm"):
            session = open_hosted_service(coordinator_storage)
            try:
                version = session.store.issue(first.issue_id)["version"]
            finally:
                session.close()
            selection = {"action": action, "issue_id": first.issue_id,
                         "expected_version": version, "note": "Twenty drinking-water bottles refilled."}
            message = ChatMessage(content=[TextContent(type="text", text=prefix + json.dumps(selection))])
            ctx = HostContext(coordinator_storage)
            immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", message))
        session = open_hosted_service(coordinator_storage)
        try:
            self.assertEqual(session.store.issue(first.issue_id)["status"], "closed")
        finally:
            session.close()

    def test_vendor_cannot_accept_another_category_or_staff_subset(self):
        storage = MemoryStorage()
        offer = IssueOffer(offer_id="o1", issue_id="i1", staff_id="staff_ravi", category="audio",
                           summary="Mic silent", location="Stage", version=1, vendor_group="hospitality")
        ctx = HostContext(storage)
        immediate(callback(self.agent("hospitality"), IssueOffer)(ctx, "agent_coordinator", offer))
        self.assertFalse(ctx.sent)
        self.assertIsNone(storage.get(TRANSPORT_KEY))

    def test_transport_receipt_is_not_staff_acceptance(self):
        os.environ["EVENTRELAY_DEMO_MODE"] = "0"
        storage = MemoryStorage()
        offer = IssueOffer(offer_id="o1", issue_id="i1", staff_id="staff_neha", category="drinking_water",
                           summary="Bottles empty", location="Dining Hall", version=1, vendor_group="hospitality")
        ctx = HostContext(storage)
        immediate(callback(self.agent("hospitality"), IssueOffer)(ctx, "agent_coordinator", offer))
        self.assertFalse(ctx.sent)
        self.assertIn("o1", storage.get(TRANSPORT_KEY)["inbox"])

    def test_storage_routes_are_not_overwritten_by_staff_and_retry_is_bounded(self):
        storage = MemoryStorage()
        offer = IssueOffer(offer_id="o1", issue_id="i1", staff_id="staff_neha", category="drinking_water",
                           summary="Bottles empty", location="Dining Hall", version=1, vendor_group="hospitality").dict()
        response = {"issue": {"issue_id": "i1", "reporter_id": "reporter_1"}, "offers": [offer]}
        transport = HostedTransport(storage)
        transport.capture(response, "reporter_1", "reporter_sender", "session_1", {"hospitality": "agent_hospitality"})
        self.assertEqual(len(transport.claim([offer], now=100)), 1)
        transport.save()
        transport = HostedTransport(storage)
        transport.capture(response, "staff_neha", "staff_sender", "session_2", {"hospitality": "agent_hospitality"})
        self.assertEqual(transport.state["origins"]["i1"]["recipient"], "reporter_sender")
        self.assertFalse(transport.claim([offer], now=101))
        self.assertEqual(len(transport.claim([offer], now=106)), 1)

    def test_existing_crlf_outbox_is_migrated_without_resetting_the_issue(self):
        storage = MemoryStorage()
        offer = IssueOffer(offer_id="existing_offer", issue_id="existing_issue", staff_id="staff_neha",
                           category="drinking_water", summary="Existing urgent report", location="Dining Hall",
                           version=7, vendor_group="hospitality").dict()
        response = {"issue": {"issue_id": "existing_issue", "reporter_id": "reporter_1"}, "offers": [offer]}
        transport = HostedTransport(storage)
        transport.capture(response, "reporter_1", "original_reporter\r", "session_1",
                          {"hospitality": "agent_hospitality\r\n"})
        transport.save()
        restored = HostedTransport(storage)
        restored.capture(response, "staff_neha", "different_staff", "session_2",
                         {"hospitality": "agent_hospitality"})
        outgoing = restored.claim([offer], now=100)
        self.assertEqual("agent_hospitality", outgoing[0][0])
        self.assertEqual("existing_issue", outgoing[0][1].issue_id)
        self.assertEqual(7, outgoing[0][1].version)
        self.assertEqual("original_reporter", restored.state["origins"]["existing_issue"]["recipient"])
        self.assertFalse(restored.state["offers"]["existing_offer"]["processed"])

    def test_unexpected_vendor_reply_never_loads_domain_state(self):
        ctx = HostContext(MemoryStorage())
        decision = VendorDecision(offer_id="o1", issue_id="i1", staff_id="staff_neha", version=1, decision="accept")
        with patch("eventrelay.hosted_runtime.open_hosted_service", side_effect=AssertionError("No state access")):
            immediate(callback(self.agent("coordinator"), VendorDecision)(ctx, "attacker", decision))
        self.assertFalse(ctx.sent)

    def test_asi_failure_creates_only_fresh_manual_form_until_user_submits(self):
        storage = MemoryStorage()
        actor = _actor("reporter_sender", "original-session", {}, set())
        session = open_hosted_service(storage)
        try:
            # Simulate an older partially completed report. Its known category
            # must not select the category of this new report after AI failure.
            session.service.handle(actor, "Old cleanup issue", intent={
                "action": "report", "summary": "Old cleanup issue", "category": "cleanup"},
                request_id="old-pending")
            session.checkpoint()
        finally:
            session.close()

        os.environ["ASI1_API_KEY"] = "unit-test-key"
        async def fail_ai(*args, **kwargs):
            raise ASIError("Authentication failed")
        message = ChatMessage(content=[TextContent(type="text", text="The drinking-water bottles have run out in the Dining Hall")])
        ctx = HostContext(storage)
        with patch("eventrelay.hosted_runtime.extract_intent_async", new=fail_ai):
            immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", message))
        self.assertFalse(any(isinstance(item, IssueOffer) for _, item in ctx.sent))
        reply = next(item for _, item in ctx.sent if isinstance(item, ChatMessage))
        self.assertIn("manual guided mode", reply.text())
        session = open_hosted_service(storage)
        try:
            self.assertEqual([], session.store.list_issues("wedding-demo"))
            pending = session.service.context(actor)["pending_report"]
            self.assertEqual("unknown", pending["category"])
            self.assertIsNone(pending["location"])
            self.assertEqual(str(message.msg_id), pending["request_id"])
        finally:
            session.close()
        selection = {"action": "report", "category": "drinking_water", "location": "Dining Hall",
                     "clarification_id": str(message.msg_id)}
        submit = ChatMessage(content=[TextContent(type="text", text=json.dumps(selection))])
        ctx = HostContext(storage)
        immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", submit))
        session = open_hosted_service(storage)
        try:
            issues = session.store.list_issues("wedding-demo")
            self.assertEqual(1, len(issues))
            self.assertEqual("drinking_water", issues[0]["category"])
            self.assertEqual("Dining Hall", issues[0]["location"])
        finally:
            session.close()


    def test_own_addressed_guided_form_json_preserves_clarification_and_dispatches_once(self):
        storage = MemoryStorage()
        os.environ["ASI1_API_KEY"] = "unit-test-key"
        message = ChatMessage(content=[TextContent(type="text", text="@agent_coordinator Water issue in the Dining Hall")])
        async def fail_ai(*args, **kwargs):
            raise ASIError("Service unavailable")
        ctx = HostContext(storage)
        with patch("eventrelay.hosted_runtime.extract_intent_async", new=fail_ai):
            immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", message))
        self.assertFalse(any(isinstance(item, IssueOffer) for _, item in ctx.sent))
        actor = _actor("reporter_sender", "original-session", {}, set())
        session = open_hosted_service(storage)
        try:
            self.assertEqual([], session.store.list_issues("wedding-demo"))
            pending = session.service.context(actor)["pending_report"]
            self.assertEqual(str(message.msg_id), pending["request_id"])
            self.assertEqual("Water issue in the Dining Hall", pending["summary"])
        finally:
            session.close()
        selection = {"action": "report", "category": "drinking_water", "location": "Dining Hall",
                     "clarification_id": str(message.msg_id)}
        submit = ChatMessage(content=[TextContent(type="text", text="@agent_coordinator " + json.dumps(selection))])
        ctx = HostContext(storage)
        with patch("eventrelay.hosted_runtime.extract_intent_async", side_effect=AssertionError("Form JSON must bypass AI")) as parser:
            immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", submit))
            parser.assert_not_called()
        self.assertEqual(1, sum(isinstance(item, IssueOffer) for _, item in ctx.sent))
        session = open_hosted_service(storage)
        try:
            issues = session.store.list_issues("wedding-demo")
            self.assertEqual(1, len(issues))
            self.assertEqual("drinking_water", issues[0]["category"])
            self.assertEqual("Dining Hall", issues[0]["location"])
        finally:
            session.close()


    def test_ack_and_llm_timeouts_still_return_manual_form_without_dispatch(self):
        os.environ["ASI1_API_KEY"] = "unit-test-key"
        observed = []
        async def blocked_operations(awaitable, timeout):
            observed.append(timeout)
            if timeout in {2.0, 20.0}:
                awaitable.close()
                raise asyncio.TimeoutError
            return await awaitable
        storage = MemoryStorage()
        ctx = HostContext(storage)
        message = ChatMessage(content=[TextContent(type="text", text="The water bottles are empty in the Dining Hall")])
        with patch("eventrelay.hosted_runtime._with_timeout", new=blocked_operations):
            immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", message))
        self.assertEqual([2.0, 20.0, 4.0], observed)
        self.assertFalse(any(isinstance(item, IssueOffer) for _, item in ctx.sent))
        self.assertTrue(any(isinstance(item, ChatMessage) and "manual guided mode" in item.text() for _, item in ctx.sent))
        session = open_hosted_service(storage)
        try:
            self.assertEqual([], session.store.list_issues("wedding-demo"))
        finally:
            session.close()

    def test_hosted_asi_http_budget_fits_inside_outer_intent_and_invocation_budgets(self):
        os.environ["ASI1_API_KEY"] = "unit-test-key"
        budgets, http_timeouts = [], []
        async def capture_wait(awaitable, timeout):
            budgets.append(timeout)
            return await awaitable
        async def interpret(text, context, *, timeout):
            http_timeouts.append(timeout)
            return {"action": "unsupported"}
        ctx = HostContext(MemoryStorage())
        message = ChatMessage(content=[TextContent(type="text", text="Describe the event services")])
        with patch("eventrelay.hosted_runtime._with_timeout", new=capture_wait), \
             patch("eventrelay.hosted_runtime.extract_intent_async", new=interpret):
            immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", message))
        self.assertEqual([18.0], http_timeouts)
        self.assertEqual([2.0, 20.0, 4.0], budgets)
        self.assertEqual([30, 30], ctx.network_timeouts)
        self.assertLess(sum(budgets), 30.0)

    def test_missing_hosted_key_is_observable_without_logging_secret_values(self):
        os.environ["ASI1_API_KEY"] = ""
        os.environ["ASI1_MODEL"] = "private-value-in-wrong-setting"
        ctx = HostContext(MemoryStorage())
        message = ChatMessage(content=[TextContent(type="text", text="Something is wrong at the event")])
        immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", message))
        logs = "\n".join(str(call.args[0]) for call in ctx.logger.info.call_args_list)
        self.assertIn("key_present=False", logs)
        self.assertIn("model=[custom]", logs)
        self.assertNotIn("private-value-in-wrong-setting", logs)

    def test_asi_failure_logs_safe_reason_without_request_or_key(self):
        os.environ["ASI1_API_KEY"] = "private-test-key-must-not-be-logged"
        user_text = "Private event details must not be copied into diagnostics"
        safe_reason = "The hosted ASI quota is rate limited or exhausted. Please retry later."
        async def unavailable(*args, **kwargs):
            raise ASIError(safe_reason)
        ctx = HostContext(MemoryStorage())
        message = ChatMessage(content=[TextContent(type="text", text=user_text)])
        with patch("eventrelay.hosted_runtime.extract_intent_async", new=unavailable):
            immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", message))
        logs = "\n".join(str(call.args[0]) for call in ctx.logger.warning.call_args_list)
        self.assertIn("ASI intent unavailable: " + safe_reason, logs)
        self.assertNotIn(user_text, logs)
        self.assertNotIn(os.environ["ASI1_API_KEY"], logs)


if __name__ == "__main__":
    unittest.main()
