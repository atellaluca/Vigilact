# Reference server configuration

The reference implementation reads these environment variables on startup. Use them only in a trusted local environment while the implementation is experimental.

| Variable | Default | Behavior |
| --- | --- | --- |
| `VIGILACT_CREDENTIALS_JSON` | **Required** | JSON mapping principal names to `{ "role": "agent" \| "operator", "key": "..." }` |
| `VIGILACT_DB_PATH` | `./vigilact.sqlite3` | SQLite persistence file |
| `VIGILACT_SWEEP_SECONDS` | `5` | Seconds between deadline evaluation passes; `0` disables periodic evaluation (startup reconciliation still happens) |
| `VIGILACT_ENABLE_COMMANDS` | `false` | Set `true`/`1` to activate command endpoints; dangerous on untrusted networks |
| `VIGILACT_MAX_REQUEST_BYTES` | `262144` | Maximum HTTP request body; must be at least 1024 bytes |

## Authentication setup

```bash
export VIGILACT_CREDENTIALS_JSON='{"sample-agent":{"role":"agent","key":"dev-only-agent-secret-123456789"},"sample-ops":{"role":"operator","key":"dev-only-operator-secret-123456789"}}'
```

**Use separate, strong secrets for each principal.** Keys must be at least 16 characters. The current server has no key-rotation or delegated authorization workflow.

## Startup

```bash
export VIGILACT_DB_PATH=./local-observer.sqlite3
poetry run uvicorn 'vigilact.server:create_app' --factory --host 127.0.0.1 --port 8000
```

## Operational endpoints

`GET /healthz` checks process liveness; `GET /readyz` verifies SQLite schema accessibility. These do not test time synchronization, agent reachability, queue drain or end-to-end delivery.

The server retries overdue evaluations after startup and every sweep interval. System time steps and downtime can affect when a result is recorded. The SQLite reference server is **single instance**, without high availability.

## What cannot be configured yet

- Per-tenant authorization, per-capability ACLs or OAuth/mTLS authentication.
- Automatic retries and exactly-once remote execution (the Python extension supports TTL and claim leases).
- Multi-observer federation.
- Built-in email/push delivery.

See [Safe command lifecycle](../protocol/command-lifecycle.md) and [Security and limitations](security.md) for risks and [Troubleshooting](troubleshooting.md) for common errors.
