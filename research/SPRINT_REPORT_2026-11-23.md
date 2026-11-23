# Vigilact research and engineering sprints — 2026-11-23

Status: **completed locally; public CI has not run**. Version remains `0.2.0a1`,
protocol remains `vigilact/0.1-experimental`; this work is **unreleased**.

## Sprint 1 — Evidence-based positioning: complete

- Compared scope and prior art: Healthchecks.io, Prometheus, Temporal,
  WS-Agreement, CloudEvents and OpenTelemetry Events.
- Documented differentiation *hypotheses* and concrete areas of overlap.
- Created `research/ECOSYSTEM_2026-11.md` and a proposed adoption experiment.
- Explicitly ruled out replacing metrics, workflow engines, notification
  services or static source analysis.

**Evidence:** links and caveats in the research documents. No community
interviews or market adoption measurements have yet been performed.

## Sprint 2 — Repeatable semantic interoperability slice: complete

- Defined 14 machine-readable expected-event traces and a public JSON Schema.
- Tested each against the **real** Python SQLite-backed reference service.
- Independently implemented a Go standard-library evaluator for the same traces.
- Confirmed both implementations produce identical JSON results locally.
- Added 15 Python regression tests (14 vector cases + schema/integrity check).
- Added a cross-language job to GitHub Actions (not yet run remotely).

**Boundary:** the Go evaluator is **not** a server, does not implement the
HTTP API or durable persistence, and cannot certify complete protocol conformance.

## Sprint 3 — Developer experience and launch credibility: complete

- Added an observe-to-authorized-diagnostic example with fully isolated creds.
- Added a regression test for the demo.
- Added two navigable documentation pages with links validated locally.
- Added an evidence-based launch kit and contributor-focused research plan.
- Verified wheel and source distribution builds via the installed setuptools
  backend, without publishing artifacts to PyPI.

## Verification evidence

| Check | Local result |
| --- | --- |
| Python tests | 41 passed |
| Python coverage | 94.92% (~95%) |
| Python semantic cases | 14 passed |
| Go semantic cases | 14 passed |
| Python/Go generated traces | Identical |
| Documentation source checks | 30 pages, 30 nav items, 13 API methods |
| Demonstration | observe → missed evidence → capability → simulated command succeeded |
| Python builds | Source distribution and wheel built |

## What remains unverified

- CI execution on GitHub runners including Python version matrix and Go 1.24.
- Ruff and the strict MkDocs build (not available in the local environment).
- Independent Go/Rust server implementing the HTTP protocol.
- Crash/restart conformance across independent servers and formal security review.
- Actual GitHub publication, real external integrations and community feedback.

## Next highest-value sprint candidates

1. Implement a **second independent HTTP observer** (Go) for the narrow core.
2. Add crash/restart, cross-owner and outbox cursor HTTP conformance traces.
3. Specify conformance levels clearly: semantic evaluator versus HTTP binding
   versus durable observer.
4. Ask independent developers to build integrations before adding DSL features.
5. Perform a security audit before any public-network deployment.

## Maintenance rule

Avoid increasing the wire format's complexity merely to add features. Each
new normative rule needs a machine-readable positive case, negative case,
versioning note and independent implementation review.
