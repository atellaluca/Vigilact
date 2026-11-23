# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
# Requires Poetry 2.5.x and a committed poetry.lock.
.PHONY: install lock check-lock test coverage lint demo specs build docs-install docs-check docs-build docs-serve observers proof backup

install:
	poetry sync --all-groups --all-extras

lock:
	poetry lock

check-lock:
	poetry check --lock

test:
	poetry run python -m pytest -q

coverage:
	poetry run python -m pytest -q --cov=vigilact --cov-report=term-missing --cov-fail-under=90

lint:
	poetry run ruff check .

demo:
	poetry run python examples/quickstart.py

specs:
	poetry run python scripts/export_specs.py

build: check-lock
	poetry build
	poetry run twine check dist/*

docs-install:
	poetry sync --all-groups --all-extras

docs-check:
	poetry run python scripts/check_docs.py
	poetry run python scripts/check_pages_config.py
	poetry run python scripts/check_branding.py

docs-build: docs-check
	poetry run mkdocs build --strict

docs-serve:
	poetry run mkdocs serve

observers:
	poetry run python scripts/test_observers.py --load 25

proof:
	poetry run python -m pytest -q
	poetry run python scripts/test_observers.py --load 25 --differential-cases 12 --seed 20261123 --report artifacts/core-evidence.json
	poetry run python scripts/render_evidence.py artifacts/core-evidence.json --output artifacts/CORE_PROOF.md

# Usage: make backup DATABASE=vigilact.sqlite3 BACKUP=vigilact-backup.sqlite3
backup:
	poetry run python scripts/backup_sqlite.py --db $(DATABASE) --output $(BACKUP)
