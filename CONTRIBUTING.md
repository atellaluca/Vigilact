# Contributing

Thank you for helping build Vigilact. The project is alpha: **avoid breaking the core wire format without a proposal**.

1. Open an issue describing the interoperability problem and an example with at least two different applications.
2. For changes to protocol semantics, submit a short design note under `spec/` before a major implementation change.
3. Keep the wire representation language-neutral; prefer existing standards to proprietary types.
4. Add tests for success, failure, duplicate/replayed messages, authorization, and time boundaries.
5. Run `poetry sync --all-groups --all-extras`, `pytest -q` and `poetry run python examples/quickstart.py`.
6. Never commit credentials or production telemetry.

By submitting a contribution, you agree to license it under Apache-2.0. This repository currently has no CLA requirement.

All discussion should follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Development environment

- CPython 3.11–3.13 and Poetry 2.5.2; Poetry manages the isolated environment.
- On the first migration checkout, generate `poetry.lock` using `poetry lock` and commit it.
- Then run `make install && make coverage && make demo && make lint`.
- For API changes: `make specs`, then review the generated schemas/OpenAPI diff.
- For release candidates: `make build`.
- Include a regression test with each behavioral change; do not update snapshots
  merely to silence an unexpected difference.

## Review readiness

Small, single-purpose PRs are easier to review. Explain the reproducible failure,
wire-format impact, trade-off and tests. For new protocol behavior, attach an ADR
and a transport-independent test scenario. Keep types and examples independent
of the Python reference implementation.

See [GOVERNANCE.md](GOVERNANCE.md) for how decisions are made. Vulnerabilities
should be reported privately, not in public PRs or issues.

## Documentation contributions

Documentation is source-controlled in `docs/` and configured through `mkdocs.yml`.
Before proposing documentation changes, run:

```bash
poetry sync --all-groups --all-extras
poetry run python scripts/check_docs.py
poetry run mkdocs build --strict
```

For API changes, update the protocol draft, generated OpenAPI and schemas,
and relevant documentation pages together. See `docs/reference/contributing.md`.
