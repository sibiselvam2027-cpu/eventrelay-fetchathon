import json
import os
import unittest
from unittest.mock import patch

from eventrelay.hosted_state import HostedStateError, STORAGE_KEY, open_hosted_service


class MemoryStorage:
    def __init__(self):
        self.values = {}
        self.writes = 0

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.writes += 1
        self.values[key] = value


class Clock:
    def __init__(self):
        self.value = 1000.0

    def __call__(self):
        return self.value


class HostedStateTests(unittest.TestCase):
    def setUp(self):
        self.storage = MemoryStorage()
        self.clock = Clock()
        self.environment = patch.dict(os.environ, {"EVENTRELAY_DEMO_MODE": "1"})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()

    def step(self, callback):
        # Every operation reconstructs all globals, just like hosted handlers.
        with open_hosted_service(self.storage, now=self.clock) as session:
            return callback(session)

    def action(self, actor, intent, request_id=None):
        return self.step(lambda session: session.service.handle(
            actor, json.dumps(intent), intent=intent, request_id=request_id))

    def test_complete_workflow_survives_every_invocation_reset(self):
        clarify = self.action("host", {"action": "report", "summary": "Water issue"}, "request-1")
        self.assertFalse(clarify["offers"])
        context = self.step(lambda session: session.service.context("host"))
        self.assertEqual("Water issue", context["pending_report"]["summary"])
        reported = self.action("host", {"action": "report", "category": "drinking_water", "location": "Dining Hall"})["issue"]
        issue_id = reported["issue_id"]
        self.assertEqual("staff_arun", reported["offered_to"])
        declined = self.action("staff_arun", {"action": "decline", "issue_id": issue_id, "version": reported["version"]})["issue"]
        self.assertEqual("staff_neha", declined["offered_to"])
        accepted = self.action("staff_neha", {"action": "accept", "issue_id": issue_id, "version": declined["version"]})["issue"]
        started = self.action("staff_neha", {"action": "start", "issue_id": issue_id, "version": accepted["version"]})["issue"]
        completed = self.action("staff_neha", {"action": "done", "issue_id": issue_id, "version": started["version"], "note": "Synthetic crew reports refill complete"})["issue"]
        self.assertEqual("awaiting_confirmation", completed["status"])
        reopened = self.action("host", {"action": "reopen", "issue_id": issue_id, "version": completed["version"], "note": "Still no bottles"})["issue"]
        self.assertEqual("staff_arun", reopened["offered_to"])
        accepted = self.action("staff_arun", {"action": "accept", "issue_id": issue_id, "version": reopened["version"]})["issue"]
        completed = self.action("staff_arun", {"action": "done", "issue_id": issue_id, "version": accepted["version"], "note": "Synthetic crew reports second refill"})["issue"]
        closed = self.action("host", {"action": "confirm", "issue_id": issue_id, "version": completed["version"]})["issue"]
        self.assertEqual("closed", closed["status"])
        replay = self.action("host", {"action": "confirm", "issue_id": issue_id, "version": completed["version"]})["issue"]
        self.assertEqual(closed["version"], replay["version"])
        duplicate = self.action("host", {"action": "report", "summary": "Water issue", "category": "drinking_water", "location": "Dining Hall"}, "request-1")["issue"]
        self.assertEqual(issue_id, duplicate["issue_id"])
        self.assertEqual(1, self.step(lambda session: len(session.store.list_issues("wedding-demo"))))
        self.assertTrue(any(event["event"] == "declined" for event in closed["events"]))
        self.assertTrue(any(event["event"] == "reopened" for event in closed["events"]))
        self.assertEqual(1, sum(event["event"] == "confirmed_closed" for event in replay["events"]))

    def test_deadlines_and_backups_survive_reconstruction(self):
        self.step(lambda session: session.store.configure_timeouts("wedding-demo", 2, 5))
        issue = self.step(lambda session: session.store.report("wedding-demo", "host", "Speaker silent", "audio", "Stage", idempotency_key="timeout"))
        self.clock.value += 2
        changed = self.step(lambda session: session.store.tick("wedding-demo"))
        self.assertEqual("staff_sara", changed[0]["offered_to"])
        accepted = self.step(lambda session: session.store.acknowledge(issue["issue_id"], "staff_sara"))
        self.assertEqual(self.clock.value + 5, accepted["follow_up_at"])
        self.clock.value += 5
        followed_up = self.step(lambda session: session.store.tick("wedding-demo"))
        self.assertTrue(followed_up[0]["escalated"])
        self.assertEqual("accepted", followed_up[0]["status"])

    def test_dependencies_and_authority_persist(self):
        parent = self.step(lambda session: session.store.report("wedding-demo", "host", "Audio check", "audio", "Stage", idempotency_key="parent"))
        child = self.step(lambda session: session.store.report("wedding-demo", "host", "Stage cleanup", "cleanup", "Stage", idempotency_key="child"))
        self.step(lambda session: session.store.acknowledge(parent["issue_id"], "staff_ravi"))
        self.step(lambda session: session.store.acknowledge(child["issue_id"], "staff_meena"))
        self.step(lambda session: session.store.link_dependency(parent["issue_id"], child["issue_id"], "staff_ravi"))
        self.assertEqual("blocked", self.step(lambda session: session.store.issue(parent["issue_id"]))["status"])
        self.step(lambda session: session.store.complete(child["issue_id"], "staff_meena", "Synthetic crew reports cleanup complete"))
        self.step(lambda session: session.store.confirm(child["issue_id"], "host", True))
        self.assertEqual("accepted", self.step(lambda session: session.store.issue(parent["issue_id"]))["status"])

    def test_one_serializable_storage_value_no_files_or_inherited_secrets(self):
        with patch.dict(os.environ, {"ASI1_API_KEY": "SENSITIVE-NEVER-IN-SNAPSHOT"}):
            with patch("pathlib.Path.mkdir", side_effect=AssertionError("No filesystem state allowed")):
                info = self.step(lambda session: session.checkpoint())
        self.assertEqual([STORAGE_KEY], list(self.storage.values))
        stored = self.storage.values[STORAGE_KEY]
        snapshot = json.loads(stored)
        self.assertEqual(1, snapshot["schema_version"])
        self.assertIn("CREATE TABLE", snapshot["event_sql"])
        self.assertIn("conversations", snapshot["conversation_sql"])
        self.assertNotIn("SENSITIVE-NEVER-IN-SNAPSHOT", stored)
        self.assertGreater(info["snapshot_bytes"], 0)

    def test_existing_dict_snapshot_is_supported_and_closed_session_cannot_checkpoint(self):
        self.step(lambda session: None)
        self.storage.values[STORAGE_KEY] = json.loads(self.storage.values[STORAGE_KEY])
        session = open_hosted_service(self.storage, now=self.clock)
        self.assertEqual(8, len(session.store.roster("wedding-demo")))
        session.close()
        session.close()
        with self.assertRaises(HostedStateError):
            session.checkpoint()

    def test_invalid_snapshot_is_not_silently_replaced(self):
        for value in ("not-json", {"schema_version": 2}, {"schema_version": 1, "event_sql": [], "conversation_sql": ""}):
            with self.subTest(value=value):
                self.storage.values[STORAGE_KEY] = value
                writes = self.storage.writes
                with self.assertRaises(HostedStateError):
                    open_hosted_service(self.storage, now=self.clock)
                self.assertEqual(writes, self.storage.writes)

    def test_unlinked_review_queue_survives_every_invocation_and_retry(self):
        self.action("host", {"action": "report", "summary": "Water issue"}, "pending-before-review")
        before = self.step(lambda session: session.service._state("host"))
        intent = {"action": "escalate", "note": "The crew has not responded; organizer review is needed."}
        first = self.action("host", intent, "stable-chat-message")["review_request"]
        replay = self.action("host", intent, "stable-chat-message")["review_request"]
        self.assertEqual(first, replay)
        own = self.action("host", {"action": "my_review_requests"})
        self.assertEqual([first], own["review_requests"])
        after = self.step(lambda session: session.service._state("host"))
        self.assertEqual(before, {key: value for key, value in after.items() if key != "review_requests"})
        self.assertEqual([], self.action("other", {"action": "my_review_requests"})["review_requests"])
        denied = self.action("other", {"action": "organizer_review_queue", "actor": "organizer_demo"})
        self.assertEqual("wrong_actor", denied["code"])
        queue = self.action("organizer_demo", {"action": "organizer_review_queue"})
        self.assertEqual([first], queue["review_requests"])
        self.assertEqual([], self.step(lambda session: session.store.list_issues("wedding-demo")))
        snapshot = json.loads(self.storage.values[STORAGE_KEY])
        self.assertEqual(1, snapshot["schema_version"])
        self.assertIn("review_requests", snapshot["conversation_sql"])
        self.assertNotIn("review_requests", snapshot["event_sql"])

    def test_known_issue_review_and_existing_offer_survive_reconstruction(self):
        issue = self.action("host", {"action": "report", "summary": "Speaker silent", "category": "audio", "location": "Stage"}, "known-review-report")["issue"]
        intent = {"action": "escalate", "issue_id": issue["issue_id"], "version": issue["version"], "note": "Please review this unresolved issue."}
        reviewed = self.action("host", intent, "known-review-request")["issue"]
        replay = self.action("host", intent, "known-review-request")["issue"]
        self.assertEqual(reviewed, replay)
        self.assertEqual(issue["version"], reviewed["version"])
        self.assertEqual(issue["offered_to"], reviewed["offered_to"])
        self.assertEqual(issue["offer_expires_at"], reviewed["offer_expires_at"])
        denied = self.action("other", intent, "foreign-review")
        self.assertEqual("wrong_actor", denied["code"])
        accepted = self.action("staff_ravi", {"action": "accept", "issue_id": issue["issue_id"], "version": issue["version"]})["issue"]
        self.assertEqual("accepted", accepted["status"])
        self.assertEqual("staff_ravi", accepted["assigned_to"])
        self.assertEqual(1, sum(item["event"] == "organizer_review_requested" for item in accepted["history"]))

    def test_older_read_only_help_exit_cannot_rollback_newer_progress(self):
        issue = self.action("host", {"action": "report", "summary": "Speaker silent", "category": "audio", "location": "Stage"}, "overlap-help")["issue"]
        accepted = self.action("staff_ravi", {"action": "accept", "issue_id": issue["issue_id"], "version": issue["version"]})["issue"]
        with open_hosted_service(self.storage, now=self.clock) as older:
            started = self.action("staff_ravi", {"action": "start", "issue_id": issue["issue_id"], "version": accepted["version"]})["issue"]
            writes = self.storage.writes
            older.service.handle("host", "help")
            checkpoint = older.checkpoint()
            self.assertFalse(checkpoint["written"])
        self.assertEqual(writes, self.storage.writes)
        current = self.step(lambda session: session.store.issue(issue["issue_id"]))
        self.assertEqual("in_progress", current["status"])
        self.assertEqual(started["version"], current["version"])

    def test_stale_domain_write_is_rejected_without_overwriting_progress(self):
        issue = self.action("host", {"action": "report", "summary": "Speaker silent", "category": "audio", "location": "Stage"}, "overlap-write")["issue"]
        accepted = self.action("staff_ravi", {"action": "accept", "issue_id": issue["issue_id"], "version": issue["version"]})["issue"]
        older = open_hosted_service(self.storage, now=self.clock)
        try:
            self.action("staff_ravi", {"action": "start", "issue_id": issue["issue_id"], "version": accepted["version"]})
            committed = self.storage.values[STORAGE_KEY]
            writes = self.storage.writes
            older.store.complete(issue["issue_id"], "staff_ravi", "This completion used an older invocation snapshot.")
            with self.assertRaises(HostedStateError) as caught:
                older.checkpoint()
            self.assertEqual("stale_snapshot", caught.exception.code)
            self.assertEqual(committed, self.storage.values[STORAGE_KEY])
            self.assertEqual(writes, self.storage.writes)
        finally:
            older.close()
        self.assertEqual("in_progress", self.step(lambda session: session.store.issue(issue["issue_id"]))["status"])

    def test_stale_conversation_mutation_is_rejected_on_context_exit(self):
        self.step(lambda session: None)
        with self.assertRaises(HostedStateError) as caught:
            with open_hosted_service(self.storage, now=self.clock) as older:
                fresh = self.action("fresh_reporter", {"action": "report", "summary": "Speaker silent", "category": "audio", "location": "Stage"}, "fresh-before-older-pending")["issue"]
                older.service.handle("older_reporter", "Water issue", request_id="older-pending")
        self.assertEqual("stale_snapshot", caught.exception.code)
        self.assertEqual(fresh["issue_id"], self.step(lambda session: session.store.list_issues("wedding-demo"))[0]["issue_id"])
        self.assertIsNone(self.step(lambda session: session.service.context("older_reporter"))["pending_report"])

    def test_normal_checkpoint_updates_baseline_and_skips_duplicate_exit_write(self):
        with open_hosted_service(self.storage, now=self.clock) as session:
            issue = session.store.report("wedding-demo", "host", "Speaker silent", "audio", "Stage", idempotency_key="baseline-advance")
            first = session.checkpoint()
            self.assertTrue(first["written"])
            writes = self.storage.writes
            self.assertFalse(session.checkpoint()["written"])
            self.assertEqual(writes, self.storage.writes)
            accepted = session.store.acknowledge(issue["issue_id"], "staff_ravi")
            self.assertTrue(session.checkpoint()["written"])
            writes = self.storage.writes
        self.assertEqual(writes, self.storage.writes)
        self.assertEqual(accepted["version"], self.step(lambda session: session.store.issue(issue["issue_id"]))["version"])

    def test_old_empty_bootstrap_session_cannot_reset_newly_created_state(self):
        older = open_hosted_service(self.storage, now=self.clock)
        try:
            fresh = self.action("host", {"action": "report", "summary": "Speaker silent", "category": "audio", "location": "Stage"}, "bootstrap-race")["issue"]
            with self.assertRaises(HostedStateError) as caught:
                older.checkpoint()
            self.assertEqual("stale_snapshot", caught.exception.code)
        finally:
            older.close()
        self.assertEqual(fresh["issue_id"], self.step(lambda session: session.store.list_issues("wedding-demo"))[0]["issue_id"])


if __name__ == "__main__":
    unittest.main()
