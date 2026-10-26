"""Conversation actions, clarification, authorization, and native ASI cards."""

from __future__ import annotations

import json
import re
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .settings import demo_mode
from .store import CATEGORIES, LOCATIONS, ORGANIZER, StoreError

EVENT = "wedding-demo"
GROUPS = {"drinking_water": "hospitality", "audio": "audio", "power": "facilities", "cleanup": "housekeeping"}
LABELS = {"drinking_water": "Drinking water", "audio": "Audio", "power": "Power / facilities", "cleanup": "Cleanup"}


def descriptive_intent(text: str) -> dict | None:
    """Answer bounded product and process questions without taking an action.

    Capability questions match in full. Process questions need an explicit
    instructional phrase; a claim that work is fixed never means confirmation.
    """
    if not isinstance(text, str) or len(text) > 8000:
        return None
    references = re.findall(r"(?<![\w-])ER-[A-Za-z0-9_-]*(?![\w-])", text, re.IGNORECASE)
    if any(not re.fullmatch(r"ER-[0-9A-F]{8}", reference, re.IGNORECASE) for reference in references):
        return {"action": "help", "help_topic": "issue_reference"}
    if len(text) > 500:
        return None
    question = " ".join(text.casefold().split()).rstrip("?.!")
    if re.fullmatch(r"ER-[0-9A-F]{8}", question, re.IGNORECASE):
        return {"action": "status", "issue_id": question.upper()}
    if re.fullmatch(
            r"(?:(?:show|list)(?: me)?(?: the)?(?: current)?(?: status of)?(?: all)? open(?: event)? issues|"
            r"what (?:is|is the|is the current) status of all open(?: event)? issues)", question):
        return {"action": "list_open"}
    if re.search(r"\b(?:how (?:do|can|should) i|how to) (?:confirm|close|mark)\b", question):
        return {"action": "help", "help_topic": "confirmation"}
    if re.search(r"\b(?:can (?:you|eventrelay)(?: please)?|how (?:do|can|should) i|how to) escalate\b", question):
        if len(references) == 1:
            return {"action": "status", "issue_id": references[0].upper()}
        return {"action": "help", "help_topic": "escalation"}
    patterns = (
        r"(?:help|what is eventrelay|what does eventrelay do|tell me about eventrelay)",
        r"what can (?:you|eventrelay) (?:do|help (?:me )?with)",
        r"how (?:does eventrelay work|do i use eventrelay|can you help(?: me)?)",
        r"(?:what|which) (?:services|capabilities|categories|issue categories|locations|areas) "
        r"(?:do you|does eventrelay) (?:support|cover|have)",
        r"(?:what|which) (?:are (?:your|the supported) (?:services|capabilities|categories|locations|areas)|"
        r"(?:services|categories|locations|areas) are supported)",
        r"(?:what|which) (?:kinds|types) of issues can (?:you|eventrelay) handle",
        r"(?:what|which) issues can (?:you handle|i report)",
        r"(?:where do you operate|where are you available|where can i report an issue)",
        r"(?:list|show) (?:your|the|supported) (?:services|capabilities|categories|locations|areas)",
    )
    clauses = question.split(" and ")
    if 1 <= len(clauses) <= 2 and all(
            any(re.fullmatch(pattern, clause) for pattern in patterns) for clause in clauses):
        return {"action": "help"}
    return None


def _clarification_summary(original, detail, text):
    """Preserve the complaint and add distinct clarification within its limit."""
    if not isinstance(original, str):
        return original
    original = original[:1000]
    if not isinstance(detail, str) or not detail.strip():
        return original
    detail = detail.strip()
    normalize = lambda value: " ".join(value.casefold().split()).strip(" .!?")
    location_only = (
        r"(?:(?:it(?:'s| is)|the location(?: is)?|location(?: is)?|we are)\s+)?"
        r"(?:(?:at|in|near|by)\s+)?(?:the\s+)?"
        r"(?:stage|dining hall|entrance|washrooms?|toilets?|food counter|entry|gate)"
        r"(?:\s+(?:area|please))?"
    )
    if (normalize(detail) in normalize(original)
            or re.fullmatch(location_only, normalize(detail))
            or re.fullmatch(location_only, normalize(text))):
        return original
    separator = " Clarification: "
    remaining = 1000 - len(original) - len(separator)
    if remaining <= 0:
        return original
    return original + separator + detail[:remaining].rstrip()


def local_intent(text: str) -> dict:
    """Transparent offline command parser; never presented as ASI reasoning."""
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except (ValueError, TypeError):
        pass
    description = descriptive_intent(text)
    if description is not None:
        return description
    value = text.strip()
    low = value.casefold()
    issue = re.search(r"ER-[0-9A-F]{8}", value.upper())
    member = re.search(r"\bstaff_[a-z]+\b", low)
    command = re.match(r"^(accept|decline|start|done|complete|confirm|reopen|status|tick|roster|help|link)\b", low)
    if command:
        action = {"complete": "done"}.get(command.group(1), command.group(1))
        result = {"action": action, "issue_id": issue.group(0) if issue else None,
                  "staff_id": member.group(0) if member else None}
        if action in {"done", "reopen"}:
            result["note"] = value.partition(":")[2].strip() or ("Worker reports the task complete." if action == "done" else "The reporter says the issue remains unresolved.")
        if action == "link":
            ids = re.findall(r"ER-[0-9A-F]{8}", value.upper())
            if len(ids) == 2:
                result.update(issue_id=ids[0], child_id=ids[1])
        return result
    category = "unknown"
    if any(term in low for term in ("drinking water", "water bottles", "water refill", "drinking_water", "refreshment")):
        category = "drinking_water"
    elif any(term in low for term in ("spill", "cleanup", "cleaning", "housekeeping")):
        category = "cleanup"
    elif any(term in low for term in ("electric", "power", "lighting", "facilities")):
        category = "power"
    elif any(term in low for term in ("microphone", "speaker", "audio", "sound", "mic ")) or low == "mic":
        category = "audio"
    if "water" in low and category == "audio":
        category = "unknown"
    location = None
    for name, aliases in (("Dining Hall", ("dining", "food counter")), ("Stage", ("stage",)),
                          ("Entrance", ("entrance", "entry", "gate")), ("Washrooms", ("washroom", "toilet"))):
        if any(alias in low for alias in aliases):
            location = name
            break
    return {"action": "report", "summary": value, "category": category,
            "location": location, "priority": "urgent" if any(term in low for term in ("urgent", "ceremony starts", "sparks", "smoke")) else "normal"}


class ConversationService:
    def __init__(self, state_path, store):
        self.path = str(state_path)
        self.store = store
        Path(state_path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.execute("CREATE TABLE IF NOT EXISTS conversations(actor TEXT PRIMARY KEY,state TEXT NOT NULL)")

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _state(self, actor):
        with self._db() as db:
            row = db.execute("SELECT state FROM conversations WHERE actor=?", (actor,)).fetchone()
        return json.loads(row["state"]) if row else {}

    def _save(self, actor, state):
        with self._db() as db:
            db.execute("INSERT INTO conversations VALUES(?,?) ON CONFLICT(actor) DO UPDATE SET state=excluded.state", (actor, json.dumps(state)))

    def context(self, actor):
        state = self._state(actor)
        last = None
        if state.get("last_issue"):
            try:
                issue = self.store.issue(state["last_issue"])
                if self._can_view(actor, issue):
                    last = {key: issue[key] for key in ("issue_id", "status", "category", "location", "summary", "version")}
            except StoreError:
                pass
        return {"pending_report": state.get("pending"), "last_issue": last,
                "categories": list(CATEGORIES), "locations": list(LOCATIONS), "demo_mode": demo_mode()}

    def _can_view(self, actor, issue):
        return demo_mode() or actor in (ORGANIZER, issue["reporter_id"], issue["assigned_to"], issue["offered_to"])

    def _open_overview(self, actor, notice=""):
        visible = [issue for issue in self.store.list_issues(EVENT)
                   if issue["status"] != "closed" and self._can_view(actor, issue)]
        issues = [{"issue_id": issue["issue_id"], "category": issue["category"],
                   "location": issue["location"], "status": issue["status"],
                   "owner": issue["assigned_to_name"] or "Nobody has accepted yet"}
                  for issue in visible[:20]]
        lines = [notice] if notice else []
        if demo_mode():
            lines.append("DEMO: synthetic wedding, people, and physical work.")
        if not issues:
            lines.append("No open issues are visible to this conversation.")
        else:
            lines.append(f"Open issues visible to this conversation: showing {len(issues)} of {len(visible)}.")
            lines.extend(f"{issue['issue_id']} · {LABELS[issue['category']]} · {issue['location']} · "
                         f"{issue['status'].replace('_', ' ')} · Owner: {issue['owner']}"
                         for issue in issues)
        return {"text": "\n".join(lines), "issues": issues, "offers": []}

    def _staff_actor(self, actor, issue, supplied=None):
        expected = issue["offered_to"] or issue["assigned_to"]
        if actor.startswith("staff_"):
            if supplied and supplied != actor:
                raise StoreError("wrong_actor", "You cannot act for another crew member.")
            return actor, False
        if demo_mode():
            return supplied or expected, True
        raise StoreError("wrong_actor", "This action requires an authenticated crew member.")

    @staticmethod
    def _offer(issue):
        if issue["offered_to"] and issue["status"] in {"offered", "blocked"}:
            staff = issue["offered_to"]
            return [{"offer_id": f"{issue['issue_id']}:{issue['version']}:{staff}",
                     "issue_id": issue["issue_id"], "staff_id": staff,
                     "category": issue["category"], "summary": issue["summary"],
                     "location": issue["location"], "version": issue["version"],
                     "vendor_group": GROUPS[issue["category"]]}]
        return []

    def _render(self, issue, notice="", simulated=False):
        status = issue["status"]
        owner = issue["assigned_to_name"] or "Nobody has accepted yet"
        lines = [notice] if notice else []
        if demo_mode():
            lines.append("DEMO: synthetic wedding, people, and physical work.")
        if simulated:
            lines.append("Simulated staff action recorded; no real worker was contacted by this action.")
        lines.extend([f"{issue['issue_id']} · {LABELS[issue['category']]} · {issue['location']}",
                      issue["summary"], f"Status: {status.replace('_', ' ')}", f"Accountable owner: {owner}"])
        if issue["offered_to_name"]:
            lines.append(f"Offer sent to {issue['offered_to_name']}; acceptance is still pending.")
        if issue["escalated"]:
            lines.append("Organizer attention required: " + str(issue["escalation_reason"]))
        if issue["blocked_by"]:
            lines.append("Waiting for linked issue(s): " + ", ".join(issue["blocked_by"]))
        if status == "awaiting_confirmation":
            lines.append("The crew reports completion. The original reporter or organizer must confirm whether the problem is resolved.")
        if status == "closed":
            lines.append("Resolution was confirmed. The full activity history is preserved.")
        ctas = []
        base = {"issue_id": issue["issue_id"], "version": issue["version"]}
        if demo_mode() and issue["offered_to"]:
            for action in ("accept", "decline"):
                ctas.append({"label": "Demo: " + action.title(), "selection": {**base, "action": action, "staff_id": issue["offered_to"]}, "primary": action == "accept"})
        if demo_mode() and status in {"accepted", "in_progress"}:
            action = "start" if status == "accepted" else "done"
            ctas.append({"label": "Demo: " + ("Start work" if action == "start" else "Report completed"),
                         "selection": {**base, "action": action, "staff_id": issue["assigned_to"], "note": "Synthetic crew reports the work complete."}, "primary": True})
        if status == "awaiting_confirmation":
            ctas.extend([{"label": "Yes, resolved", "selection": {**base, "action": "confirm"}, "primary": True},
                         {"label": "Still a problem", "selection": {**base, "action": "reopen", "note": "The reporter says the issue remains unresolved."}}])
        ctas.append({"label": "Refresh status", "selection": {"action": "status", "issue_id": issue["issue_id"]}})
        return {"text": "\n".join(lines), "issue": issue, "offers": self._offer(issue),
                "card": {"kind": "detail", "payload": {"title": "EventRelay · " + issue["issue_id"],
                    "summary_rows": [{"label": "Issue", "value": issue["summary"]}, {"label": "Location", "value": issue["location"]},
                                     {"label": "Status", "value": status.replace("_", " ")}, {"label": "Accepted by", "value": owner},
                                     {"label": "Event", "value": "Synthetic wedding demonstration"}], "ctas": ctas}}}

    def _clarify(self, actor, state, pending):
        state["pending"] = pending
        self._save(actor, state)
        fields = []
        questions = []
        if pending.get("category") not in CATEGORIES:
            questions.append("What kind of issue is it: drinking-water refill, audio, cleanup, or power/facilities?")
            fields.append({"name": "category", "kind": "select", "label": "Issue type", "required": True,
                           "options": [{"value": key, "label": value} for key, value in LABELS.items()]})
        if pending.get("location") not in LOCATIONS:
            questions.append("Where is it: Stage, Dining Hall, Entrance, or Washrooms?")
            fields.append({"name": "location", "kind": "select", "label": "Location", "required": True,
                           "options": [{"value": name, "label": name} for name in LOCATIONS]})
        return {"text": " ".join(questions) + " No crew has been dispatched yet.", "offers": [],
                "card": {"kind": "form", "payload": {"title": "Clarify the event issue", "fields": fields,
                    "submit_cta": {"label": "Report issue", "selection": {"action": "report", "clarification_id": pending["request_id"]}}}}}

    def guided_report(self, actor, text, request_id=None):
        """Start a fresh explicit form after AI failure, without dispatching.

        Known fields from an older pending report must not silently select the
        category or location for this new manual report.
        """
        if not isinstance(actor, str) or not actor or len(actor) > 200:
            return {"text": "The caller identity is missing.", "offers": []}
        summary = text.strip()[:1000] if isinstance(text, str) else "Event issue"
        pending = {"summary": summary or "Event issue", "category": "unknown",
                   "location": None, "priority": "normal",
                   "request_id": request_id or "guided_" + secrets.token_hex(12)}
        response = self._clarify(actor, self._state(actor), pending)
        response["text"] = ("AI service unavailable. Choose the category and location to continue in manual guided mode. "
                            "No ASI reasoning was used for this report. " + response["text"])
        response["manual_guided"] = True
        return response

    def handle(self, actor, text, intent=None, request_id=None):
        if not isinstance(actor, str) or not actor or len(actor) > 200:
            return {"text": "The caller identity is missing.", "offers": []}
        if not isinstance(text, str) or len(text) > 8000:
            return {"text": "Please keep the message under 8,000 characters.", "offers": []}
        intent = local_intent(text) if intent is None else intent
        if not isinstance(intent, dict):
            return {"text": "Please describe the issue or choose an available action.", "offers": []}
        intent = dict(intent)
        if intent.get("version") is None and intent.get("expected_version") is not None:
            intent["version"] = intent["expected_version"]
        if not intent.get("note") and intent.get("evidence"):
            intent["note"] = intent["evidence"]
        state = self._state(actor)
        action = intent.get("action", "report")
        try:
            if action == "list_open":
                return self._open_overview(actor)
            if action == "help" or action == "unsupported":
                if intent.get("help_topic") == "issue_reference":
                    return {"text": "An issue reference must be ER- followed by exactly eight hexadecimal characters (0–9 and A–F). Copy the exact reference from your issue card, then send status followed by that reference. No issue was created or changed.", "offers": []}
                if intent.get("help_topic") == "confirmation":
                    return {"text": "First send status followed by the exact ER-XXXXXXXX reference from your issue card. Wait until the crew has reported completion and the state is awaiting confirmation. Then the original reporter, in the same conversation, can select Yes, resolved or send confirm followed by the issue reference. A configured organizer can also confirm. If the fix did not work, select Still a problem or send reopen followed by the reference. This question has not closed an issue.", "offers": []}
                if intent.get("help_topic") == "escalation":
                    return self._open_overview(actor, "Which issue needs attention? Send its exact ER-XXXXXXXX issue reference, or send status followed by the reference. This question has not applied an escalation.")
                return {"text": "EventRelay coordinates event-day issues for drinking water, audio, cleanup, and power/facilities. Supported locations: Stage, Dining Hall, Entrance, and Washrooms. Describe the problem and location to report it. Track it with status; crew use accept/decline, start, and done. Only the original reporter or organizer can confirm resolution or reject the reported fix with reopen. Demo staff actions are labelled as simulated.", "offers": []}
            if action == "roster":
                if not demo_mode() and actor != ORGANIZER:
                    raise StoreError("wrong_actor", "The full staff roster is available to the organizer only.")
                roster = self.store.roster(EVENT)
                return {"text": "\n".join(f"{person['name']} · {LABELS[person['category']]} · {person['role']} · {'busy' if person['busy'] else 'available' if person['available'] else 'unavailable'}" for person in roster), "roster": roster, "offers": []}
            if action == "tick":
                if not demo_mode() and actor != ORGANIZER:
                    raise StoreError("wrong_actor", "Only the organizer can request an event-wide follow-up sweep.")
                changed = self.store.tick(EVENT)
                return {"text": f"Follow-up check completed. {len(changed)} issue(s) changed. No physical work was marked complete.", "issues": changed,
                        "offers": [offer for issue in changed for offer in self._offer(issue)]}
            if action == "report":
                pending = dict(state.get("pending") or {})
                if intent.get("clarification_id") and intent["clarification_id"] != pending.get("request_id"):
                    raise StoreError("stale_clarification", "That clarification form is no longer current. Describe the issue again.")
                for name in ("summary", "category", "location", "priority"):
                    value = intent.get(name)
                    if value is not None and value != "" and value != "unknown":
                        if name == "summary" and pending.get("summary"):
                            pending[name] = _clarification_summary(pending[name], value, text)
                        else:
                            pending[name] = value
                pending.setdefault("summary", text.strip())
                pending.setdefault("priority", "normal")
                pending.setdefault("request_id", request_id or "report_" + secrets.token_hex(12))
                if pending.get("category") not in CATEGORIES or pending.get("location") not in LOCATIONS:
                    return self._clarify(actor, state, pending)
                if pending.get("priority") not in {"normal", "urgent"}:
                    raise StoreError("invalid_priority", "Choose normal or urgent priority.")
                issue = self.store.report(EVENT, actor, pending["summary"], pending["category"], pending["location"], pending["priority"], pending["request_id"])
                state.pop("pending", None)
                state["last_issue"] = issue["issue_id"]
                self._save(actor, state)
                return self._render(issue, "Issue recorded and routed using the event's responsibility roster.")
            issue_id = intent.get("issue_id") or state.get("last_issue")
            if not isinstance(issue_id, str) or not re.fullmatch(r"ER-[0-9A-F]{8}", issue_id):
                return {"text": "Which issue? Include its ER-XXXXXXXX reference.", "offers": []}
            issue = self.store.issue(issue_id)
            if not self._can_view(actor, issue):
                raise StoreError("wrong_actor", "That issue is not available to this caller.")
            version = intent.get("version")
            closed_retry = action == "confirm" and issue["status"] == "closed"
            if version is not None and not closed_retry and (type(version) is not int or issue["version"] != version):
                raise StoreError("stale_version", "The issue changed. Refresh its status before acting.")
            state["last_issue"] = issue_id
            self._save(actor, state)
            simulated = False
            if action in {"accept", "decline", "start", "done"}:
                staff, simulated = self._staff_actor(actor, issue, intent.get("staff_id"))
                if action in {"accept", "decline"}:
                    issue = self.store.acknowledge(issue_id, staff, action, expected_version=version)
                elif action == "start":
                    issue = self.store.start(issue_id, staff, expected_version=version)
                else:
                    issue = self.store.complete(issue_id, staff, intent.get("note") or "Crew reports the work complete.", expected_version=version)
            elif action in {"confirm", "reopen"}:
                issue = self.store.confirm(issue_id, actor, action == "confirm", intent.get("note") or "", expected_version=version)
            elif action == "link":
                if not isinstance(intent.get("child_id"), str):
                    raise StoreError("invalid_request", "Include the prerequisite issue reference.")
                issue = self.store.link_dependency(issue_id, intent["child_id"], actor)
            elif action == "status":
                self.store.tick(EVENT)
                issue = self.store.issue(issue_id)
            else:
                raise StoreError("unsupported_action", "Choose a supported issue action.")
            return self._render(issue, simulated=simulated)
        except StoreError as exc:
            response = {"text": str(exc), "code": exc.code, "offers": []}
            if state.get("last_issue"):
                try:
                    current = self.store.issue(state["last_issue"])
                    if self._can_view(actor, current):
                        response["issue"] = current
                        response["offers"] = self._offer(current)
                except StoreError:
                    pass
            return response

    def staff_response(self, issue_id, staff_id, decision, version):
        try:
            issue = self.store.acknowledge(issue_id, staff_id, decision, expected_version=version)
            return self._render(issue, "Vendor decision recorded: " + decision + ".", simulated=demo_mode())
        except StoreError as exc:
            try:
                issue = self.store.issue(issue_id)
                response = self._render(issue, "Vendor response could not be applied: " + str(exc))
                response["code"] = exc.code
                return response
            except StoreError:
                return {"text": str(exc), "code": exc.code, "offers": []}

    def pending_offers(self):
        """Coordinator-only transport sweep catches offers created by any timer."""
        return [offer for issue in self.store.list_issues(EVENT) for offer in self._offer(issue)]
