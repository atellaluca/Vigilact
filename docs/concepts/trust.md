# Identity and trust boundaries

The current reference server authenticates an HTTP principal via two headers:

```http
X-Vigilact-Principal: sample-agent
X-Vigilact-Key: <secret>
```

Keys are configured in `VIGILACT_CREDENTIALS_JSON`. The roles are `agent` and `operator`.

| Operation | Agent | Operator | Anonymous |
| --- | :---: | :---: | :---: |
| `/v1/info`, `/healthz`, `/readyz` | Yes | Yes | Yes |
| Propose contract; submit evidence | Yes | No | No |
| Read own contract | Yes | Yes (global) | No |
| Replace own capabilities | Yes | No | No |
| Read capability manifest | Self only | Yes (global) | No |
| Read observer evaluation outbox | No | Yes | No |
| Queue command, if enabled | No | Yes | No |
| Claim or finish own command, if enabled | Yes | No | No |

## Source attribution

The reference server validates that incoming evidence uses `source: "urn:vigilact:agent:<authenticated-principal>"`. Supplying another principal's source is rejected.

This authenticates the **sender identity**, not the truth of what the sender reports. Real-world attestation, event signatures and trusted third-party evidence are not implemented.

## Capability is not authorization

An agent can advertise `backup.retry`, but that declaration alone **must never cause local execution**. Command requests are disabled by default at the observer, restricted to authenticated operators when enabled, and must be checked and explicitly handled by a local agent allow-list.

## Inherent alpha limitations

- Static API keys without rotation or mTLS/OAuth delegation.
- Operators have broad visibility and command authority rather than per-tenant scopes.
- No rate limiting or quota enforcement; the 256 KiB request limit is only one mitigation.
- No signed evidence or secure remote-agent execution sandbox.

Read [Security and limitations](../reference/security.md) before experimenting outside a local environment.
