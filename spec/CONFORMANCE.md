# Conformance — experimental v0.1 profile

## Current status

This repository contains **reference implementation tests**, not yet a vendor-neutral certification suite. Two independently implemented HTTP Core observers (Python and Go) pass the same bounded regression suite. No claim of universal interoperability is made.

## Candidate conformance requirements

1. Reject a proposal whose deadline is not in the future, while accepting a bytewise equivalent normalized repeat for an existing `client_ref`.
2. Bind contract ownership to an authenticated agent, never a client-controlled field.
3. Distinguish `PENDING`, `SATISFIED` and `NOT_OBSERVED` without retroactively rewriting outcomes.
4. Evaluate the receipt-time boundary precisely (`received_at <= deadline_at` passes).
5. Treat absent evidence as `NOT_OBSERVED`, not proof of the underlying operation's failure.
6. Deduplicate events by `(source,id)` and reject conflicting reuse.
7. Prevent an unauthorized agent from satisfying another agent's contract.
8. Emit exactly one logical evaluation outbox entry per resolved contract.
9. Require explicit agent opt-in and operator role before queueing a command.
10. Restrict command claim and result submission to its target agent; reject conflicting resolutions.
11. Recover accepted contracts and pending evaluations after restart.
12. Disclose supported features and protocol version in `/v1/info`.

## How to run

```bash
poetry sync --all-groups --all-extras
pytest -q
poetry run python examples/quickstart.py
```

The suite is **not** exhaustive (e.g., disk faults, clock steps, malicious payload fuzzing, mixed-version interoperability and external security review). Two Core servers pass the shared subset, but neither is a certified implementation.

## Independent HTTP smoke runner (0.4.0a1)

Prefer environment variables for secrets to avoid revealing keys in process
arguments. Set `VIGILACT_CONFORMANCE_AGENT_KEY` and, optionally,
`VIGILACT_CONFORMANCE_OPERATOR_KEY`, then run:

```bash
python scripts/conformance_http.py --url http://127.0.0.1:8000 \
  --agent my-test-agent --operator my-test-operator
```

The operator argument is optional if no operator key is supplied. The runner
can target any observer implementing the experimental HTTP binding. The runner
uses **only httpx and wire-format requests**; it does not import Vigilact's
Python SDK, DTO models or server code.

The runner tests protocol discovery, unauthorized requests, proposal acceptance,
reference idempotence, conflict rejection, source authorization, evidence
acceptance, event deduplication, persisted outcomes, and optionally evaluation
outbox publication. It generates unique synthetic identifiers and short-lived
contracts; it will leave those synthetic records in the test server. Use an
isolated test instance, not a production database.

Passing this smoke run proves basic API behavior, **not full conformance**.
Timeout, missing-event, command, concurrency, multi-process and cross-language
semantics need richer test vectors and independent implementations.


## Golden semantic vectors (experimental)

A new fixture collection under `spec/vectors/expected-event.json` defines
14 reproducible examples for the one-shot expected-event decision rules.
`python scripts/expected_event_vectors.py --check` exercises the persisted
Python service. `go run ./implementations/go-vector-evaluator/main.go --check`
uses an independent Go state evaluator. Both emit the same traces and are
verified in CI. This proves only the selected semantic slice; the Go program
is **not** a second protocol server and cannot certify full interoperability.

## Independent Core HTTP parity and bounded concurrency

Run `poetry run python scripts/test_observers.py --load 25` with installed development
dependencies and Go. The script builds and starts both independent observers,
executes the same 22 black-box checks per server and, optionally, 25 synthetic
concurrent contract/event transactions per server. The test verifies that
every successful observation emits exactly one event in the outbox; recorded
timings are only local, environment-specific smoke measurements.

The `agent.commands/0.1` Python extension is **not part of Core conformance**.
Its optional TTL and claim-state behavior is separately regression-tested.
