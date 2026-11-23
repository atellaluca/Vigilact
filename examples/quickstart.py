# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella

"""Self-contained executable demo, no running web server required.

Run: python examples/quickstart.py
"""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from vigilact.server import create_app


class Clock:
    def __init__(self):
        self.now = datetime(2030, 1, 1, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.now


DEMO_KEYS = {
    "backup-agent": {"role": "agent", "key": "demo-agent-local-only-123456"},
    "operator": {"role": "operator", "key": "demo-operator-local-only-123456"},
}


def auth(principal):
    return {"X-Vigilact-Principal": principal, "X-Vigilact-Key": DEMO_KEYS[principal]["key"]}


def check(result):
    if result.status_code >= 400:
        raise RuntimeError(f"HTTP {result.status_code}: {result.text}")
    return result.json()


def main():
    clock = Clock()
    with tempfile.TemporaryDirectory() as directory:
        app = create_app(db_path=Path(directory) / "demo.db", credentials=DEMO_KEYS,
                         clock=clock, sweep_seconds=0, enable_commands=True)
        with TestClient(app) as api:
            deadline = (clock.now + timedelta(minutes=5)).isoformat()
            proposal = {"client_ref": "backup-2030-01-01", "subject": "backup://node-a",
                        "observation": {"kind": "expected_event", "event_type": "backup.completed",
                                        "deadline_at": deadline}}
            first = check(api.post("/v1/contracts", json=proposal, headers=auth("backup-agent")))
            print("1. Contract accepted:", first["id"])

            capabilities = {"capabilities": [{"name": "backup.inspect", "mode": "query"},
                                              {"name": "backup.retry", "mode": "command", "invocable": True}]}
            check(api.put("/v1/agents/me/capabilities", json=capabilities, headers=auth("backup-agent")))
            print("2. Agent capabilities registered")

            clock.now += timedelta(minutes=2)
            incoming = {"specversion": "1.0", "id": "backup-run-1",
                        "source": "urn:vigilact:agent:backup-agent", "type": "backup.completed",
                        "subject": "backup://node-a", "data": {"duration_s": 27}}
            result = check(api.post("/v1/events", json=incoming, headers=auth("backup-agent")))
            print("3. Evidence received:", result["status"], "satisfied:", len(result["satisfied_contracts"]))

            # Another commitment is never satisfied: simulate time passing deterministically.
            second = dict(proposal)
            second["client_ref"] = "backup-2030-01-02"
            second["observation"] = dict(proposal["observation"], deadline_at=(clock.now + timedelta(minutes=3)).isoformat())
            missing = check(api.post("/v1/contracts", json=second, headers=auth("backup-agent")))
            clock.now += timedelta(minutes=4)
            app.state.service.evaluate_due()
            outcome = check(api.get("/v1/contracts/" + missing["id"], headers=auth("operator")))
            print("4. Missing evidence outcome:", outcome["outcome"])

            cmd = check(api.post("/v1/commands", headers=auth("operator"), json={
                "request_id": "inspect-1", "target_agent": "backup-agent",
                "capability": "backup.retry", "arguments": {"job": "nightly"}}))
            pending = check(api.get("/v1/agents/me/commands", headers=auth("backup-agent")))
            assert pending["commands"][0]["id"] == cmd["id"]
            check(api.post(f"/v1/agents/me/commands/{cmd['id']}/claim", headers=auth("backup-agent")))
            completed = check(api.post(f"/v1/agents/me/commands/{cmd['id']}/result",
                                       headers=auth("backup-agent"), json={
                                           "status": "succeeded", "output": {"queued_locally": True}}))
            print("5. Authorized command acknowledged:", completed["status"])

            outbox = check(api.get("/v1/outbox", headers=auth("operator")))
            print("6. Neutral event log:")
            for item in outbox["entries"]:
                print("   -", item["event"]["type"])
            print("\nDEMO COMPLETE — no notification service required.")


if __name__ == "__main__":
    main()
