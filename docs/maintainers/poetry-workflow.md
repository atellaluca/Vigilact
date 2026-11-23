# Reproducible Python environments with Poetry

Vigilact uses Python 3.11–3.13 and [Poetry](https://python-poetry.org/) **2.5.2**, `poetry-core`, and a single `pyproject.toml` for packaging, development, and docs.

## First-time setup

Install Poetry in an isolated environment (for example with `pipx install poetry==2.5.2`). Then:

```bash
poetry config virtualenvs.in-project true --local
poetry lock             # first time only; requires access to PyPI
poetry sync --all-groups --all-extras
poetry run python examples/quickstart.py
poetry run pytest -q
poetry build
```

**Lockfile status:** this migration was made in an offline environment without Poetry or PyPI access. The included `pyproject.toml` is authoritative, but a genuine `poetry.lock` could **not** be generated or verified here. Commit an actual `poetry.lock` from `poetry lock` **before** calling the project fully reproducible or cutting a PyPI release. Do not commit an invented or manually edited lockfile.

A GitHub Actions workflow named **Generate Poetry lock** can create a fresh lockfile as a downloadable artifact. Add it to the repository and re-run CI. Once committed, `poetry check --lock` validates metadata/lock consistency, and `poetry sync` will use locked versions.

The Python package installation uses Poetry only as a *build tool*. External consumers can still install a published wheel using normal `pip install vigilact-protocol` without Poetry.

## Groups and extras

- Default: Python server runtime (FastAPI, Pydantic, Uvicorn).
- `client` extra: optional HTTPX SDK dependency.
- `dev` group: pytest, coverage, Ruff, JSON Schema, build checks.
- `docs` group (optional): MkDocs.
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
