# JavaScript / Node.js client

The protocol is language-independent. The repository includes a Node.js example that uses **built-in `fetch`** and does not import the Python SDK.

Requirements: **Node.js 20+** and the [local observer](../getting-started/install.md).

## Run the checked-in example

In a terminal configured with the same agent identity as the observer:

```bash
export VIGILACT_AGENT=sample-agent
export VIGILACT_AGENT_KEY=dev-only-agent-secret-123456789
export VIGILACT_URL=http://127.0.0.1:8000
node examples/node_client.mjs
```

The script generates a fresh UTC deadline, submits a one-shot contract, and then submits a matching CloudEvents-style event.

## How it works

```javascript
const base = "http://127.0.0.1:8000";
const principal = "sample-agent";
const key = process.env.VIGILACT_AGENT_KEY;
if (!key) throw new Error("Set VIGILACT_AGENT_KEY");

const response = await fetch(`${base}/v1/info`);
if (!response.ok) throw new Error(`Discovery failed: ${response.status}`);
const server = await response.json();
console.log(server.protocol, server.profiles);
```

For authenticated calls, pass `X-Vigilact-Principal` and `X-Vigilact-Key` headers. Never place an operator secret in client-side browser code. The reference server does not provide browser-oriented session authentication.

**Why this example matters:** it demonstrates that Python implementation internals are not part of the client contract. An independent Go HTTP Core observer now exists; the shared black-box suite verifies its limited profile, not every optional feature.

See the [HTTP API](../protocol/http-api.md) and [event envelope](../protocol/events.md).
