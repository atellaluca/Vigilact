# Five-minute HTTP walkthrough

This walkthrough runs against the **reference HTTP observer**, not against an imaginary service. It creates one synthetic contract, submits matching evidence, verifies its outcome, and reads the neutral evaluation outbox.

!!! warning "Local demonstration only"
    **Local sandbox only.** The reference server is experimental. The commands below use demonstration credentials. Do not expose the instance outside `127.0.0.1`.


## 1. Prepare the environment

From the repository root, create a Python 3.11+ virtual environment and install the developer dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # PowerShell: .venv\Scripts\Activate.ps1
poetry sync --all-groups --all-extras
```

## 2. Start the observer

In terminal A:

```bash
export VIGILACT_CREDENTIALS_JSON='{"sample-agent":{"role":"agent","key":"dev-only-agent-secret-123456789"},"sample-ops":{"role":"operator","key":"dev-only-operator-secret-123456789"}}'
export VIGILACT_DB_PATH=./local-demo.sqlite3
poetry run uvicorn 'vigilact.server:create_app' --factory --host 127.0.0.1 --port 8000
```

Verify its liveness in a different terminal with `curl -fsS http://127.0.0.1:8000/healthz`.

## 3. Execute a real HTTP example

In terminal B, with the same virtual environment:

```bash
export VIGILACT_AGENT=sample-agent
export VIGILACT_AGENT_KEY=dev-only-agent-secret-123456789
export VIGILACT_OPERATOR=sample-ops
export VIGILACT_OPERATOR_KEY=dev-only-operator-secret-123456789
python examples/http_contract_demo.py
```

The example generates unique identifiers and a deadline **five minutes in the future**. It exercises `POST /v1/contracts`, `POST /v1/events`, `GET /v1/contracts/{contract_id}`, and `GET /v1/outbox` over HTTP. You should see an `outcome: SATISFIED` and an event type of `dev.vigilact.observation.satisfied`.

This file is tested by `tests/test_documentation_walkthrough.py`. If the HTTP API changes, the test will fail rather than silently leaving the guide broken.

## 4. Explore the failure path

Read [Your first contract](first-contract.md) to create an observation that deliberately receives no evidence. When its deadline passes, the observer should eventually emit `dev.vigilact.observation.not_observed`.

The absence of an event **does not establish** that a backup or job failed — only that timely evidence was not received. See [Evaluation semantics](../concepts/evaluation-semantics.md).

## Next steps

Try [the Python client](../guides/python.md), inspect [the HTTP API](../protocol/http-api.md), or understand [the failure modes](../concepts/failure-semantics.md). No notification service is required.
