# Mental model and scope

Vigilact is an experiment in **observable operational commitments**. Its reference implementation answers a narrow question: *Did the observer receive the expected evidence in time?*

## Four separate concerns

| Concern | Responsible party | Current alpha behavior |
| --- | --- | --- |
| **Intent** | Proposing agent | Proposes an exact expected event and a deadline |
| **Agreement** | Observer | Accepts terms or rejects them, then persists the contract |
| **Evidence** | Agent | Sends a restricted CloudEvents JSON message |
| **Evaluation** | Observer | Records `SATISFIED` or `NOT_OBSERVED` and emits a neutral event |

A fifth concern, **reaction**, belongs to downstream software: operators, notification platforms, ticketing systems or automation products may subscribe to the outbox and decide what to do next. Vigilact does not deliver emails or push messages.

## Contract ≠ event ≠ observation ≠ notification

- A **contract** defines what is expected and by when. It is persistent state.
- An **event** is a claim about something that occurred. It is evidence, not proof of real-world truth.
- An **observation** is the deterministic predicate applied to evidence received by the observer.
- A **notification** is a communication policy — outside the core protocol.

```text
Agent                    Observer                        Consumer
  |   propose terms         |                               |
  +------------------------>| persist contract              |
  |                         |                               |
  |   publish evidence      |                               |
  +------------------------>| evaluate observation          |
  |                         +------ neutral event --------->|
  |                                                         |
```

## Where Vigilact fits

Vigilact does not replace monitoring exporters, workflow engines, cron schedulers, durable task queues, or notification providers. It can receive evidence produced by those systems and record narrowly defined observer outcomes. The alpha profile does not orchestrate task execution or guarantee delivery of an external action.

For example, Kopia can be responsible for actually running a backup. An integration submits evidence from the job. Vigilact records whether the evidence reached the observer by the deadline. A separate adapter may send an email, open an incident, or do nothing.

## Current boundaries

The reference implementation supports **one agent as proposer and evidence owner per contract**, one expected event, a one-shot deadline, and a single SQLite observer. Multi-agent contracts, federation, thresholds, recurring schedules, and trusted attestations remain future research topics. See [Compatibility](../reference/compatibility.md) and the [Roadmap](https://github.com/atellaluca/vigilact/blob/main/ROADMAP.md).
