# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Executable HTTP walkthrough for the one-shot contract profile.

Run against a *disposable local reference observer*; creates a contract,
publishes synthetic evidence, and reads the resulting evaluation event.
No remote commands are enabled or invoked by this example.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx


def _headers(principal: str, key: str) -> dict[str, str]:
    return {"X-Vigilact-Principal": principal, "X-Vigilact-Key": key}


async def walkthrough(
    client: httpx.AsyncClient,
    *,
    agent: str,
    agent_key: str,
    operator: str,
    operator_key: str,
    now: datetime | None = None,
) -> dict[str, str]:
    """Run a non-destructive, synthetic contract/evidence flow over HTTP.

    This is a reproducible *demo*, not an integration harness: the outbox
    query uses cursor zero and should only target a fresh local database.
    """
    now = now or datetime.now(timezone.utc)
    run_id = uuid.uuid4().hex
    subject = f"demo://http-contract/{run_id}"
    proposal = {
        "client_ref": f"demo-{run_id}",
        "subject": subject,
        "observation": {
            "kind": "expected_event",
            "event_type": "demo.operation.completed",
            "deadline_at": (now + timedelta(minutes=5)).isoformat(),
        },
    }
    r = await client.post("/v1/contracts", json=proposal, headers=_headers(agent, agent_key))
    r.raise_for_status()
    contract = r.json()
    assert contract["state"] == "ACTIVE" and contract["outcome"] == "PENDING"

    event = {
        "specversion": "1.0",
        "id": f"evidence-{run_id}",
        "source": f"urn:vigilact:agent:{agent}",
        "type": "demo.operation.completed",
        "subject": subject,
        "data": {"demo": True},
    }
    r = await client.post("/v1/events", json=event, headers=_headers(agent, agent_key))
    r.raise_for_status()
    receipt = r.json()
    assert receipt["status"] == "accepted"
    assert contract["id"] in receipt["satisfied_contracts"]

    r = await client.get(f"/v1/contracts/{contract['id']}", headers=_headers(agent, agent_key))
    r.raise_for_status()
    assert r.json()["outcome"] == "SATISFIED"

    # In a real consumer persist the cursor only AFTER its effect succeeds.
    r = await client.get("/v1/outbox", params={"after": 0, "limit": 500},
                         headers=_headers(operator, operator_key))
    r.raise_for_status()
    expected_type = "dev.vigilact.observation.satisfied"
    matching = [entry for entry in r.json()["entries"]
                if entry["event"]["type"] == expected_type
                and entry["event"]["data"].get("contract_id") == contract["id"]]
    assert len(matching) == 1, "Expected one neutral evaluation entry for this contract"

    return {"contract_id": contract["id"], "outcome": "SATISFIED",
            "outbox_sequence": str(matching[0]["seq"]), "event_type": expected_type}


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000",
                        help="Use only an isolated local development observer")
    args = parser.parse_args()
    required = ["VIGILACT_AGENT", "VIGILACT_AGENT_KEY", "VIGILACT_OPERATOR", "VIGILACT_OPERATOR_KEY"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        parser.error("Missing environment variables: " + ", ".join(missing))
    async with httpx.AsyncClient(base_url=args.url, timeout=10) as client:
        result = await walkthrough(
            client,
            agent=os.environ["VIGILACT_AGENT"], agent_key=os.environ["VIGILACT_AGENT_KEY"],
            operator=os.environ["VIGILACT_OPERATOR"], operator_key=os.environ["VIGILACT_OPERATOR_KEY"],
        )
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
