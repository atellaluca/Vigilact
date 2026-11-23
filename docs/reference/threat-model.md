# Security threat model — public alpha

This is a **maintainer-authored threat analysis**, not an independent security
audit. The reference services should not be exposed directly to the public
internet. Use network isolation and TLS at an authenticated reverse proxy when
experimenting outside localhost.

| Asset | Threat | Current mitigation | Residual risk |
| --- | --- | --- | --- |
| Agent identities | Stolen/replayed static API keys | Explicit keys, constant-time comparison | No key rotation, expiry, OAuth, or mTLS |
| Contracts | Cross-agent disclosure or modification | Owner-scoped lookups and server-assigned owners | Operators may see all contracts; no tenancy model |
| Evidence | Spoofed event origin | Source must match authenticated agent | Agents can lie; no cryptographic content attestation |
| Deadline decisions | Clock manipulation or outage | Server-side receive time; persistent state; restart reconciliation | No trusted time/HA/monotonic cross-node consensus |
| Outbox | Duplicate/omitted consumption | Durable ordered cursor | Unbounded storage; consumer retries required |
| Commands | Unsafe execution or retry | Off by default, explicit invocability, TTL/lease, never auto-retry | Agent must sandbox/allow-list; results can be forged by compromised agent |
| HTTP ingress | Oversized payload / malformed JSON | Body limits, strict models, schema validation | No per-client quota or distributed rate limiting |
| Go JSON state | Disk corruption or multi-process writes | Atomic single-process snapshot, restrictive file mode | Not designed for HA or concurrent writers |
| CI/website | Supply-chain abuse | Minimal workflows/permissions, release checks | Maintainers must verify GitHub Actions and package provenance |

## Trust boundaries

1. A claimed event is **evidence from an authenticated agent**, not independent
   proof that a real-world action happened.
2. The observer may evaluate a missed deadline, but cannot distinguish failed
   operations from network partition, failed agent delivery, or inaccurate clocks.
3. The outbound event consumer is a separate integration and must handle
   duplicates, outages, and authorization independently.
4. Remotely invoked actions are **never sandboxed by Vigilact**; agent-side
   dispatch policies are mandatory. Disabling commands avoids that attack surface.

## Security verification checklist

- [x] JSON body bound to 256 KiB by default (reference Python and Go implementations).
- [x] Source/owner isolation and replay/conflict regressions.
- [x] Command expiry and uncertain outcomes without automatic retry (Python extension).
- [x] Cross-language Core conformance tests.
- [ ] Independent security review and dependency vulnerability analysis.
- [ ] Rate limiting, delegated scopes, secret rotation, mTLS/OIDC and tenancy isolation.
- [ ] Production HA, tamper-evident audit trail and tested retention policy.

Report suspected vulnerabilities according to [`SECURITY.md`](https://github.com/atellaluca/vigilact/blob/main/SECURITY.md).
