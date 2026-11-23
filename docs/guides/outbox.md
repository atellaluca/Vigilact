# Consume evaluation events

Vigilact produces **neutral outcome events**. A notification server, monitoring adapter or audit service may consume them, but the observer does not deliver notifications.

## Polling pattern

1. Authenticate as an `operator`.
2. Read `GET /v1/outbox?after=<last-processed-seq>&limit=100`.
3. Process entries in sequence order.
4. **Only after successful processing** persist the last processed `seq`.
5. Retry on error; the consumer must tolerate duplicates.

## Minimal example (development only)

The script below retrieves events but deliberately **does not store a cursor**; it is a read-only inspection example, not a durable adapter.

```python
import os
import httpx

base = os.environ.get("VIGILACT_URL", "http://127.0.0.1:8000")
headers = {
    "X-Vigilact-Principal": os.environ["VIGILACT_OPERATOR"],
    "X-Vigilact-Key": os.environ["VIGILACT_OPERATOR_KEY"],
}

with httpx.Client(timeout=10) as http:
    response = http.get(f"{base}/v1/outbox", params={"after": 0, "limit": 100}, headers=headers)
    response.raise_for_status()
    page = response.json()
    for entry in page["entries"]:
        print(entry["seq"], entry["event"]["type"])
```

For local testing:

```bash
export VIGILACT_OPERATOR=sample-ops
export VIGILACT_OPERATOR_KEY=dev-only-operator-secret-123456789
```

## Production-ready adapters require more

A real consumer needs a durable cursor, idempotent effects, backoff, monitoring, restart recovery and separate secret management. These are responsibilities of the integration, not features already provided by the alpha.

### Why not directly send alerts from Vigilact?

Observation concerns the **truth conditions of a commitment**; delivery concerns recipients and channels. Keeping them separate allows many consumers to reuse the same event without coupling the protocol to one notification product.

See [Evidence and evaluations](../protocol/events.md).
