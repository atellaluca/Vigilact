# Core expected-event observer profile — experimental 0.1

**Status: implementation-aligned draft, not a ratified or production standard.**

The requirements below define the common **observed behavior** of the Python and
Go reference observers. The key words **MUST**, **MUST NOT**, **SHOULD**, and **MAY**
are normative within this experimental profile, following RFC 2119/RFC 8174.
These rules do **not** define the internal storage technology, scheduler, SDK,
or notification channel.

## Scope

This profile supports: authenticated agent principals; one-shot expected-event
contract proposals; same-principal evidence; server-receipt-time evaluation;
read-only outcome retrieval; and an operator-readable, append-only evaluation
outbox. One accepted contract resolves to exactly one of `SATISFIED` or
`NOT_OBSERVED` (unless it is still `PENDING`).

Non-goals: cron schedules, metric thresholds, multi-party contracts, signed
attestations, broker delivery, exactly-once execution, notifications,
remote commands, or arbitrary expressions. Optional agent capabilities and
commands are implemented in Python but **not part of this Core profile**.

## Contract acceptance

- A proposal contains `client_ref`, `subject`, `observation.kind` =
  `expected_event`, `observation.event_type`, and a timezone-aware
  `observation.deadline_at`.
- A server MUST reject a deadline not later than its current clock at initial
  acceptance (HTTP 422). A retry of a previously accepted identical proposal
  MUST return the original contract, even if its deadline has passed.
- `(principal, client_ref)` is the idempotency identity. A different proposal
  using the same pair MUST return HTTP 409 and MUST NOT silently modify a
  previously accepted contract.
- Contracts MUST be accepted and recorded durably before HTTP 201 is returned.
  After an ordinary server restart, accepted contracts MUST remain accessible.

## Evidence

- Agent authentication MUST be enforced. The restricted event JSON shape MUST
  include CloudEvents 1.0 `id`, `source`, `type`, and `subject`.
- The authenticated source for agent `name` is
  `urn:vigilact:agent:name`. A different `source` MUST be rejected.
- `(source, id)` identifies an evidence event. A repeated identical event MUST
  return `duplicate`, MUST NOT satisfy a second contract, and MUST NOT produce
  a second evaluation event. A conflicting body for that identity MUST
  return HTTP 409.
- Matching is based on principal, `subject`, `type`, accepted observation and
  server **receipt time**. The event's optional `time` is retained as evidence
  metadata but MUST NOT move the receipt-time evaluation boundary.

## Temporal semantics

- If server receipt time is **equal to** `deadline_at`, matching evidence MAY
  satisfy a `PENDING` contract. At any time strictly **later** than deadline,
  the server MUST resolve an unresolved contract to `NOT_OBSERVED` before
  considering new evidence.
- A `NOT_OBSERVED` result means a matching event was **not accepted in time**;
  it is not proof the underlying operation failed.
- The result of a resolved contract MUST NOT be overwritten by late evidence.
- An observer MUST reconcile overdue persisted contracts after startup and
  during normal operation. Timeliness of actual wake-up is **not** guaranteed
  while the observer is down or its wall clock is wrong.
- Reference implementations normalize timestamps to UTC with microsecond
  precision. This experimental precision rule requires further cross-language
  work before stabilization.

## Evaluation and outbox

- Transition to a terminal outcome and append of its corresponding evaluation
  event MUST be atomic at the observer's persistence boundary.
- The observer MUST append exactly one `dev.vigilact.observation.satisfied`
  or `dev.vigilact.observation.not_observed` event for the terminal resolution.
- The outbox cursor MUST advance monotonically and permit replay of events by
  authenticated operators. **Delivery to downstream consumers is not covered.**
- Consumers SHOULD checkpoint `next_cursor` only after handling the entries.
  This produces at-least-once consumption, not exactly-once side effects.

## Failure and compatibility policy

- An observer MUST NOT claim production readiness or full Vigilact conformance
  solely because it passes the present Core HTTP checks.
- A reference implementation MAY use file-backed SQLite or an atomic local
  JSON snapshot; internal storage is not a protocol requirement.
- The profile identifier is `core.expected_event/0.1`; discovery is available
  via `GET /v1/info`. Clients SHOULD inspect the declared profiles before
  invoking optional features.
- Error bodies use `application/problem+json` with an experimental `error`
  extension following the Problem Details model of RFC 9457. The complete
  error registry is not yet stable.

## Evidence for implementation parity

Run `python scripts/test_observers.py` to build the Go server and execute the
**same black-box HTTP suite** against the Python server and the Go server,
including restart recovery and late evidence. Run `pytest` and `go test -race`
for implementation-specific checks. The direct semantic vectors in
`spec/vectors/expected-event.json` provide additional deterministic boundary
cases, but no current test proves all possible execution traces equivalent.

## External specifications

- CloudEvents specification: https://github.com/cloudevents/spec
- RFC 9457 Problem Details: https://www.rfc-editor.org/rfc/rfc9457
- RFC 2119 / RFC 8174 requirement vocabulary.
