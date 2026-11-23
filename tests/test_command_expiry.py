# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Command safety regressions: timeouts never trigger blind re-execution."""

import sqlite3
from contextlib import closing

from fastapi.testclient import TestClient
from conftest import KEYS, Clock, headers
from vigilact.server import create_app


CAPABILITIES = {"capabilities": [{"name": "backup.retry", "mode": "command", "invocable": True}]}


def enqueue(api, request_id, ttl=300):
    return api.post("/v1/commands", headers=headers("ops"), json={
        "request_id": request_id, "target_agent": "node-a", "capability": "backup.retry",
        "ttl_seconds": ttl, "arguments": {"job": "nightly"}})


def enable_agent(api):
    assert api.put("/v1/agents/me/capabilities", headers=headers(), json=CAPABILITIES).status_code == 200


def test_unclaimed_expiry_prevents_execution_and_is_durable(context):
    api, clock, _ = context
    enable_agent(api)
    queued = enqueue(api, "expires", ttl=10)
    assert queued.status_code == 201
    cmd = queued.json()
    assert cmd["status"] == "PENDING" and cmd["expires_at"]
    clock.jump(seconds=10)
    assert api.get("/v1/agents/me/commands", headers=headers()).json()["commands"] == []
    url = "/v1/agents/me/commands/" + cmd["id"]
    assert api.post(url + "/claim", headers=headers()).status_code == 409
    same = enqueue(api, "expires", ttl=10).json()
    assert same["status"] == "EXPIRED" and same["id"] == cmd["id"]
    assert enqueue(api, "expires", ttl=300).status_code == 409


def test_claimed_lease_becomes_unknown_without_requeue(context):
    api, clock, _ = context
    enable_agent(api)
    queued = enqueue(api, "lease", ttl=3600).json()
    url = "/v1/agents/me/commands/" + queued["id"]
    claimed = api.post(url + "/claim", headers=headers()).json()
    assert claimed["status"] == "CLAIMED" and claimed["lease_expires_at"]
    clock.jump(seconds=120)
    assert api.get("/v1/agents/me/commands", headers=headers()).json()["commands"] == []
    assert api.post(url + "/claim", headers=headers()).status_code == 409
    assert enqueue(api, "lease", ttl=3600).json()["status"] == "UNKNOWN"
    # The original agent may report a verified late result, but commands are never requeued.
    result = {"status": "succeeded", "output": {"recovered": True}}
    finished = api.post(url + "/result", json=result, headers=headers())
    assert finished.status_code == 200 and finished.json()["status"] == "SUCCEEDED"
    assert api.post(url + "/result", json=result, headers=headers()).status_code == 200
    assert api.post(url + "/result", json={"status": "failed"}, headers=headers()).status_code == 409


def test_commands_survive_restart_and_expire_before_claim(tmp_path):
    clock = Clock()
    db = tmp_path / "commands.db"
    with TestClient(create_app(db, credentials=KEYS, clock=clock, sweep_seconds=0,
                               enable_commands=True)) as api:
        enable_agent(api)
        cmd = enqueue(api, "restart", ttl=3).json()
    clock.jump(seconds=4)
    with TestClient(create_app(db, credentials=KEYS, clock=clock, sweep_seconds=0,
                               enable_commands=True)) as api:
        assert api.post("/v1/agents/me/commands/" + cmd["id"] + "/claim",
                        headers=headers()).status_code == 409
        assert enqueue(api, "restart", ttl=3).json()["status"] == "EXPIRED"


def test_legacy_command_database_is_migrated_fail_closed(tmp_path):
    clock = Clock()
    db = tmp_path / "legacy.db"
    with TestClient(create_app(db, credentials=KEYS, clock=clock, sweep_seconds=0,
                               enable_commands=True)) as api:
        enable_agent(api)
        old = enqueue(api, "legacy", ttl=30).json()
    # Simulate a 0.3-era database that predates the command lifecycle columns.
    with closing(sqlite3.connect(db)) as conn, conn:
        conn.execute("ALTER TABLE commands RENAME TO commands_current")
        conn.execute("""CREATE TABLE commands (
          id TEXT PRIMARY KEY, operator TEXT NOT NULL, request_id TEXT NOT NULL,
          target_agent TEXT NOT NULL, capability TEXT NOT NULL, arguments_json TEXT NOT NULL,
          status TEXT NOT NULL, result_json TEXT, created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL, UNIQUE(operator, request_id))""")
        conn.execute("""INSERT INTO commands
          (id, operator, request_id, target_agent, capability, arguments_json,
          status, result_json, created_at, updated_at)
          SELECT id, operator, request_id, target_agent, capability, arguments_json,
          status, result_json, created_at, updated_at FROM commands_current""")
        conn.execute("DROP TABLE commands_current")
    with TestClient(create_app(db, credentials=KEYS, clock=clock, sweep_seconds=0,
                               enable_commands=True)) as api:
        # The previous command's lifetime cannot be established, so it is expired.
        assert api.post("/v1/agents/me/commands/" + old["id"] + "/claim",
                        headers=headers()).status_code == 409


def test_reject_invalid_command_lifetimes(context):
    api, _, _ = context
    enable_agent(api)
    for lifetime in (0, -1, 86401, 1.5, "infinite"):
        result = api.post("/v1/commands", headers=headers("ops"), json={
            "request_id": "invalid", "target_agent": "node-a", "capability": "backup.retry",
            "ttl_seconds": lifetime})
        assert result.status_code == 422


def test_command_operator_read_is_scoped_and_reports_expiry(context):
    api, clock, _ = context
    enable_agent(api)
    c = enqueue(api, 'operator-read', ttl=2).json()
    u = '/v1/commands/' + c['id']
    assert api.get(u, headers=headers()).status_code == 403
    assert api.get(u, headers=headers('ops')).json()['status'] == 'PENDING'
    clock.jump(seconds=2)
    assert api.get(u, headers=headers('ops')).json()['status'] == 'EXPIRED'
    assert api.get('/v1/commands/no-such-command', headers=headers('ops')).status_code == 404


def test_other_operator_cannot_inspect_queued_command(tmp_path):
    clock = Clock()
    credentials = {**KEYS, 'secondary-ops': {
        'role': 'operator', 'key': 'another-local-operator-secret-key-abc123'}}
    app = create_app(tmp_path / 'operator-scope.db', credentials=credentials,
                     clock=clock, sweep_seconds=0, enable_commands=True)
    with TestClient(app) as api:
        enable_agent(api)
        cmd = enqueue(api, 'private-result').json()
        secret_headers = {'X-Vigilact-Principal': 'secondary-ops',
                          'X-Vigilact-Key': credentials['secondary-ops']['key']}
        assert api.get('/v1/commands/' + cmd['id'], headers=secret_headers).status_code == 404
        assert api.get('/v1/commands/' + cmd['id'], headers=headers('ops')).status_code == 200
