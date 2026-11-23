# Python community: technical post (English)

**I built a tiny operational-contract protocol and tried to prove that its semantics aren't Python-specific. Looking for critical feedback.**

Vigilact explores a narrow idea: an agent proposes a one-shot expected event; an observer persists the agreement and records whether matching evidence arrived by the server-side deadline. A missing observation is *not* proof that the underlying task failed.

The Python reference uses FastAPI, Pydantic and SQLite. To avoid testing only my own SDK, I wrote an independent Go HTTP observer for the same limited Core profile.

Before sharing it publicly I added:

- one black-box suite with **22 HTTP/restart checks per observer**;
- seeded **two-agent differential traces** covering authentication boundaries, replay/conflict handling and outbox cardinality;
- matching SHA-256 digests of canonical *observable behavior* for **12 scenarios**;
- Python fault injection at the transaction/outbox boundary to verify rollback and recovery;
- locally passing **62 Python tests** (CI still to be verified on the hosted repository).

These are *bounded engineering experiments*, not formal verification, a certified protocol, or a production-ready server. The Go implementation deliberately excludes the optional Python command extension.

I'm interested in feedback about **receipt-time deadline semantics**, contract idempotency and how to evolve the profile without making it a full workflow engine. What failure mode would you test next?

Code, spec, tests, and docs: **[add the GitHub URL only after publication]**.

#Python #FastAPI #OpenSource #DistributedSystems
