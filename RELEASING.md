# Release and supply-chain process

This documents a proposed release workflow. **No GitHub release or PyPI
publication has been made merely by adding these files.**

## Pre-release checklist

**Poetry lock gate:** create and commit a genuine `poetry.lock` with Poetry 2.5.2 (see `docs/maintainers/poetry-workflow.md`). Verify it with `poetry check --lock` and install with `poetry sync --all-groups --all-extras`. This is required before claiming reproducible environments or publishing on PyPI.

1. Start from a reviewed branch. Require CI checks and code review through GitHub
   branch protection / rulesets (configure in repository settings).
2. Update `CHANGELOG.md`, `ROADMAP.md`, and version in
   `src/vigilact/__init__.py`, `pyproject.toml`, and `CITATION.cff`.
3. Run `make test`, `make coverage`, `make demo`, `make lint` and `make build`. Also run the independent Core observer gate `poetry run python scripts/test_observers.py` (requires Go).
4. Regenerate and review `api/openapi.json` and `schemas/`. Confirm no unintentional
   changes to the documented HTTP binding.
5. Confirm a clean checkout builds both wheel and sdist and that their metadata
   passes `twine check`. Execute the HTTP conformance smoke runner against a
   localhost reference instance.
6. Review open security issues and the release's declared limitations. Never
   insert credentials, production data or private incident details into artifacts.
7. Create a signed tag if release infrastructure is configured, e.g.
   `git tag -s v0.4.0a2 -m 'Vigilact v0.4.0a2'`. Signing is recommended, not
   silently assumed.
8. Publish release notes and build artifacts on GitHub. Record SHA-256 checksums.
   Check both the packaged source and a clean installation before publishing.

## PyPI (not automatic)

PyPI project ownership and the GitHub repository must first be created and
verified by the maintainer. For future publication, configure **PyPI Trusted
Publishing** with GitHub OIDC and a protected environment; avoid stored PyPI
API tokens. A tag must **not** automatically publish to PyPI before that setup.

References: [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/),
[PyPA release workflow](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).

## Supply-chain policy

- The core CI actions use reviewed commit pins. The GitHub Pages
  workflow uses pinned commit hashes for its deployment actions; verify the pins
  against official releases when updating them. Token
  permissions default to read-only, with OIDC/pages privileges limited to
  the documentation deployment job. Dependabot proposes updates for review.
- CI validates tests, coverage, generated specs, a locally built package and
  a protocol smoke run using only synthetic credentials.
- Enable GitHub private vulnerability reporting, dependency alerts, secret
  scanning (if available), repository rulesets and CodeQL default setup in
  GitHub settings. Those account-side features are **not activated** by this
  source archive.
- No SLSA level, vulnerability-free certification or formal audit is claimed.
