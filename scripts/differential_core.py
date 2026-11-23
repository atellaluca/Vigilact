# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Black-box, seeded *behavioral* differential test for Core observers.

Uses HTTP only and does not import either observer or SDK. A canonical trace
excludes generated UUIDs/timestamps and compares observable invariants.
This is deliberately a bounded test, not a claim of formal equivalence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from datetime import datetime, timedelta, timezone

import httpx


def run(url: str, *, seed: int, cases: int, agents: dict[str, str], operator: tuple[str, str]) -> dict:
    if not 1 <= cases <= 100:
        raise ValueError("cases must be between 1 and 100")
    if len(agents) != 2:
        raise ValueError("exactly two agent identities are needed")
    rng = random.Random(seed)
    names = sorted(agents)
    headers = {name: {"X-Vigilact-Principal": name, "X-Vigilact-Key": key}
               for name, key in agents.items()}
    ops_headers = {"X-Vigilact-Principal": operator[0], "X-Vigilact-Key": operator[1]}
    run_id = f"diff-{seed:x}-{rng.getrandbits(64):016x}"
    # Do not depend on the caller clock being exactly in sync with the server.
    deadline = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    trace = []

    with httpx.Client(base_url=url.rstrip("/"), timeout=10, follow_redirects=False) as api:
        initial = api.get("/v1/outbox", headers=ops_headers)
        assert initial.status_code == 200, initial.text
        cursor = initial.json()["next_cursor"]
        for index in range(cases):
            subject = f"proof://{run_id}/{index}"
            event_type = f"proof.completed.{rng.randrange(4)}"
            contracts = {}
            for name in names:
                proposal = {"client_ref": f"{run_id}-{index}-{name}", "subject": subject,
                            "observation": {"kind": "expected_event", "event_type": event_type,
                                            "deadline_at": deadline}}
                response = api.post("/v1/contracts", json=proposal, headers=headers[name])
                assert response.status_code == 201, (response.status_code, response.text)
                contract = response.json()
                assert contract["outcome"] == "PENDING"
                contracts[name] = contract["id"]
                duplicate = api.post("/v1/contracts", json=proposal, headers=headers[name])
                assert duplicate.status_code == 201 and duplicate.json()["id"] == contract["id"]
                trace.append(["contract", name, 201, "PENDING", "idempotent"])

            first, other = (names if rng.randrange(2) else names[::-1])
            event = {"specversion": "1.0", "id": f"e-{run_id}-{index}-{first}",
                     "source": f"urn:vigilact:agent:{first}", "type": event_type,
                     "subject": subject, "data": {"sequence": index}}
            # Tenant isolation: caller cannot impersonate another event producer.
            forged = api.post("/v1/events", json=event, headers=headers[other])
            assert forged.status_code == 403
            trace.append(["source_auth", 403])

            accepted = api.post("/v1/events", json=event, headers=headers[first])
            assert accepted.status_code == 200 and accepted.json()["status"] == "accepted"
            assert accepted.json()["satisfied_contracts"] == [contracts[first]]
            own = api.get(f"/v1/contracts/{contracts[first]}", headers=headers[first])
            other_state = api.get(f"/v1/contracts/{contracts[other]}", headers=headers[other])
            assert own.json()["outcome"] == "SATISFIED" and other_state.json()["outcome"] == "PENDING"
            denied = api.get(f"/v1/contracts/{contracts[other]}", headers=headers[first])
            assert denied.status_code == 404  # No tenant existence oracle.
            trace.append(["isolation", first, 200, "SATISFIED", "PENDING", 404])
            duplicate = api.post("/v1/events", json=event, headers=headers[first])
            assert duplicate.status_code == 200 and duplicate.json()["status"] == "duplicate"
            changed = {**event, "data": {"sequence": -1}}
            conflict = api.post("/v1/events", json=changed, headers=headers[first])
            assert conflict.status_code == 409
            trace.append(["event_idempotency", 200, 409])

            # Other tenant independently satisfies its own contract.
            event_other = {**event, "source": f"urn:vigilact:agent:{other}",
                           "id": f"e-{run_id}-{index}-{other}"}
            accepted_other = api.post("/v1/events", json=event_other, headers=headers[other])
            assert accepted_other.status_code == 200
            assert accepted_other.json()["satisfied_contracts"] == [contracts[other]]
            trace.append(["second_tenant", other, 200, "SATISFIED"])

        outbox = []
        while True:
            page = api.get("/v1/outbox", params={"after": cursor, "limit": 25}, headers=ops_headers)
            assert page.status_code == 200
            data = page.json()
            entries = data["entries"]
            outbox.extend(entries)
            if not entries:
                break
            assert data["next_cursor"] > cursor
            cursor = data["next_cursor"]
        target = [entry for entry in outbox
                  if entry["event"].get("data", {}).get("subject", "").startswith(f"proof://{run_id}/")]
        assert len(target) == cases * 2, (len(target), cases * 2)
        assert all(e["event"]["type"] == "dev.vigilact.observation.satisfied" for e in target)
        trace.append(["outbox", len(target), "unique_evaluations"])

    canonical = json.dumps(trace, sort_keys=True, separators=(",", ":"))
    return {"profile": "core.expected_event/0.1", "seed": seed, "cases": cases,
            "assertions": len(trace), "semantic_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "trace": trace}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", required=True)
    p.add_argument("--seed", type=int, default=20261123)
    p.add_argument("--cases", type=int, default=12)
    p.add_argument("--agent-a", default="ci-agent")
    p.add_argument("--key-a", required=True)
    p.add_argument("--agent-b", default="ci-agent-b")
    p.add_argument("--key-b", required=True)
    p.add_argument("--operator", default="ci-operator")
    p.add_argument("--operator-key", required=True)
    a = p.parse_args()
    result = run(a.url, seed=a.seed, cases=a.cases,
                 agents={a.agent_a: a.key_a, a.agent_b: a.key_b},
                 operator=(a.operator, a.operator_key))
    print(json.dumps({k:v for k,v in result.items() if k != "trace"}, indent=2))


if __name__ == "__main__":
    main()
