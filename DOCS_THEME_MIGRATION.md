# Documentation theme alignment with ImportSpy

Vigilact documentation now uses **Material for MkDocs**, matching the design system visible at [ImportSpy](https://importspy.atellaluca.com/): tabbed top-level navigation, instant navigation, built-in search, and Material typography. The primary color is now **Vigilact navy** (`#132E49`), with a **teal interactive accent** (`#007A74`) drawn from the logo’s signal teal (`#08B6A4`).

Vigilact retains its own V logo, favicon, canonical `https://vigilact.atellaluca.com/`, social links, and technical content. No protocol, API, SDK, or Go observer behavior was changed.

## Applying to the live repository

1. Copy the changed docs and configuration files (or extract the *docs-only* archive at the repository root).
2. Run `poetry lock` to add the new `mkdocs-material` dependency to the lockfile.
3. Run `poetry sync --all-groups --all-extras` (or `poetry sync --with docs` if using a lean environment).
4. Run `poetry run python scripts/check_docs.py`, `poetry run python scripts/check_branding.py`, and `poetry run mkdocs build --strict`.
5. Commit the changed files **including** `poetry.lock`, then push to `main`. The existing GitHub Pages workflow will deploy the site.

## Known constraint

The source snapshot predates the user's local lockfile commit. The distributed ZIP contains no `poetry.lock`; keep the version already committed locally, regenerate it with Poetry after modifying `pyproject.toml`, and do not remove it.

## Brand palette adjustment

This docs-only patch sets `theme.palette.primary` and `theme.palette.accent` to `custom` and defines Material theme CSS variables in `docs/assets/styles.css`. No Python/Go functionality, Poetry dependencies, lockfile, domain, or social links change.

Apply this patch at the repository root and run:

```bash
poetry run pytest -q tests/test_docs_material_theme.py
poetry run python scripts/check_docs.py
poetry run mkdocs build --strict
```

Commit the changed files and push to deploy the existing GitHub Pages site.
