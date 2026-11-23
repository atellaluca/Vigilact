# Capability manifests

Capabilities describe **what an agent can offer**. They do not contain executable code, confer permission or guarantee availability.

```http
PUT /v1/agents/me/capabilities
```

```json
{
  "capabilities": [
    {"name": "backup.status", "mode": "query", "invocable": false,
     "description": "Read latest backup status"},
    {"name": "backup.retry", "mode": "command", "invocable": true,
     "description": "Request an agent-side retry"}
  ]
}
```

The manifest is replaced on every PUT, not patched. Names must be unique, start with a lowercase ASCII letter, and contain only lowercase letters, digits, `_`, `-` or `.`. Up to **100** capabilities are accepted. An `invocable: true` capability must use `mode: "command"`.

Read it with:

```http
GET /v1/agents/{agent}/capabilities
```

An agent can inspect its own manifest; operators can read any manifest in this experimental implementation. A `query` capability is currently descriptive only: **there is no remote query execution endpoint**.

Revoking an invocable capability by removing it from the manifest or setting `invocable: false` cancels its **unclaimed** queued commands. Already claimed commands are not automatically cancelled.

Continue to [Command exchange](commands.md) for the separate execution/authorization boundary.
