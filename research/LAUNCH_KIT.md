# Vigilact launch kit (draft; no accounts have been posted to)

This messaging is for an early **alpha / research project**, not a standardized
or production-ready monitoring solution.

## Repository settings

- Owner: `atellaluca` (publish only when ready)
- Proposed name: `vigilact` (confirm name availability and trademark conflicts)
- GitHub description: `Open protocol experiment for observable operational commitments, evidence and authorized agent capabilities.`
- Suggested topics: `distributed-systems`, `observability`, `protocol`, `python`, `golang`, `cloudevents`, `open-source`, `event-driven`
- Docs address after Pages activation: `https://vigilact.atellaluca.com/`

## Developer-first launch narrative

**Headline:** Why a missing heartbeat isn't enough: observable operational commitments.

**Problem:** The distinction between evidence arriving late, an action failing,
and an observer being unreachable gets blurred in application-specific glue code.

**Approach:** An agent proposes a one-shot commitment, an observer persists and
evaluates it according to receipt time, and a separate capability model lets an
operator *request* explicit diagnostics without granting implicit execution.

**Proof:** 41 Python tests plus 14 shared semantic vectors evaluated by Python
and Go (rerun them at launch); a reproducible observe-and-act demo; published
OpenAPI and documented HTTP smoke tests.

**Limit:** No full second HTTP implementation, recurring schedules,
production-grade identity or security, SLA guarantees, or ecosystem adoption.

## Suggested issue labels and starting tasks

- `good first issue`: improve public examples or explain a single vector.
- `protocol/rfc`: propose one normative semantic change with positive and negative traces.
- `interop`: write an independent HTTP observer implementing the narrow current profile.
- `security`: report issues privately via SECURITY.md before opening a public issue.
- `docs`: clarify which behaviours are guaranteed and which are accidental.

## Launch checklist

- [ ] Verify repository name and licensing before first public push.
- [ ] Run `pytest -q`, docs checks and the Go/Python semantic runners.
- [ ] Confirm GitHub Actions and Pages actually succeed on the remote repository.
- [ ] Confirm that secrets are not included in the commit history.
- [ ] Publish an alpha release with limitations; don't suggest production use.
- [ ] Invite concrete feedback: one missing invariant or independent implementation.
- [ ] Track downstream use and issue quality instead of solely stars.

## Suggested post (copy/edit, not published)

**Vigilact is an experimental open protocol for observable operational commitments.**
An agent can propose a deadline-bound expectation, an observer can accept it and
record whether evidence arrived on time, and separate opt-in capabilities can
support authorized diagnostics. It's intentionally *not* another notification
service or workflow engine. I've published a Python reference implementation,
14 semantic vectors with an independent Go evaluator, and an HTTP demo.
I'd especially value critiques of receipt-time semantics, identity boundaries,
and what a truly independent second server would need to implement.
