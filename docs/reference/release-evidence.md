# Release evidence and scope

This page distinguishes reproducible engineering checks from work that still
requires a repository owner or external reviewer.

## Reproduce locally

```bash
poetry sync --all-groups --all-extras
poetry run python -m pytest -q
poetry run python scripts/test_observers.py --load 25 --differential-cases 12 --seed 20261123 --report artifacts/core-evidence.json
poetry run python scripts/check_docs.py
poetry run python scripts/check_pages_config.py
(cd implementations/go-observer && go test -race ./... && go vet ./...)
```

`test_observers.py` builds the independent Go Core observer and runs the same
black-box checks against Python and Go, including restart and late-evidence
reconciliation. Go currently implements only `core.expected_event/0.1`.

The optional commands extension is implemented only by Python and is excluded
from cross-server Core conformance. New tests exercise expiry and lease rules.

## Required before GitHub release

1. Push the repository and inspect the **actual** CI and Docs jobs on GitHub.
2. Run the strict MkDocs build and the Ruff/Twine gates on CI (not guaranteed
   available in offline developer environments).
3. Enable repository security advisories and branch protection.
4. Set the custom domain in **Settings → Pages** and configure the DNS CNAME;
   a docs file alone is not enough.
5. Publish as **alpha**, identify known risks and invite external review.

## Deliberately not claimed

The project is not a ratified standard, security-certified service, production
HA platform, or externally audited protocol. Two implementations have passed
the same limited Core suite; that does not certify their behavior in all cases.

For deterministic cross-implementation isolation, rollback/fault injection, and canonical digests, see [Engineering proof](engineering-evidence.md).
