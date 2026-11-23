# First contract — end to end

In this guide an agent declares that a matching `backup.completed` event must be **received** before a future deadline.

Start the local observer using the [installation guide](install.md). In a second terminal, set the agent credentials used there:

```bash
export VIGILACT_AGENT=sample-agent
export VIGILACT_AGENT_KEY=dev-only-agent-secret-123456789
```

## 1. Propose an observable commitment

Use Python to calculate a fresh UTC deadline. This avoids hard-coded past dates in copyable examples:

```bash
export VIGILACT_DEADLINE="$(python -c 'from datetime import datetime,timezone,timedelta; print((datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat())')"
export VIGILACT_REF="backup-$(python -c 'import uuid;print(uuid.uuid4())')"
```

```bash
curl -fsS -X POST http://127.0.0.1:8000/v1/contracts \
  -H "X-Vigilact-Principal: $VIGILACT_AGENT" \
  -H "X-Vigilact-Key: $VIGILACT_AGENT_KEY" \
  -H 'Content-Type: application/json' \
  -d "{\"client_ref\":\"$VIGILACT_REF\",\"subject\":\"backup://my-laptop\",\"observation\":{\"kind\":\"expected_event\",\"event_type\":\"backup.completed\",\"deadline_at\":\"$VIGILACT_DEADLINE\"}}"
```

A successful response has HTTP **201**, a generated contract `id`, `state: "ACTIVE"`, and `outcome: "PENDING"`. Save that `id` if you want to query the contract later.

## 2. Submit evidence

```bash
export VIGILACT_EVENT_ID="$(python -c 'import uuid;print(uuid.uuid4())')"
curl -fsS -X POST http://127.0.0.1:8000/v1/events \
  -H "X-Vigilact-Principal: $VIGILACT_AGENT" \
  -H "X-Vigilact-Key: $VIGILACT_AGENT_KEY" \
  -H 'Content-Type: application/json' \
  -d "{\"specversion\":\"1.0\",\"id\":\"$VIGILACT_EVENT_ID\",\"source\":\"urn:vigilact:agent:$VIGILACT_AGENT\",\"type\":\"backup.completed\",\"subject\":\"backup://my-laptop\",\"data\":{\"duration_seconds\":27}}"
```

The event receipt has `status: "accepted"` and `satisfied_contracts`, listing contracts matched and satisfied by this event. Publishing **the same event ID and exact payload** again yields `status: "duplicate"`; reusing that ID with a different payload is a conflict.

## 3. Read the evaluation outbox

```bash
curl -fsS 'http://127.0.0.1:8000/v1/outbox?after=0&limit=20' \
  -H 'X-Vigilact-Principal: sample-ops' \
  -H 'X-Vigilact-Key: dev-only-operator-secret-123456789'
```

Look for the event type `dev.vigilact.observation.satisfied`.

## What happens if no evidence arrives?

Create a new contract with a short **future** deadline, do not send its event, and let the observer reconcile the missed deadline. A background sweep normally runs every 5 seconds. The outcome becomes `NOT_OBSERVED` and an evaluation event is appended to the outbox. This means *no timely evidence was received*, **not** that the underlying backup definitely failed.

## What this example deliberately avoids

- Recurrence/cron scheduling: create another contract for another occurrence.
- Remote command execution: [command exchange](../protocol/commands.md) is opt-in and separate.
- Notification delivery: consumers read the outbox and decide how to react.

Next: [Contracts and observations](../concepts/contracts.md).
