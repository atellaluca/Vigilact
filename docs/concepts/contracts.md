# Contracts and observations

A **contract** is an accepted, stored commitment. An **observation** is the rule used to evaluate evidence submitted against that commitment. A **subject** names the resource or process being observed.

## One-shot proposal

```json
{
  "client_ref": "backup-run-2026-11-22",
  "subject": "backup://node-a",
  "observation": {
    "kind": "expected_event",
    "event_type": "backup.completed",
    "deadline_at": "2030-01-01T02:30:00Z"
  }
}
```

The server accepts the **exact** requested terms or rejects them. Counter-offers, templates, revisions, and multi-party delegation are not part of the current experimental profile.

## Fields and constraints

| Field | Meaning |
| --- | --- |
| `client_ref` | Agent-scoped idempotency identifier; 1–96 characters with an implementation-defined safe-character pattern |
| `subject` | Name of the resource/job; required string, at most 255 characters |
| `observation.kind` | Only `expected_event` is implemented |
| `observation.event_type` | Required matching CloudEvents `type`, at most 200 characters |
| `observation.deadline_at` | Timezone-aware deadline, strictly in the future at acceptance |

## Determining success

A matching event must satisfy **all** of the following:

1. Authenticated evidence owner equals the contract owner.
2. Event `type` equals `observation.event_type`.
3. Event `subject` equals the contract `subject`.
4. Observer **receipt time** occurs on or before the contract deadline.
5. The observation has not already resolved.

If several pending contracts have identical owner, subject and event type, one event can satisfy more than one contract. Use sufficiently distinct subjects or event types when tracking unrelated jobs.

## Boundary semantics

- Evidence received **at exactly** the deadline can satisfy an observation (`received_at <= deadline_at`).
- A pending observation resolves to `NOT_OBSERVED` when the observer's current time becomes **strictly greater** than the deadline.
- Timestamps supplied by agents cannot backdate receipt time.
- Observer downtime can delay evaluation and outbox publication.
- `NOT_OBSERVED` describes the absence of *received evidence*, not necessarily a failed task.

## Idempotency

Within one agent, submitting the same `client_ref` with equivalent terms returns the same contract. Submitting different terms under that reference returns HTTP 409. Event deduplication is a separate mechanism using `(source, id)`.

**To represent a recurring task today**, create a *new one-shot contract with a distinct `client_ref` for each occurrence*. Automatic recurrence is on the roadmap; there is no `cron` field in the current API.

For wire-level requirements, see the canonical [protocol draft](https://github.com/atellaluca/vigilact/blob/main/spec/PROTOCOL.md) and [JSON Schema](https://github.com/atellaluca/vigilact/tree/main/schemas).
