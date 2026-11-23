# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella

#!/usr/bin/env python3
"""Language-neutral HTTP smoke conformance tests against any Vigilact observer.

Only the public v0.1 profile is exercised: this script never imports the server,
its Python models or its SDK. A passing result is NOT full protocol certification.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx


def check(condition: bool, message: str, results: list[dict]):
    results.append({"test": message, "passed": bool(condition)})
    if not condition:
        raise AssertionError(message)


def run(url: str, agent: str, key: str, operator: str | None,
        operator_key: str | None) -> list[dict]:
    results: list[dict] = []
    token = uuid4().hex[:16]
    agent_headers = {"X-Vigilact-Principal": agent, "X-Vigilact-Key": key}
    ops_headers = ({"X-Vigilact-Principal": operator,
                    "X-Vigilact-Key": operator_key} if operator and operator_key else None)
    subject = f"conformance://{token}"
    deadline = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    proposal = {"client_ref": f"conformance-{token}", "subject": subject,
                "observation": {"kind": "expected_event", "event_type": "conformance.completed",
                                "deadline_at": deadline}}
    with httpx.Client(base_url=url.rstrip("/"), timeout=15, follow_redirects=False) as api:
        info = api.get("/v1/info")
        check(info.status_code == 200 and
              info.json().get("protocol") == "vigilact/0.1-experimental",
              "protocol discovery", results)
        denied = api.post("/v1/contracts", json=proposal)
        check(denied.status_code == 401, "anonymous proposal denied", results)
        # Negative wire cases must match in both server implementations.
        for bad, label in (
            (1912353660, "epoch timestamp rejected"),
            ("2031-04-05T12:01:00.1234567Z", "excess precision rejected"),
            ("2031-04-05T12:01:00", "naive timestamp rejected"),
        ):
            invalid = {**proposal, "observation": {**proposal["observation"], "deadline_at": bad}}
            check(api.post("/v1/contracts", json=invalid, headers=agent_headers).status_code == 422,
                  label, results)
        unexpected = {**proposal, "undocumented_extension": True}
        check(api.post("/v1/contracts", json=unexpected, headers=agent_headers).status_code == 422,
              "unknown contract field rejected", results)
        first = api.post("/v1/contracts", json=proposal, headers=agent_headers)
        check(first.status_code == 201 and first.json().get("outcome") == "PENDING",
              "contract accepted", results)
        contract_id = first.json()["id"]
        repeat = api.post("/v1/contracts", json=proposal, headers=agent_headers)
        check(repeat.status_code == 201 and repeat.json().get("id") == contract_id,
              "idempotent contract reference", results)
        conflict = {**proposal, "observation": {**proposal["observation"],
                     "event_type": "conformance.different"}}
        check(api.post("/v1/contracts", json=conflict, headers=agent_headers).status_code == 409,
              "conflicting contract rejected", results)
        event = {"specversion": "1.0", "id": f"conformance-{token}",
                 "source": f"urn:vigilact:agent:{agent}",
                 "type": "conformance.completed", "subject": subject, "data": {"test": True}}
        invalid_data = {**event, "data": None}
        check(api.post("/v1/events", json=invalid_data, headers=agent_headers).status_code == 422,
              "null data object rejected", results)
        invalid_time = {**event, "time": "2031-04-05T12:01:00.1234567Z"}
        check(api.post("/v1/events", json=invalid_time, headers=agent_headers).status_code == 422,
              "invalid evidence timestamp rejected", results)
        forged = {**event, "source": "urn:vigilact:agent:some-other-agent"}
        check(api.post("/v1/events", json=forged, headers=agent_headers).status_code == 403,
              "forged event source rejected", results)
        accepted = api.post("/v1/events", json=event, headers=agent_headers)
        check(accepted.status_code == 200 and contract_id in
              accepted.json().get("satisfied_contracts", []),
              "evidence satisfies contract", results)
        duplicate = api.post("/v1/events", json=event, headers=agent_headers)
        check(duplicate.status_code == 200 and duplicate.json().get("status") == "duplicate",
              "event deduplication", results)
        conflict_event = {**event, "data": {"test": False}}
        check(api.post("/v1/events", json=conflict_event,
                       headers=agent_headers).status_code == 409,
              "conflicting event ID rejected", results)
        state = api.get(f"/v1/contracts/{contract_id}", headers=agent_headers)
        check(state.status_code == 200 and state.json().get("outcome") == "SATISFIED",
              "contract outcome persisted", results)
        if ops_headers:
            invalid_cursor = api.get("/v1/outbox?after=1junk", headers=ops_headers)
            check(invalid_cursor.status_code == 422, "invalid cursor rejected", results)
            page = api.get("/v1/outbox", headers=ops_headers)
            ok = page.status_code == 200 and any(
                item.get("event", {}).get("subject") == contract_id and
                item["event"].get("type") == "dev.vigilact.observation.satisfied"
                for item in page.json().get("entries", []))
            check(ok, "evaluation event in outbox", results)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Vigilact observer base URL")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--agent-key", default=os.environ.get("VIGILACT_CONFORMANCE_AGENT_KEY"),
                        help="Agent key; prefer VIGILACT_CONFORMANCE_AGENT_KEY env var")
    parser.add_argument("--operator", help="Optional operator principal for outbox test")
    parser.add_argument("--operator-key", default=os.environ.get("VIGILACT_CONFORMANCE_OPERATOR_KEY"),
                        help="Operator key; prefer VIGILACT_CONFORMANCE_OPERATOR_KEY env var")
    args = parser.parse_args()
    if not args.agent_key:
        parser.error("Set --agent-key or VIGILACT_CONFORMANCE_AGENT_KEY")
    if bool(args.operator) != bool(args.operator_key):
        parser.error("--operator and --operator-key must be supplied together")
    try:
        results = run(args.url, args.agent, args.agent_key,
                      args.operator, args.operator_key)
        print(json.dumps({"passed": len(results), "failed": 0,
                          "results": results}, indent=2))
        return 0
    except (AssertionError, httpx.HTTPError, KeyError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
