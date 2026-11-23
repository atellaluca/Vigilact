# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Concurrency invariants for SQLite-backed reference semantics."""
from concurrent.futures import ThreadPoolExecutor

from conftest import Clock, event, proposal
from vigilact.models import CloudEvent, ContractProposal
from vigilact.service import VigilactService


def test_concurrent_retries_do_not_multiply_contracts_or_outbox(tmp_path):
    clock = Clock()
    service = VigilactService(tmp_path / "concurrent.db", clock=clock)
    terms = ContractProposal.model_validate(proposal(clock))
    evidence = CloudEvent.model_validate(event())

    with ThreadPoolExecutor(max_workers=8) as pool:
        created = list(pool.map(lambda _: service.create_contract("node-a", terms), range(24)))
    ids = {item["id"] for item in created}
    assert len(ids) == 1

    with ThreadPoolExecutor(max_workers=8) as pool:
        receipts = list(pool.map(lambda _: service.publish_event("node-a", evidence), range(24)))
    assert sum(r["status"] == "accepted" for r in receipts) == 1
    assert sum(r["status"] == "duplicate" for r in receipts) == 23
    assert sum(len(r["satisfied_contracts"]) for r in receipts) == 1
    assert len(service.read_outbox()["entries"]) == 1
    assert service.get_contract(next(iter(ids)), "node-a")["outcome"] == "SATISFIED"
