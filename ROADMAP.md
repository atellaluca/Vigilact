# Roadmap — current alpha gates and deliberately deferred capabilities

## Verified engineering milestones for 0.4.0a1

- [x] Independent Python and Go HTTP observers for `core.expected_event/0.1`.
- [x] Shared negative, idempotency, restart and deadline tests (21 each).
- [x] Restricted RFC 3339 timestamp precision consistently enforced.
- [x] Bounded synthetic concurrent load smoke for both HTTP observers.
- [x] Python command TTL, claimed-lease `UNKNOWN`, operator status inspection.
- [x] SQLite online backup helper with integrity check and restore test.
- [x] Docs-as-code for custom domain `vigilact.atellaluca.com` through GitHub Pages.
- [x] JSON Schema, OpenAPI, tests and contributor documentation.

## Next milestones (not implemented)

- [ ] Formal contract revisions and counter-proposal semantics.
- [ ] Separately modeled proposer, subject, observer and evidence-provider roles.
- [ ] Scheduled/recurring, threshold and correlated observations.
- [ ] A full credential rotation and delegated authorization model.
- [ ] Storage retention, quotas and production rate limiting.
- [ ] HA, federation, multi-instance consensus and long-running chaos/soak tests.
- [ ] Independent external security audit and at least two external adopters.
- [ ] Stable protocol schema and non-experimental 1.0 compatibility promise.

## Community starter tasks

- Add a Rust third-party observer targeting the same published test vectors.
- Expand temporal semantics with clock step, leap and replay cases.
- Produce OpenAPI response examples and better typed error identifiers.
- Help test packaging on Linux, Windows and macOS.
- Review key management and source authentication threats.

**Guiding principle:** do not claim production readiness or universality from
a passing alpha smoke suite. Preserve implementation independence and neutral
evaluation events; Vigilact remains separate from LTG Notify.
