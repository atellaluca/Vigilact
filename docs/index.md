# Vigilact

**An open protocol experiment for negotiated operational contracts and observable commitments.**

Vigilact lets an agent propose what evidence should arrive before a deadline. An observer accepts supported terms, persists the agreement and publishes a neutral outcome that other software can consume.

```text
Agent                     Observer                     Downstream systems
  |                          |                                |
  |-- propose contract ----->|                                |
  |<------ accepted ---------|                                |
  |-- publish evidence ----->|                                |
  |                    evaluate obligation                    |
  |                          |-- outcome event -------------->|
```

!!! warning "Experimental alpha — 0.4.0a3"
    Vigilact advertises the `vigilact/0.1-experimental` protocol profile. It is neither a ratified standard nor a production-hardened observer. APIs and semantics may change; do not expose the reference server to untrusted networks.

## Get started

- [Install and run](getting-started/install.md), then follow the [five-minute HTTP demo](getting-started/five-minute-demo.md).
- [Build an integration](guides/backup-integration.md) with the [Python SDK](guides/python.md) or [JavaScript client](guides/javascript.md).
- [Review the protocol](concepts/evaluation-semantics.md), including [failure semantics](concepts/failure-semantics.md) and [conformance](reference/conformance.md).

## What Vigilact observes

| Phase | Responsibility |
| --- | --- |
| Contract | An authenticated agent proposes an `expected_event` commitment and deadline. |
| Acceptance | The observer validates and persists supported terms or rejects them. |
| Evidence | The agent publishes a restricted CloudEvents-style event. |
| Evaluation | The observer records `SATISFIED` or `NOT_OBSERVED` according to receipt time. |
| Integration | A downstream consumer decides whether to notify, audit, or automate. |

An observation marked `NOT_OBSERVED` means **no matching evidence was received by its deadline**. It does *not* prove the operation itself failed. See [Failure semantics](concepts/failure-semantics.md).

## Architecture

![An agent proposes a contract and publishes evidence; an observer records evaluations for independent downstream consumers.](assets/architecture.svg)

## Implemented versus planned

| Included now | Not yet implemented |
| --- | --- |
| One-shot `expected_event` contracts | Cron and recurring observations |
| Receipt-time deadlines and SQLite state | High availability and federation |
| Event idempotency and durable outbox | Full CloudEvents compatibility |
| Agent capability manifests | Capability schemas and negotiation |
| Commands with TTL and uncertain outcomes (disabled by default) | Exactly-once remote execution guarantees |

## Read next

- [Core protocol profile](concepts/core-profile.md) · [HTTP API](protocol/http-api.md) · [Error catalog](reference/error-catalog.md)
- [Security and limitations](reference/security.md) · [Compatibility](reference/compatibility.md) · [Engineering evidence](reference/engineering-evidence.md)
- [Project and maintainer](project-and-maintainer.md) · [Contributing](reference/contributing.md)

Vigilact **is not a notification product**. It emits independent evaluation events and has no required dependency on LTG Notify or any other delivery service.

## Maintained by

Vigilact is an independent Apache-2.0 project maintained by **Luca Atella**. Find technical background and contact details at [profile.atellaluca.com](https://profile.atellaluca.com/), [GitHub](https://github.com/atellaluca), [LinkedIn](https://www.linkedin.com/in/luca-atella/) or [info@atellaluca.com](mailto:info@atellaluca.com).
