# Architecture

Vigilact is designed around **observable semantics** rather than an opinionated deployment topology. The Python server is a demonstration of the protocol, not its only permitted implementation.

```text
+-------------------+              +-------------------------------+
| Agent             |              | Observer                      |
|                   |  proposal -->| Contract registry             |
| Event producer    |  evidence -->| Evidence ingestion           |
| Capability owner  |  manifest -->| Capability registry          |
+-------------------+              | Observation evaluator         |
         ^                         | Durable evaluation outbox     |
         | commands (poll)         | Optional command queue        |
         +-------------------------+-------------------------------+
                                               |
                                               | neutral evaluation events
                                               v
                                 +-------------------------------+
                                 | Consumer: monitoring, audit,  |
                                 | tickets, notification service |
                                 +-------------------------------+
```

## Responsibility boundaries

| Actor / service | Owns | Does *not* promise |
| --- | --- | --- |
| Agent | Proposals, evidence, capability manifest | That all reports are true just because they are signed in |
| Observer | Accepted terms, receipt timestamps, deterministic outcomes, outbox | That an absent event proves a real-world failure |
| Operator | Authorized reads and optional command requests | Unrestricted authority to execute on agent machines |
| External consumer | Interpretation/delivery of evaluation events | To change prior observation history |

## Why contracts persist without connections

The observer stores the accepted contract, then evaluates evidence independently of whether the agent stays connected. The **reference implementation** uses SQLite transactions, a periodic sweeper and a durable outbox. A restart triggers reconciliation of outstanding deadlines.

### Current evaluation model

- `PENDING` → `SATISFIED` when matching evidence arrives in time.
- `PENDING` → `NOT_OBSERVED` after the deadline passes without qualifying evidence.
- A later event never rewrites a resolved outcome.

`state: ACTIVE` is a **different field** from the observation outcome; the current implementation does not support revocation, expiry or negotiation revisions.

## Separation from notifications

The observer emits `dev.vigilact.observation.*` events. A downstream integration may deliver email or push notifications, open an incident, or feed a report. Vigilact does not ship a notification transport or mandate LTG Notify.

## Explicit limits of this alpha

One agent owns the contract and produces evidence. Generalized agreements involving independent proposers, third-party evidence issuers, federated observers or multiple subjects are future design work. See [Compatibility and conformance](../reference/conformance.md) for what can actually be relied on.
