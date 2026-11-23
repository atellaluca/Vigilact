# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Build-time guard for Vigilact's public project identity.

Does not attempt a network check; URLs can change outside this repository.
"""
from __future__ import annotations

import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
REQUIRED_CONTACTS = (
    'https://profile.atellaluca.com/',
    'https://github.com/atellaluca',
    'https://www.linkedin.com/in/luca-atella/',
    'info@atellaluca.com',
)


def verify() -> None:
    config = yaml.safe_load((ROOT / 'mkdocs.yml').read_text(encoding='utf-8'))
    assert config['site_url'] == 'https://vigilact.atellaluca.com/'
    assert config['theme']['name'] == 'mkdocs'
    assert (DOCS / 'img/favicon.ico').is_file(), 'MkDocs built-in theme expects docs/img/favicon.ico'
    assert (DOCS / 'img/favicon.ico').read_bytes() == (DOCS / 'assets/favicon.ico').read_bytes(), 'favicon copies differ'
    assert (DOCS / 'project-and-maintainer.md').is_file()
    nav = repr(config['nav'])
    assert 'project-and-maintainer.md' in nav

    for file in [DOCS / 'index.md', DOCS / 'project-and-maintainer.md', ROOT / 'README.md']:
        content = file.read_text(encoding='utf-8')
        for ref in REQUIRED_CONTACTS:
            assert ref in content, f'{file.relative_to(ROOT)} missing {ref}'

    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    banner = 'docs/assets/vigilact-readme-banner.png'
    footer = 'docs/assets/vigilact-logo.svg'
    assert banner in readme, 'README missing header banner'
    assert readme.index(banner) < readme.index('# Vigilact'), 'Banner must appear before README title'
    assert footer in readme[-1400:], 'README missing footer logo'
    assert (DOCS / 'assets/vigilact-readme-banner.png').read_bytes()[:8] == b'\x89PNG\r\n\x1a\n', 'invalid README banner PNG'

    svg = DOCS / 'assets/vigilact-logo.svg'
    root = ET.fromstring(svg.read_text(encoding='utf-8'))
    assert root.tag.endswith('svg')
    assert root.attrib['viewBox'] == '0 0 256 256'
    for name in ['favicon.ico', 'favicon.png', 'vigilact-16.png',
                 'vigilact-32.png', 'vigilact-48.png', 'vigilact-180.png',
                 'vigilact-192.png', 'vigilact-512.png', 'vigilact-original-artwork.png']:
        assert (DOCS / 'assets' / name).is_file(), f'missing branding asset {name}'

    icon = (DOCS / 'assets/favicon.ico').read_bytes()
    reserved, icon_type, image_count = struct.unpack_from('<HHH', icon)
    assert (reserved, icon_type) == (0, 1), 'invalid ICO header'
    assert image_count >= 2, 'favicon should include at least two resolutions'
    for name in ['favicon.png', 'vigilact-16.png', 'vigilact-192.png']:
        data = (DOCS / 'assets' / name).read_bytes()
        assert data[:8] == b'\x89PNG\r\n\x1a\n', f'invalid PNG header {name}'

    print('Branding: SVG, favicon ICO/PNG, homepage, author and contacts checked')


if __name__ == '__main__':
    verify()
