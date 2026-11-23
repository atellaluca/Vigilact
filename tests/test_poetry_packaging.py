# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Static pre-publish guards for Poetry packaging and branding migration."""
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def read_pyproject():
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_poetry_core_backend_and_project_metadata():
    config = read_pyproject()
    assert config["build-system"]["build-backend"] == "poetry.core.masonry.api"
    assert config["project"]["name"] == "vigilact-protocol"
    assert config["project"]["version"] == "0.4.0a3"
    assert config["tool"]["poetry"]["packages"] == [{"include": "vigilact", "from": "src"}]


def test_poetry_groups_and_http_extra():
    config = read_pyproject()
    groups = config["tool"]["poetry"]["group"]
    assert {"dev", "docs"}.issubset(groups)
    assert "mkdocs" in groups["docs"]["dependencies"]
    assert "pytest" in groups["dev"]["dependencies"]
    assert "httpx>=0.27,<1" in config["project"]["optional-dependencies"]["client"]


def test_version_metadata_matches_package_and_citation():
    import vigilact
    assert vigilact.__version__ == read_pyproject()["project"]["version"]
    assert "version: 0.4.0a3" in (ROOT / "CITATION.cff").read_text()


def test_all_workflows_use_poetry_and_require_a_real_lock():
    for name in ("ci", "docs"):
        workflow = (ROOT / f".github/workflows/{name}.yml").read_text()
        assert "poetry check --lock" in workflow
        assert "poetry sync --all-groups --all-extras" in workflow
        assert "pip install -e" not in workflow
    generator = (ROOT / ".github/workflows/poetry-lock.yml").read_text()
    assert "poetry lock" in generator
    assert "path: poetry.lock" in generator


def test_readme_branding_files_exist_and_order():
    readme = (ROOT / "README.md").read_text()
    banner = "docs/assets/vigilact-readme-banner.png"
    logo = "docs/assets/vigilact-logo.svg"
    assert (ROOT / banner).is_file()
    assert (ROOT / logo).is_file()
    assert readme.index(banner) < readme.index("# Vigilact")
    assert readme.rfind(logo) > readme.rfind("##")


def test_no_parallel_python_package_manifests():
    assert not (ROOT / "MANIFEST.in").exists()
    assert not (ROOT / "requirements-docs.txt").exists()
    assert "poetry.lock" not in (ROOT / ".gitignore").read_text().splitlines()
