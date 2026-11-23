# Draft GitHub pre-release notes — Vigilact v0.4.0a1

**Experimental software. Do not deploy publicly or use for critical systems.**

Vigilact is a vendor-neutral experiment for **operational commitments**: an
agent proposes what evidence should arrive by a deadline; an observer records
outcomes and emits neutral events for downstream systems.

## Highlights

- Independent Python and Go HTTP Core observers for `core.expected_event/0.1`.
- The same black-box checks run against both observers: authentication, temporal
  validation, idempotency, persistence, restart, and outbox behavior.
- Stronger timestamp validation, no-backdating semantics and no lost evaluation
  events in a bounded 4-worker synthetic load smoke.
- Python-only, opt-in command exchange now offers TTL, claim-state uncertainty,
  and operator result inspection **without retrying ambiguous commands**.
- SQLite online backup helper and regression test.
- MkDocs site configured for `https://vigilact.atellaluca.com/` using GitHub
  Actions; publication requires DNS and repository owner setup.

## What this release is not

No ratified standard, production-grade HA, external security audit, general
contract/DSL engine, orchestration platform, or remotely trusted action system.
The wire protocol is still `vigilact/0.1-experimental`; breaking changes are
possible before stable 1.0.

## Get started

```bash
python -m pip install -e '.[dev]'
python examples/quickstart.py
python scripts/test_observers.py --load 25
```

Read `docs/index.md`, `docs/concepts/core-profile.md`, `SECURITY.md` and
`OPEN_SOURCE_READINESS.md`. Contributions and counterexamples welcome!
