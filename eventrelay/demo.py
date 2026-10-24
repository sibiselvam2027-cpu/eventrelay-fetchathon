"""Repeatable end-to-end evidence using synthetic staff and real state changes."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import tempfile

from .router import ConversationService
from .settings import ROOT
from .store import EventStore


def run_scenario():
    os.environ["EVENTRELAY_DEMO_MODE"] = "1"
    base = ROOT / "data"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="scenario_", dir=base) as directory:
        store = EventStore(Path(directory) / "event.db")
        store.seed_demo()
        service = ConversationService(Path(directory) / "chat.db", store)
        actor = "reporter_scenario"
        steps = []

        def capture(label, response):
            issue = response.get("issue")
            steps.append({"step": label, "text": response["text"], "status": issue["status"] if issue else "clarification", "version": issue["version"] if issue else None})
            return issue

        response = service.handle(actor, "There is a water issue in the dining hall", request_id="initial-report")
        assert not store.list_issues("wedding-demo"), "Ambiguous reports must not dispatch staff."
        capture("clarify ambiguous water report", response)
        issue = capture("route drinking-water report", service.handle(actor, "drinking water"))
        assert issue["offered_to"] == "staff_arun" and issue["assigned_to"] is None
        issue = capture("primary declines; backup offered", service.staff_response(issue["issue_id"], "staff_arun", "decline", issue["version"]))
        assert issue["offered_to"] == "staff_neha" and issue["assigned_to"] is None
        issue = capture("backup explicitly accepts", service.staff_response(issue["issue_id"], "staff_neha", "accept", issue["version"]))
        reference = issue["issue_id"]
        assert issue["status"] == "accepted"
        issue = capture("worker starts", service.handle(actor, "start"))
        issue = capture("worker reports completion", service.handle(actor, "done: Water bottles replenished at the dining counter"))
        assert issue["status"] == "awaiting_confirmation" and issue["closed_at"] is None
        issue = capture("reporter rejects incomplete fix", service.handle(actor, "reopen: The second counter still has no water"))
        assert issue["issue_id"] == reference and issue["status"] == "offered"
        issue = capture("primary declines reopened work", service.staff_response(reference, "staff_arun", "decline", issue["version"]))
        issue = capture("backup accepts reopened work", service.staff_response(reference, "staff_neha", "accept", issue["version"]))
        capture("worker restarts", service.handle(actor, "start"))
        issue = capture("worker reports both counters complete", service.handle(actor, "done: Both water counters replenished"))
        before_close_version = issue["version"]
        issue = capture("reporter confirms resolution", service.handle(actor, "confirm"))
        assert issue["status"] == "closed"
        issue = capture("replayed confirmation does not close twice", service.handle(actor, "confirm", intent={"action": "confirm", "issue_id": reference, "version": before_close_version}))
        assert sum(event["event"] == "confirmed_closed" for event in issue["history"]) == 1
        return {"scenario": "EventRelay synthetic wedding end-to-end", "generated_at": datetime.now(timezone.utc).isoformat(),
                "physical_work": "simulated", "vendor_decisions": "explicit local simulator calls, not network transport",
                "checks_passed": ["clarification before dispatch", "offer distinct from acceptance", "backup routing", "completion distinct from closure", "reopening preserves issue ID", "reporter-confirmed closure", "duplicate confirmation idempotent"],
                "steps": steps, "history": issue["history"],
                "sdk_versions": {name: importlib.metadata.version(name) for name in ("uagents", "uagents-core", "pydantic")}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/demo-proof.json")
    args = parser.parse_args()
    proof = run_scenario()
    target = Path(args.output)
    if not target.is_absolute():
        target = ROOT / target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    for step in proof["steps"]:
        print(step["step"] + ": " + step["status"])
    print(f"Passed {len(proof['checks_passed'])} workflow checks. Evidence saved to {target.name}.")


if __name__ == "__main__":
    main()
