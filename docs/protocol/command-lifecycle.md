# Safe command lifecycle (Python reference)

Vigilact's optional `agent.commands/0.1` experimental profile is **not remote
code execution**. The server queues named capabilities; the agent must implement
its own explicit allow-list, argument validation and authorization. The feature
is disabled by default (`VIGILACT_ENABLE_COMMANDS=false`). It is **not part of
the Go observer Core profile**.

## Lifecycle

```text
                       claim                         result
PENDING --------------------------------> CLAIMED -------------> SUCCEEDED / FAILED
  |                                          |
  | expiration                               | 120s lease elapsed
  v                                          v
EXPIRED                                    UNKNOWN
  |                                          |
  | no retry                                 | late original-agent result
  v                                          v
terminal                                SUCCEEDED / FAILED

PENDING --> CANCELLED (invocable capability removed)
```

- An operator queues a `request_id`, `capability`, arguments and optional `ttl_seconds` (default 300, range 1–86400).
- `expires_at` is calculated by the server; after it passes, **unclaimed** work becomes `EXPIRED` and cannot be claimed.
- When the target agent claims a command, `lease_expires_at` becomes 120 seconds after the claim. This **does not authorize re-dispatch**.
- If no result is received before the lease ends, the server records `UNKNOWN` (execution may have happened). The command is never automatically requeued.
- The original authenticated agent may later report a definitive result, including from `UNKNOWN`; repeated identical reports are idempotent, conflicting results are rejected.
- Startup reconciliation and each command API access update elapsed states. No automatic command repetition is performed.

## Why UNKNOWN instead of a retry?

After a network interruption an operation can have completed even if its
acknowledgement was lost. Blindly retrying e.g. a device restart or database
mutation could create duplicate side effects. Applications that need retry must
supply their own *idempotent* handlers and operation identifiers.

## Example

```json
{
  "request_id": "diagnostic-2026-11-23-001",
  "target_agent": "backup-node",
  "capability": "backup.inspect",
  "arguments": {"job": "daily"},
  "ttl_seconds": 180
}
```

The response contains `expires_at` and `lease_expires_at` (null until claimed).
A `CLAIMED` command is not proof of execution, and `SUCCEEDED` is the agent's
reported outcome, not independent verification by the observer.

## Security and migration notes

- The server cannot prove that the reported agent result is truthful.
- Keep the command feature off when you only need observation.
- Reference databases from earlier alphas can be upgraded in place. Previously
  unclaimed or claimed commands with no recorded lifetime become expired/unknown,
  respectively, rather than being executed after an unsafe migration.
- Back up SQLite before upgrading and test on a copy first.

See [Commands](commands.md), [Security](../reference/security.md) and
[Failure semantics](../concepts/failure-semantics.md).
