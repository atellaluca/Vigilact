# Vigilact — Engineering evidence sprints (23 November 2026)

**Version:** 0.4.0a2 | **Protocol:** `vigilact/0.1-experimental` (unchanged)

## Sprint A — deterministic differential tests

Added `scripts/differential_core.py`. It uses only HTTP and `httpx` to exercise the independent observers. It creates two agent identities with the same subject and event type, verifies impersonation rejection, idempotency, tenant visibility and exactly two terminal events for each scenario. The runner computes a SHA-256 digest of the **normalized** outcomes, excluding generated UUIDs and wall clock timestamps.

**Local result:** 12 scenarios per server; 73 recorded behavioral assertions per implementation; the same digest in both:

`782b74896fc3a16e0c180bab12dcf932ef39d1a426efb4dfe55f4e53fac1468c`

The digest measures selected behaviors only. It is not a formal equivalence or cryptographic attestation of the implementations.

## Sprint B — transaction failure injection

Added `tests/test_fault_injection_transactions.py`:

- injected outbox failure causes the event, contract outcome and outbox to roll back together;
- injected failure during a batch sweep rolls back all affected contracts, followed by a successful retry and restart;
- four fixed seeds test concurrent receipt-vs-sweep interleavings without duplicate terminal events.

**Local result:** 6 new tests passed.

**Exclusions:** no power failure, filesystem corruption or network partition simulation.

## Sprint C — auditable publication evidence

The release runner produces `--report artifacts/core-evidence.json` and a fail-closed Markdown summary via `scripts/render_evidence.py`. CI will upload both as build artifacts after the hosted job actually passes.

**Local result:** 62/62 Python tests passed; ~95% Python coverage, 22/22 Core HTTP/restart checks for each server, 14/14 golden vectors on each language, and Go unit tests with race detector. Each server completed a bounded 25 contract/event-pair concurrent load smoke. Docs checker: 40 pages and 14 HTTP operations.

**Not verified locally:** hosted GitHub Actions, full Ruff/Twine/MkDocs strict pipeline, real internet deployment, third-party audit or production load.

## Sprint D — developer-oriented communication

Added `outreach/` drafts for LinkedIn, the personal website and Python communities in English and Italian. Drafts deliberately leave the GitHub/docs URLs unpublished until the maintainer has enabled and checked them.

## Reproduction

```bash
python -m pip install -e '.[dev]'
python -m pytest -q --cov=vigilact --cov-report=term-missing
(cd implementations/go-observer && go test -race ./... && go vet ./...)
python scripts/expected_event_vectors.py --check
go run ./implementations/go-vector-evaluator/main.go --check
python scripts/test_observers.py --load 25 --differential-cases 12 --seed 20261123 \
  --report artifacts/core-evidence.json
python scripts/render_evidence.py artifacts/core-evidence.json --output artifacts/CORE_PROOF.md
python scripts/check_docs.py
python scripts/check_pages_config.py
```

## Next maturity gates

1. Verify every GitHub CI job against the pushed repository and preserve a passing run URL.
2. Have an independent contributor reproduce the test using a fresh checkout and report discrepancies.
3. Test process-kill and disk-full fault modes before claiming durable crash consistency.
4. Specify stronger identity/permission boundaries, retention and quota behavior before exposing reference implementations to untrusted networks.
5. Invite review of protocol semantics and prior art, especially receipt-time deadlines, explicit negotiation and contract revision.
