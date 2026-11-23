# Glossary

A shared vocabulary helps two independent implementations interpret the same protocol.

| Term | Meaning in Vigilact |
| --- | --- |
| **Agent** | Authenticated software identity that proposes contracts and publishes evidence |
| **Operator** | Authenticated administrative identity with read and optional command privileges in the reference server |
| **Observer** | Server component that accepts contracts and evaluates received evidence |
| **Contract** | Durable accepted commitment with an agreed observation rule and deadline |
| **Proposal** | Request to create a contract; this alpha accepts exact terms only |
| **Observation** | Predicate that determines whether relevant evidence arrived within the agreed window |
| **Evidence** | Agent-published CloudEvents-style message used to evaluate a contract; it does not prove physical truth |
| **Subject** | String identifying the job or resource being observed |
| **Receipt time** | Observer time at which a new evidence message is accepted |
| **Deadline** | Last acceptable receipt time for a one-shot observation |
| **Outcome** | `PENDING`, `SATISFIED` or `NOT_OBSERVED` in the current implementation |
| **Capability** | Metadata about an operation the agent advertises; not a grant of authorization |
| **Command** | Operator-originated request queued for an agent's opt-in, locally authorized handler |
| **Outbox** | Persistent ordered sequence of neutral observer evaluation events |
| **Cursor** | Sequence position after which the consumer requests the next outbox page |
| **Profile** | Named subset of protocol features advertised in discovery |
| **Binding** | Transport-specific representation of the protocol, currently HTTP/JSON |
| **Idempotency** | Repeat of the same logical request does not create a second logical state change |

Start with the [mental model](../concepts/mental-model.md) or [protocol overview](../protocol/http-api.md).
