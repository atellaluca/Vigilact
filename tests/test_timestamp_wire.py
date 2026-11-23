# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""RFC3339 syntax and precision are mandatory at the public boundary."""
from conftest import headers, proposal, event


def test_reject_epoch_numeric_or_nonstandard_deadlines(context):
    api, clock, _ = context
    for bad in (1912353660, "2031-04-05 12:01:00Z", "2031-04-05T12:01:00.1234567Z",
                "2031-04-05T12:01:00", "2031-04-05t12:01:00Z"):
        data = proposal(clock)
        data["observation"]["deadline_at"] = bad
        assert api.post("/v1/contracts", json=data, headers=headers()).status_code == 422


def test_reject_epoch_numeric_or_nonstandard_event_timestamps(context):
    api, _, _ = context
    for bad in (1912353660, "2031-04-05T12:01:00.123456789Z", "2031-04-05T12:01:00"):
        evidence = event(id="invalid-time")
        evidence["time"] = bad
        assert api.post("/v1/events", json=evidence, headers=headers()).status_code == 422


def test_offset_normalized_and_idempotent(context):
    api, clock, _ = context
    a = proposal(clock)
    a["observation"]["deadline_at"] = "2031-04-05T14:01:00+02:00"
    first = api.post("/v1/contracts", json=a, headers=headers())
    assert first.status_code == 201
    a["observation"]["deadline_at"] = "2031-04-05T12:01:00Z"
    assert api.post("/v1/contracts", json=a, headers=headers()).json()["id"] == first.json()["id"]
