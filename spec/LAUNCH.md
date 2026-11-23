# Open-source launch playbook

The goal is **developer adoption and credible engineering visibility**, not artificial star growth. Do not publish claims about adoption, security certification or interoperability until independently verified.

## GitHub repository setup

- Owner: `atellaluca`
- Suggested repo name: `vigilact` (check availability at publishing time)
- About: `Open protocol experiment for negotiated operational contracts, evidence observation, and authorized agent capabilities.`
- Website: initially the repository README; add a real docs site only after stability.
- Topics: `open-source`, `observability`, `protocol`, `distributed-systems`, `cloudevents`, `python`, `fastapi`, `event-driven`, `monitoring`.
- License: Apache-2.0 (review and confirm before public release).
- Enable Discussions and private vulnerability reporting. Protect `main` with required CI once available.

## Launch sequence

1. **Publish a GitHub alpha** with README, runnable quickstart, CI badge, changelog and an honest security warning.
2. **Record a 60–90 second demo** showing accepted contract → evidence → `SATISFIED`, and missed event → `NOT_OBSERVED`, followed by a separate authorized command. Use the same deterministic example every time.
3. **Write a technical article** focusing on the design lesson: why missing evidence is not the same as a failed operation, and why capabilities must be separate from authorization.
4. **Ask for design criticism** in appropriate Python, distributed systems or self-hosting communities. Prefer precise questions over promotional slogans.
5. **Review 30 days after release**: external users completing the quickstart, issue quality, contributions and independent clients matter more than raw stars.

## Ready-to-adapt GitHub release description

### Vigilact v0.2.0 alpha — Observe the commitments, not just the events

Vigilact is an experimental open protocol for software that needs to describe **what must happen** and evaluate whether evidence arrived on time. It separates durable operational contracts from notifications and remote command execution.

This alpha source release includes an executable Python reference server, CloudEvents-style event ingestion, a neutral outbox, opt-in agent capabilities, default-disabled remote commands, an independent HTTP smoke runner, and a deterministic end-to-end demo. It is **not production-ready** and currently supports only one-shot expected-event commitments. Feedback on temporal semantics and independent implementations is especially welcome.

## First article outline

**Title:** `I built an open protocol for things that should happen — not just things that happened`

1. The missing-event problem in backups and background jobs.
2. Contract negotiation versus an ordinary webhook.
3. Evidence versus truth; why time semantics are difficult.
4. What `SATISFIED` and `NOT_OBSERVED` actually mean.
5. Security: why a capability is not permission to execute.
6. Demo GIF/video and repository link.
7. Known limits and a request for independent implementations.

## Metrics worth tracking

- Successful external quickstarts (issues/discussions from actual users).
- Independent API client implementations.
- High-signal bug reports and pull requests.
- Conformance cases contributed by other developers.
- Adoption of one observation profile outside your own infrastructure.

Do not buy stars, send spam or claim that the project is an established standard.

## Publication quality gates

- Do not claim GitHub Actions passed until the first public workflow run succeeds.
- Do not mark the repository as `production-ready`, `CNCF`, `certified` or `stable`.
- Do not publish to PyPI before verifying ownership of the distribution name and
  setting up a secure release process.
- Ensure the README contains a first-run demo result and an easy-to-find
  design-proposal issue template.
- Ask for a Go/Rust observer implementation or a written conformance review;
  those are stronger proof of developer interest than GitHub stars alone.
