# HTTP error representation (implementation 0.4.0a1)

The reference observer returns an `application/problem+json` document inspired
by RFC 9457 for validation failures, role/authentication failures, contract
conflicts and body-size rejections. `type: about:blank` is used for these
pre-stabilization errors; clients SHOULD rely on the `status` and stable
implementation-local `error` extension rather than parsing human text.

```json
{
  "type": "about:blank",
  "title": "Protocol error",
  "status": 409,
  "detail": "client_ref already exists with different terms",
  "error": "reference_conflict"
}
```

Currently used error identifiers include `reference_conflict`, `deadline_elapsed`,
`source_mismatch`, `event_conflict`, `request_conflict`,
`capability_unavailable`, `commands_disabled`, `payload_too_large`,
`validation_error` and `http_error`. Additional identifiers are not frozen.
Request validation responses intentionally do not echo raw untrusted input.

This is not a complete formal registry; future revisions will stabilize the
error `type` identifiers and response model as part of protocol conformance.
