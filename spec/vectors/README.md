# Expected-event semantic vectors (experimental profile 0.1)

`expected-event-vectors.schema.json` under `schemas/` is the JSON Schema for the fixture format.

`expected-event.json` contains deterministic behavioral cases for a *single*
one-shot expected-event contract. The base time is fixed so results can be
reproduced without depending on actual wall-clock time.

The vectors exercise:

- arrival before, at and after the deadline (strict `>` boundary);
- no evidence and unresolved observations;
- wrong owner, subject, type and source;
- event deduplication and conflicting IDs;
- observer receipt time versus the event's claimed timestamp;
- single emission per contract after resolution.

The outcomes and receipts are part of this **experimental** fixture format.
They are not yet an official certification suite. The fixture uses relative
seconds and intentionally excludes networking, persistence, authentication
handshakes, complex contracts, multi-observer consensus and race conditions.

Run against the actual SQLite reference engine:

```bash
PYTHONPATH=src python scripts/expected_event_vectors.py --check
```

Run the independently written Go evaluator (standard library only):

```bash
go run ./implementations/go-vector-evaluator/main.go --check
```

The two tools can also output JSON without `--check`. They must produce
identical traces. This verifies the **semantic slice**, not protocol-wide
interoperability or production readiness.
