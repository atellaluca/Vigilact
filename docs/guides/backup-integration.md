# Integration pattern: a scheduled backup

This guide explains how to apply the current **one-shot** protocol to backup software, job schedulers or CI tasks. Vigilact is not the scheduler: it watches for evidence from an execution initiated elsewhere.

## A minimal workflow

1. Before an individual backup run, the agent proposes a contract with a **future** UTC deadline.
2. It uses an occurrence-specific `client_ref` and `subject`, for example `backup://node-a/2026-11-23`.
3. The job executes using its own scheduler and software.
4. When the run finishes, the integration submits evidence with the same `subject` and the agreed event type (`backup.completed`).
5. Vigilact emits either a satisfaction or a missing-observation event. A separate consumer decides whether to notify anyone.

## Design the identity carefully

Use a stable, authenticated agent identity such as `backup-node-a`. The emitted CloudEvents `source` is then `urn:vigilact:agent:backup-node-a`, and the *same agent identity* must have proposed the contract. The server currently rejects evidence claiming another agent's source.

Example **proposal shape**, with a deadline you must compute freshly:

```json
{
  "client_ref": "backup-node-a-2026-11-23",
  "subject": "backup://node-a/2026-11-23",
  "observation": {
    "kind": "expected_event",
    "event_type": "backup.completed",
    "deadline_at": "2026-11-23T02:30:00Z"
  }
}
```

Example evidence, sent before that deadline:

```json
{
  "specversion": "1.0",
  "id": "node-a-backup-2026-11-23",
  "source": "urn:vigilact:agent:backup-node-a",
  "type": "backup.completed",
  "subject": "backup://node-a/2026-11-23",
  "data": {"result": "completed", "duration_seconds": 74}
}
```

These payloads are **illustrative historical values**, not copy-and-paste commands for today's date. For a fully runnable example with a dynamically computed deadline use [the HTTP walkthrough](../getting-started/five-minute-demo.md).

## Frequent mistakes

| Mistake | Consequence | Preferred approach |
| --- | --- | --- |
| Reuse the same subject for multiple overlapping jobs | One event can satisfy several contracts | Include a run identifier in the subject |
| Treat no evidence as proof of backup failure | Incorrect operational inference | Report "completion not observed by deadline" |
| Schedule using naive timestamps | Rejected timezone validation | Use aware RFC 3339 timestamps, ideally UTC |
| Retry with new event IDs | Duplicate logical messages | Persist one stable ID per run |
| Assume Vigilact delivers messages | No email or push will be sent | Subscribe an external consumer to the evaluation outbox |

## What about recurring schedules?

Automatic cron or interval recurrence is **not implemented** in this release. The integration should propose one contract per run. This limits the number of unknowns while the core protocol is being validated.

Next: [Outbox consumer](outbox.md) or [Evaluation semantics](../concepts/evaluation-semantics.md).
