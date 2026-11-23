# Vigilact Go Observer — independent Core implementation

**Experimental `core.expected_event/0.1` only.** A separate HTTP observer
written with the Go standard library. It has no Python dependencies or
imports from the Python Vigilact server. It stores local JSON snapshots
with atomic replacement and validates the shared HTTP behavior using the
black-box conformance runner.

## Start locally

Requires Go 1.23+. Do **not** expose this server to public networks.

```bash
export VIGILACT_CREDENTIALS_JSON='{"agent1":{"role":"agent","key":"replace-with-unique-long-local-secret-1"},"ops":{"role":"operator","key":"replace-with-unique-long-local-secret-2"}}'
cd implementations/go-observer
go run . --addr 127.0.0.1:18949 --db ./vigilact-go-state.json
```

```bash
curl http://127.0.0.1:18949/v1/info
```

## Engineering scope

Implemented: authenticated proposal, idempotent contract identity, restricted
CloudEvents JSON, source identity checks, duplicate event rejection, terminal
outcome processing, durable outbox, automatic reconciliation at startup and
every 250 ms, health/readiness. `go test -race ./...` tests concurrent event
retries, access control, exact deadline and persistence after restart.

Not implemented: agent capability endpoints, remote commands, cron/recurring
observations, SQLite/Postgres, clustering, file lock between two processes,
compaction/retention, rate limiting, key rotation, TLS termination, signed
evidence or high-availability. **The JSON snapshot model is O(total history)
in memory and per mutation** and should not be used for large event volumes.
The same state file MUST NOT be opened by multiple observer processes.

The Go observer is a proof of *Core profile implementability*, not a drop-in
replacement for the optional Python server features.
