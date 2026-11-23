# Publishing the docs on vigilact.atellaluca.com

The canonical documentation address is **<https://vigilact.atellaluca.com/>**.
The GitHub Pages source is **GitHub Actions**, not a `gh-pages` branch.
The site is *not* live until the GitHub repository owner completes the steps below.

## 1. Configure the GitHub repository

1. Publish this repository as `atellaluca/vigilact` and make it public.
2. Open **Settings → Pages → Build and deployment**; choose **GitHub Actions** as the source.
3. Under **Custom domain**, set `vigilact.atellaluca.com` and save.
4. After the Pages deployment and certificate provisioning succeed, enable **Enforce HTTPS**.
5. Optional but recommended: verify ownership of `atellaluca.com` under your GitHub account's Pages domain-verification settings. Keep GitHub's verification TXT record in DNS.

Do **not** point the subdomain at an arbitrary third-party Pages site. Configure the
custom domain in the intended repository **before** adding a public DNS record;
this avoids an unnecessary domain-takeover window.

## 2. Configure DNS

At your DNS provider, add this record (the name may be `vigilact` or the fully
qualified hostname, according to the provider's UI):

| Type | Host/name | Value/target |
| --- | --- | --- |
| `CNAME` | `vigilact` | `atellaluca.github.io` |

Do **not** include `https://`, the trailing `/vigilact` repository path, or an IP
address in the CNAME destination. Do not add a conflicting A/AAAA record for the
same hostname. If Cloudflare or another proxy is in use, initially use DNS-only
mode to avoid complicating GitHub's certificate validation.

## 3. Build and publish

The workflow `.github/workflows/docs.yml` checks Markdown navigation, local
links, HTTP route coverage and custom-domain settings; builds with
`poetry run mkdocs build --strict`; uploads the static files and deploys to GitHub Pages
on pushes to `main`. Pull requests **build but never deploy**.

The repository also contains `docs/CNAME` as a human-readable declaration of
its canonical hostname and for alternative branch-based hosting workflows.
**GitHub ignores this file for a custom GitHub Actions publishing source**:
only the custom-domain setting on **Settings → Pages** configures the domain.

Run the same quality gates locally:

```bash
poetry sync --all-groups --all-extras
poetry run python scripts/check_docs.py
poetry run python scripts/check_pages_config.py
poetry run mkdocs build --strict
```

## 4. Verify deployment

From a terminal after configuring DNS:

```bash
dig +short CNAME vigilact.atellaluca.com
# Expected: atellaluca.github.io. (possibly normalized to a trailing dot)
curl -I https://vigilact.atellaluca.com/
```

Check the GitHub Actions **Docs** workflow is green; then follow a few links and
verify that internal links use the root of the custom subdomain, **not**
`/vigilact/`. Verify HTTPS is enabled in Pages settings. DNS changes and
certificate issuance can take time; do not infer success from a green build alone.

## Troubleshooting

- **404 on the custom hostname:** check Pages custom-domain setting, DNS CNAME and whether deployment finished.
- **Wrong URL `/vigilact/`:** confirm `mkdocs.yml` sets `site_url: https://vigilact.atellaluca.com/` and rebuild.
- **Certificate unavailable:** remove conflicting records, avoid a proxy during initial configuration, and check GitHub Pages settings.
- **Custom domain claimed elsewhere:** complete account-level verification or contact GitHub Support.

Sources: [GitHub: custom domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site), [GitHub: Actions publishing](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).


## Project identity and site icon

The docs homepage includes the independent Vigilact project symbol. Material for MkDocs serves the icon from `docs/assets/favicon.ico`, as declared in `mkdocs.yml`. Source artwork and scalable assets are maintained in `docs/assets/`. The [Project & maintainer](../project-and-maintainer.md) page and homepage provide the maintainer's professional profile, GitHub, LinkedIn and contact address. `python scripts/check_branding.py` guards these references in CI.
