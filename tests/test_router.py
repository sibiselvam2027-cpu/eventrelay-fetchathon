"""Integration checks for chat ownership, clarification and state-changing actions."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from eventrelay.router import ConversationService, local_intent
from eventrelay.store import EventStore


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("EVENTRELAY_TEST_TEMP"))
        root = Path(self.temp.name)
        self.store = EventStore(root / "events.db")
        self.store.seed_demo()
        self.service = ConversationService(root / "conversations.db", self.store)
        self.environment = patch.dict(os.environ, {"EVENTRELAY_DEMO_MODE": "0"})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()

    def report(self, actor="reporter_alice", request_id="report-1", **changes):
        intent = {"action": "report", "summary": "The microphone is silent at the Stage.",
                  "category": "audio", "location": "Stage", "priority": "normal"}
        intent.update(changes)
        return self.service.handle(actor, intent["summary"], intent=intent, request_id=request_id)

    def action(self, actor, issue_id, action, **extra):
        intent = {"action": action, "issue_id": issue_id, **extra}
        return self.service.handle(actor, "selected action", intent=intent)

    def waiting_for_confirmation(self, actor="reporter_alice"):
        issue = self.report(actor=actor)["issue"]
        staff = issue["offered_to"]
        issue = self.action(staff, issue["issue_id"], "accept", version=issue["version"])["issue"]
        issue = self.action(staff, issue["issue_id"], "start", version=issue["version"])["issue"]
        issue = self.action(staff, issue["issue_id"], "done", version=issue["version"],
                            note="Crew reports that a replacement microphone has been tested.")["issue"]
        self.assertEqual("awaiting_confirmation", issue["status"])
        return issue

    def test_ambiguous_water_does_not_dispatch_then_native_form_preserves_report(self):
        complaint = "There is a water issue in the Dining Hall."
        response = self.service.handle("reporter_alice", complaint, request_id="water-1")
        self.assertNotIn("issue", response)
        self.assertEqual([], response["offers"])
        self.assertEqual([], self.store.list_issues("wedding-demo"))
        self.assertEqual("form", response["card"]["kind"])
        fields = response["card"]["payload"]["fields"]
        self.assertEqual(["category"], [field["name"] for field in fields])
        # An ASI form selection need not repeat the original summary/location.
        response = self.service.handle("reporter_alice", '{"action":"report","category":"drinking_water"}')
        issue = response["issue"]
        self.assertEqual(complaint, issue["summary"])
        self.assertEqual("Dining Hall", issue["location"])
        self.assertEqual("drinking_water", issue["category"])
        self.assertEqual("reporter_alice", issue["reporter_id"])
        self.assertEqual("staff_arun", issue["offered_to"])
        self.assertIsNone(issue["assigned_to"])

    def test_missing_category_and_location_require_both_before_assignment(self):
        response = self.service.handle("reporter_alice", "Something is wrong.")
        names = {field["name"] for field in response["card"]["payload"]["fields"]}
        self.assertEqual({"category", "location"}, names)
        response = self.service.handle("reporter_alice", '{"action":"report","category":"cleanup"}')
        self.assertNotIn("issue", response)
        self.assertEqual([], self.store.list_issues("wedding-demo"))
        response = self.service.handle("reporter_alice", '{"action":"report","location":"Entrance"}')
        self.assertEqual("cleanup", response["issue"]["category"])
        self.assertEqual("Entrance", response["issue"]["location"])

    def test_public_reporter_cannot_accept_decline_or_complete_as_crew(self):
        issue = self.report()["issue"]
        for action in ("accept", "decline", "start", "done"):
            response = self.action("reporter_alice", issue["issue_id"], action,
                                   staff_id=issue["offered_to"], note="I claim this is complete.")
            self.assertEqual("wrong_actor", response["code"])
            current = self.store.issue(issue["issue_id"])
            self.assertEqual("offered", current["status"])
            self.assertIsNone(current["assigned_to"])

    def test_authenticated_staff_can_accept_and_the_original_reporter_can_close(self):
        issue = self.waiting_for_confirmation()
        self.assertEqual("Crew reports that a replacement microphone has been tested.", issue["completion_note"])
        response = self.action("reporter_alice", issue["issue_id"], "confirm", version=issue["version"])
        self.assertEqual("closed", response["issue"]["status"])
        events = [entry["event"] for entry in response["issue"]["events"]]
        self.assertIn("accepted", events)
        self.assertIn("completion_reported", events)
        self.assertEqual("confirmed_closed", events[-1])

    def test_json_actor_and_reporter_fields_cannot_override_transport_identity(self):
        response = self.service.handle("reporter_bob", "untrusted report", intent={
            "action": "report", "summary": "The Stage microphone is silent.",
            "category": "audio", "location": "Stage", "priority": "normal",
            "actor": "organizer_demo", "actor_id": "organizer_demo", "reporter_id": "organizer_demo",
        }, request_id="forged-report")
        issue = response["issue"]
        self.assertEqual("reporter_bob", issue["reporter_id"])
        response = self.service.handle("reporter_bob", "forged crew action", intent={
            "action": "accept", "issue_id": issue["issue_id"], "staff_id": issue["offered_to"],
            "actor": "staff_ravi", "actor_id": "staff_ravi",
        })
        self.assertEqual("wrong_actor", response["code"])
        self.assertIsNone(self.store.issue(issue["issue_id"])["assigned_to"])

    def test_staff_cannot_claim_another_staff_identity_even_in_demo_mode(self):
        os.environ["EVENTRELAY_DEMO_MODE"] = "1"
        issue = self.report()["issue"]
        response = self.action("staff_sara", issue["issue_id"], "accept", staff_id="staff_ravi")
        self.assertEqual("wrong_actor", response["code"])
        self.assertEqual("offered", self.store.issue(issue["issue_id"])["status"])

    def test_demo_staff_actions_are_labelled_but_do_not_grant_reporter_closure(self):
        os.environ["EVENTRELAY_DEMO_MODE"] = "1"
        issue = self.report()["issue"]
        response = self.action("reporter_alice", issue["issue_id"], "accept", staff_id=issue["offered_to"])
        self.assertIn("Simulated staff action", response["text"])
        issue = response["issue"]
        issue = self.action("reporter_alice", issue["issue_id"], "done", staff_id=issue["assigned_to"],
                            note="Synthetic crew reports completion.")["issue"]
        response = self.action("reporter_bob", issue["issue_id"], "confirm", version=issue["version"])
        self.assertEqual("wrong_actor", response["code"])
        self.assertEqual("awaiting_confirmation", self.store.issue(issue["issue_id"])["status"])
        response = self.action("organizer_demo", issue["issue_id"], "confirm", version=issue["version"])
        self.assertEqual("closed", response["issue"]["status"])

    def test_stale_confirmation_card_cannot_close_a_later_completion(self):
        issue = self.waiting_for_confirmation()
        old_version = issue["version"]
        issue_id = issue["issue_id"]
        reopened = self.action("reporter_alice", issue_id, "reopen", version=old_version,
                               note="The microphone still cuts out.")["issue"]
        self.assertEqual(issue_id, reopened["issue_id"])
        staff = reopened["offered_to"]
        accepted = self.action(staff, issue_id, "accept", version=reopened["version"])["issue"]
        current = self.action(staff, issue_id, "done", version=accepted["version"],
                              note="Crew reports a second fix.")["issue"]
        self.assertGreater(current["version"], old_version)
        stale = self.action("reporter_alice", issue_id, "confirm", version=old_version)
        self.assertEqual("stale_version", stale["code"])
        self.assertEqual("awaiting_confirmation", self.store.issue(issue_id)["status"])
        closed = self.action("reporter_alice", issue_id, "confirm", version=current["version"])
        self.assertEqual("closed", closed["issue"]["status"])

    def test_clarification_and_last_issue_are_isolated_between_chats(self):
        self.service.handle("reporter_alice", "Water issue in the Dining Hall.", request_id="alice-water")
        bob = self.report(actor="reporter_bob", request_id="bob-audio")["issue"]
        alice = self.service.handle("reporter_alice", "It is drinking water refill.")["issue"]
        self.assertNotEqual(alice["issue_id"], bob["issue_id"])
        self.assertEqual("drinking_water", alice["category"])
        self.assertEqual("Dining Hall", alice["location"])
        self.assertEqual("Water issue in the Dining Hall.", alice["summary"])
        self.assertEqual("audio", bob["category"])
        self.assertEqual(alice["issue_id"], self.service.context("reporter_alice")["last_issue"]["issue_id"])
        self.assertEqual(bob["issue_id"], self.service.context("reporter_bob")["last_issue"]["issue_id"])
        forbidden = self.action("reporter_bob", alice["issue_id"], "status")
        self.assertEqual("wrong_actor", forbidden["code"])

    def test_duplicate_report_with_same_request_id_creates_one_issue(self):
        first = self.report(request_id="same-transport-message")["issue"]
        second = self.report(request_id="same-transport-message")["issue"]
        self.assertEqual(first["issue_id"], second["issue_id"])
        self.assertEqual(1, len(self.store.list_issues("wedding-demo")))
        self.assertEqual(1, sum(event["event"] == "reported" for event in second["events"]))

    def test_reusing_report_key_for_changed_content_is_rejected(self):
        first = self.report(request_id="same-key")["issue"]
        response = self.report(request_id="same-key", summary="A spill at the Entrance.", category="cleanup", location="Entrance")
        self.assertEqual("idempotency_conflict", response["code"])
        self.assertEqual(1, len(self.store.list_issues("wedding-demo")))
        self.assertEqual(first["summary"], self.store.issue(first["issue_id"])["summary"])

    def test_local_commands_complete_the_primary_flow_without_fake_asi_claims(self):
        issue = self.service.handle("reporter_alice", "The microphone is silent at the Stage.", request_id="commands")["issue"]
        issue_id = issue["issue_id"]
        self.assertEqual("audio", local_intent("The microphone is silent at the Stage.")["category"])
        issue = self.service.handle("staff_ravi", f"accept {issue_id}")["issue"]
        self.assertEqual("accepted", issue["status"])
        issue = self.service.handle("staff_ravi", f"start {issue_id}")["issue"]
        self.assertEqual("in_progress", issue["status"])
        issue = self.service.handle("staff_ravi", f"done {issue_id}: Replacement microphone tested.")["issue"]
        self.assertEqual("Replacement microphone tested.", issue["completion_note"])
        issue = self.service.handle("reporter_alice", f"confirm {issue_id}")["issue"]
        self.assertEqual("closed", issue["status"])

    def test_context_and_pending_clarification_survive_service_restart(self):
        self.service.handle("reporter_alice", "Water issue in the Dining Hall.", request_id="persist-water")
        resumed = ConversationService(self.service.path, self.store)
        issue = resumed.handle("reporter_alice", '{"action":"report","category":"drinking_water"}')["issue"]
        self.assertEqual("Water issue in the Dining Hall.", issue["summary"])
        self.assertEqual("Dining Hall", issue["location"])
        self.assertEqual(1, len(self.store.list_issues("wedding-demo")))


if __name__ == "__main__":
    unittest.main()
