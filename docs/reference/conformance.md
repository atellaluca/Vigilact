# Compatibility and conformance

**Implementation and protocol versions are different.** The Python package is `0.4.0a2`, while the wire protocol advertises `vigilact/0.1-experimental`.

`/v1` is a URL prefix, not a finalized stable-v1 contract. Pre-1.0 releases may intentionally change shapes and semantics. Always inspect `GET /v1/info`.

## Current profiles

| Advertised profile | Meaning |
| --- | --- |
| `core.expected_event/0.1` | One-shot receipt-time commitments |
| `agent.capabilities/0.1` | Replace/read capability manifests |
| `agent.commands/0.1` | Command exchange, only when enabled by the observer |

Unknown JSON fields are rejected by the reference models. An SDK does not determine what is normative: the protocol draft plus observable wire behavior define the experimental contract.

## Run local checks

```bash
poetry run python -m pytest -q
poetry run python examples/quickstart.py
poetry run python scripts/export_specs.py
```

For an independent **HTTP smoke** check against a disposable local server:

```bash
export VIGILACT_CONFORMANCE_AGENT_KEY='dev-only-agent-secret-123456789'
export VIGILACT_CONFORMANCE_OPERATOR_KEY='dev-only-operator-secret-123456789'
python scripts/conformance_http.py \
  --url http://127.0.0.1:8000 \
  --agent sample-agent --operator sample-ops
```

The smoke runner creates synthetic data. **Do not run it against a production database.** Passing it demonstrates basic discovery, authentication, idempotency, evidence handling and outbox behavior; it is not certification or a complete interoperability proof.

## What would justify a stabilized release?

- A clear normative specification of state transitions and failure semantics.
- Expanded conformance beyond the current negative, idempotency, restart and temporal smoke cases.
- An independent Go HTTP Core observer now passes the same bounded black-box suite; broader validation and independent external review remain open.
- Compatibility, security, and operational review with third-party feedback.

Canonical source documents: [Protocol](https://github.com/atellaluca/vigilact/blob/main/spec/PROTOCOL.md), [Conformance](https://github.com/atellaluca/vigilact/blob/main/spec/CONFORMANCE.md), [Compatibility](https://github.com/atellaluca/vigilact/blob/main/spec/COMPATIBILITY.md).
