# Errors and retry policy

The reference server uses `application/problem+json` for many HTTP failures. This is an **experimental implementation convention**, not a finalized error registry. Clients should inspect status codes and the `error` extension instead of parsing human-readable `detail` strings.

```json
{
  "type": "about:blank",
  "title": "Protocol error",
  "status": 409,
  "detail": "client_ref already exists with different terms",
  "error": "reference_conflict"
}
```

## Error catalog

| HTTP | `error` field | Likely cause | Suggested client action |
| --- | --- | --- | --- |
| 401 | `http_error` | Missing or invalid identity/key | Fix credentials; do not retry unchanged |
| 403 | `http_error` | Role or resource access denied | Request correct authorization |
| 403 | `source_mismatch` | CloudEvent `source` does not match agent | Fix the `source` field |
| 403 | `commands_disabled` | Server command feature is disabled | Do not assume remote commands are available |
| 404 | `not_found` | Contract or command not visible/found | Check ID and access scope |
| 409 | `reference_conflict` | Reused contract `client_ref` with different terms | Use an occurrence-specific reference |
| 409 | `event_conflict` | Same `(source, id)`, changed payload | Reuse the original payload or a genuinely new event ID |
| 409 | `request_conflict` | Reused operator command request ID with different arguments | Resolve the request ID collision |
| 409 | `not_pending`, `not_claimed`, `result_conflict` | Command state no longer permits transition | Inspect the command lifecycle; do not blindly repeat side effects |
| 422 | `validation_error` | Invalid field shape, value or timestamp | Correct the JSON and retry |
| 422 | `deadline_elapsed` | Contract deadline already passed at acceptance | Propose a new future deadline |
| 422 | `capability_unavailable` | Target command is not currently invocable | Check manifest and local policy |
| 413 | `payload_too_large` | Body exceeds configured limit | Reduce payload size |

Other error identifiers may be introduced without notice during the alpha. Consult [HTTP API](../protocol/http-api.md), [Command exchange](../protocol/commands.md), and the canonical [`spec/ERRORS.md`](https://github.com/atellaluca/vigilact/blob/main/spec/ERRORS.md).

## Retry guidance

- **Network timeout or transient transport failure:** repeat an *identical* idempotent request, with exponential backoff and a bounded retry budget.
- **HTTP 409:** treat as a conflict, not a transient outage.
- **HTTP 401/403/422:** generally correct the caller configuration or request rather than retrying unchanged.
- **Claimed commands:** do not automatically retry an unknown execution outcome; a lapsed claim lease becomes `UNKNOWN` and is never automatically requeued.

Authentication headers carry secrets. Do not include their values in telemetry, screenshots, error reports or logs.
