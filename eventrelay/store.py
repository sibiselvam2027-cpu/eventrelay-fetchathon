"""Event-specific dispatch with explicit acceptance and reporter closure.

All actors passed here must already be authenticated by the controller. This
engine records crew reports; it never diagnoses a hazard or certifies a venue
safe. The bundled event, vendors, staff and service incidents are synthetic.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import secrets
import sqlite3
import time
from typing import Callable


CATEGORIES = ("drinking_water", "audio", "cleanup", "power")
LOCATIONS = ("Stage", "Dining Hall", "Entrance", "Washrooms")
PRIORITIES = ("normal", "urgent")
ORGANIZER = "organizer_demo"


class StoreError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


EventError = StoreError


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _text(value, label: str, limit: int = 1000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise StoreError("invalid_request", f"Invalid {label}.")
    return value.strip()


class EventStore:
    def __init__(self, path: str | Path, now: Callable[[], float] = time.time,
                 offer_timeout_seconds: int = 60, resolution_timeout_seconds: int = 300):
        self._now = now
        if type(offer_timeout_seconds) is not int or offer_timeout_seconds < 1:
            raise ValueError("Offer timeout must be a positive integer.")
        if type(resolution_timeout_seconds) is not int or resolution_timeout_seconds < 1:
            raise ValueError("Follow-up timeout must be a positive integer.")
        self.offer_timeout_seconds = offer_timeout_seconds
        self.resolution_timeout_seconds = resolution_timeout_seconds
        self._anchor = None
        if str(path) == ":memory:":
            self._path = f"file:eventrelay_{secrets.token_hex(12)}?mode=memory&cache=shared"
            self._uri = True
            self._anchor = self._connect()
        else:
            destination = Path(path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            self._path = str(destination)
            self._uri = False
        conn = self._connect()
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY, name TEXT NOT NULL,
                    organizer_id TEXT NOT NULL, synthetic INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS staff (
                    staff_id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(event_id),
                    name TEXT NOT NULL, category TEXT NOT NULL, vendor_id TEXT NOT NULL,
                    vendor_name TEXT NOT NULL, rank INTEGER NOT NULL, available INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS event_settings (
                    event_id TEXT PRIMARY KEY REFERENCES events(event_id),
                    offer_timeout_seconds INTEGER NOT NULL,
                    resolution_timeout_seconds INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS issues (
                    issue_id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(event_id),
                    reporter_id TEXT NOT NULL, summary TEXT NOT NULL, category TEXT NOT NULL,
                    location TEXT NOT NULL, priority TEXT NOT NULL, status TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    assigned_to TEXT REFERENCES staff(staff_id), offered_to TEXT REFERENCES staff(staff_id),
                    offer_expires_at REAL, accepted_at REAL, resolution_deadline REAL,
                    resume_status TEXT, completion_note TEXT, completed_at REAL, closed_at REAL,
                    escalated_at REAL, escalation_reason TEXT,
                    created_at REAL NOT NULL, updated_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS issues_event ON issues(event_id);
                CREATE TABLE IF NOT EXISTS report_keys (
                    event_id TEXT NOT NULL, reporter_id TEXT NOT NULL,
                    key_hash TEXT NOT NULL, request_hash TEXT NOT NULL,
                    issue_id TEXT NOT NULL REFERENCES issues(issue_id),
                    PRIMARY KEY(event_id, reporter_id, key_hash)
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    issue_id TEXT NOT NULL REFERENCES issues(issue_id),
                    staff_id TEXT NOT NULL REFERENCES staff(staff_id), status TEXT NOT NULL,
                    PRIMARY KEY(issue_id, staff_id)
                );
                CREATE TABLE IF NOT EXISTS issue_history (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_id TEXT NOT NULL REFERENCES issues(issue_id),
                    event TEXT NOT NULL, timestamp REAL NOT NULL, actor_id TEXT NOT NULL,
                    version INTEGER NOT NULL, details TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS dependencies (
                    parent_id TEXT NOT NULL REFERENCES issues(issue_id),
                    child_id TEXT NOT NULL REFERENCES issues(issue_id),
                    PRIMARY KEY(parent_id, child_id)
                );
            """)
        finally:
            conn.close()

    def _connect(self):
        conn = sqlite3.connect(self._path, uri=self._uri, timeout=15, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=15000")
        return conn

    @contextmanager
    def _tx(self, write=True):
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield conn
            if conn.in_transaction:
                conn.commit()
        except Exception:
            if conn.in_transaction:
                conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _event(conn, event_id):
        _text(event_id, "event id", 120)
        row = conn.execute("SELECT * FROM events WHERE event_id=?", (event_id,)).fetchone()
        if row is None:
            raise StoreError("unknown_event", "The event is not configured.")
        return row

    @staticmethod
    def _row(conn, issue_id):
        _text(issue_id, "issue id", 120)
        row = conn.execute("SELECT * FROM issues WHERE issue_id=?", (issue_id,)).fetchone()
        if row is None:
            raise StoreError("unknown_issue", "The issue does not exist.")
        return row

    @staticmethod
    def _version(row, expected_version):
        if expected_version is not None and (type(expected_version) is not int or row["version"] != expected_version):
            raise StoreError("stale_version", "This issue changed. Refresh it before acting.")

    @staticmethod
    def _history(conn, issue_id, event, timestamp, actor, details):
        version = EventStore._row(conn, issue_id)["version"]
        conn.execute("""INSERT INTO issue_history(issue_id,event,timestamp,actor_id,version,details)
                        VALUES(?,?,?,?,?,?)""", (issue_id, event, timestamp, actor, version, _json(details)))

    @staticmethod
    def _change(conn, issue_id, timestamp, **values):
        # Column names originate only from this module, never from callers.
        assignments = ",".join(f"{name}=?" for name in values)
        conn.execute(f"UPDATE issues SET {assignments},version=version+1,updated_at=? WHERE issue_id=?",
                     (*values.values(), timestamp, issue_id))

    @staticmethod
    def _blocked(conn, issue_id):
        return [row[0] for row in conn.execute("""SELECT d.child_id FROM dependencies d
                JOIN issues c ON c.issue_id=d.child_id WHERE d.parent_id=? AND c.status!='closed'
                ORDER BY d.child_id""", (issue_id,)).fetchall()]

    @staticmethod
    def _busy(conn, staff_id):
        return conn.execute("""SELECT issue_id FROM issues WHERE
            (offered_to=? AND status IN ('offered','blocked')) OR
            (assigned_to=? AND status IN ('accepted','in_progress','blocked')) LIMIT 1""",
            (staff_id, staff_id)).fetchone()

    def _settings(self, conn, event_id):
        row = conn.execute("SELECT * FROM event_settings WHERE event_id=?", (event_id,)).fetchone()
        return dict(row) if row else {"event_id": event_id,
                                      "offer_timeout_seconds": self.offer_timeout_seconds,
                                      "resolution_timeout_seconds": self.resolution_timeout_seconds}

    def _offer(self, conn, issue_id, timestamp, actor="system"):
        row = self._row(conn, issue_id)
        offer_timeout = self._settings(conn, row["event_id"])["offer_timeout_seconds"]
        blocked = bool(self._blocked(conn, issue_id))
        candidate = None
        roster = conn.execute("""SELECT * FROM staff WHERE event_id=? AND category=? AND available=1
            AND staff_id NOT IN (SELECT staff_id FROM attempts WHERE issue_id=?)
            ORDER BY rank,staff_id""", (row["event_id"], row["category"], issue_id)).fetchall()
        for member in roster:
            if self._busy(conn, member["staff_id"]) is None:
                candidate = member
                break
        if candidate is None:
            self._change(conn, issue_id, timestamp, status="blocked" if blocked else "escalated",
                         resume_status="escalated" if blocked else None,
                         assigned_to=None, offered_to=None, offer_expires_at=None,
                         escalated_at=timestamp, escalation_reason="no_available_staff")
            self._history(conn, issue_id, "escalated", timestamp, actor,
                          {"reason": "No eligible configured crew member is available; organizer action required."})
        else:
            self._change(conn, issue_id, timestamp, status="blocked" if blocked else "offered",
                         resume_status="offered" if blocked else None,
                         assigned_to=None, offered_to=candidate["staff_id"],
                         offer_expires_at=timestamp + offer_timeout,
                         escalated_at=None, escalation_reason=None)
            conn.execute("INSERT INTO attempts(issue_id,staff_id,status) VALUES(?,?,?)",
                         (issue_id, candidate["staff_id"], "offered"))
            self._history(conn, issue_id, "offered", timestamp, actor,
                          {"staff_id": candidate["staff_id"], "staff_name": candidate["name"],
                           "accept_by": timestamp + offer_timeout,
                           "accepted": False})

    def _snapshot(self, conn, issue_id):
        row = self._row(conn, issue_id)
        result = dict(row)
        for field in ("assigned_to", "offered_to"):
            member = conn.execute("SELECT * FROM staff WHERE staff_id=?", (row[field],)).fetchone() if row[field] else None
            result[field + "_name"] = member["name"] if member else None
            if member:
                result["vendor_id"] = member["vendor_id"]
                result["vendor_name"] = member["vendor_name"]
        result.setdefault("vendor_id", None)
        result.setdefault("vendor_name", None)
        history = conn.execute("SELECT * FROM issue_history WHERE issue_id=? ORDER BY event_id", (issue_id,)).fetchall()
        result["events"] = [{"event_id": item["event_id"], "event": item["event"],
                             "timestamp": item["timestamp"], "actor_id": item["actor_id"],
                             "version": item["version"], "details": json.loads(item["details"])} for item in history]
        result["history"] = result["events"]
        result["blocked_by"] = self._blocked(conn, issue_id)
        result["dependencies"] = [dict(item) for item in conn.execute("""SELECT c.issue_id,c.status,c.summary
            FROM dependencies d JOIN issues c ON c.issue_id=d.child_id
            WHERE d.parent_id=? ORDER BY c.issue_id""", (issue_id,)).fetchall()]
        result["escalated"] = row["escalated_at"] is not None
        result["accept_by"] = row["offer_expires_at"]
        result["follow_up_at"] = row["resolution_deadline"]
        result["synthetic"] = True
        return result

    def seed_demo(self):
        rows = (
            ("drinking_water", "hospitality_demo", "Demo Hospitality (synthetic)", "Arun", "Neha"),
            ("audio", "av_demo", "Demo AV (synthetic)", "Ravi", "Sara"),
            ("cleanup", "housekeeping_demo", "Demo Housekeeping (synthetic)", "Meena", "Kiran"),
            ("power", "facilities_demo", "Demo Facilities (synthetic)", "Vikram", "Pooja"),
        )
        with self._tx() as conn:
            conn.execute("INSERT OR IGNORE INTO events VALUES(?,?,?,1)",
                         ("wedding-demo", "Wedding operations demonstration (synthetic)", ORGANIZER))
            conn.execute("INSERT OR IGNORE INTO event_settings VALUES(?,?,?)",
                         ("wedding-demo", self.offer_timeout_seconds, self.resolution_timeout_seconds))
            for category, vendor_id, vendor_name, primary, backup in rows:
                for rank, name in enumerate((primary, backup)):
                    conn.execute("""INSERT OR IGNORE INTO staff
                        (staff_id,event_id,name,category,vendor_id,vendor_name,rank) VALUES(?,?,?,?,?,?,?)""",
                        ("staff_" + name.lower(), "wedding-demo", name, category, vendor_id, vendor_name, rank))
        return {"event_id": "wedding-demo", "synthetic": True}

    def roster(self, event_id):
        with self._tx(False) as conn:
            self._event(conn, event_id)
            rows = conn.execute("SELECT * FROM staff WHERE event_id=? ORDER BY category,rank", (event_id,)).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item["available"] = bool(row["available"])
                busy = self._busy(conn, row["staff_id"])
                item["busy"] = busy is not None
                item["busy_issue_id"] = busy["issue_id"] if busy else None
                item["role"] = "primary" if row["rank"] == 0 else "backup"
                item["synthetic"] = True
                result.append(item)
            return result

    def report(self, event_id, reporter_id, summary, category, location, priority="normal", idempotency_key=None):
        event_id = _text(event_id, "event id", 120)
        reporter_id = _text(reporter_id, "reporter id", 200)
        summary = _text(summary, "summary")
        if category not in CATEGORIES:
            raise StoreError("unknown_category", "Clarify the issue category before dispatch.")
        if location not in LOCATIONS:
            raise StoreError("unknown_location", "Choose Stage, Dining Hall, Entrance or Washrooms.")
        if priority not in PRIORITIES:
            raise StoreError("invalid_priority", "Priority must be normal or urgent.")
        key = _text(idempotency_key, "idempotency key", 300)
        request_hash = hashlib.sha256(_json([summary, category, location, priority]).encode()).hexdigest()
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        timestamp = float(self._now())
        with self._tx() as conn:
            self._event(conn, event_id)
            previous = conn.execute("""SELECT * FROM report_keys
                WHERE event_id=? AND reporter_id=? AND key_hash=?""", (event_id, reporter_id, key_hash)).fetchone()
            if previous:
                if previous["request_hash"] != request_hash:
                    raise StoreError("idempotency_conflict", "This request key belongs to a different report.")
                return self._snapshot(conn, previous["issue_id"])
            self._tick_conn(conn, event_id, timestamp)
            issue_id = "ER-" + secrets.token_hex(4).upper()
            conn.execute("""INSERT INTO issues
                (issue_id,event_id,reporter_id,summary,category,location,priority,status,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,'reported',?,?)""",
                (issue_id, event_id, reporter_id, summary, category, location, priority, timestamp, timestamp))
            conn.execute("INSERT INTO report_keys VALUES(?,?,?,?,?)", (event_id, reporter_id, key_hash, request_hash, issue_id))
            self._history(conn, issue_id, "reported", timestamp, reporter_id, {"category": category, "location": location})
            self._offer(conn, issue_id, timestamp)
            return self._snapshot(conn, issue_id)

    def acknowledge(self, issue_id, staff_id, decision="accept", expected_version=None):
        staff_id = _text(staff_id, "staff id", 200)
        if decision not in ("accept", "decline"):
            raise StoreError("invalid_decision", "Choose accept or decline.")
        timestamp = float(self._now())
        with self._tx() as conn:
            row = self._row(conn, issue_id)
            self._version(row, expected_version)
            if row["offered_to"] != staff_id:
                raise StoreError("wrong_actor", "Only the currently offered crew member can respond.")
            if row["status"] not in ("offered", "blocked"):
                raise StoreError("invalid_transition", "There is no active offer to acknowledge.")
            if timestamp >= row["offer_expires_at"]:
                self._tick_conn(conn, row["event_id"], timestamp)
                conn.commit()
                raise StoreError("offer_expired", "The acceptance deadline passed and the offer was rerouted.")
            member = conn.execute("SELECT available FROM staff WHERE staff_id=?", (staff_id,)).fetchone()
            if member is None or not member["available"]:
                conn.execute("UPDATE attempts SET status='unavailable' WHERE issue_id=? AND staff_id=?",
                             (issue_id, staff_id))
                self._change(conn, issue_id, timestamp, offered_to=None, offer_expires_at=None)
                self._history(conn, issue_id, "offer_withdrawn", timestamp, "system",
                              {"staff_id": staff_id, "reason": "Configured availability was withdrawn before acceptance."})
                self._offer(conn, issue_id, timestamp)
                conn.commit()
                raise StoreError("staff_unavailable", "The offered crew member became unavailable; the job was rerouted.")
            conn.execute("UPDATE attempts SET status=? WHERE issue_id=? AND staff_id=?",
                         ("accepted" if decision == "accept" else "declined", issue_id, staff_id))
            if decision == "decline":
                self._change(conn, issue_id, timestamp, offered_to=None, offer_expires_at=None)
                self._history(conn, issue_id, "declined", timestamp, staff_id, {})
                self._offer(conn, issue_id, timestamp)
            else:
                blocked = bool(self._blocked(conn, issue_id))
                follow_up_timeout = self._settings(conn, row["event_id"])["resolution_timeout_seconds"]
                self._change(conn, issue_id, timestamp, status="blocked" if blocked else "accepted",
                             resume_status="accepted" if blocked else None, assigned_to=staff_id,
                             offered_to=None, offer_expires_at=None, accepted_at=timestamp,
                             resolution_deadline=timestamp + follow_up_timeout,
                             escalated_at=None, escalation_reason=None)
                self._history(conn, issue_id, "accepted", timestamp, staff_id,
                              {"follow_up_at": timestamp + follow_up_timeout,
                               "note": "Configured follow-up deadline; not a crew arrival promise."})
            return self._snapshot(conn, issue_id)

    def start(self, issue_id, staff_id, expected_version=None):
        staff_id = _text(staff_id, "staff id", 200)
        timestamp = float(self._now())
        with self._tx() as conn:
            row = self._row(conn, issue_id)
            self._version(row, expected_version)
            if row["assigned_to"] != staff_id:
                raise StoreError("wrong_actor", "Only the assigned crew member can start work.")
            if row["status"] == "in_progress":
                return self._snapshot(conn, issue_id)
            if row["status"] != "accepted" or self._blocked(conn, issue_id):
                raise StoreError("invalid_transition", "Accept the job and clear its dependencies before starting.")
            self._change(conn, issue_id, timestamp, status="in_progress")
            self._history(conn, issue_id, "started", timestamp, staff_id, {})
            return self._snapshot(conn, issue_id)

    def complete(self, issue_id, staff_id, note, expected_version=None):
        staff_id = _text(staff_id, "staff id", 200)
        note = _text(note, "completion note")
        timestamp = float(self._now())
        with self._tx() as conn:
            row = self._row(conn, issue_id)
            self._version(row, expected_version)
            if row["assigned_to"] != staff_id:
                raise StoreError("wrong_actor", "Only the assigned crew member can report completion.")
            if self._blocked(conn, issue_id):
                raise StoreError("dependency_open", "A linked prerequisite is still open; completion is blocked.")
            if row["status"] == "awaiting_confirmation":
                return self._snapshot(conn, issue_id)
            if row["status"] not in ("accepted", "in_progress"):
                raise StoreError("invalid_transition", "Only accepted or in-progress work can be reported complete.")
            self._change(conn, issue_id, timestamp, status="awaiting_confirmation", completed_at=timestamp,
                         completion_note=note, resolution_deadline=None, escalated_at=None, escalation_reason=None)
            self._history(conn, issue_id, "completion_reported", timestamp, staff_id,
                          {"note": note, "reporter_confirmation_required": True})
            return self._snapshot(conn, issue_id)

    def request_escalation(self, issue_id, actor_id, note="", expected_version=None, idempotency_key=None):
        """Record organizer review without replacing crew or notifying a human."""
        actor_id = _text(actor_id, "actor id", 200)
        if not isinstance(note, str) or len(note) > 1000:
            raise StoreError("invalid_request", "Invalid organizer-review note.")
        note = note.strip() or "Organizer review requested."
        key = _text(idempotency_key, "request id", 200) if idempotency_key is not None else None
        key_hash = hashlib.sha256(key.encode()).hexdigest() if key else None
        request_hash = hashlib.sha256(_json({"note": note}).encode()).hexdigest()
        timestamp = float(self._now())
        with self._tx() as conn:
            row = self._row(conn, issue_id)
            event = self._event(conn, row["event_id"])
            if actor_id not in (row["reporter_id"], event["organizer_id"]):
                raise StoreError("wrong_actor", "Only the original reporter or organizer can request escalation for this issue.")
            if row["status"] == "closed":
                raise StoreError("invalid_transition", "A closed issue cannot be escalated. Report a new unresolved problem.")
            if row["status"] == "awaiting_confirmation":
                raise StoreError("invalid_transition", "The crew has reported completion. Confirm the fix or use Still a problem to reopen it before requesting escalation.")
            previous = conn.execute("""SELECT timestamp,details FROM issue_history
                WHERE issue_id=? AND event='organizer_review_requested' AND actor_id=?
                ORDER BY event_id DESC""", (issue_id, actor_id)).fetchall()
            for entry in previous:
                details = json.loads(entry["details"])
                same_key = key_hash is not None and details.get("request_key_hash") == key_hash
                same_active_request = (key_hash is None and row["escalated_at"] is not None
                                       and entry["timestamp"] >= row["escalated_at"]
                                       and details.get("request_hash") == request_hash)
                if same_key or same_active_request:
                    if details.get("request_hash") != request_hash:
                        raise StoreError("idempotency_conflict", "This review request ID was already used with a different note.")
                    return self._snapshot(conn, issue_id)
            self._version(row, expected_version)
            # Review metadata must not invalidate the version on an in-flight
            # crew offer. No operational fields or deadlines are changed.
            conn.execute("""UPDATE issues SET escalated_at=?,escalation_reason=?,updated_at=?
                WHERE issue_id=?""", (row["escalated_at"] if row["escalated_at"] is not None else timestamp,
                                      row["escalation_reason"] or "organizer_review_requested", timestamp, issue_id))
            self._history(conn, issue_id, "organizer_review_requested", timestamp, actor_id,
                          {"note": note, "request_key_hash": key_hash, "request_hash": request_hash,
                           "organizer_notification_sent": False, "crew_responsibility_unchanged": True})
            return self._snapshot(conn, issue_id)

    def confirm(self, issue_id, actor_id, resolved: bool, note="", expected_version=None):
        actor_id = _text(actor_id, "actor id", 200)
        if type(resolved) is not bool:
            raise StoreError("invalid_request", "resolved must be true or false.")
        if not isinstance(note, str) or len(note) > 1000:
            raise StoreError("invalid_request", "Invalid confirmation note.")
        timestamp = float(self._now())
        with self._tx() as conn:
            row = self._row(conn, issue_id)
            event = self._event(conn, row["event_id"])
            if actor_id not in (row["reporter_id"], event["organizer_id"]):
                raise StoreError("wrong_actor", "Only the original reporter or organizer can confirm resolution.")
            if row["status"] == "closed" and resolved:
                return self._snapshot(conn, issue_id)
            self._version(row, expected_version)
            if row["status"] != "awaiting_confirmation":
                raise StoreError("invalid_transition", "Wait for crew-reported completion before confirming.")
            if resolved:
                self._change(conn, issue_id, timestamp, status="closed", closed_at=timestamp)
                self._history(conn, issue_id, "confirmed_closed", timestamp, actor_id, {"note": note})
                self._unblock_dependents(conn, issue_id, timestamp)
            else:
                self._change(conn, issue_id, timestamp, status="reported", assigned_to=None,
                             offered_to=None, completion_note=None, completed_at=None,
                             accepted_at=None, resolution_deadline=None, closed_at=None,
                             resume_status=None, escalated_at=None, escalation_reason=None)
                conn.execute("DELETE FROM attempts WHERE issue_id=?", (issue_id,))
                self._history(conn, issue_id, "reopened", timestamp, actor_id, {"note": note})
                self._offer(conn, issue_id, timestamp)
            return self._snapshot(conn, issue_id)

    def link_dependency(self, parent_id, child_id, actor_id):
        actor_id = _text(actor_id, "actor id", 200)
        timestamp = float(self._now())
        with self._tx() as conn:
            parent = self._row(conn, parent_id)
            child = self._row(conn, child_id)
            event = self._event(conn, parent["event_id"])
            if actor_id not in (parent["assigned_to"], event["organizer_id"]):
                raise StoreError("wrong_actor", "Only the organizer or assigned crew can link prerequisites.")
            if parent["event_id"] != child["event_id"]:
                raise StoreError("cross_event_dependency", "Dependencies must belong to the same event.")
            if parent_id == child_id:
                raise StoreError("dependency_cycle", "An issue cannot depend on itself.")
            if parent["status"] in ("closed", "awaiting_confirmation"):
                raise StoreError("invalid_transition", "Do not add prerequisites after completion is reported.")
            cycle = conn.execute("""WITH RECURSIVE descendants(issue_id) AS (
                SELECT child_id FROM dependencies WHERE parent_id=?
                UNION SELECT d.child_id FROM dependencies d JOIN descendants x ON d.parent_id=x.issue_id
                ) SELECT 1 FROM descendants WHERE issue_id=? LIMIT 1""", (child_id, parent_id)).fetchone()
            if cycle:
                raise StoreError("dependency_cycle", "This dependency would create a cycle.")
            exists = conn.execute("SELECT 1 FROM dependencies WHERE parent_id=? AND child_id=?", (parent_id, child_id)).fetchone()
            if exists:
                return self._snapshot(conn, parent_id)
            conn.execute("INSERT INTO dependencies VALUES(?,?)", (parent_id, child_id))
            if child["status"] != "closed":
                resume = parent["resume_status"] if parent["status"] == "blocked" else parent["status"]
                self._change(conn, parent_id, timestamp, status="blocked", resume_status=resume)
            else:
                self._change(conn, parent_id, timestamp, status=parent["status"])
            self._history(conn, parent_id, "dependency_linked", timestamp, actor_id,
                          {"child_id": child_id, "child_status": child["status"],
                           "note": "A crew/reporting workflow dependency; not a diagnosis or safety certification."})
            return self._snapshot(conn, parent_id)

    def _unblock_dependents(self, conn, child_id, timestamp):
        parents = conn.execute("SELECT parent_id FROM dependencies WHERE child_id=?", (child_id,)).fetchall()
        for parent in parents:
            row = self._row(conn, parent["parent_id"])
            if row["status"] == "blocked" and not self._blocked(conn, row["issue_id"]):
                status = row["resume_status"] or "accepted"
                self._change(conn, row["issue_id"], timestamp, status=status, resume_status=None)
                self._history(conn, row["issue_id"], "dependencies_cleared", timestamp, "system",
                              {"resumed_status": status, "last_closed_child": child_id})

    def _tick_conn(self, conn, event_id, timestamp):
        changed = set()
        expired = conn.execute("""SELECT * FROM issues WHERE event_id=? AND offered_to IS NOT NULL
            AND status IN ('offered','blocked') AND offer_expires_at<=?
            ORDER BY CASE priority WHEN 'urgent' THEN 0 ELSE 1 END,created_at,issue_id""",
            (event_id, timestamp)).fetchall()
        # Release all expired offers before reallocating; ordering cannot keep
        # an expired reservation blocking another eligible backup.
        for row in expired:
            conn.execute("UPDATE attempts SET status='timeout' WHERE issue_id=? AND staff_id=?",
                         (row["issue_id"], row["offered_to"]))
            self._change(conn, row["issue_id"], timestamp, offered_to=None, offer_expires_at=None)
            self._history(conn, row["issue_id"], "offer_timed_out", timestamp, "system",
                          {"staff_id": row["offered_to"], "accepted": False})
            changed.add(row["issue_id"])
        for row in expired:
            self._offer(conn, row["issue_id"], timestamp)
        overdue = conn.execute("""SELECT * FROM issues WHERE event_id=? AND assigned_to IS NOT NULL
            AND status IN ('accepted','in_progress','blocked') AND resolution_deadline<=?
            AND escalated_at IS NULL""", (event_id, timestamp)).fetchall()
        for row in overdue:
            self._change(conn, row["issue_id"], timestamp, escalated_at=timestamp,
                         escalation_reason="resolution_follow_up_overdue", resolution_deadline=None)
            self._history(conn, row["issue_id"], "follow_up_escalated", timestamp, "system",
                          {"organizer_id": self._event(conn, event_id)["organizer_id"],
                           "assigned_staff_retains_responsibility": True,
                           "note": "Follow-up required; no automatic completion or arrival claim."})
            changed.add(row["issue_id"])
        return sorted(changed)

    def tick(self, event_id):
        with self._tx() as conn:
            self._event(conn, event_id)
            changed = self._tick_conn(conn, event_id, float(self._now()))
            return [self._snapshot(conn, issue_id) for issue_id in changed]

    def issue(self, issue_id):
        with self._tx(False) as conn:
            return self._snapshot(conn, issue_id)

    def list_issues(self, event_id):
        with self._tx(False) as conn:
            self._event(conn, event_id)
            rows = conn.execute("SELECT issue_id FROM issues WHERE event_id=? ORDER BY created_at,issue_id", (event_id,)).fetchall()
            return [self._snapshot(conn, row["issue_id"]) for row in rows]

    def set_availability(self, staff_id, available: bool, actor_id=ORGANIZER):
        """Trusted demo/organizer operation; it never cancels accepted work."""
        staff_id = _text(staff_id, "staff id", 200)
        actor_id = _text(actor_id, "actor id", 200)
        if type(available) is not bool:
            raise StoreError("invalid_request", "Availability must be true or false.")
        with self._tx() as conn:
            member = conn.execute("SELECT * FROM staff WHERE staff_id=?", (staff_id,)).fetchone()
            if member is None:
                raise StoreError("unknown_staff", "The crew member is not on the configured roster.")
            event = self._event(conn, member["event_id"])
            if actor_id != event["organizer_id"]:
                raise StoreError("wrong_actor", "Only the event organizer can configure roster availability.")
            conn.execute("UPDATE staff SET available=? WHERE staff_id=?", (int(available), staff_id))
            return {"staff_id": staff_id, "available": available}

    def configure_timeouts(self, event_id, offer_timeout_seconds, resolution_timeout_seconds,
                           actor_id=ORGANIZER):
        """Organizer configuration for future offers; existing deadlines persist."""
        actor_id = _text(actor_id, "actor id", 200)
        if (type(offer_timeout_seconds) is not int or not 1 <= offer_timeout_seconds <= 86400
                or type(resolution_timeout_seconds) is not int or not 1 <= resolution_timeout_seconds <= 604800):
            raise StoreError("invalid_request", "Use positive configured deadlines of at most one day and one week.")
        with self._tx() as conn:
            event = self._event(conn, event_id)
            if actor_id != event["organizer_id"]:
                raise StoreError("wrong_actor", "Only the organizer can configure event deadlines.")
            conn.execute("""INSERT INTO event_settings VALUES(?,?,?)
                ON CONFLICT(event_id) DO UPDATE SET offer_timeout_seconds=excluded.offer_timeout_seconds,
                resolution_timeout_seconds=excluded.resolution_timeout_seconds""",
                (event_id, offer_timeout_seconds, resolution_timeout_seconds))
            return self._settings(conn, event_id)
