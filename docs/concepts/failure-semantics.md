# Failure semantics and recovery

Distributed systems must describe what they **know**, not simply infer that an operation failed. The table below maps fault scenarios to behavior in the current reference implementation.

| Failure scenario | What the observer can conclude | Recovery / caller responsibility |
| --- | --- | --- |
| Agent offline before its deadline | Timely evidence was not received | Keep the contract; evaluate `NOT_OBSERVED` after the deadline |
| Agent completed work but lost connectivity | The observer cannot distinguish it from missing work | If evidence arrives late, preserve the missing-observation outcome |
| Observer restarted while contracts were pending | Persisted contracts remain available | Startup reconciliation checks expired deadlines |
| Observer paused for ten minutes | Timing of result emission may be delayed | Do not interpret `resolved_at` as the instant of an external failure |
| HTTP event response lost after successful commit | Client does not know whether the event was accepted | Retry the **same** event ID and body |
| Two retries reuse one event ID with different data | Payloads conflict | Treat HTTP 409 as an application error; do not overwrite evidence |
| Consumer crashed after causing an external effect, before saving cursor | The effect may happen again | Consumer must make side effects idempotent |
| Command claimed and agent crashed | Execution outcome is unknown | No lease or automatic requeue in the alpha; investigate manually |
| Capability revoked before pending command is claimed | Pending unclaimed command is cancelled | Agent still must enforce a local handler allow-list |
| Clock moves forward/backward | Timing evaluation may become inaccurate | Deploy only with a well-managed clock; no distributed time guarantees |

## Retry semantics

**Event submission:** Retrying the same `(source, id)` with an identical JSON payload is safe at the protocol level. Creating a new ID on each network retry can result in duplicate logical evidence.

**Contracts:** An agent's `client_ref` is scoped to that agent. Repeating equivalent terms returns the same contract; changing terms produces `reference_conflict`.

**Commands:** The Python command extension uses `(operator, request_id)` for
idempotency. Commands have a TTL; claim leases expire into `UNKNOWN`, never
automatic redelivery. This does **not** imply exactly-once remote execution.
See [Safe command lifecycle](../protocol/command-lifecycle.md).

## Independent consumer safety

The outbox is persistent and ordered by increasing `seq`. A consumer asks for entries after a cursor, processes each item, and **only then** advances its cursor. On a crash, an entry can be delivered again. Prefer an idempotency key derived from the outbox sequence or CloudEvent ID when writing external effects.

See [Outbox guide](../guides/outbox.md), [Command exchange](../protocol/commands.md) and [Security](../reference/security.md).
