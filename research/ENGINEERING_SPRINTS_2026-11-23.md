# Vigilact — Engineering and functional publication sprints

**Date:** 2026-11-23  
**Candidate software release:** `0.3.0a1`  
**Wire protocol:** `vigilact/0.1-experimental`  
**License:** Apache-2.0  
**Publication status:** source archive prepared, GitHub not yet published.

## Sprint 1 — independent observer implementation

**Hypothesis:** the Core expected-event contract is implementable without
importing the Python reference implementation, and works over the same HTTP
interface.

**Implemented:** Go standard-library HTTP observer in
`implementations/go-observer/` with a separately implemented contract store,
source/authentication checks, evidence matching, idempotency, deadline sweeper,
atomic local snapshot persistence and append-only evaluation outbox.

**Verified:** the Go observer compiled, `go vet` passed, Go unit tests passed
with `-race`, and the Python conformance runner passed 11/11 against Go.

**Scope:** only `core.expected_event/0.1`. Capability discovery and command
queues remain optional Python-only experimental features.

## Sprint 2 — durable, black-box parity

**Hypothesis:** two implementations recover correctly after restart and give
consistent outcomes for contracts and late evidence.

**Implemented:** `scripts/test_observers.py` compiles Go, launches real Python
and Go HTTP servers on loopback ports with isolated data files, and applies
identical black-box checks:

1. Protocol discovery.
2. Anonymous access denied.
3. Contract acceptance.
4. Idempotent contract reference.
5. Conflicting contract rejected.
6. Forged evidence source rejected.
7. Evidence satisfies a pending contract.
8. Duplicate event detected.
9. Conflicting duplicate rejected.
10. Outcome is retrievable.
11. Terminal event is in the outbox.
12. Restart recovers an overdue contract.
13. Restart emits exactly one missing-outcome event.
14. Late evidence cannot satisfy the recovered contract.
15. Late evidence cannot duplicate terminal evaluation.

**Verified locally:** Python **15/15**; Go **15/15**. Separate semantic vector
suite also passes **14/14** with the Python engine and independent Go vector
implementation. The two black-box traces are not proofs of trace equivalence
under all inputs.

## Sprint 3 — reproducible release gate and documentation

**Implemented:** profile requirement draft (`spec/CORE_EXPECTED_EVENT.md`),
Go implementation guide, protocol-boundary and publication-gate docs, CI job
for Go race/vet and cross-server HTTP parity, and updated package metadata.
CI workflow action references use full commit pins. The Python and Go
implementations have no mandatory cross-language imports.

**Local results:**

| Check | Result |
|---|---|
| Python tests (CPython 3.13) | 41/41 passed |
| Python coverage | ~95% |
| Go unit tests, race detector | Passed |
| Go statement coverage | ~71% |
| Go `vet` | Passed |
| HTTP observer parity | 15/15 Python; 15/15 Go |
| Python semantic vectors | 14/14 passed |
| Documentation checker | 33 pages; 13 method/path pairs |
| In-process quickstart demo | Passed |
| Python wheel build (no dependency download) | Passed |
| Python sdist | Built; Go sources and `go.mod` included |
| Actual hosted CI / GitHub Pages | Not yet run |
| MkDocs strict, Ruff and Twine locally | Not run; tools unavailable |

## Engineering tradeoffs and release limits

- The Go observer writes full JSON snapshots on every mutation. This is
  deliberately simple for an independent reference, **not scalable or
  multi-process safe**. Both servers are experimental and not internet ready.
- Matching uses observer receipt time, not unverified producer event time.
  A missing result means **no matching evidence observed by the deadline**.
- The Go observer and Python observer share a small Core profile but not
  optional capabilities and commands. A 15-check shared suite is meaningful,
  but not equivalent to exhaustive conformance, security certification, or
  production readiness.
- Static agent keys, no production-grade authorization delegation, no rate
  limits/quotas, no network hardening, no storage retention and no external
  audit remain explicit risks.

## Before a public GitHub release

1. Create `atellaluca/vigilact`, push the source and enable protected `main`.
2. Run **all** hosted CI jobs (Python 3.11–3.13, Go race/vet, protocol parity,
   Ruff, generated artifacts, strict MkDocs, wheel/sdist and Twine).
3. Enable private vulnerability reporting and review the current `SECURITY.md`.
4. Inspect the release archive for sensitive data and check SHA256 sums.
5. Publish a **pre-release** `v0.3.0a1`, not a stable standard.
6. Ask independent developers for design and compatibility feedback, and
   collect usage evidence before claiming wide adoption.

The engineering improvement is evidenced by a second complete **Core** HTTP
implementation plus a shared restart test. It is not a claim that Vigilact
is the universal or definitive operational contract standard.
