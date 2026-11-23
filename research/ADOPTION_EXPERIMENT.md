# Adoption experiment (proposal; not executed)

Do not confuse repository completeness with user demand.

## Candidate audience

Infrastructure engineers, homelab developers, authors of backup/automation
agents and independent developers integrating multiple operational systems.

## Research-first launch sequence

1. Publish source + docs with honest alpha limitations and runnable demos.
2. Ask for technical critique from maintainers using Healthchecks, Prometheus
   and workflow systems; **do not** frame posts as endorsements or promotions.
3. Share one concrete "why not a cron monitor?" example: contractual acceptance,
   neutral evaluation events and separately authorized agent capabilities.
4. Invite a small outside implementation using only the wire spec and golden vectors.
5. Publish a retrospective listing which assumptions survived external feedback.

## Proposed evaluation after a 30-day launch window

| Signal | Target for learning, not a forecast |
| --- | --- |
| Meaningful external reviews of the protocol | >= 5 |
| Independent real integrations (not authored by maintainer) | >= 2 |
| Documented cases where current semantics are insufficient | >= 3 |
| Independent observer passing basic HTTP conformance suite | >= 1 |

Interpretation: failure to meet these targets is not proof that the protocol
cannot work, but a reason to revisit positioning and onboarding before adding
more features. Do not game metrics or solicit shallow stars.

## Potential channels (no automatic posting)

GitHub Discussions, targeted technical communities, Hacker News *Show HN* after
there is a public working demo, and a technical engineering article under the
maintainer's own name. Follow each community's self-promotion rules.

## Proposed article title

**"Why a missing heartbeat isn't enough: experimenting with observable software commitments"**

Use architecture, reproducible failures, and measured tradeoffs. Cite related
work rather than claiming invention of operational contracts.
