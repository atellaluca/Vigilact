# Poetry migration verification

The Python build backend and metadata are migrated to Poetry in `pyproject.toml`.

**One external prerequisite remains:** `poetry.lock` can only be generated and checked when Poetry can access package indexes. The delivery environment had no Poetry and no PyPI access, so it is **not included**; this is intentional, not an empty placeholder.

Run the **Generate Poetry lock** workflow on GitHub or locally with Poetry 2.5.2, then commit the actual `poetry.lock` in the repository. CI will then use its exact versions and fail if the file is absent or outdated.

```bash
pipx install poetry==2.5.2
poetry lock
poetry check --lock
poetry sync --all-groups --all-extras
poetry run pytest -q
poetry build
```

This change does not modify the experimental Vigilact wire protocol or replace the independent Go observer. Original test results must be rechecked after the lockfile is committed. The `docs/assets/vigilact-readme-banner.png` and `docs/assets/vigilact-logo.svg` assets are included for GitHub README branding.
