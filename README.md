<div align="center">

<img src="https://raw.githubusercontent.com/atellaluca/vigilact/main/docs/assets/vigilact-readme-banner.png" alt="Vigilact — stylized V logo and wordmark" width="100%" />

# Vigilact

**Declare commitments. Observe evidence. Act with permission.**

A small, open protocol experiment for **negotiated operational contracts** between software systems.

[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Status: experimental](https://img.shields.io/badge/status-experimental-orange.svg)](ROADMAP.md)
[![CI](https://github.com/atellaluca/vigilact/actions/workflows/ci.yml/badge.svg)](https://github.com/atellaluca/vigilact/actions/workflows/ci.yml)

</div>

> **Alpha / research implementation.** The wire format and semantics may change. Do not deploy on production networks, or expose the reference server publicly without additional hardening.

## What problem does it solve?

Applications often know **what should happen**, but monitoring services only see **what did happen**. Each integration reinvents deadlines, missing-event alerts, retries and remote diagnostics.

Vigilact experiments with a reusable agreement:

1. An agent **proposes** an operational commitment to an observer.
2. The observer **accepts** supported terms and persists them.
3. The agent publishes **evidence**; the observer evaluates whether it arrived on time.
4. The observer emits a **neutral evaluation event** (not an email, push or alert).
5. The agent may separately **advertise capabilities** that an authorized operator may request.

```text
       software / agent                       observer
       ───────────────                       ────────
          propose contract ──────────────────> accept + persist
          publish evidence ──────────────────> evaluate commitment
                                               │
          publish capabilities ──────────────> registry
          poll authorized commands <────────── operator queue
                                               │
                                               ▼
                                         CloudEvents outbox
                                               │
                            any notification, audit or automation adapter
```

**Two independent Core observers are now available (Python and Go).** Run `poetry run python scripts/test_observers.py` to exercise the same 22 black-box HTTP/restart checks against each one. The Go observer implements only `core.expected_event/0.1`, not the optional Python agent capabilities or command queue. See [`implementations/go-observer/README.md`](implementations/go-observer/README.md) and the [Core profile draft](spec/CORE_EXPECTED_EVENT.md).

**This is not a notification service.** Vigilact does not send email, Telegram or push notifications. It can publish evaluation events that other products — including LTG Notify, if desired — consume independently.

## Quickstart with Poetry

**Environment:** Poetry 2.5.2 manages all Python dependencies using `pyproject.toml`. A checked-in `poetry.lock` is required for exact-version installs; see [Poetry migration status](POETRY_MIGRATION.md).

Requires Python 3.11–3.13 and Poetry 2.5.2. The first dependency resolution requires access to PyPI; subsequent environments can be synchronized against the committed `poetry.lock`.

```bash
# Once, while the initial poetry.lock is being prepared: poetry lock
poetry sync --all-groups --all-extras
poetry run python examples/quickstart.py
poetry run pytest -q
poetry run python scripts/export_specs.py  # regenerate OpenAPI and JSON Schemas
```

The deterministic demo exercises **successful evidence**, **a missed deadline**, **opt-in agent capabilities**, **an authorized remote command**, and **CloudEvents output**. It runs in-process, uses a disposable SQLite database and opens no network sockets.

Sample output:

```text
1. Contract accepted: <generated UUID>
2. Agent capabilities registered
3. Evidence received: accepted satisfied: 1
4. Missing evidence outcome: NOT_OBSERVED
5. Authorized command acknowledged: SUCCEEDED
6. Neutral event log:
   - dev.vigilact.observation.satisfied
   - dev.vigilact.observation.not_observed

DEMO COMPLETE — no notification service required.
```

## Run the reference HTTP server

This example uses **local development credentials only**. Replace them with strong, unique secrets; use TLS in front of the server, and do not expose it to the internet as-is.

```bash
export VIGILACT_CREDENTIALS_JSON='{"backup-agent":{"role":"agent","key":"change-me-agent-unique-secret-123"},"ops":{"role":"operator","key":"change-me-operator-unique-secret-123"}}'
export VIGILACT_DB_PATH=./vigilact.sqlite3
poetry run uvicorn 'vigilact.server:create_app' --factory --host 127.0.0.1 --port 8000
```

On another terminal:

```bash
curl -fsS http://127.0.0.1:8000/v1/info
```

Explore the interactive API at `http://127.0.0.1:8000/docs` and the generated OpenAPI contract at `/openapi.json`.

### Example: propose an expected event

```bash
# Edit the deadline to a future UTC timestamp.
curl -X POST http://127.0.0.1:8000/v1/contracts \
  -H 'Content-Type: application/json' \
  -H 'X-Vigilact-Principal: backup-agent' \
  -H 'X-Vigilact-Key: change-me-agent-unique-secret-123' \
  -d '{
    "client_ref":"nightly-backup-001",
    "subject":"backup://node-1",
    "observation":{
      "kind":"expected_event",
      "event_type":"backup.completed",
      "deadline_at":"2030-01-01T02:30:00Z"
    }
  }'
```

A corresponding event uses the CloudEvents JSON envelope (restricted v0.1 profile):

```json
{
  "specversion": "1.0",
  "id": "job-nightly-001",
  "source": "urn:vigilact:agent:backup-agent",
  "type": "backup.completed",
  "subject": "backup://node-1",
  "data": {"duration_seconds": 42}
}
```

Submit it to `POST /v1/events` with the same agent credentials **before the deadline**. An operator can read derived events from `GET /v1/outbox?after=0`. The demo shows the complete sequence without manually preparing credentials or dates.

## See the protocol boundaries in action

The [observe-and-act example](examples/observe_and_act.py) shows an accepted
contract, a **missed** observation, a neutral evaluation event, and an
**explicitly authorized** diagnostic capability. It does not send a notification
or execute arbitrary remote code.

```bash
PYTHONPATH=src python examples/observe_and_act.py
```

We also publish [14 deterministic semantic vectors](spec/vectors/expected-event.json).
The actual Python reference service and an **independent Go semantic evaluator**
pass the same traces. The independent Go observer now also implements the HTTP Core profile; run
`poetry run python scripts/test_observers.py` to exercise the same black-box suite across
Python and Go. It is **not** a full-featured or independently certified observer.

```bash
PYTHONPATH=src python scripts/expected_event_vectors.py --check
go run ./implementations/go-vector-evaluator/main.go --check
```

See the [ecosystem/prior-art review](research/ECOSYSTEM_2026-11.md) and
[adoption hypothesis](research/ADOPTION_EXPERIMENT.md). These documents
explicitly distinguish engineering proof from market validation.

## What's actually supported in this alpha?

| Feature | Status |
|---|---|
| Explicit proposal + server acceptance/rejection | ✅ Implemented |
| One-shot `expected_event` observation | ✅ Implemented |
| Durable SQLite contract/outbox/command state | ✅ Python implementation |
| Independent Go HTTP Core observer | ✅ Implemented (limited Core) |
| Agent-scoped CloudEvents JSON evidence | ✅ Implemented (subset) |
| Server receipt-time deadlines and late-event handling | ✅ Implemented |
| Client reference and event idempotency | ✅ Implemented |
| Agent capability advertisement | ✅ Implemented |
| Opt-in command queue, claim, result, TTL, unknown-outcome handling | ✅ Python-only extension |
| Full counter-proposals and revisions | ◻️ Planned |
| Cron, recurring windows, thresholds, multi-agent contracts | ◻️ Planned |
| Command TTL + claim leases to `UNKNOWN` | ✅ Python-only experimental |
| Automatic retry/requeue of uncertain effects | ❌ Deliberately unsupported |
| Federation, SLA enforcement, production-grade security | ◻️ Out of scope for alpha |

The one-shot observation is deliberately narrow. **`NOT_OBSERVED` means evidence was not received by the server before its deadline; it does not prove the underlying operation failed.** Event timestamps submitted by agents do not override receipt time.

## Reproduce the engineering evidence

Beyond the basic smoke suite, a seeded two-agent HTTP scenario runner tests
**tenant isolation**, **idempotent evidence**, **outbox cardinality**, and
**behavioral agreement** across the independently implemented Python and Go
observers. Deliberate SQLite exception injection verifies transaction rollback
at the contract/evaluation/outbox boundary.

```bash
poetry run python -m pytest -q
poetry run python scripts/test_observers.py --differential-cases 12 --seed 20261123 \
  --load 25 --report artifacts/core-evidence.json
```

The report includes a reproducible seed and a SHA-256 digest of the normalized
observed behaviors. **Matching traces demonstrate a bounded set of properties,
not complete semantic equivalence**. See [Engineering proof](docs/reference/engineering-evidence.md)
for assumptions, limits, and reproducibility.

## Documentation

**Documentation source:** [docs/index.md](docs/index.md) · [Five-minute HTTP demo](docs/getting-started/five-minute-demo.md) · [Evaluation semantics](docs/concepts/evaluation-semantics.md) · **Proposed GitHub Pages address (available only after deployment):** `https://vigilact.atellaluca.com/`.

Build a searchable local documentation site:

```bash
poetry sync --all-groups --all-extras
poetry run python scripts/check_docs.py
poetry run python scripts/check_pages_config.py
poetry run mkdocs build --strict
poetry run mkdocs serve
```

The custom domain must also be configured in **Settings → Pages → Custom domain**
and the DNS CNAME must point to `atellaluca.github.io`; a repository `CNAME`
file is ignored by GitHub Actions publishing. See [Pages deployment](docs/maintainers/github-pages.md).

The tested `examples/http_contract_demo.py` script demonstrates real HTTP calls with dynamic deadlines. The `Docs` GitHub Actions workflow checks links and navigation, builds the site, and can deploy to GitHub Pages after the repository owner enables **Settings → Pages → GitHub Actions**. MkDocs is intentionally kept out of the runtime dependencies.

- [Protocol draft and HTTP binding](spec/PROTOCOL.md)
- [Architecture and design decisions](spec/ARCHITECTURE.md)
- [Security model and limitations](SECURITY.md)
- [Conformance rules](spec/CONFORMANCE.md)
- [Roadmap and good first issues](ROADMAP.md)
- [Changelog](CHANGELOG.md)
- [Contributor guide](CONTRIBUTING.md)
- [Developer launch plan](spec/LAUNCH.md)
- [Generated OpenAPI document](api/openapi.json)
- [JSON Schemas](schemas/)

## Design principles

**Protocol-first.** A future Go, Rust, Node or embedded implementation must be able to interoperate without importing Python code.

**Contract ≠ connection.** Agreements are durable even while agents disconnect.

**Evidence ≠ truth.** Observations report what can be inferred from received evidence.

**Capability ≠ authorization.** Advertising a function does not permit it to be invoked. Commands additionally need operator authorization, opt-in and an agent-side allow-listed handler.

**Effects are external.** Observations produce neutral events that independent services can route, audit or notify on.

**Small, testable core.** We prefer proving precise semantics over claiming universal coverage.

## Standards and prior art

Vigilact builds on the [CloudEvents 1.0](https://github.com/cloudevents/spec) envelope rather than inventing a new event wire format. Its API is described by [OpenAPI](https://www.openapis.org/), and its input models have [JSON Schema](https://json-schema.org/) representations. Operational agreements are an established research area; see [WS-Agreement](https://www.ogf.org/documents/GFD.107.pdf) as related prior art. These projects do **not** endorse Vigilact.

## Contribute

We particularly welcome feedback on deadline semantics, independent implementations, multiple evidence producers and capability security. Open a design issue with a concrete use case, expected behavior and failure case; see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0. Copyright © 2026 Luca Atella. See [LICENSE](LICENSE).

Vigilact is an independent open source project; it does not require LTG Notify or any notification backend.

## Open source project status — implementation 0.4.0a2

This source distribution expands command safety, cross-language conformance,
documentation deployment and operational checks without
changing the **experimental `vigilact/0.1-experimental` protocol**. It is not a
1.0 standard, certified implementation, secure network appliance or high
availability production system.

### Safer defaults

The reference server now **disables remote command endpoints by default**.
To enable them *only for an isolated, trusted development environment*, set
`VIGILACT_ENABLE_COMMANDS=true`. Agent capabilities and operator credentials
are still required; enabling this does not create a comprehensive authorization
system. A request body size limit of 256 KiB is applied by default, including to
streamed requests; adjust via `VIGILACT_MAX_REQUEST_BYTES` if needed.
Validation failures return `application/problem+json` without echoing request
payloads. See [Security](SECURITY.md) and [Errors](spec/ERRORS.md).

### Test an independent observer over HTTP

Vigilact ships a conformance **smoke** tool that makes only public HTTP calls,
without importing the reference server or its SDK:

```bash
export VIGILACT_CONFORMANCE_AGENT_KEY='your-test-agent-key'
export VIGILACT_CONFORMANCE_OPERATOR_KEY='your-test-operator-key'
python scripts/conformance_http.py --url http://127.0.0.1:8000 \
  --agent backup-agent --operator ops
```

Run it only against a disposable test observer. It creates synthetic contracts,
events and outbox entries. Passing this check does **not** establish full
independent-implementation conformance.

### Repository maintenance

- [Governance and decision-making](GOVERNANCE.md)
- [Contribution instructions](CONTRIBUTING.md)
- [Support policy](SUPPORT.md)
- [Protocol version compatibility](spec/COMPATIBILITY.md)
- [Release and supply-chain checklist](RELEASING.md)
- [Open source readiness audit](OPEN_SOURCE_READINESS.md)
- [Issue and protocol proposal templates](.github/ISSUE_TEMPLATE/)

Automated CI is configured for Python 3.11–3.13, coverage, smoke conformance,
static checks, packaging and generated specification review. Enabling GitHub
branch protection and private security advisories still requires repository
owner action. The source archive itself is not a live GitHub repository.

For basic local diagnostics use `/healthz` (process liveness) and `/readyz`
(storage readiness). A healthy response does not imply production availability
or clock accuracy.

## Release 0.4.0a2 engineering checks

Both reference observers pass the same restricted Core HTTP conformance tests.
The optional Python command extension has expiry and lease-state regressions,
but is intentionally **not** in the Go Core profile.

```bash
poetry run python scripts/test_observers.py --load 25  # isolated disposable local stores
python scripts/backup_sqlite.py --db vigilact.sqlite3 --output ./backup.sqlite3
```

The load smoke is a bounded demonstration, not a throughput guarantee.
See [release evidence](docs/reference/release-evidence.md),
[command lifecycle](docs/protocol/command-lifecycle.md) and the
[threat model](docs/reference/threat-model.md).


## Project maintainer & contact

Vigilact is maintained by [Luca Atella](https://profile.atellaluca.com/). For technical contributions, use [GitHub issues](https://github.com/atellaluca/vigilact/issues) and the contribution guide. For collaborations, contact [info@atellaluca.com](mailto:info@atellaluca.com).

[Personal GitHub](https://github.com/atellaluca) · [LinkedIn](https://www.linkedin.com/in/luca-atella/) · [Professional profile](https://profile.atellaluca.com/) · [Documentation](https://vigilact.atellaluca.com/)

---

<div align="center">
  <img src="https://raw.githubusercontent.com/atellaluca/vigilact/main/docs/assets/vigilact-logo.svg" alt="Vigilact logo" width="96" />
  <p><small>Vigilact · Apache-2.0 · <a href="https://profile.atellaluca.com/">Luca Atella</a> · <a href="mailto:info@atellaluca.com">Contact</a> · <a href="https://github.com/atellaluca">GitHub</a> · <a href="https://www.linkedin.com/in/luca-atella/">LinkedIn</a></small></p>
</div>
