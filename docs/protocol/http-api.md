# HTTP API reference

The reference observer exposes an experimental **HTTP/JSON binding**. Most methods require `X-Vigilact-Principal` and `X-Vigilact-Key`. The `/v1` prefix is a route family, **not** a stable v1 protocol guarantee.

## Discovery and health

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/healthz` | Public | Process liveness |
| `GET` | `/readyz` | Public | SQLite storage readiness |
| `GET` | `/v1/info` | Public | Implementation, protocol and enabled profiles |

The discovery response advertises protocol `vigilact/0.1-experimental`, profiles and `features.remote_commands`. Check it before relying on optional functionality.

## Contracts and evidence

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| `POST` | `/v1/contracts` | Agent | Submit an exact-term contract proposal; success: 201 |
| `GET` | `/v1/contracts/{contract_id}` | Owner agent / operator | Read state and outcome |
| `POST` | `/v1/events` | Agent | Submit CloudEvents-style evidence |
| `GET` | `/v1/outbox` | Operator | Paginate ordered evaluation events |

`GET /v1/outbox` accepts `after` (non-negative sequence cursor, default 0) and `limit` (1–500, default 100). On response, consume `entries` and persist `next_cursor` **only after** the corresponding work has succeeded.

## Capability and command endpoints

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| `PUT` | `/v1/agents/me/capabilities` | Agent | Replace own capability manifest |
| `GET` | `/v1/agents/{agent}/capabilities` | Same agent / operator | Read manifest |
| `POST` | `/v1/commands` | Operator | Queue request (opt-in feature) |
| `GET` | `/v1/commands/{command_id}` | Requesting operator | Inspect command state, expiry and result (opt-in) |
| `GET` | `/v1/agents/me/commands` | Agent | Poll pending requests (opt-in) |
| `POST` | `/v1/agents/me/commands/{command_id}/claim` | Target agent | Claim request (opt-in) |
| `POST` | `/v1/agents/me/commands/{command_id}/result` | Target agent | Report result (opt-in) |

Command endpoints are **disabled by default**; all return `403 commands_disabled` while disabled. Enabling this experimental feature does not make it safe for untrusted users or public networks.

## Request and response formats

- Every mutation is JSON with `Content-Type: application/json`.
- The default maximum HTTP body size is **262144 bytes**.
- Invalid JSON shapes return `422` with a generic `application/problem+json` body.
- Authentication failures produce `401`, incorrect roles `403`, conflicts such as repeated identifiers with altered content `409`, and over-limit bodies `413`.
- Problem responses include the non-stable `error` extension, for example `reference_conflict`, `source_mismatch` or `commands_disabled`.

```json
{
  "type": "about:blank",
  "title": "Protocol error",
  "status": 409,
  "detail": "client_ref already exists with different terms",
  "error": "reference_conflict"
}
```

The full OpenAPI contract is committed at [`api/openapi.json`](https://github.com/atellaluca/vigilact/blob/main/api/openapi.json), or read it from `GET /openapi.json` on a running reference server. Generated JSON Schemas live under [`schemas/`](https://github.com/atellaluca/vigilact/tree/main/schemas).

Command request bodies may include `ttl_seconds` (1–86400, default 300). The claim response supplies `lease_expires_at`; the server never retries an uncertain command automatically. See [Safe command lifecycle](command-lifecycle.md).
