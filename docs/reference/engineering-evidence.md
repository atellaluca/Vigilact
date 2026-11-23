# Reproducible engineering evidence

Vigilact publishes **bounded tests** for the experimental `core.expected_event/0.1` profile. These exercises measure concrete behavior, not universal conformance, security certification, benchmark performance, or production suitability.

## 1. Shared HTTP conformance

The black-box runner launches the Python/FastAPI and independent Go observer using separate persistent stores and checks authentication, proposals, deduplication, recovery after restart, outbox, and late evidence.

```bash
poetry run python scripts/test_observers.py --report artifacts/core-evidence.json
```

The profile has **22 named shared HTTP/recovery assertions per observer** in the current runner. Both implementations are tested through their public HTTP APIs, not through shared code.

## 2. Seeded differential scenarios

```bash
poetry run python scripts/test_observers.py --differential-cases 12 --seed 20261123 \
  --report artifacts/core-evidence.json
```

The generator uses the same seed for both implementations and verifies:

- two authenticated agents can independently commit to the same event type and subject;
- one agent cannot publish evidence as another agent (`403`);
- an agent cannot read another agent's contract (`404`);
- repeating a proposal is idempotent; conflicting evidence IDs return `409`;
- a matching event satisfies only the correct agent's contract;
- **exactly two** terminal outbox evaluations are emitted per two-agent scenario.

A **canonical behavioral trace** removes nondeterministic UUIDs and timestamps. The script compares SHA-256 hashes of the resulting trace. An identical digest is evidence that these specific assertions agree, **not** proof that the entire protocol is equivalent for all possible messages.

The seed, case count, trace and hashes are recorded in the JSON report. The script does not require Go's internal code, Python's server models or the Python SDK.

## 3. Fault injection / atomicity

```bash
poetry run python -m pytest -q tests/test_fault_injection_transactions.py
```

Tests deliberately throw exceptions while the SQLite observer attempts to append terminal events. They assert that the contract resolution, received evidence, and outbox event roll back together. A clean retry then succeeds. Additional seeded tests race evidence ingestion against deadline reconciliation and require exactly **one terminal event** for each contract.

**Scope:** application exception injection only. These tests do not simulate actual disk corruption, power loss, filesystem failure, unreliable networks, Byzantine inputs, or high availability.

## 4. Bounded concurrent smoke

```bash
poetry run python scripts/test_observers.py --load 25 --differential-cases 12 \
  --seed 20261123 --report artifacts/core-evidence.json
```

This adds 25 concurrent contract/event pairs on **each** observer and checks that all 25 terminal evaluation events are present. Per-run timings are provided for diagnostics, not for marketing throughput claims: host load, disk and interpreter matter.

## 5. What we deliberately do not claim

- Only the *one-shot expected-event* Core subset is covered, not cron schedules or multi-party agreements.
- Go does **not** implement the optional Python command/capability endpoints.
- At-rest JSON snapshots in the Go reference are not designed for high-throughput or multiple writer processes.
- These tests do not replace a third-party audit, threat modelling or field experience.
- CI, Code Scanning and GitHub Pages must be verified on the actual public repository before citing them as passing.

See the [Core draft](../concepts/core-profile.md), [threat model](threat-model.md) and [publication gates](publication-gates.md) for full limitations.
