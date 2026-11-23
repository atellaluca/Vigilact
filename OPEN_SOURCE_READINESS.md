# Vigilact — open source release readiness (0.4.0a2)

**Assessment date:** 2026-11-23. **Status:** local alpha release candidate,
**not published** and **not production-ready**.

## Directly verified in the working environment

| Check | Evidence / result |
| --- | --- |
| Python unit and regression suite (Python 3.13) | **62/62 passed** |
| Python coverage | ~95%, minimum CI gate 90% |
| Python and independent Go Core HTTP observers | **22/22 black-box checks each** |
| Bounded 4-worker HTTP load smoke | 25 synthetic successful contract/event pairs per observer, no outbox loss |
| Go tests and race detector | Passed |
| Seeded two-agent differential traces | 12 per implementation, 73 normalized behavioral assertions, matching trace digests |
| Injected SQLite transaction failures | 6 new tests; rollback and retry confirmed |
| Go vet | Passed |
| MkDocs navigation, relative links and API routes | **40 pages** and **14 HTTP methods** checked |
| Canonical GitHub Pages configuration checker | Passed for `https://vigilact.atellaluca.com/` |
| JSON Schema and OpenAPI generation | 11 schemas and 14 HTTP operations exported |
| Python sdist/wheel | Built using local PEP 517 backend |
| Command TTL/lease/migration | New Python regression tests passed; Python extension only |
| SQLite online backup/restore | Integrity and restore regression tests passed |

A local JSON evidence file and a Markdown summary are produced by `scripts/test_observers.py --differential-cases 12 --report ...` and `scripts/render_evidence.py`. Hosted artifact publishing is prepared but unverified.

Synthetic timing results are environment-specific and **not** throughput or
latency SLAs; see `research/CONFORMANCE_LOCAL_2026-11-23.json`.

## Prepared but not yet verified remotely

- GitHub Actions on actual repository, Python 3.11 and 3.12 matrices.
- Ruff and Twine gates (dependencies not available in offline workspace).
- `mkdocs build --strict` (MkDocs not installed in this local workspace).
- GitHub Pages deployment, DNS propagation and TLS certificate provision.
- Public security-scanning and external review; no independent audit exists.
- Repository ruleset, branch protection, release signatures and PyPI trusted publishing.

## Remaining functional constraints

- The **only** cross-language profile is `core.expected_event/0.1`, with single
  one-shot deadline and authenticated owner-scoped evidence.
- Python has optional capability manifests and a no-auto-retry command exchange.
  The Go reference does not claim those profiles.
- No cron, thresholds, federation, multi-agent agreements, revisions, key
  rotation, ACL delegation, storage retention, rate limits or HA.
- Static API keys require network isolation. Agent-reported evidence cannot
  independently prove real-world execution. Current references are not safe for
  untrusted public networks.

## Owner's remaining launch actions

1. Create public `atellaluca/vigilact`, push the clean repo and enable GitHub Actions.
2. Verify CI, Go, docs, Ruff and wheel metadata jobs **actually pass**.
3. Set **Settings → Pages → Source: GitHub Actions** and **Custom domain:
   vigilact.atellaluca.com**.
4. Add DNS `CNAME vigilact → atellaluca.github.io`, verify certificate and
   enable Enforce HTTPS. The repo `docs/CNAME` is ignored for an Actions source.
5. Enable branch protection and vulnerability reporting; publish `v0.4.0a2`
   as a **pre-release**, with these limitations and an invitation to contribute.

See [GitHub Pages setup](docs/maintainers/github-pages.md), [threat model](docs/reference/threat-model.md), [release procedure](RELEASING.md) and [roadmap](ROADMAP.md).
