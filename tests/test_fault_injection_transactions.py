# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Deterministic crash-window simulations for SQLite atomicity.

These deliberately inject exceptions at an effect emission boundary. They do
not claim to simulate a real power loss, storage corruption or network outage.
"""
import sqlite3
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor

import pytest

from conftest import Clock, event, proposal
from vigilact.models import CloudEvent, ContractProposal
from vigilact.service import VigilactService


def _service(tmp_path):
    clock = Clock()
    return VigilactService(tmp_path / "faults.sqlite3", clock=clock), clock


def _raise_on_emit(*_args):
    raise OSError("injected outbox write failure")


def test_event_and_observation_roll_back_together(tmp_path, monkeypatch):
    svc, clock = _service(tmp_path)
    p = ContractProposal.model_validate(proposal(clock))
    cid = svc.create_contract("node-a", p)["id"]
    evt = CloudEvent.model_validate(event())
    original = svc._emit
    monkeypatch.setattr(svc, "_emit", _raise_on_emit)
    with pytest.raises(OSError, match="injected"):
        svc.publish_event("node-a", evt)
    assert svc.get_contract(cid, "node-a")["outcome"] == "PENDING"
    assert svc.read_outbox()["entries"] == []
    with sqlite3.connect(svc.db_path) as db:
        assert db.execute("SELECT COUNT(*) FROM received_events").fetchone()[0] == 0
    monkeypatch.setattr(svc, "_emit", original)
    result = svc.publish_event("node-a", evt)
    assert result["status"] == "accepted" and result["satisfied_contracts"] == [cid]
    assert len(svc.read_outbox()["entries"]) == 1


def test_missing_observation_sweep_rolls_back_entire_batch(tmp_path, monkeypatch):
    svc, clock = _service(tmp_path)
    ids = [svc.create_contract("node-a", ContractProposal.model_validate(
        proposal(clock, ref=f"batch-{i}", subject=f"backup://batch-{i}", offset=10)))["id"]
           for i in range(4)]
    clock.jump(seconds=11)
    calls = 0
    original = svc._emit

    def fail_after_first(conn, typ, contract, at):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected partial-batch failure")
        original(conn, typ, contract, at)

    monkeypatch.setattr(svc, "_emit", fail_after_first)
    with pytest.raises(OSError, match="partial-batch"):
        svc.evaluate_due()
    assert all(svc.get_contract(cid, "node-a")["outcome"] == "PENDING" for cid in ids)
    assert svc.read_outbox()["entries"] == []
    monkeypatch.setattr(svc, "_emit", original)
    assert svc.evaluate_due() == 4
    assert svc.evaluate_due() == 0
    restarted = VigilactService(svc.db_path, clock=clock)
    assert all(restarted.get_contract(cid, "node-a")["outcome"] == "NOT_OBSERVED" for cid in ids)
    assert len(restarted.read_outbox()["entries"]) == 4


@pytest.mark.parametrize("seed", [1, 7, 23, 20261123])
def test_seeded_event_and_sweep_interleavings_never_duplicate_outcomes(tmp_path, seed):
    """Concurrent event receipt vs sweep may choose either outcome, not both."""
    import random
    rng = random.Random(seed)
    svc, clock = _service(tmp_path)
    for index in range(12):
        offset = 20 + index
        ref = f"case-{index}"
        subject = f"backup://{seed}/{index}"
        cid = svc.create_contract("node-a", ContractProposal.model_validate(
            proposal(clock, ref=ref, subject=subject, offset=offset)))["id"]
        # Each iteration has a deadline after its own creation; deterministic choices.
        clock.value += timedelta(seconds=offset + rng.choice([-1, 1]))
        evt = CloudEvent.model_validate(event(id=f"receipt-{index}", subject=subject))
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_event = pool.submit(svc.publish_event, "node-a", evt)
            f_sweep = pool.submit(svc.evaluate_due)
            f_event.result()
            f_sweep.result()
        result = svc.get_contract(cid, "node-a")
        assert result["outcome"] in {"SATISFIED", "NOT_OBSERVED"}
        evidence = [e for e in svc.read_outbox(limit=500)["entries"] if e["event"]["subject"] == cid]
        assert len(evidence) == 1
        assert evidence[0]["event"]["type"].endswith(
            "satisfied" if result["outcome"] == "SATISFIED" else "not_observed")
