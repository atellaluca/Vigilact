"""Guard the shared visual language and Vigilact-specific assets."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

def config():
    return yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))

def test_material_layout_with_vigilact_brand_palette():
    c = config()
    assert c["theme"]["name"] == "material"
    assert c["theme"]["palette"][0]["primary"] == "custom"
    assert c["theme"]["palette"][0]["accent"] == "custom"
    assert {"navigation.tabs", "navigation.instant"} <= set(c["theme"]["features"])
    css = (ROOT / "docs/assets/styles.css").read_text(encoding="utf-8").lower()
    assert "--md-primary-fg-color: #132e49" in css
    assert "--md-accent-fg-color: #007a74" in css
    logo = (ROOT / "docs/assets/vigilact-logo.svg").read_text(encoding="utf-8").lower()
    assert "#132e49" in logo and "#08b6a4" in logo

def test_vigilact_still_has_its_own_brand_and_domain():
    c = config()
    assert c["site_url"] == "https://vigilact.atellaluca.com/"
    for key in ("logo", "favicon"):
        assert (ROOT / "docs" / c["theme"][key]).is_file()
    assert c["repo_url"] == "https://github.com/atellaluca/vigilact"

def test_maintainer_links_in_footer_and_homepage():
    c = config()
    footer = {entry["link"] for entry in c["extra"]["social"]}
    home = (ROOT / "docs/index.md").read_text(encoding="utf-8")
    for link in ("https://profile.atellaluca.com/",
                 "https://github.com/atellaluca",
                 "https://www.linkedin.com/in/luca-atella/",
                 "mailto:info@atellaluca.com"):
        assert link in footer
        assert link in home

def test_material_dependency_and_docs_workflow():
    py = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/docs.yml").read_text(encoding="utf-8")
    assert "mkdocs-material" in py
    assert "mkdocs build --strict" in workflow
