# Vigilact: ecosystem and positioning review

**Research date:** 2026-11-23  
**Status:** source-backed competitive mapping, NOT user demand validation  
**Scope:** distinguish a narrow experimental protocol from established products and specifications.

## Core research question

Is there room for a transport-neutral, versioned agreement in which one system
commits to provide observable evidence and another independently evaluates its
arrival, with separately discoverable and authorized capabilities?

**Preliminary answer:** technically plausible, but adoption remains unproven.
Vigilact's novelty cannot be defined as merely checking missed jobs, collecting
alerts, or defining SLAs: those capabilities already exist.

## Nearest alternatives

| System | What it already does | Implication for Vigilact |
| --- | --- | --- |
| [Healthchecks.io](https://healthchecks.io/docs/) | Watches periodic jobs and missed pings; alerts when expected check-ins do not arrive. | A missing-backup demo is not a sufficient differentiation claim. |
| [Prometheus alerting](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/) | Evaluates metric expressions and emits alerts to receivers. | Avoid inventing another metric query language or Alertmanager. |
| [Temporal](https://docs.temporal.io/durable-execution) | Durable workflow execution, timers and recovery. | Vigilact observes *external* commitments; it does not run the workflow. |
| [WS-Agreement (OGF)](https://interoperable-europe.ec.europa.eu/collection/ict-standards-procurement/solution/gfd-r192-web-services-agreement-specification-ws-agreement) | Machine-readable agreements, lifecycle and monitoring. | Contract negotiation and monitoring are prior art, not unique inventions. |
| [CloudEvents](https://github.com/cloudevents/spec) | Portable event envelope (stable JSON format v1.0.2 at time of review). | Reuse CloudEvents where possible; current implementation only supports a subset. |
| [OpenTelemetry Events](https://opentelemetry.io/docs/specs/semconv/general/events/) | Shared semantic conventions for structured event records. | Complement telemetry pipelines rather than replace them. |

## Specific, falsifiable positioning

Vigilact aims to enable a consumer to declare an expected operational observation,
have an observer accept and persist those exact terms, and evaluate bounded
evidence without requiring an always-online client. Separately, an agent can
advertise capabilities without implicitly authorizing their invocation.

This is **not** yet a general-purpose SLA engine, a normative industry standard,
a multi-agent contract protocol, or a production-ready remote-management system.

## Important limitation

The current alpha supports only *one-shot expected-event* contracts between
an authenticated agent and observer. A correct demo is not proof of ecosystem
adoption. The Go semantic evaluator checks selected decision rules independently;
it is **not** a complete second server, API implementation or a persistence test.

## Decisions for the next technical phase

1. Prioritize tests of invariants and observable semantics above DSL breadth.
2. Give contributors tiny executable examples and vendor-neutral test vectors.
3. Keep notification routing, static code analysis and dynamic plugin loaders out of core.
4. Do not call an experiment "universal", "certified", or "production-ready".
5. Invite external use cases before expanding roles, recurring schedules and federation.

## How to falsify the value proposition

Test with three unrelated applications: a backup agent, a periodic data pipeline,
and a device health monitor. Measure the number of lines of glue code and
conceptual changes needed to reuse a contract across independent observers.
If custom adapters or domain exceptions dominate, reduce scope or reconsider the
protocol approach. Public stars alone are weak evidence; prioritize actual
independent integrations and bugs filed by external developers.
