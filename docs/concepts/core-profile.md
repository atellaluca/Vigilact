# Core profile and normative behavior

The engineering requirements for the shared expected-event profile are
maintained in the repository as
[CORE_EXPECTED_EVENT.md](https://github.com/atellaluca/vigilact/blob/main/spec/CORE_EXPECTED_EVENT.md).

The profile covers **one-shot, evidence-based operational commitments**:

1. An authenticated agent proposes a unique, future-deadline contract.
2. An observer persists and accepts it.
3. The same agent submits a matching CloudEvents-style evidence event.
4. The observer records `SATISFIED` if the matching event was received on time,
   otherwise `NOT_OBSERVED` after the deadline.
5. Exactly one evaluation event is appended for that terminal outcome.

A missing event is not proof of application failure. The event's producer time
is not used to backdate receipt, and late evidence cannot revise a terminal
outcome. A negotiated contract is **not** a distributed transaction or a
service-level guarantee across network partitions.

The Python observer and independent Go observer currently implement this
restricted Core profile. Other parts of the broader Vigilact architecture
remain proposals or optional Python features.

See [Run the independent Go observer](../guides/go-observer.md) and
[Conformance](../reference/conformance.md).
