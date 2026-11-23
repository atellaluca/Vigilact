# Install and run

This guide uses the **reference implementation** in the repository. It is intended for local development only.

## Requirements

- Python **3.11–3.13** and [Poetry 2.5.2](https://python-poetry.org/).
- Git to clone the source, if the repository has been published.
- No Redis, message broker or external database is required; the reference server uses SQLite.

## Set up the workspace

```bash
# Once the repository is published:
git clone https://github.com/atellaluca/vigilact.git
cd vigilact
# On an existing repository use the committed poetry.lock.
poetry sync --all-groups --all-extras
```

Poetry creates and manages the virtual environment automatically. See the [Poetry workflow](../maintainers/poetry-workflow.md).

> If you're using the downloaded repository archive, extract it, open the extracted project root, and omit the `git clone` step.

## Run the deterministic quickstart

```bash
poetry run python examples/quickstart.py
poetry run python -m pytest -q
```

This runs without network sockets and uses a disposable database. The demonstration includes successful and missed observations, capability advertisement and a locally authorized command. It does not enable commands on a public HTTP server.

## Start an HTTP observer

For local use only, create **two different credentials** (one agent and one operator). The values below are illustrative and must not be used outside an isolated development machine.

```bash
export VIGILACT_CREDENTIALS_JSON='{"sample-agent":{"role":"agent","key":"dev-only-agent-secret-123456789"},"sample-ops":{"role":"operator","key":"dev-only-operator-secret-123456789"}}'
export VIGILACT_DB_PATH=./local-observer.sqlite3
poetry run uvicorn 'vigilact.server:create_app' --factory --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/readyz
curl -fsS http://127.0.0.1:8000/v1/info
```

The interactive FastAPI API explorer is available at `http://127.0.0.1:8000/docs`; the machine-readable specification is at `/openapi.json`. **Both are part of the running server**, not this static documentation site.

!!! warning "Experimental server"
    The HTTP server is an alpha research implementation. Keep it bound to loopback; do not expose it to an untrusted network or use the example credentials for real data.


## Next step

Try [the five-minute HTTP walkthrough](five-minute-demo.md), complete [your first contract](first-contract.md) and explore the [Python SDK](../guides/python.md).
