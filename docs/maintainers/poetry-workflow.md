# Reproducible Python environments with Poetry

Vigilact uses Python 3.11–3.13 and [Poetry](https://python-poetry.org/) **2.5.2**, `poetry-core`, and a single `pyproject.toml` for packaging, development, and docs.

## First-time setup

Install Poetry in an isolated environment (for example with `pipx install poetry==2.5.2`). Then:

```bash
poetry config virtualenvs.in-project true --local
poetry sync --all-groups --all-extras
poetry run python examples/quickstart.py
poetry run pytest -q
poetry build
```

Commit the genuine `poetry.lock` and keep it synchronized with `pyproject.toml`.
Whenever dependencies change (including the docs-only `mkdocs-material` dependency),
run `poetry lock`, review the resulting diff, and commit both files. The CI gate
`poetry check --lock` verifies this consistency before builds and releases.

The Python package installation uses Poetry only as a *build tool*. External consumers can still install a published wheel using normal `pip install vigilact-protocol` without Poetry.

## Groups and extras

- Default: Python server runtime (FastAPI, Pydantic, Uvicorn).
- `client` extra: optional HTTPX SDK dependency.
- `dev` group: pytest, coverage, Ruff, JSON Schema, build checks.
- `docs` group (optional): MkDocs and Material for MkDocs (matching ImportSpy).
- `poetry sync --all-groups --all-extras`: complete contributor environment.
- `poetry sync --only main --extras client`: runtime with optional client dependency.

Go observer remains managed by `go.mod`, because Poetry does not manage Go tooling. CI installs Go separately.

## One release process

```bash
poetry check --lock
poetry run ruff check .
poetry run pytest -q --cov=vigilact --cov-fail-under=90
poetry run python scripts/check_docs.py
poetry run mkdocs build --strict
poetry build
poetry run twine check dist/*
```

The CI workflow enforces the committed lockfile. The provided lock-generation workflow only produces an artifact and does not mutate repository branches or publish distributions.
