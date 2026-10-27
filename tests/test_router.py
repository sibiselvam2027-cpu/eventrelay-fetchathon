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

    def test_model_main_stage_aliases_use_registered_stage_without_a_location_loop(self):
        prompt = "Drinking water has run out at the main stage, please find a crew and get them to accept the job."
        for index, alias in enumerate(("Main Stage", "MainStage", "main_stage", "main-stage")):
            with self.subTest(alias=alias):
                response = self.service.handle(f"reporter_stage_{index}", prompt, intent={
                    "action": "report", "summary": prompt, "category": "drinking_water", "location": alias},
                    request_id=f"model-stage-{index}")
                self.assertEqual("Stage", response["issue"]["location"])
                self.assertNotEqual("form", response.get("card", {}).get("kind"))

    def test_main_stage_model_clarification_resolves_category_without_reasking_location(self):
        original = "Water issue at the Main Stage."
        first = self.service.handle("reporter_alice", original, intent={
            "action": "report", "summary": original, "category": "unknown", "location": "MainStage"},
            request_id="stage-clarification")
        self.assertEqual(["category"], [field["name"] for field in first["card"]["payload"]["fields"]])
        followup = "The water ran out at the Main Stage."
        response = self.service.handle("reporter_alice", followup, intent={
            "action": "report", "summary": followup, "category": "drinking_water", "location": "main_stage"})
        self.assertEqual("Stage", response["issue"]["location"])
        self.assertEqual("drinking_water", response["issue"]["category"])

    def test_natural_followup_repairs_a_persisted_legacy_main_stage_location(self):
        self.service._save("reporter_alice", {"pending": {
            "summary": "Drinking water has run out.", "category": "drinking_water", "location": "Main Stage",
            "priority": "normal", "request_id": "legacy-stage-pending"}})
        response = self.service.handle("reporter_alice", "The water ran out at the Main Stage.")
        self.assertEqual("Stage", response["issue"]["location"])
        self.assertEqual("drinking_water", response["issue"]["category"])

    def test_dining_hall_variants_are_bounded_to_the_registered_location(self):
        for index, alias in enumerate(("DiningHall", "dining_hall", "dining-hall", "  DINING   HALL  ")):
            response = self.service.handle(f"reporter_dining_{index}", "A spill needs cleanup.", intent={
                "action": "report", "summary": "A spill needs cleanup.", "category": "cleanup", "location": alias},
                request_id=f"dining-alias-{index}")
            self.assertEqual("Dining Hall", response["issue"]["location"])
        for index, location in enumerate(("Main Stage 2", "Stage A", "Dining Hall balcony", "Terrace")):
            response = self.service.handle(f"reporter_unknown_{index}", "The speaker is silent.", intent={
                "action": "report", "summary": "The speaker is silent.", "category": "audio", "location": location})
            self.assertNotIn("issue", response)
            self.assertEqual([], response["offers"])
            self.assertEqual(["location"], [field["name"] for field in response["card"]["payload"]["fields"]])

    def test_descriptive_questions_answer_scope_without_consuming_pending_report(self):
        self.service.handle("reporter_alice", "Water issue in the Dining Hall.", request_id="pending-water")
        pending = self.service.context("reporter_alice")["pending_report"]
        for question in ("What can you do?", "Which locations do you support?",
                         "What can EventRelay do and which locations are supported?"):
            with self.subTest(question=question):
                response = self.service.handle("reporter_alice", question)
                self.assertIn("drinking water", response["text"])
                self.assertIn("Stage, Dining Hall, Entrance, and Washrooms", response["text"])
                self.assertNotIn("issue", response)
                self.assertEqual([], response["offers"])
                self.assertEqual(pending, self.service.context("reporter_alice")["pending_report"])
        self.assertEqual([], self.store.list_issues("wedding-demo"))

    def test_leaking_pipe_does_not_dispatch_power_crew(self):
        response = self.service.handle("reporter_alice", "A pipe is leaking water near the Stage.")
        self.assertNotIn("issue", response)
        self.assertEqual([], response["offers"])
        self.assertEqual("form", response["card"]["kind"])
        self.assertEqual(["category"], [field["name"] for field in response["card"]["payload"]["fields"]])
        self.assertEqual([], self.store.list_issues("wedding-demo"))

    def test_descriptive_words_inside_an_actual_report_do_not_hide_it(self):
        response = self.service.handle("reporter_alice", "The speaker at the Stage says 'what can you do' but has no sound.")
        self.assertEqual("audio", response["issue"]["category"])
        self.assertEqual("Stage", response["issue"]["location"])
        self.assertEqual("staff_ravi", response["issue"]["offered_to"])

    def test_asi_clarification_enriches_the_original_ambiguous_report(self):
        original = "Water issue in the Dining Hall."
        detail = "It is a cleanup issue involving a water spill in the Dining Hall."
        self.service.handle("reporter_alice", original, request_id="water-clarification")
        response = self.service.handle("reporter_alice", detail, intent={
            "action": "report", "summary": detail, "category": "cleanup", "location": "Dining Hall"})
        issue = response["issue"]
        self.assertEqual(original + " Clarification: " + detail, issue["summary"])
        self.assertEqual("cleanup", issue["category"])
        self.assertEqual("Dining Hall", issue["location"])
        self.assertEqual("reporter_alice", issue["reporter_id"])

    def test_location_only_answers_and_native_selections_preserve_the_complaint(self):
        original = "The microphone is silent."
        for index, location in enumerate(("Stage", "at the Stage", "It is at the Stage.")):
            actor = "reporter_location_" + str(index)
            self.service.handle(actor, original, request_id="location-" + str(index))
            response = self.service.handle(actor, location)
            self.assertEqual(original, response["issue"]["summary"])
            self.assertEqual("Stage", response["issue"]["location"])
        complaint = "Water issue in the Dining Hall."
        self.service.handle("reporter_native", complaint, request_id="native-clarification")
        response = self.service.handle("reporter_native", '{"action":"report","category":"cleanup","clarification_id":"native-clarification"}')
        self.assertEqual(complaint, response["issue"]["summary"])

    def test_stale_clarification_cannot_enrich_or_dispatch_the_pending_report(self):
        self.service.handle("reporter_alice", "Water issue in the Dining Hall.", request_id="current-form")
        pending = self.service.context("reporter_alice")["pending_report"]
        response = self.service.handle("reporter_alice", "It is a spill.", intent={
            "action": "report", "summary": "It is a spill.", "category": "cleanup",
            "location": "Dining Hall", "clarification_id": "old-form"})
        self.assertEqual("stale_clarification", response["code"])
        self.assertEqual(pending, self.service.context("reporter_alice")["pending_report"])
        self.assertEqual([], self.store.list_issues("wedding-demo"))

    def test_repeated_clarification_does_not_duplicate_summary_detail(self):
        original = "There is a water issue."
        detail = "It is a cleanup issue involving a water spill."
        self.service.handle("reporter_alice", original, request_id="repeat-detail")
        clarification = {"action": "report", "summary": detail, "category": "cleanup",
                         "clarification_id": "repeat-detail"}
        for _ in range(2):
            self.service.handle("reporter_alice", detail, intent=clarification)
        pending = self.service.context("reporter_alice")["pending_report"]
        self.assertEqual(original + " Clarification: " + detail, pending["summary"])
        issue = self.service.handle("reporter_alice", "Dining Hall")["issue"]
        self.assertEqual(pending["summary"], issue["summary"])

    def test_clarification_summary_keeps_original_and_stays_within_store_limit(self):
        original = "Water issue: " + "x" * 930
        detail = "The water spill needs cleanup. " * 30
        self.service.handle("reporter_alice", original, request_id="bounded-detail")
        self.service.handle("reporter_alice", detail, intent={
            "action": "report", "summary": detail, "category": "cleanup"})
        pending = self.service.context("reporter_alice")["pending_report"]
        self.assertTrue(pending["summary"].startswith(original + " Clarification: "))
        self.assertLessEqual(len(pending["summary"]), 1000)
        self.assertGreater(len(pending["summary"]), len(original))
        issue = self.service.handle("reporter_alice", "Entrance")["issue"]
        self.assertEqual(pending["summary"], issue["summary"])

    def test_confirmation_instructions_never_close_a_completed_issue(self):
        issue = self.waiting_for_confirmation()
        response = self.service.handle("reporter_alice", "I've checked on site and the water supply is restored — how do I confirm the issue as resolved?")
        self.assertIn("same conversation", response["text"])
        self.assertIn("awaiting confirmation", response["text"])
        self.assertEqual([], response["offers"])
        self.assertNotIn("issue", response)
        current = self.store.issue(issue["issue_id"])
        self.assertEqual("awaiting_confirmation", current["status"])
        self.assertEqual(issue["version"], current["version"])

    def test_escalation_question_requests_reference_without_changing_the_issue(self):
        issue = self.report()["issue"]
        response = self.service.handle("reporter_bob", "The problem is still not resolved and the crew hasn't responded in a while — can you escalate it?")
        self.assertIn("exact ER-XXXXXXXX issue reference", response["text"])
        self.assertIn("No existing incident was changed", response["text"])
        self.assertNotIn("issue", response)
        self.assertEqual([], response["offers"])
        self.assertEqual(issue, self.store.issue(issue["issue_id"]))
        self.assertEqual(1, len(self.store.list_issues("wedding-demo")))
        self.assertRegex(response["review_request"]["review_id"], r"^RV-[0-9A-F]{8}$")
        self.assertEqual("queued", response["review_request"]["status"])
        self.assertEqual("reporter_bob", response["review_request"]["actor"])

    def test_malformed_issue_reference_never_becomes_a_new_report(self):
        for question in ("ER-10245", "Can you check the status of issue ER-10245? The speaker is silent at the Stage."):
            with self.subTest(question=question):
                response = self.service.handle("reporter_alice", question)
                self.assertIn("exactly eight hexadecimal characters", response["text"])
                self.assertEqual([], response["offers"])
                self.assertNotIn("issue", response)
                self.assertNotIn("card", response)
        self.assertEqual([], self.store.list_issues("wedding-demo"))
        response = self.service.handle("reporter_alice", "status ER-ABCDEF12")
        self.assertEqual("unknown_issue", response["code"])

    def test_open_overview_filters_private_and_closed_issues_without_mutation(self):
        own = self.report(request_id="alice-open")["issue"]
        hidden = self.report(actor="reporter_bob", request_id="bob-open", category="cleanup", location="Entrance")["issue"]
        closed = self.waiting_for_confirmation()
        self.action("reporter_alice", closed["issue_id"], "confirm")
        self.service.handle("reporter_alice", "Water issue in the Dining Hall.", request_id="pending-list")
        before_state = self.service._state("reporter_alice")
        before_issues = self.store.list_issues("wedding-demo")
        with patch.object(self.store, "tick", side_effect=AssertionError("Overview must not tick")):
            response = self.service.handle("reporter_alice", "Show me the current status of all open event issues")
        self.assertEqual([own["issue_id"]], [issue["issue_id"] for issue in response["issues"]])
        self.assertNotIn(hidden["issue_id"], response["text"])
        self.assertNotIn(closed["issue_id"], response["text"])
        self.assertEqual([], response["offers"])
        self.assertEqual(before_state, self.service._state("reporter_alice"))
        self.assertEqual(before_issues, self.store.list_issues("wedding-demo"))
        stranger = self.service.handle("reporter_stranger", '{"action":"list_open","actor":"organizer_demo"}')
        self.assertEqual([], stranger["issues"])
        self.assertIn("No open issues are visible", stranger["text"])

    def test_open_overview_filters_before_limiting_to_twenty_visible_results(self):
        hidden = [self.report(actor="reporter_bob", request_id=f"hidden-{i}")["issue"]["issue_id"] for i in range(21)]
        visible = [self.report(actor="reporter_alice", request_id=f"visible-{i}")["issue"]["issue_id"] for i in range(21)]
        response = self.service.handle("reporter_alice", "List all open issues.")
        self.assertEqual(20, len(response["issues"]))
        self.assertTrue({issue["issue_id"] for issue in response["issues"]}.issubset(visible))
        self.assertIn("showing 20 of 21", response["text"])
        self.assertTrue(all(reference not in response["text"] for reference in hidden))
        self.assertEqual([], response["offers"])

    def test_unlinked_escalation_acknowledges_context_without_unrelated_incidents(self):
        os.environ["EVENTRELAY_DEMO_MODE"] = "1"
        own = self.report(request_id="alice-escalation-choice")["issue"]
        hidden = self.report(actor="reporter_bob", request_id="bob-escalation-choice", category="cleanup", location="Entrance")["issue"]
        before = self.service._state("reporter_alice")
        with patch.object(self.store, "tick", side_effect=AssertionError("Issue choice must not tick")):
            response = self.service.handle("reporter_alice", "The problem is still not resolved and the crew hasn't responded in a while — can you escalate it?")
        self.assertIn("problem is still unresolved and the crew has not responded", response["text"])
        self.assertIn("Escalation request recorded for organizer review as " + response["review_request"]["review_id"] + " (queued)", response["text"])
        self.assertNotIn(own["issue_id"], response["text"])
        self.assertNotIn(hidden["issue_id"], response["text"])
        self.assertNotIn("issues", response)
        self.assertNotIn("Open issues", response["text"])
        self.assertIn("DEMO: synthetic", response["text"])
        self.assertEqual([], response["offers"])
        after = self.service._state("reporter_alice")
        self.assertEqual(before, {key: value for key, value in after.items() if key != "review_requests"})
        self.assertEqual(1, len(after["review_requests"]))
        self.assertEqual(own, self.store.issue(own["issue_id"]))
        self.assertEqual(2, len(self.store.list_issues("wedding-demo")))

    def test_unlinked_review_retries_preserve_pending_and_last_issue(self):
        issue = self.report()["issue"]
        self.service.handle("reporter_alice", "Water issue in the Dining Hall.", request_id="pending-review-context")
        before = self.service._state("reporter_alice")
        prompt = "The problem is still not resolved — can you escalate it?"
        first = self.service.handle("reporter_alice", prompt, request_id="chat-message-uuid")
        replay = self.service.handle("reporter_alice", prompt, request_id="chat-message-uuid")
        self.assertEqual(first["review_request"], replay["review_request"])
        self.assertIn("Escalation request recorded for organizer review as " + first["review_request"]["review_id"], first["text"])
        self.assertEqual("queued", first["review_request"]["status"])
        after = self.service._state("reporter_alice")
        self.assertEqual(before, {key: value for key, value in after.items() if key != "review_requests"})
        self.assertEqual(1, len(after["review_requests"]))
        self.assertEqual(issue, self.store.issue(issue["issue_id"]))
        conflict = self.service.handle("reporter_alice", "Can you escalate a different problem?", request_id="chat-message-uuid")
        self.assertEqual("idempotency_conflict", conflict["code"])
        self.assertEqual([], conflict["offers"])
        self.assertEqual(after, self.service._state("reporter_alice"))

    def test_generic_review_request_does_not_invent_unresponsive_crew(self):
        response = self.service.handle("reporter_alice", "Can you escalate it?", request_id="generic-review")
        self.assertIn("Your request for organizer follow-up has been recorded", response["text"])
        self.assertNotIn("crew has not responded", response["text"])
        self.assertNotIn("problem is still unresolved", response["text"])
        self.assertEqual("queued", response["review_request"]["status"])
        self.assertEqual([], self.store.list_issues("wedding-demo"))

    def test_unlinked_review_queue_bounds_notes_and_never_drops_queued_requests(self):
        for index in range(20):
            response = self.service.handle("reporter_alice", "Request review", intent={
                "action": "escalate", "note": "x" * 1500}, request_id=f"review-{index}")
            self.assertEqual(1000, len(response["review_request"]["note"]))
        before = self.service._state("reporter_alice")
        full = self.service.handle("reporter_alice", "Can you escalate it?", request_id="one-too-many")
        self.assertEqual("review_queue_full", full["code"])
        self.assertEqual([], full["offers"])
        self.assertEqual(before, self.service._state("reporter_alice"))
        replay = self.service.handle("reporter_alice", "Request review", intent={
            "action": "escalate", "note": "x" * 1500}, request_id="review-0")
        self.assertEqual(before["review_requests"][0], replay["review_request"])
        self.assertEqual([], self.store.list_issues("wedding-demo"))

    def test_review_requests_are_own_only_and_aggregate_requires_organizer_even_demo(self):
        alice = self.service.handle("reporter_alice", "Can you escalate the audio problem?", request_id="alice-review")["review_request"]
        bob = self.service.handle("reporter_bob", "Can you escalate the cleanup problem?", request_id="bob-review")["review_request"]
        for mode in ("0", "1"):
            os.environ["EVENTRELAY_DEMO_MODE"] = mode
            own = self.service.handle("reporter_alice", "my review requests")
            self.assertEqual([alice], own["review_requests"])
            self.assertNotIn(bob["review_id"], own["text"])
            denied = self.service.handle("reporter_alice", '{"action":"organizer_review_queue","actor":"organizer_demo"}')
            self.assertEqual("wrong_actor", denied["code"])
            self.assertNotIn("review_requests", denied)
            self.assertNotIn(bob["review_id"], denied["text"])
        queue = self.service.handle("organizer_demo", "organizer review queue")
        self.assertEqual({alice["review_id"], bob["review_id"]}, {item["review_id"] for item in queue["review_requests"]})
        self.assertEqual([], queue["offers"])

    def test_review_listings_and_how_to_questions_are_read_only(self):
        self.service.handle("reporter_alice", "Can you escalate it?", request_id="read-only-review")
        self.service.handle("reporter_alice", "Water issue in the Dining Hall.", request_id="pending-listing")
        before = self.service._state("reporter_alice")
        with patch.object(self.store, "tick", side_effect=AssertionError("Listing must not tick")), \
             patch.object(self.service, "_save", side_effect=AssertionError("Listing must not save")):
            for actor, command in (("reporter_alice", "my review requests"),
                                   ("organizer_demo", "organizer review queue"),
                                   ("reporter_alice", "How do I escalate an issue?")):
                response = self.service.handle(actor, command)
                self.assertEqual([], response["offers"])
        self.assertEqual(before, self.service._state("reporter_alice"))
        self.assertEqual([], self.store.list_issues("wedding-demo"))

    def test_known_escalation_uses_actual_reporter_authority_even_in_demo(self):
        os.environ["EVENTRELAY_DEMO_MODE"] = "1"
        issue = self.report()["issue"]
        prompt = "Can you escalate " + issue["issue_id"] + "?"
        denied = self.service.handle("reporter_bob", prompt, request_id="unauthorized-review")
        self.assertEqual("wrong_actor", denied["code"])
        self.assertEqual([], denied["offers"])
        self.assertEqual(issue, self.store.issue(issue["issue_id"]))
        before_state = self.service._state("reporter_alice")
        requested = self.service.handle("reporter_alice", prompt, request_id="authorized-review")
        self.assertTrue(requested["issue"]["escalated"])
        self.assertEqual(issue["status"], requested["issue"]["status"])
        self.assertEqual(issue["offered_to"], requested["issue"]["offered_to"])
        self.assertEqual(issue["version"], requested["issue"]["version"])
        self.assertEqual([], requested["offers"])
        self.assertEqual(before_state, self.service._state("reporter_alice"))

    def test_model_cannot_guess_an_owned_last_issue_for_escalation(self):
        issue = self.report()["issue"]
        before = self.service._state("reporter_alice")
        response = self.service.handle("reporter_alice", "Please get an organizer to review the unresolved problem.", intent={
            "action": "escalate", "issue_id": issue["issue_id"], "note": "Model selected the last issue."},
            request_id="unlinked-not-guessed")
        self.assertEqual("queued", response["review_request"]["status"])
        self.assertNotIn("Model selected", response["review_request"]["note"])
        self.assertEqual(issue, self.store.issue(issue["issue_id"]))
        after = self.service._state("reporter_alice")
        self.assertEqual(before, {key: value for key, value in after.items() if key != "review_requests"})
        self.assertEqual([], response["offers"])

    def test_standalone_reference_and_identified_escalation_use_status_authority(self):
        issue = self.report()["issue"]
        denied = self.service.handle("reporter_bob", issue["issue_id"])
        self.assertEqual("wrong_actor", denied["code"])
        response = self.service.handle("reporter_alice", issue["issue_id"].lower())
        self.assertEqual(issue["issue_id"], response["issue"]["issue_id"])
        response = self.service.handle("reporter_alice", "Can you escalate " + issue["issue_id"] + "?")
        self.assertEqual(issue["issue_id"], response["issue"]["issue_id"])
        unknown = self.service.handle("reporter_stranger", "ER-ABCDEF12")
        self.assertEqual("unknown_issue", unknown["code"])
        self.assertEqual([], unknown["offers"])
        malformed = self.service.handle("reporter_stranger", "ER-102934")
        self.assertIn("exactly eight hexadecimal characters", malformed["text"])
        self.assertEqual(1, len(self.store.list_issues("wedding-demo")))

    def test_overview_words_inside_a_report_do_not_hide_the_incident(self):
        response = self.service.handle("reporter_alice", "There is a spill at the Entrance. Show me all open event issues.")
        self.assertEqual("cleanup", response["issue"]["category"])
        self.assertEqual("Entrance", response["issue"]["location"])

    def test_cleanup_without_available_crew_explains_actual_organizer_escalation(self):
        os.environ["EVENTRELAY_DEMO_MODE"] = "1"
        for index in range(2):
            issue = self.report(category="cleanup", location="Dining Hall",
                                summary="A spill needs cleanup in the Dining Hall.", request_id=f"busy-cleanup-{index}")["issue"]
            self.action(issue["offered_to"], issue["issue_id"], "accept")
        response = self.report(category="cleanup", location="Dining Hall",
                               summary="Another spill needs cleanup in the Dining Hall.", request_id="no-cleanup-capacity")
        issue = response["issue"]
        self.assertEqual("escalated", issue["status"])
        self.assertEqual("no_available_staff", issue["escalation_reason"])
        self.assertIsNone(issue["assigned_to"])
        self.assertEqual([], response["offers"])
        self.assertIn(issue["issue_id"], response["text"])
        self.assertIn("No eligible configured cleanup crew is currently available", response["text"])
        self.assertIn("escalated for organizer attention", response["text"])
        self.assertIn("nobody has accepted", response["text"])
        self.assertIn("DEMO: synthetic", response["text"])
        self.assertNotIn("no_available_staff", response["text"])

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
        self.assertEqual("Water issue in the Dining Hall. Clarification: It is drinking water refill.", alice["summary"])
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
