import os
from pathlib import Path
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from eventrelay.store import EventStore, StoreError


class Clock:
    def __init__(self):
        self.value = 1000.0

    def __call__(self):
        return self.value


class EventStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("EVENTRELAY_TEST_TEMP"))
        self.path = Path(self.temp.name) / "events.sqlite"
        self.clock = Clock()
        self.store = EventStore(self.path, self.clock)
        self.store.seed_demo()
        self.sequence = 0

    def tearDown(self):
        self.temp.cleanup()

    def report(self, category="audio", **changes):
        self.sequence += 1
        args = dict(event_id="wedding-demo", reporter_id="host_1", summary="Microphone is silent",
                    category=category, location="Stage", idempotency_key=f"report-{self.sequence}")
        args.update(changes)
        return self.store.report(**args)

    def accepted(self, category="audio", **changes):
        issue = self.report(category, **changes)
        return self.store.acknowledge(issue["issue_id"], issue["offered_to"], expected_version=issue["version"])

    def assertDenied(self, code, operation):
        with self.assertRaises(StoreError) as caught:
            operation()
        self.assertEqual(code, caught.exception.code)

    def test_offer_is_not_acceptance_and_only_offered_staff_can_accept(self):
        issue = self.report()
        self.assertEqual("offered", issue["status"])
        self.assertIsNone(issue["assigned_to"])
        self.assertEqual("staff_ravi", issue["offered_to"])
        self.assertDenied("wrong_actor", lambda: self.store.acknowledge(issue["issue_id"], "staff_sara"))
        accepted = self.store.acknowledge(issue["issue_id"], "staff_ravi")
        self.assertEqual("accepted", accepted["status"])
        self.assertEqual("staff_ravi", accepted["assigned_to"])
        self.assertIsNone(accepted["offered_to"])

    def test_requested_escalation_preserves_crew_capacity_deadlines_and_retries(self):
        before = self.accepted()
        issue_id = before["issue_id"]
        self.clock.value += 1
        reviewed = self.store.request_escalation(issue_id, "host_1", "Crew has not responded.",
                                                expected_version=before["version"], idempotency_key="review-message-1")
        for field in ("status", "version", "assigned_to", "offered_to", "offer_expires_at", "resolution_deadline", "accepted_at"):
            self.assertEqual(before[field], reviewed[field])
        self.assertTrue(reviewed["escalated"])
        self.assertEqual("organizer_review_requested", reviewed["escalation_reason"])
        replay = self.store.request_escalation(issue_id, "host_1", "Crew has not responded.",
                                              expected_version=before["version"], idempotency_key="review-message-1")
        self.assertEqual(reviewed, replay)
        self.assertEqual(1, sum(item["event"] == "organizer_review_requested" for item in replay["history"]))
        self.assertEqual("staff_sara", self.report()["offered_to"])
        self.assertDenied("idempotency_conflict", lambda: self.store.request_escalation(
            issue_id, "host_1", "Changed note", idempotency_key="review-message-1"))

    def test_review_metadata_does_not_invalidate_an_inflight_staff_offer(self):
        offered = self.report()
        self.store.request_escalation(offered["issue_id"], "host_1", "Please review this unaccepted offer.",
                                      expected_version=offered["version"], idempotency_key="offered-review")
        accepted = self.store.acknowledge(offered["issue_id"], offered["offered_to"], expected_version=offered["version"])
        self.assertEqual("accepted", accepted["status"])
        self.assertEqual(offered["offered_to"], accepted["assigned_to"])

    def test_requested_escalation_requires_reporter_or_organizer_even_in_demo(self):
        issue = self.accepted()
        for actor in ("another_reporter", "staff_ravi"):
            self.assertDenied("wrong_actor", lambda actor=actor: self.store.request_escalation(issue["issue_id"], actor))
        self.assertEqual(issue, self.store.issue(issue["issue_id"]))
        result = self.store.request_escalation(issue["issue_id"], "organizer_demo", idempotency_key="organizer-review")
        self.assertTrue(result["escalated"])
        self.assertEqual(issue["assigned_to"], result["assigned_to"])

    def test_requested_escalation_respects_completed_closed_and_stale_versions(self):
        offered = self.report()
        accepted = self.store.acknowledge(offered["issue_id"], offered["offered_to"])
        self.assertDenied("stale_version", lambda: self.store.request_escalation(
            offered["issue_id"], "host_1", expected_version=offered["version"]))
        self.assertEqual(accepted, self.store.issue(offered["issue_id"]))
        completed = self.store.complete(offered["issue_id"], accepted["assigned_to"], "Crew reports a sound check.")
        self.assertDenied("invalid_transition", lambda: self.store.request_escalation(offered["issue_id"], "host_1"))
        self.assertEqual(completed, self.store.issue(offered["issue_id"]))
        closed = self.store.confirm(offered["issue_id"], "host_1", True)
        self.assertDenied("invalid_transition", lambda: self.store.request_escalation(offered["issue_id"], "host_1"))
        self.assertEqual(closed, self.store.issue(offered["issue_id"]))

    def test_concurrent_same_review_request_records_one_audit_event(self):
        issue = self.accepted()
        def request(_):
            return self.store.request_escalation(issue["issue_id"], "host_1", "Please review.",
                                                 expected_version=issue["version"], idempotency_key="same-review")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(request, range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(1, sum(item["event"] == "organizer_review_requested" for item in results[0]["history"]))

    def test_decline_uses_backup_then_escalates_without_claiming_acceptance(self):
        issue = self.report()
        backup = self.store.acknowledge(issue["issue_id"], "staff_ravi", "decline")
        self.assertEqual("staff_sara", backup["offered_to"])
        self.assertEqual("offered", backup["status"])
        escalated = self.store.acknowledge(issue["issue_id"], "staff_sara", "decline")
        self.assertEqual("escalated", escalated["status"])
        self.assertIsNone(escalated["assigned_to"])
        self.assertIsNone(escalated["offered_to"])

    def test_timeout_reroutes_once_then_unowned_escalation_is_visible(self):
        issue = self.report()
        self.clock.value += 60
        changed = self.store.tick("wedding-demo")
        self.assertEqual(1, len(changed))
        self.assertEqual("staff_sara", changed[0]["offered_to"])
        self.clock.value += 60
        self.assertEqual("escalated", self.store.tick("wedding-demo")[0]["status"])
        self.assertEqual([], self.store.tick("wedding-demo"))
        self.assertFalse(any(event["event"] == "accepted" for event in self.store.issue(issue["issue_id"])["events"]))

    def test_accepting_expired_offer_persists_reroute_but_denies_old_actor(self):
        issue = self.report()
        self.clock.value += 61
        self.assertDenied("offer_expired", lambda: self.store.acknowledge(issue["issue_id"], "staff_ravi"))
        self.assertEqual("staff_sara", self.store.issue(issue["issue_id"])["offered_to"])

    def test_closed_requires_reporter_confirmation_and_reopen_routes_same_issue(self):
        issue = self.accepted()
        self.assertDenied("wrong_actor", lambda: self.store.start(issue["issue_id"], "staff_sara"))
        started = self.store.start(issue["issue_id"], "staff_ravi")
        completed = self.store.complete(issue["issue_id"], "staff_ravi", "Crew reports the spare mic is working")
        self.assertEqual("awaiting_confirmation", completed["status"])
        self.assertDenied("wrong_actor", lambda: self.store.confirm(issue["issue_id"], "staff_ravi", True))
        reopened = self.store.confirm(issue["issue_id"], "host_1", False, "Still silent")
        self.assertEqual(issue["issue_id"], reopened["issue_id"])
        self.assertEqual("offered", reopened["status"])
        self.assertEqual("staff_ravi", reopened["offered_to"])
        self.store.acknowledge(issue["issue_id"], "staff_ravi")
        self.store.complete(issue["issue_id"], "staff_ravi", "Crew reports sound checked")
        closed = self.store.confirm(issue["issue_id"], "organizer_demo", True, "Host confirms it works")
        self.assertEqual("closed", closed["status"])
        self.assertGreater(closed["version"], started["version"])

    def test_completion_frees_capacity_but_does_not_close(self):
        first = self.accepted()
        second = self.report()
        self.assertEqual("staff_sara", second["offered_to"])
        completed = self.store.complete(first["issue_id"], "staff_ravi", "Crew reports complete")
        self.assertEqual("awaiting_confirmation", completed["status"])
        third = self.report()
        self.assertEqual("staff_ravi", third["offered_to"])

    def test_idempotent_reports_persist_and_changed_payload_conflicts(self):
        first = self.report(idempotency_key="duplicate-key")
        second = self.report(idempotency_key="duplicate-key")
        self.assertEqual(first["issue_id"], second["issue_id"])
        self.assertEqual(1, len(self.store.list_issues("wedding-demo")))
        self.assertDenied("idempotency_conflict", lambda: self.report(idempotency_key="duplicate-key", summary="Different issue"))
        reopened = EventStore(self.path, self.clock)
        reopened.seed_demo()
        self.assertEqual(first["issue_id"], reopened.list_issues("wedding-demo")[0]["issue_id"])

    def test_stale_acknowledgement_and_completion_are_rejected(self):
        issue = self.report()
        accepted = self.store.acknowledge(issue["issue_id"], "staff_ravi", expected_version=issue["version"])
        self.assertDenied("stale_version", lambda: self.store.acknowledge(issue["issue_id"], "staff_ravi", expected_version=issue["version"]))
        self.store.start(issue["issue_id"], "staff_ravi")
        self.assertDenied("stale_version", lambda: self.store.complete(issue["issue_id"], "staff_ravi", "Done", expected_version=accepted["version"]))

    def test_start_and_confirmation_check_atomic_versions_but_closed_replay_is_idempotent(self):
        issue = self.accepted()
        self.assertDenied("stale_version", lambda: self.store.start(issue["issue_id"], "staff_ravi", expected_version=issue["version"] - 1))
        started = self.store.start(issue["issue_id"], "staff_ravi", expected_version=issue["version"])
        completed = self.store.complete(issue["issue_id"], "staff_ravi", "Crew reports working", expected_version=started["version"])
        self.assertDenied("stale_version", lambda: self.store.confirm(issue["issue_id"], "host_1", True, expected_version=started["version"]))
        closed = self.store.confirm(issue["issue_id"], "host_1", True, expected_version=completed["version"])
        replay = self.store.confirm(issue["issue_id"], "host_1", True, expected_version=completed["version"])
        self.assertEqual("closed", replay["status"])
        self.assertEqual(closed["version"], replay["version"])
        self.assertEqual(1, sum(event["event"] == "confirmed_closed" for event in replay["events"]))
        self.assertDenied("wrong_actor", lambda: self.store.confirm(issue["issue_id"], "unknown", True))

    def test_none_actor_cannot_link_dependency_by_matching_unassigned_staff(self):
        parent = self.report()
        child = self.report("cleanup")
        self.assertDenied("invalid_request", lambda: self.store.link_dependency(parent["issue_id"], child["issue_id"], None))
        self.assertEqual("offered", self.store.issue(parent["issue_id"])["status"])

    def test_bad_actor_or_completion_note_types_fail_as_safe_errors(self):
        issue = self.accepted()
        self.assertDenied("invalid_request", lambda: self.store.complete(issue["issue_id"], "staff_ravi", {"note": "bad"}))
        self.assertDenied("invalid_request", lambda: self.store.complete(issue["issue_id"], "staff_ravi", "x" * 1001))
        self.assertDenied("invalid_request", lambda: self.store.start(issue["issue_id"], None))
        self.assertDenied("invalid_request", lambda: self.store.confirm(issue["issue_id"], None, True))

    def test_event_deadlines_are_configurable_persistent_and_not_arrival_promises(self):
        self.assertDenied("wrong_actor", lambda: self.store.configure_timeouts("wedding-demo", 2, 5, "guest"))
        self.store.configure_timeouts("wedding-demo", 2, 5)
        issue = self.report()
        self.assertEqual(self.clock.value + 2, issue["accept_by"])
        self.clock.value += 2
        changed = self.store.tick("wedding-demo")
        self.assertEqual("staff_sara", changed[0]["offered_to"])
        accepted = self.store.acknowledge(issue["issue_id"], "staff_sara")
        self.assertEqual(self.clock.value + 5, accepted["follow_up_at"])
        reopened = EventStore(self.path, self.clock)
        reopened.seed_demo()
        water = reopened.report("wedding-demo", "host", "Water refill", "drinking_water", "Dining Hall", idempotency_key="water")
        self.assertEqual(self.clock.value + 2, water["accept_by"])

    def test_followup_escalates_without_freeing_staff_or_faking_completion(self):
        issue = self.accepted()
        self.clock.value += 300
        changed = self.store.tick("wedding-demo")
        self.assertTrue(changed[0]["escalated"])
        self.assertEqual("accepted", changed[0]["status"])
        self.assertEqual("staff_ravi", changed[0]["assigned_to"])
        self.assertEqual([], self.store.tick("wedding-demo"))
        self.assertEqual("staff_sara", self.report()["offered_to"])
        self.assertEqual("awaiting_confirmation", self.store.complete(issue["issue_id"], "staff_ravi", "Crew now reports completion")["status"])

    def test_dependency_blocks_completion_until_child_is_reporter_confirmed_closed(self):
        parent = self.accepted()
        child = self.accepted("cleanup", summary="Spill reported near stage")
        self.assertDenied("wrong_actor", lambda: self.store.link_dependency(parent["issue_id"], child["issue_id"], "unrelated_guest"))
        blocked = self.store.link_dependency(parent["issue_id"], child["issue_id"], "staff_ravi")
        self.assertEqual("blocked", blocked["status"])
        self.assertDenied("dependency_open", lambda: self.store.complete(parent["issue_id"], "staff_ravi", "Done"))
        self.store.complete(child["issue_id"], "staff_meena", "Crew reports cleanup complete")
        self.assertEqual("blocked", self.store.issue(parent["issue_id"])["status"])
        self.store.confirm(child["issue_id"], "host_1", True, "Reported area task confirmed complete")
        resumed = self.store.issue(parent["issue_id"])
        self.assertEqual("accepted", resumed["status"])
        self.assertEqual([], resumed["blocked_by"])
        self.assertEqual("awaiting_confirmation", self.store.complete(parent["issue_id"], "staff_ravi", "Audio check reported complete")["status"])

    def test_dependency_can_block_offer_before_acceptance_and_cycles_are_denied(self):
        parent = self.report()
        child = self.report("cleanup")
        self.store.link_dependency(parent["issue_id"], child["issue_id"], "organizer_demo")
        self.assertDenied("dependency_cycle", lambda: self.store.link_dependency(child["issue_id"], parent["issue_id"], "organizer_demo"))
        accepted = self.store.acknowledge(parent["issue_id"], "staff_ravi")
        self.assertEqual("blocked", accepted["status"])
        self.assertEqual("accepted", accepted["resume_status"])

    def test_concurrent_reports_never_reserve_one_staff_member_twice(self):
        barrier = threading.Barrier(3)

        def create(index):
            barrier.wait(timeout=5)
            return self.store.report("wedding-demo", f"guest-{index}", "Microphone fault",
                                     "audio", "Stage", idempotency_key=f"concurrent-{index}")

        with ThreadPoolExecutor(max_workers=3) as pool:
            issues = list(pool.map(create, range(3)))
        offered = [issue["offered_to"] for issue in issues if issue["offered_to"]]
        self.assertCountEqual(["staff_ravi", "staff_sara"], offered)
        self.assertEqual(1, sum(issue["status"] == "escalated" for issue in issues))

    def test_unavailable_staff_and_invalid_routes_are_explicit(self):
        self.assertDenied("wrong_actor", lambda: self.store.set_availability("staff_ravi", False, "guest"))
        self.store.set_availability("staff_ravi", False)
        self.assertEqual("staff_sara", self.report()["offered_to"])
        self.assertDenied("unknown_category", lambda: self.report(category="water issue"))
        self.assertDenied("unknown_location", lambda: self.report(location="somewhere"))
        self.assertDenied("invalid_request", lambda: self.report(idempotency_key=None))
        roster = self.store.roster("wedding-demo")
        self.assertEqual(8, len(roster))
        self.assertTrue(all(row["synthetic"] for row in roster))

    def test_availability_revoked_after_offer_is_rechecked_atomically_before_acceptance(self):
        issue = self.report()
        self.assertEqual("staff_ravi", issue["offered_to"])
        self.store.set_availability("staff_ravi", False)
        self.assertDenied("staff_unavailable", lambda: self.store.acknowledge(
            issue["issue_id"], "staff_ravi", expected_version=issue["version"]))
        current = self.store.issue(issue["issue_id"])
        self.assertEqual("offered", current["status"])
        self.assertEqual("staff_sara", current["offered_to"])
        self.assertIsNone(current["assigned_to"])
        self.assertTrue(any(event["event"] == "offer_withdrawn" for event in current["events"]))
        self.assertFalse(any(event["event"] == "accepted" for event in current["events"]))
        self.assertGreater(current["version"], issue["version"])

    def test_availability_change_after_acceptance_does_not_silently_cancel_responsibility(self):
        issue = self.accepted()
        self.store.set_availability("staff_ravi", False)
        current = self.store.issue(issue["issue_id"])
        self.assertEqual("accepted", current["status"])
        self.assertEqual("staff_ravi", current["assigned_to"])
        self.assertEqual("awaiting_confirmation", self.store.complete(issue["issue_id"], "staff_ravi", "Crew reports completion")["status"])


if __name__ == "__main__":
    unittest.main()
