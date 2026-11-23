# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Offline static checks for the intended GitHub Pages custom domain."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'vigilact.atellaluca.com'


def validate() -> None:
    config = yaml.safe_load((ROOT / 'mkdocs.yml').read_text())
    assert config['site_url'] == f'https://{DOMAIN}/', 'Wrong canonical documentation URL'
    assert (ROOT / 'docs/CNAME').read_text().strip() == DOMAIN, 'Wrong docs/CNAME'
    workflow = (ROOT / '.github/workflows/docs.yml').read_text()
    for required in ('mkdocs build --strict', 'actions/upload-pages-artifact@',
                     'actions/deploy-pages@', 'id-token: write', 'pages: write',
                     "github.event_name != 'pull_request'"):
        assert required in workflow, f'Missing Pages workflow requirement: {required}'
    assert (ROOT / 'docs/maintainers/github-pages.md').is_file()
    print(f'GitHub Pages configuration checked for https://{DOMAIN}/')


if __name__ == '__main__':
    validate()
