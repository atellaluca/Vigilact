# Security and limitations

<div class="vigilact-note"><strong>Research implementation only.</strong> No release is production-supported. Do not expose the observer to the public Internet or use it for controlling important systems without substantial independent security engineering.</div>

## Current protections

- Explicit credentials required at startup; no built-in default credentials.
- Authenticated `agent` and `operator` roles for non-public endpoints.
- Agent-owned event `source` binding and agent-scoped contract ownership.
- Commands disabled by default (`VIGILACT_ENABLE_COMMANDS=false`).
- 256 KiB default HTTP body limit, including streaming requests.
- Generic validation errors that avoid echoing untrusted request content.
- Parameter validation with Pydantic models.

## Known gaps

| Risk area | Current limitation |
| --- | --- |
| Authentication | Static keys without rotation, replay protection or federated identities |
| Authorization | Operators are globally privileged; no tenant scoping or policy engine |
| Resource protection | No rate limits, per-principal quota or durable abuse prevention |
| Network | No automatic TLS/mTLS provisioning |
| Evidence authenticity | Agent identity is authenticated, but evidence is not signed or independently attested |
| Commands | TTL and indeterminate claim leases; no execution sandbox, delegated ACL or exactly-once guarantee |
| Persistence | Single-node SQLite without HA, encrypted persistence or cross-node consensus |
| Time | Deadlines rely on the server's wall clock |
| Browser clients | No safe public-browser session authentication design |

## Responsible disclosure

Use the GitHub repository's **Report a vulnerability** mechanism (private security advisory), if enabled. Do not report exploit payloads, keys or affected hosts in a public issue. The source repository has a full [SECURITY.md policy](https://github.com/atellaluca/vigilact/blob/main/SECURITY.md).

## Safety principle

`Capability != authorization`. An agent-advertised command is still only metadata. An agent **must** allow-list local handlers and validate arguments; never execute a command based solely on a server-supplied capability string.

This docs site does not authorize any deployment beyond local development.


For a structured account of attack surfaces and mitigations, see the [security threat model](threat-model.md).
