# Maintaining the documentation

Documentation is code. A protocol feature is not ready for public release until its behavior is explained, backed by executable tests, and reflected in the API/schema artifacts.

## Local authoring

```bash
poetry sync --all-groups --all-extras
poetry sync --all-groups --all-extras
poetry run python scripts/check_docs.py
poetry run mkdocs build --strict
poetry run mkdocs serve
```

Use the [Poetry environment and packaging guide](poetry-workflow.md) to create `poetry.lock` for a reproducible workspace. The link checker runs without MkDocs. `mkdocs build --strict` is the authoritative site build and is also configured in GitHub Actions. A successful link check alone **does not** prove the complete MkDocs build works.

## Before submitting a documentation pull request

1. Update the relevant `docs/` page and, when normative behavior changes, `spec/`.
2. Add new pages to `mkdocs.yml` navigation — the checker rejects orphan pages.
3. Update the Python models/server and tests if you changed implemented behavior.
4. Run `poetry run python scripts/export_specs.py`, then review changes to `api/` and `schemas/`.
5. Update `CHANGELOG.md` for notable changes, including breaking documentation or semantics.
6. Re-run tests and the strict docs build; include an example request/response where possible.

## Language and promises

Use English with precise, short explanations. Prefer *observed*, *received*, and *evaluated* over claims like *guaranteed successful*, especially in failure scenarios. Never document a planned feature as implemented. Label unsafe local examples clearly; do not include real credentials or keys.

Use relative links for internal pages and canonical external URLs for standards. Avoid references that depend on a specific notification vendor. Always include a path back to a guide, a definition and/or protocol reference.

## Automated guards

- `scripts/check_docs.py` verifies site navigation, local links, HTTP route coverage and documentation assets.
- `tests/test_documentation_walkthrough.py` executes the documented synthetic HTTP example against the Python server in-process.
- `.github/workflows/docs.yml` builds the MkDocs site with `--strict` before publishing via GitHub Pages.

## Reporting corrections

For inaccuracies that could affect security, prefer the [Security Policy](https://github.com/atellaluca/vigilact/blob/main/SECURITY.md) over a public issue. For typos, broken links and examples, use a documentation pull request or a normal issue.


For GitHub Pages custom-domain deployment see [Publishing on vigilact.atellaluca.com](github-pages.md).


## Branding and maintainer references

The README opens with `docs/assets/vigilact-readme-banner.png` and closes with `docs/assets/vigilact-logo.svg`. The documentation uses the independent **Vigilact** symbol at `docs/assets/vigilact-logo.svg`, a PNG artwork variant, and multi-resolution favicons (`favicon.ico`, `favicon.png`). Keep the SVG as the editable source for future favicon variants. The built-in MkDocs theme reads the actual deployed favicon from `docs/img/favicon.ico`; maintain it in sync with `docs/assets/favicon.ico`. Brand assets are distributed with the repository under Apache-2.0.

The public docs must retain the founding maintainer references: [professional profile](https://profile.atellaluca.com/), [personal GitHub](https://github.com/atellaluca), [LinkedIn](https://www.linkedin.com/in/luca-atella/), and [contact email](mailto:info@atellaluca.com). Keep the [Project & maintainer](../project-and-maintainer.md) page and homepage links accurate.

Run `python scripts/check_branding.py` before merging docs changes. The check is also part of GitHub Actions.
