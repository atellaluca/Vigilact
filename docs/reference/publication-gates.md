# Engineering publication gates

Before making a public release or describing a compatibility claim, run:

```bash
poetry sync --all-groups --all-extras
poetry run python -m pytest -q
python scripts/expected_event_vectors.py --check
cd implementations/go-observer && go test -race ./... && cd ../..
poetry run python scripts/test_observers.py
poetry run python scripts/check_docs.py
poetry run python scripts/export_specs.py
```

In GitHub Actions, additionally enforce Ruff, artifact metadata validation,
`mkdocs build --strict`, and Python 3.11–3.13. CI is configured to exercise
both HTTP observer implementations and repeat the independent Go race tests.

**Pass criteria:** No failing test, no diverging generated schema artifact,
no missing documentation navigation entry or internal link, and 22/22 HTTP
checks for **each** independent server under the same Core profile.

Passing these checks only supports the **experimental Core profile** claim.
There has been no independent third-party review, comprehensive fuzzing,
formal model check, security audit, production stress test or multi-node
availability validation. The Go reference server is not suitable for high
volume due to full-file persistence.

The most useful next milestones are interoperability feedback from an
independent maintainer, a richer corpus of adversarial event sequences,
security review and opt-in developer adopters.


For Poetry packaging use `poetry check --lock`, `poetry sync --all-groups --all-extras` and `poetry build`. The initial lockfile must be generated online and committed; see [Poetry workflow](../maintainers/poetry-workflow.md).
