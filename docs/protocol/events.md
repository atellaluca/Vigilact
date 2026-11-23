# Evidence and evaluation events

Evidence arrives as a **restricted CloudEvents 1.0 JSON envelope**. It is not full CloudEvents compatibility: arbitrary extension attributes, binary payloads, and `data_base64` are currently unsupported.

## Submit evidence

```json
{
  "specversion": "1.0",
  "id": "run-2026-11-22-a",
  "source": "urn:vigilact:agent:sample-agent",
  "type": "backup.completed",
  "subject": "backup://my-laptop",
  "datacontenttype": "application/json",
  "data": {"duration_seconds": 27}
}
```

The `source` must correspond to the agent identity used to authenticate the request. Evidence is evaluated using **server receipt time**, not the optional CloudEvents `time` field.

## Event deduplication

The tuple `(source, id)` identifies an evidence message:

- First submission: `status: "accepted"`.
- Identical retry: `status: "duplicate"`.
- Same tuple with different contents: `409 event_conflict`.

Use stable identifiers when retrying a failed HTTP call. Do **not** generate a different event ID for each retry of the same logical message.

## Evaluation events

The observer appends exactly one logical evaluation entry for each resolved contract to a durable outbox:

| Event type | Meaning |
| --- | --- |
| `dev.vigilact.observation.satisfied` | Matching evidence was received in time |
| `dev.vigilact.observation.not_observed` | Matching evidence was not received by the deadline |

Evaluation events are useful for notifications, tickets, reporting and audit trails, but Vigilact does not perform those actions directly.

## Delivery model

Consumers **poll** the ordered outbox and persist the sequence cursor *after* processing entries successfully. The model allows at-least-once consumption: duplicates can occur after a consumer crash. Consumers must implement their own idempotency.

See [Consume the outbox](../guides/outbox.md) for a working integration pattern and [contract semantics](../concepts/contracts.md) for receipt-time rules.
