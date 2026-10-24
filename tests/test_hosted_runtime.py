import asyncio
import json
import os
import unittest
from unittest.mock import Mock, patch

from uagents_core.contrib.protocols.chat import ChatMessage, TextContent
from eventrelay.fetch_agents import IssueOffer, VendorDecision
from eventrelay.hosted_runtime import HostedTransport, TRANSPORT_KEY, attach, _send
from eventrelay.hosted_state import open_hosted_service
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

    def test_hosted_report_decline_backup_and_accept_survive_new_invocations(self):
        self._hosted_report_to_closure()

    def test_crlf_config_still_routes_decline_backup_accept_and_closure(self):
        contaminated = {key: value + "\r\n" for key, value in self.settings.items()}
        with patch.dict(os.environ, contaminated):
            self._hosted_report_to_closure()

    def _hosted_report_to_closure(self):
        coordinator_storage, hospitality_storage = MemoryStorage(), MemoryStorage()
        coordinator = self.agent("coordinator")
        report = ChatMessage(content=[TextContent(type="text", text=json.dumps({
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
            message = ChatMessage(content=[TextContent(type="text", text=json.dumps(selection))])
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


    def test_ack_and_llm_timeouts_still_return_manual_form_without_dispatch(self):
        os.environ["ASI1_API_KEY"] = "unit-test-key"
        observed = []
        async def blocked_operations(awaitable, timeout):
            observed.append(timeout)
            if timeout in {2.0, 8.0}:
                awaitable.close()
                raise asyncio.TimeoutError
            return await awaitable
        storage = MemoryStorage()
        ctx = HostContext(storage)
        message = ChatMessage(content=[TextContent(type="text", text="The water bottles are empty in the Dining Hall")])
        with patch("eventrelay.hosted_runtime._with_timeout", new=blocked_operations):
            immediate(callback(self.agent("coordinator"), ChatMessage)(ctx, "reporter_sender", message))
        self.assertEqual([2.0, 8.0, 4.0], observed)
        self.assertFalse(any(isinstance(item, IssueOffer) for _, item in ctx.sent))
        self.assertTrue(any(isinstance(item, ChatMessage) and "manual guided mode" in item.text() for _, item in ctx.sent))
        session = open_hosted_service(storage)
        try:
            self.assertEqual([], session.store.list_issues("wedding-demo"))
        finally:
            session.close()

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


if __name__ == "__main__":
    unittest.main()
