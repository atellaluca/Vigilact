# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Backup helper must be safe for an open reference database."""
import importlib.util
from contextlib import closing
import sqlite3
from pathlib import Path

import pytest
from conftest import headers, proposal, Clock, KEYS
from fastapi.testclient import TestClient
from vigilact.server import create_app


def backup_function():
    module_file = Path(__file__).resolve().parents[1] / "scripts/backup_sqlite.py"
    spec = importlib.util.spec_from_file_location("vigilact_backup", module_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.backup


def test_database_backup_restore_does_not_copy_inconsistent_state(tmp_path):
    database = tmp_path / "running.db"
    target = tmp_path / "backup.db"
    clock = Clock()
    with TestClient(create_app(database, credentials=KEYS, clock=clock, sweep_seconds=0)) as api:
        contract = api.post("/v1/contracts", json=proposal(clock), headers=headers()).json()
        backup_function()(database, target)
    with closing(sqlite3.connect(target)) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with TestClient(create_app(target, credentials=KEYS, clock=clock, sweep_seconds=0)) as api:
        got = api.get("/v1/contracts/" + contract["id"], headers=headers())
        assert got.status_code == 200 and got.json()["outcome"] == "PENDING"


def test_backup_refuses_to_overwrite(tmp_path):
    original = tmp_path / "original.db"
    with closing(sqlite3.connect(original)) as db:
        db.execute("CREATE TABLE sample (x INTEGER)")
    output = tmp_path / "exists.db"
    output.write_text("never overwrite")
    with pytest.raises(ValueError, match="new file"):
        backup_function()(original, output)
    assert output.read_text() == "never overwrite"
    with pytest.raises(ValueError, match="new file"):
        backup_function()(original, original)
