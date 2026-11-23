# Security policy and threat model

## Supported versions

No versions are production-supported. Version `0.4.0a1` is an experimental local reference implementation. Earlier alpha builds are not supported.

## Report a vulnerability

Use GitHub's **Report a vulnerability** private advisory feature when available. Otherwise contact the repository maintainer privately through a channel on their GitHub profile. Do not open a public issue with exploit details, secrets or target addresses.

## Trust boundaries

1. API keys identify a single principal and role; no anonymous contract creation is allowed.
2. Agents may only publish evidence using `urn:vigilact:agent:<their principal>`.
3. Event publication does **not** prove the factual truth of the event body; a compromised authorized agent can still lie.
4. An advertised capability is not a privilege. The agent must explicitly mark a command `invocable=true` before a server can queue it.
5. A command queue entry is still **not** an instruction to execute without local checks. Agents must whitelist handlers and validate inputs.
6. Only operators can read the global event outbox and queue commands; a production implementation should further enforce per-tenant scopes.

## Known security gaps (do not expose to untrusted networks)

- Long-lived static API keys in environment variables, without rotation, OAuth2, mTLS, replay nonce or granular per-command authorization.
- A request body size cap exists, but there is no API-side rate limit or per-principal quota; authenticated clients can still exhaust CPU, disk or memory.
- No multi-tenant isolation for operators; operators can observe and command every registered agent.
- No browser-facing authorization model; OpenAPI documentation is public.
- Agent capability schemas and permission grants are not negotiated or versioned.
- Pending commands have no expiry, claimed commands have no lease or retry recovery.
- SQLite is single-instance storage; no HA, clustering or distributed consensus.
- No automatic TLS setup. Always put a hardened TLS-terminating proxy in front of a deployment.
- All timestamps rely on the server's wall clock; operator and agent clock drift are not independently attested.
- No cryptographic event signatures; accepted identity is not proof of real-world execution.

## Before production

Introduce TLS + strong credential lifecycle, scoped authz, payload/rate limits, audit retention/PII policy, durable async workers, tamper-evident evidence or signed attestations when needed, command approval and leasing, and security tests/fuzzing. External review is recommended.

**Never expose the demo keys from the README or examples to the public internet.**

## Alpha hardening added in 0.2.0a1

- Remote command endpoints are **off by default**. The reference server only
  permits them when created with `enable_commands=True` or started with
  `VIGILACT_ENABLE_COMMANDS=true`. This is a risk-bearing, opt-in feature; do
  not enable it for internet-facing installations or untrusted operators.
- HTTP request bodies are limited to **262144 bytes** by default (also for
  streamed bodies lacking Content-Length). Set `VIGILACT_MAX_REQUEST_BYTES`
  only after evaluating denial-of-service impact; it must be at least 1024.
- Validation errors use `application/problem+json` and do not echo the original
  request payload to the client.
- **This does not introduce rate limiting**, quota enforcement, key rotation,
  automatic command redelivery, end-to-end signatures, or production-grade isolation.

- `/healthz` indicates process liveness; `/readyz` tests the availability of the
  SQLite schema. Neither proves that clock accuracy or external connectivity
  are healthy.

## Go reference observer specific risks

The Go observer is single-process only and uses a complete JSON-state snapshot
on every mutation. Do **not** run multiple processes against the same JSON file,
or use it for high-volume monitoring. There is no storage retention, key
rotation, TLS, per-principal quota, or DoS-resilient multi-tenant boundary.
The Go implementation only supports the expected-event Core profile; command
execution is not implemented.
