# Python SDK

The optional `VigilactClient` is a small synchronous HTTP wrapper implemented using `httpx`. The SDK is **not** required to implement the protocol: a compatible client can use ordinary JSON HTTP requests.

## Install

From the repository:

```bash
poetry sync --all-groups --all-extras
```

For local development and running tests use `'.[dev]'` instead.

## Propose and satisfy a one-shot contract

Start the local observer according to [Install and run](../getting-started/install.md). Then:

```python
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from vigilact.client import VigilactClient

with VigilactClient(
    "http://127.0.0.1:8000",
    principal="sample-agent",
    key="dev-only-agent-secret-123456789",
) as agent:
    run_id = str(uuid4())
    subject = f"backup://demo/{run_id}"
    deadline = datetime.now(timezone.utc) + timedelta(minutes=5)

    contract = agent.propose(
        client_ref=run_id,
        subject=subject,
        event_type="backup.completed",
        deadline_at=deadline,
    )
    print("Contract:", contract["id"])

    receipt = agent.event(
        subject=subject,
        event_type="backup.completed",
        event_id=run_id,
        data={"duration_seconds": 42},
    )
    print("Evidence status:", receipt["status"])
```

Expected: a new contract and evidence receipt with `status: accepted`, normally including that contract ID in `satisfied_contracts`.

## Additional agent methods

| Method | Role |
| --- | --- |
| `propose(...)` | Create/retrieve an accepted one-shot contract |
| `event(...)` | Publish CloudEvents-style evidence |
| `publish_capabilities([...])` | Replace the agent capability manifest |
| `pending_commands()` | Poll commands if the observer explicitly enabled them |
| `claim_command(id)` | Claim a pending command |
| `finish_command(id, success, output)` | Resolve a claimed command |

The client raises `httpx.HTTPStatusError` on non-success responses. It has a 10-second request timeout and no automatic retry policy. Apply your own bounded retry strategy with stable idempotency keys; don't blindly repeat non-idempotent commands.

Use TLS, secret management and scoped authorization in any non-local experiment. The reference implementation is [not ready for production](../reference/security.md).

For reproducible tests without HTTP sockets, start with `examples/quickstart.py` in the repository.
