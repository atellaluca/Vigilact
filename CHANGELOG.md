## 0.4.0a3 — Poetry packaging and README identity (2026-11-23)

- Migrated the Python package build to `poetry-core` with single-source dev/docs dependency groups.
- Updated Makefile, GitHub Actions, docs and release instructions to run through Poetry.
- Added branded README banner and footer logo. No experimental wire-protocol changes.
- A genuine `poetry.lock` must be generated in an online Poetry environment and committed before declaring locked environment reproducibility.

## 0.4.0a2 — reproducible engineering evidence (2026-11-23)

- Added seeded, two-agent differential HTTP scenarios against independent Python and Go Core observers.
- Added transaction failure injection at evaluation-outbox boundaries, verifying rollback and safe retry.
- Extended the publication gate with machine-readable local evidence and canonical trace comparison.
- Added technical evidence documentation, boundaries, and outreach drafts for public review.
- **No wire-protocol changes:** `vigilact/0.1-experimental` and `core.expected_event/0.1` remain unchanged.

## 0.4.0a1 — command safety, reproducibility and custom-domain docs (2026-11-23)

- Added Python command TTL, lease timeout -> `UNKNOWN`, safe no-retry semantics, late agent results, and operator command lookup.
- Added in-place fail-closed migration for older SQLite command tables and online backup/restore helper.
- Enforced RFC 3339 timestamps with at most microsecond precision across Python and Go Core observers.
- Expanded shared black-box HTTP conformance to 22 checks per observer and added bounded concurrent load smoke.
- Added explicit threat model, release evidence, command lifecycle and documentation hosted at the intended custom domain.
- Prepared GitHub Pages workflow, DNS guide, canonical URL and docs/CNAME declaration; deployment requires owner configuration.
- Preserved `vigilact/0.1-experimental` and the narrow `core.expected_event/0.1` profile; no production guarantees.

## 0.3.0a1 — Independent Core observer and publication gates (2026-11-23)

- Introduced an independent Go HTTP observer (`core.expected_event/0.1`) with file-backed local persistence, startup reconciliation and race-tested concurrent ingest.
- Added black-box 15-check HTTP + restart publication gate for **both** reference servers.
- Documented Core profile requirements, implementation boundaries, public release checks, and explicit Go scaling limitations.
- Preserved protocol identifier `vigilact/0.1-experimental`; no stable 1.0 claim.

# Changelog

All notable changes are documented here. Versions refer to the reference
implementation; the experimental wire protocol has a separate version.

## Unreleased — semantic conformance and research sprints (no protocol change)

- Added 14 public expected-event golden vectors and their JSON Schema, checked against the real Python service and an independent standard-library Go evaluator.
- Added CI cross-language comparison, documentation of vector limitations, and a repeatable observe-to-authorized-diagnostic demo.
- Added an ecosystem/prior-art review and adoption hypothesis document.
- No change to `vigilact/0.1-experimental` wire protocol; Go is not yet a full independent server.

## Unreleased — documentation (no protocol change)

- Added a searchable MkDocs documentation site with expanded guides, examples,
  API reference, security guidance and troubleshooting.
- Added docs validation in CI and optional GitHub Pages deployment.
- Added a tested end-to-end HTTP walkthrough, detailed evaluation/failure semantics,
  versioning, glossary, error catalog, FAQ and contributor docs workflow.
- Expanded documentation verification to include HTTP methods and broken links.
- Kept the documentation builder out of server runtime dependencies.

## 0.2.0a1 — Open source hardening (prepared, not yet released)

### Added

- Default-off remote command endpoints, with explicit server-side opt-in.
- Separate liveness (`/healthz`) and SQLite-backed readiness (`/readyz`) endpoints.
- Request body cap for declared-length and streaming HTTP requests.
- Problem Details-style error payloads without reflecting untrusted input.
- Independent HTTP conformance smoke runner against any accessible observer.
- Regression tests for deadline boundaries, disabled commands, malicious inputs,
  oversized bodies and idempotent references.
- GitHub Actions CI matrix, coverage gate, package builds and SHA-pinned actions.
- Dependabot, governance, release policy, contribution and protocol issue templates,
  citation metadata, compatibility rules and a maintainer checklist.

### Compatibility notes

- **Breaking runtime default:** command endpoints were usable when an operator
  and agent opted in; they now additionally require explicit server enablement.
- Error HTTP media type changed to `application/problem+json` while preserving
  the existing `error` extension field.
- **Protocol profile remains experimental 0.1**; the implementation version
  bump does not assert protocol stabilization.

## 0.1.0a1 — Initial experimental reference implementation

- Single expected-event contracts, SQLite observer, limited CloudEvents JSON
  evidence, opt-in capability advertisement, remote command queue and demo.

Earlier versions were provided as source archives; no GitHub or PyPI publication
is implied by this changelog.

