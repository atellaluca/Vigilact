# Cross-language semantic vectors

Vigilact's expected-event profile is defined by observable semantics, not by
Python classes. To catch mismatches between implementations, we maintain
public data-only vectors in `spec/vectors/expected-event.json`.

## Run the checks

From the repository root:

```bash
PYTHONPATH=src python scripts/expected_event_vectors.py --check
go run ./implementations/go-vector-evaluator/main.go --check
```

Both runners test the same cases. The Python runner uses the **real SQLite-backed
reference service**; the Go runner independently models this limited state
machine using only the Go standard library. The GitHub CI compares their JSON
traces as well as each expected result.

## Covered cases

Deadline boundary, early and late evidence, missing events, agent isolation,
wrong subject/type, conflicting event IDs, replay of identical evidence, and
claims about event time that differ from observer receipt time.

## Not covered

The Go runner is **not** a second server. This suite does not verify HTTP,
storage durability, asynchronous scheduling, multi-process concurrency, security
properties or production correctness. See [Conformance](conformance.md),
[Evaluation semantics](../concepts/evaluation-semantics.md), and
[Failure semantics](../concepts/failure-semantics.md).
