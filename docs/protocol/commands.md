# Remote command exchange

<div class="vigilact-note"><strong>Off by default.</strong> Remote command endpoints must be explicitly enabled by the observer and must not be exposed to untrusted operators or public networks in this alpha.</div>

Commands are **requests delivered to an agent**; the server never runs arbitrary shell commands. The agent decides whether and how to execute a locally allow-listed handler.

## Local development opt-in

```bash
export VIGILACT_ENABLE_COMMANDS=true
# Restart the local uvicorn process after changing the environment.
```

You still need the operator role, an advertised agent capability with `mode: "command"` and `invocable: true`, and a local allow-list.

## Wire workflow

1. The agent `PUT`s its manifest to `/v1/agents/me/capabilities`.
2. An operator `POST`s a request to `/v1/commands`:

   ```json
   {
     "request_id": "manual-retry-001",
     "target_agent": "sample-agent",
     "capability": "backup.retry",
     "arguments": {"job": "nightly"}
   }
   ```

3. The agent polls `GET /v1/agents/me/commands`.
4. The agent `POST`s `/v1/agents/me/commands/{command_id}/claim` to atomically claim one request.
5. Only after validating the name, arguments and local policy, the agent executes its allow-listed handler.
6. The agent posts `/v1/agents/me/commands/{command_id}/result`:

   ```json
   {"status": "succeeded", "output": {"attempted": true}}
   ```

## Lifecycle and failure model

The Python extension now supports server-controlled command expiry and claim
leases. Unclaimed work expires; claimed work whose lease lapses becomes
`UNKNOWN` and is **never** automatically requeued. An agent may provide a late
result for an unknown command. See [Safe command lifecycle](command-lifecycle.md)
for the state diagram, migration rules and security limitations.

## Security rules for agents

- Never map capability names to arbitrary subprocess/shell commands.
- Allow-list explicit handler names.
- Validate each argument against local constraints.
- Check the agent's current authorization before execution.
- Treat duplicates and unknown outcomes as potentially unsafe.

Read [Identity and trust](../concepts/trust.md) and [Security limitations](../reference/security.md) first.
