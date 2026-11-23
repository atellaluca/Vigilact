# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Offline structural documentation checks.

No MkDocs dependency required: the full MkDocs --strict build is a separate
GitHub Actions gate. Validate all local markdown/media links, navigation pages,
and documented HTTP *method/path* pairs against the exported OpenAPI contract.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
MARKDOWN_LINK = re.compile(r"!?(?:\[[^\]]+\])\(([^)]+)\)")
HTML_REF = re.compile(r'(?:href|src)=["\']([^"\']+)["\']')
ROUTE_ROW = re.compile(r"^\|\s*`(GET|POST|PUT|DELETE|PATCH)`\s*\|\s*`(/[^`]+)`\s*\|", re.M)
HEADLINE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.M)
HTML_ID = re.compile(r'\bid=["\']([^"\']+)["\']')


def iter_nav(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_nav(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_nav(item)


def is_local_link(target: str) -> bool:
    return not (target.startswith(("#", "//")) or
                urlsplit(target).scheme in {"http", "https", "mailto", "tel"})


def resolved_target(source: Path, target: str) -> Path | None:
    path = unquote(urlsplit(target).path)
    if not path:
        return None
    candidate = (source.parent / path).resolve()
    if path.endswith("/"):
        route_page = candidate.with_suffix(".md")
        candidate = route_page if route_page.exists() else candidate / "index.md"
    if not candidate.exists() and not candidate.suffix:
        for fallback in (candidate.with_suffix(".md"), candidate / "index.md"):
            if fallback.exists():
                candidate = fallback
                break
    return candidate


def heading_ids(markdown: str) -> set[str]:
    """Approximate MkDocs/Python-Markdown heading IDs for standard headings."""
    ids: set[str] = set(HTML_ID.findall(markdown))
    counts: dict[str, int] = {}
    for title in HEADLINE.findall(markdown):
        title = re.sub(r"`([^`]+)`", r"\1", title)
        title = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", title)
        slug = re.sub(r"[^\w\- ]", "", title.lower()).strip().replace(" ", "-")
        i = counts.get(slug, 0)
        counts[slug] = i + 1
        ids.add(slug if not i else f"{slug}_{i}")
    return ids


def main() -> int:
    errors: list[str] = []
    config = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
    if config.get("docs_dir", "docs") != "docs":
        errors.append("mkdocs.yml must use docs_dir: docs")
    nav_items = list(iter_nav(config.get("nav", [])))
    nav_paths = set(nav_items)
    pages = {p.relative_to(DOCS).as_posix() for p in DOCS.rglob("*.md")}
    for name in sorted(nav_paths - pages):
        errors.append(f"missing navigation page: {name}")
    for name in sorted(pages - nav_paths):
        errors.append(f"unlisted navigation page: {name}")
    for name in sorted({name for name in nav_items if nav_items.count(name) > 1}):
        errors.append(f"duplicate navigation entry: {name}")

    for name in sorted(pages):
        source = DOCS / name
        content = source.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(content) + HTML_REF.findall(content):
            target = target.split(' "', 1)[0].strip("<>")
            if not is_local_link(target):
                continue
            candidate = resolved_target(source, target)
            if candidate and (DOCS not in candidate.parents and candidate != DOCS):
                errors.append(f"{name}: link escapes docs/: {target}")
            elif candidate and not candidate.exists():
                errors.append(f"{name}: missing local link: {target}")
            elif candidate and candidate.suffix == ".md":
                fragment = unquote(urlsplit(target).fragment)
                if fragment and fragment not in heading_ids(candidate.read_text(encoding="utf-8")):
                    errors.append(f"{name}: unknown heading #{fragment} in {target}")

    for asset in config.get("extra_css", []):
        if not (DOCS / asset).is_file():
            errors.append(f"missing stylesheet: docs/{asset}")

    spec = json.loads((ROOT / "api/openapi.json").read_text(encoding="utf-8"))
    actual = {(method.upper(), path) for path, methods in spec["paths"].items()
              for method in methods if method.lower() in {"get", "post", "put", "patch", "delete"}}
    api_doc = (DOCS / "protocol/http-api.md").read_text(encoding="utf-8")
    documented = set(ROUTE_ROW.findall(api_doc))
    for method, path in sorted(actual - documented):
        errors.append(f"protocol/http-api.md: missing method/path: {method} {path}")
    for method, path in sorted(documented - actual):
        errors.append(f"protocol/http-api.md: undocumented actual route: {method} {path}")

    if errors:
        for error in errors:
            print(f"DOC ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Docs: {len(pages)} pages, {len(nav_items)} nav entries; "
          f"local links, assets and {len(actual)} HTTP methods checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
