# Versions, compatibility and portability

Vigilact has **three distinct identifiers**, and confusing them can cause integration failures.

| Identifier | Current example | Meaning |
| --- | --- | --- |
| Python implementation | `0.4.0a2` | Version of the reference package |
| Protocol discovery | `vigilact/0.1-experimental` | Experimental wire-level behavior reported at `/v1/info` |
| Advertised profile | `core.expected_event/0.1` | Specific feature family supported by the observer |

The `/v1/...` URL prefix is **not a promise of protocol 1.0 stability**. Before stabilization, both shapes and semantics can change. SDKs should check discovery, validate responses, and handle unsupported profiles explicitly.

## Current conformance surface

A candidate observer must match the behaviors covered by its advertised profiles. For the one-shot core this includes contract creation and idempotency, evidence validation, receipt-time deadline behavior, terminal evaluation, and outbox semantics. The independent HTTP smoke runner is useful, but **not a certification**.

```bash
python scripts/conformance_http.py \
  --url http://127.0.0.1:8000 --agent sample-agent --operator sample-ops
```

Set the matching `VIGILACT_CONFORMANCE_AGENT_KEY` and `VIGILACT_CONFORMANCE_OPERATOR_KEY` environment variables first. Only run against an **isolated disposable test database**.

## Portability today

The Python and independent Go HTTP observers implement the same limited
`core.expected_event/0.1` profile. Both pass the shared black-box tests, including
restarts, malformed timestamps, role isolation, deduplication and outbox behavior.
The Go observer **does not** implement commands or capability manifests; neither
server is externally certified, production-hardened or proof of a complete standard.

## Compatibility policy proposal

1. Preserve a clear distinction between package releases and protocol profiles.
2. Add conformance fixtures before considering a profile stable.
3. Document breaking changes in the changelog and migration notes.
4. Never claim support for a feature that is not tested through the public API.
5. Avoid assuming unknown fields can be ignored: current Pydantic request models reject them.

See [the canonical compatibility policy](https://github.com/atellaluca/vigilact/blob/main/spec/COMPATIBILITY.md) and [Conformance](conformance.md).
