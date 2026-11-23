# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella

"""SQLite-backed reference semantics (not a normative server architecture)."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterator

from .models import (
    CapabilityManifest,
    CloudEvent,
    CommandRequest,
    CommandResult,
    ContractProposal,
    ensure_utc,
)


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _timestamp(value: datetime) -> str:
    return ensure_utc(value).isoformat(timespec="microseconds")


class ProtocolError(Exception):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


class VigilactService:
    def __init__(
        self,
        db_path: str | Path,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.db_path = str(db_path)
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        if self.db_path == ":memory:":
            raise ValueError("Use a file-backed SQLite database for this reference server")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 10000")
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connection() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS contracts (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, client_ref TEXT NOT NULL,
                    subject TEXT NOT NULL, event_type TEXT NOT NULL,
                    deadline_at TEXT NOT NULL, accepted_at TEXT NOT NULL,
                    outcome TEXT NOT NULL DEFAULT 'PENDING', resolved_at TEXT,
                    proposal_json TEXT NOT NULL,
                    UNIQUE(owner, client_ref)
                );
                CREATE INDEX IF NOT EXISTS idx_contracts_due
                    ON contracts(outcome, deadline_at);
                CREATE TABLE IF NOT EXISTS received_events (
                    source TEXT NOT NULL, event_id TEXT NOT NULL, owner TEXT NOT NULL,
                    received_at TEXT NOT NULL, event_json TEXT NOT NULL,
                    PRIMARY KEY (source, event_id)
                );
                CREATE TABLE IF NOT EXISTS outbox (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL, event_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS capabilities (
                    agent TEXT NOT NULL, name TEXT NOT NULL, mode TEXT NOT NULL,
                    description TEXT NOT NULL, invocable INTEGER NOT NULL,
                    PRIMARY KEY (agent, name)
                );
                CREATE TABLE IF NOT EXISTS commands (
                    id TEXT PRIMARY KEY, operator TEXT NOT NULL, request_id TEXT NOT NULL,
                    target_agent TEXT NOT NULL, capability TEXT NOT NULL,
                    arguments_json TEXT NOT NULL, status TEXT NOT NULL,
                    result_json TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    ttl_seconds INTEGER NOT NULL DEFAULT 300,
                    expires_at TEXT, lease_expires_at TEXT,
                    UNIQUE(operator, request_id)
                );
                CREATE INDEX IF NOT EXISTS idx_command_queue
                    ON commands(target_agent, status, created_at);
            """)
            # Safe forward migration of the 0.3 alpha reference database.
            cols = {r["name"] for r in c.execute("PRAGMA table_info(commands)")}
            for name, ddl in (
                ("ttl_seconds", "INTEGER NOT NULL DEFAULT 300"),
                ("expires_at", "TEXT"),
                ("lease_expires_at", "TEXT"),
            ):
                if name not in cols:
                    c.execute(f"ALTER TABLE commands ADD COLUMN {name} {ddl}")
            # Legacy pending/claimed commands have unknown time-to-live. Fail closed.
            c.execute("UPDATE commands SET expires_at=created_at WHERE expires_at IS NULL")
            c.execute("UPDATE commands SET lease_expires_at=updated_at "
                      "WHERE lease_expires_at IS NULL AND status='CLAIMED'")

    def check_storage(self) -> bool:
        """Check reference-storage availability and required schema presence."""
        try:
            with self._connection() as conn:
                conn.execute("SELECT 1 FROM contracts LIMIT 1").fetchone()
            return True
        except sqlite3.Error:
            return False

    def _now(self) -> str:
        return _timestamp(self.clock())

    @staticmethod
    def _contract(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"], "owner": row["owner"],
            "client_ref": row["client_ref"], "subject": row["subject"],
            "observation": {"kind": "expected_event", "event_type": row["event_type"],
                            "deadline_at": row["deadline_at"]},
            "state": "ACTIVE", "outcome": row["outcome"],
            "accepted_at": row["accepted_at"], "resolved_at": row["resolved_at"],
        }

    def create_contract(self, owner: str, proposal: ContractProposal) -> dict:
        normalized = _json(proposal.model_dump(mode="json"))
        now = self._now()
        with self._connection() as c:
            previous = c.execute(
                "SELECT * FROM contracts WHERE owner=? AND client_ref=?", (owner, proposal.client_ref)
            ).fetchone()
            if previous:
                if previous["proposal_json"] != normalized:
                    raise ProtocolError("reference_conflict", "client_ref already exists with different terms", 409)
                return self._contract(previous)
            deadline = _timestamp(proposal.observation.deadline_at)
            if deadline <= now:
                raise ProtocolError("deadline_elapsed", "The deadline must be in the future", 422)
            contract_id = str(uuid.uuid4())
            c.execute("""INSERT INTO contracts
                (id, owner, client_ref, subject, event_type, deadline_at,
                 accepted_at, outcome, proposal_json)
                 VALUES (?,?,?,?,?,?,?,'PENDING',?)""",
                      (contract_id, owner, proposal.client_ref, proposal.subject,
                       proposal.observation.event_type, deadline, now, normalized))
            return self._contract(c.execute("SELECT * FROM contracts WHERE id=?", (contract_id,)).fetchone())

    def get_contract(self, contract_id: str, principal: str, operator: bool = False) -> dict:
        with self._connection() as c:
            row = c.execute("SELECT * FROM contracts WHERE id=?", (contract_id,)).fetchone()
            if row is None or (row["owner"] != principal and not operator):
                raise ProtocolError("not_found", "Contract not found", 404)
            return self._contract(row)

    def _emit(self, c: sqlite3.Connection, typ: str, contract: sqlite3.Row, at: str) -> None:
        event = {
            "specversion": "1.0", "id": str(uuid.uuid4()),
            "source": "urn:vigilact:reference-server", "type": typ,
            "subject": contract["id"], "time": at,
            "datacontenttype": "application/json",
            "data": {"contract_id": contract["id"], "owner": contract["owner"],
                     "subject": contract["subject"], "deadline_at": contract["deadline_at"],
                     "expected_event_type": contract["event_type"]},
        }
        c.execute("INSERT INTO outbox (created_at,event_json) VALUES (?,?)", (at, _json(event)))

    def _evaluate_in_transaction(self, c: sqlite3.Connection, now: str) -> int:
        rows = c.execute(
            "SELECT * FROM contracts WHERE outcome='PENDING' AND deadline_at < ? ORDER BY deadline_at, id",
            (now,),
        ).fetchall()
        for row in rows:
            c.execute("UPDATE contracts SET outcome='NOT_OBSERVED', resolved_at=? WHERE id=?",
                      (now, row["id"]))
            self._emit(c, "dev.vigilact.observation.not_observed", row, now)
        return len(rows)

    def evaluate_due(self) -> int:
        """Reconcile overdue one-shot observations (also run by server background loop)."""
        with self._connection() as c:
            return self._evaluate_in_transaction(c, self._now())

    def publish_event(self, owner: str, event: CloudEvent) -> dict:
        expected_source = f"urn:vigilact:agent:{owner}"
        if event.source != expected_source:
            raise ProtocolError("source_mismatch", f"source must be {expected_source}", 403)
        encoded = _json(event.model_dump(mode="json", exclude_none=True))
        now = self._now()
        with self._connection() as c:
            previous = c.execute(
                "SELECT event_json FROM received_events WHERE source=? AND event_id=?",
                (event.source, event.id),
            ).fetchone()
            if previous:
                if previous["event_json"] != encoded:
                    raise ProtocolError("event_conflict", "Event ID reused with different content", 409)
                return {"status": "duplicate", "satisfied_contracts": []}
            # Evaluate before accepting newly arrived events: late messages cannot satisfy a deadline.
            self._evaluate_in_transaction(c, now)
            c.execute("""INSERT INTO received_events
                (source, event_id, owner, received_at, event_json) VALUES (?,?,?,?,?)""",
                (event.source, event.id, owner, now, encoded))
            eligible = c.execute("""SELECT * FROM contracts
                WHERE owner=? AND subject=? AND event_type=?
                  AND outcome='PENDING' AND accepted_at <= ? AND deadline_at >= ? ORDER BY id""",
                (owner, event.subject, event.type, now, now),
            ).fetchall()
            for contract in eligible:
                c.execute("UPDATE contracts SET outcome='SATISFIED', resolved_at=? WHERE id=?",
                          (now, contract["id"]))
                self._emit(c, "dev.vigilact.observation.satisfied", contract, now)
            return {"status": "accepted", "satisfied_contracts": [row["id"] for row in eligible]}

    def read_outbox(self, after: int = 0, limit: int = 100) -> dict:
        with self._connection() as c:
            rows = c.execute("SELECT * FROM outbox WHERE seq>? ORDER BY seq LIMIT ?", (after, limit)).fetchall()
        entries = [{"seq": row["seq"], "event": json.loads(row["event_json"])} for row in rows]
        return {"entries": entries, "next_cursor": entries[-1]["seq"] if entries else after}

    def put_capabilities(self, agent: str, manifest: CapabilityManifest) -> dict:
        with self._connection() as c:
            c.execute("DELETE FROM capabilities WHERE agent=?", (agent,))
            for cap in manifest.capabilities:
                c.execute("""INSERT INTO capabilities
                    (agent,name,mode,description,invocable) VALUES (?,?,?,?,?)""",
                    (agent, cap.name, cap.mode, cap.description, int(cap.invocable)))
            # A revoked capability must not leave an unclaimed remote command executable.
            # Already-claimed commands remain indeterminate and require agent-side checks.
            c.execute("""UPDATE commands
                SET status='CANCELLED', updated_at=?, result_json=?
                WHERE target_agent=? AND status='PENDING'
                  AND NOT EXISTS (
                    SELECT 1 FROM capabilities
                    WHERE capabilities.agent=commands.target_agent
                      AND capabilities.name=commands.capability
                      AND capabilities.mode='command'
                      AND capabilities.invocable=1
                  )""", (self._now(), _json({"reason": "capability_revoked"}), agent))
        return self.read_capabilities(agent)

    def read_capabilities(self, agent: str) -> dict:
        with self._connection() as c:
            rows = c.execute("SELECT * FROM capabilities WHERE agent=? ORDER BY name", (agent,)).fetchall()
        return {"agent": agent, "capabilities": [
            {"name": r["name"], "mode": r["mode"], "description": r["description"],
             "invocable": bool(r["invocable"])} for r in rows
        ]}

    @staticmethod
    def _command(row: sqlite3.Row) -> dict:
        return {"id": row["id"], "request_id": row["request_id"],
                "target_agent": row["target_agent"], "capability": row["capability"],
                "arguments": json.loads(row["arguments_json"]), "status": row["status"],
                "result": json.loads(row["result_json"]) if row["result_json"] else None,
                "created_at": row["created_at"], "updated_at": row["updated_at"],
                "expires_at": row["expires_at"],
                "lease_expires_at": row["lease_expires_at"]}

    def _reconcile_commands(self, c: sqlite3.Connection, now: str) -> None:
        """Expire unclaimed work; mark expired claims indeterminate, never retry them."""
        c.execute("""UPDATE commands SET status='EXPIRED', updated_at=?
            WHERE status='PENDING' AND expires_at <= ?""", (now, now))
        c.execute("""UPDATE commands SET status='UNKNOWN', updated_at=?
            WHERE status='CLAIMED' AND lease_expires_at <= ?""", (now, now))

    def reconcile_commands(self) -> None:
        with self._connection() as c:
            self._reconcile_commands(c, self._now())

    def enqueue_command(self, operator: str, request: CommandRequest) -> dict:
        args_json = _json(request.arguments)
        now = self._now()
        with self._connection() as c:
            self._reconcile_commands(c, now)
            old = c.execute("SELECT * FROM commands WHERE operator=? AND request_id=?",
                            (operator, request.request_id)).fetchone()
            if old:
                if (old["target_agent"], old["capability"], old["arguments_json"], old["ttl_seconds"]) != (
                    request.target_agent, request.capability, args_json, request.ttl_seconds
                ):
                    raise ProtocolError("request_conflict", "request_id already used for another command", 409)
                return self._command(old)
            cap = c.execute("""SELECT * FROM capabilities
                WHERE agent=? AND name=? AND mode='command' AND invocable=1""",
                (request.target_agent, request.capability)).fetchone()
            if cap is None:
                raise ProtocolError("capability_unavailable", "No opt-in invocable capability", 422)
            command_id = str(uuid.uuid4())
            expires_at = _timestamp(datetime.fromisoformat(now) + timedelta(seconds=request.ttl_seconds))
            c.execute("""INSERT INTO commands
                (id,operator,request_id,target_agent,capability,arguments_json,status,
                 created_at,updated_at,ttl_seconds,expires_at)
                VALUES (?,?,?,?,?,?,'PENDING',?,?,?,?)""",
                (command_id, operator, request.request_id, request.target_agent,
                 request.capability, args_json, now, now, request.ttl_seconds, expires_at))
            row = c.execute("SELECT * FROM commands WHERE id=?", (command_id,)).fetchone()
            return self._command(row)

    def get_command(self, operator: str, command_id: str) -> dict:
        """Inspect a command requested by this operator without leaking other operators' work."""
        with self._connection() as c:
            self._reconcile_commands(c, self._now())
            row = c.execute("SELECT * FROM commands WHERE id=? AND operator=?",
                            (command_id, operator)).fetchone()
        if row is None:
            raise ProtocolError("not_found", "Command not found", 404)
        return self._command(row)

    def pending_commands(self, agent: str) -> list[dict]:
        with self._connection() as c:
            self._reconcile_commands(c, self._now())
            rows = c.execute("""SELECT * FROM commands
                WHERE target_agent=? AND status='PENDING' ORDER BY created_at, id LIMIT 100""",
                (agent,)).fetchall()
        return [self._command(row) for row in rows]

    def claim_command(self, agent: str, command_id: str) -> dict:
        now = self._now()
        with self._connection() as c:
            self._reconcile_commands(c, now)
            row = c.execute("SELECT * FROM commands WHERE id=? AND target_agent=?",
                            (command_id, agent)).fetchone()
            if row is None:
                raise ProtocolError("not_found", "Command not found", 404)
            if row["status"] != "PENDING":
                raise ProtocolError("not_pending", "Command is not pending", 409)
            lease_expiry = _timestamp(datetime.fromisoformat(now) + timedelta(seconds=120))
            c.execute("UPDATE commands SET status='CLAIMED', updated_at=?, lease_expires_at=? WHERE id=?",
                      (now, lease_expiry, command_id))
            return self._command(c.execute("SELECT * FROM commands WHERE id=?", (command_id,)).fetchone())

    def resolve_command(self, agent: str, command_id: str, result: CommandResult) -> dict:
        encoded = _json(result.model_dump(mode="json"))
        now = self._now()
        with self._connection() as c:
            self._reconcile_commands(c, now)
            row = c.execute("SELECT * FROM commands WHERE id=? AND target_agent=?",
                            (command_id, agent)).fetchone()
            if row is None:
                raise ProtocolError("not_found", "Command not found", 404)
            if row["status"] in ("SUCCEEDED", "FAILED"):
                if row["result_json"] == encoded:
                    return self._command(row)
                raise ProtocolError("result_conflict", "Command already resolved differently", 409)
            # An agent may attest a late result after its lease becomes UNKNOWN;
            # the server never automatically requeues an uncertain operation.
            if row["status"] not in ("CLAIMED", "UNKNOWN"):
                raise ProtocolError("not_claimed", "Command must be claimed first", 409)
            state = "SUCCEEDED" if result.status == "succeeded" else "FAILED"
            c.execute("UPDATE commands SET status=?, result_json=?, updated_at=? WHERE id=?",
                      (state, encoded, now, command_id))
            return self._command(c.execute("SELECT * FROM commands WHERE id=?", (command_id,)).fetchone())
