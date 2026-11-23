# Evaluation semantics and time boundaries

This page describes the **implemented** `core.expected_event/0.1` profile. It is a precise description of the Python reference server, not a stabilized cross-vendor standard.

## Contract and outcome are different dimensions

All currently accepted contracts have `state: ACTIVE`. Their observation progresses from `PENDING` to one of two terminal outcomes: `SATISFIED` or `NOT_OBSERVED`.

```text
                 successful matching evidence before deadline
 PENDING ----------------------------------------------------------> SATISFIED
    |
    | server time strictly greater than deadline;
    | no qualifying evidence received
    +-------------------------------------------------------------> NOT_OBSERVED
```

In the current alpha, resolved outcomes are not reopened. Contract cancellation, suspension, revision, and recurrent windows are **not implemented**. Do not assume `NOT_OBSERVED` means the underlying job definitively failed.

## What counts as a matching event?

A new event must have exactly the same authenticated agent, `subject`, and `type` as the pending contract. The observer's **receipt time** must be on or before the accepted deadline. An optional agent-supplied `time` cannot backdate arrival.

| Situation | Outcome / observable effect |
| --- | --- |
| Matching event received before the deadline | Contract becomes `SATISFIED` |
| Matching event received at the deadline | Contract can become `SATISFIED` (`<=`) |
| No matching event and observer time passes deadline | Contract becomes `NOT_OBSERVED` (`>`) |
| Event received after the deadline | No retroactive satisfaction; `NOT_OBSERVED` is preserved |
| Event has wrong subject, event type, or owner | Does not satisfy that contract |
| Repeated event with identical `(source, id)` and payload | Receipt has `status: duplicate`; no new evaluation |
| Same `(source, id)` with changed contents | HTTP 409, `event_conflict` |

In the reference server, a synchronous evidence submission evaluates overdue contracts before inserting the new event. A periodic sweep evaluates outstanding deadlines; it can be delayed by downtime and scheduling latency.

## A concrete example

Suppose an accepted contract requires `backup.completed` for `backup://server-a` by `12:30:00Z`:

- At `12:29:59Z`, matching evidence is accepted and the outcome becomes `SATISFIED`.
- At exactly `12:30:00Z`, it is still eligible.
- At `12:30:01Z`, a newly received event cannot satisfy the original contract.
- If the server was offline until `12:40Z`, it may record the missing-observation outcome at startup; that timestamp represents the **evaluation**, not the exact instant the backup failed.

## Multiple contracts

One matching evidence message can satisfy multiple pending contracts of the same owner, subject and event type. For distinct job occurrences, use distinct subjects or type values and a unique `client_ref` per accepted contract.

## What is not guaranteed

There is no synchronized distributed clock, event-time watermarking, proof of event authenticity, or exactly-once delivery to outbox consumers. The reference server uses a wall clock and durable SQLite transactions; any external side effects require downstream idempotency.

Related: [Failure semantics](failure-semantics.md), [Evidence events](../protocol/events.md), [Conformance](../reference/conformance.md).
