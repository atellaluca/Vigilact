#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Create a consistent SQLite backup without copying a live database file.

This operational helper is deliberately separate from the protocol specification.
Usage: python scripts/backup_sqlite.py --db vigilact.sqlite3 --output backup.sqlite3
"""
from __future__ import annotations

import argparse
from contextlib import closing
import os
import sqlite3
from pathlib import Path


def backup(source: Path, output: Path) -> None:
    source, output = source.resolve(), output.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Source database does not exist: {source}")
    if source == output or output.exists():
        raise ValueError("Destination must be a new file distinct from the source")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with closing(sqlite3.connect(f"file:{source}?mode=ro", uri=True)) as original:
            with closing(sqlite3.connect(output)) as destination:
                original.backup(destination)
                result = destination.execute("PRAGMA integrity_check").fetchone()[0]
                if result != "ok":
                    raise RuntimeError(f"Backup integrity check failed: {result}")
        os.chmod(output, 0o600)
    except BaseException:
        output.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True, help="Existing SQLite database")
    parser.add_argument("--output", type=Path, required=True, help="New backup file (must not exist)")
    args = parser.parse_args()
    backup(args.db, args.output)
    print(f"Consistent SQLite backup written to: {args.output}")


if __name__ == "__main__":
    main()
