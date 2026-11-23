# Troubleshooting

## The server refuses to start

**`Set VIGILACT_CREDENTIALS_JSON`** — create explicit `agent` and/or `operator` credentials. Names must be safe ASCII, roles must be `agent` or `operator`, and keys must be at least 16 characters.

**A key or JSON object is invalid** — validate the environment JSON. In shell environments, quote it as a single string.

## HTTP 401 / 403

- `401`: missing or invalid principal/key pair.
- `403`: a valid identity lacks the required role, is accessing another agent's resource, or the command feature is disabled.
- `commands_disabled`: the reference observer requires explicit opt-in and a restart. Only enable commands on isolated test networks.

## HTTP 409 / 413 / 422

- `409 reference_conflict`: reused a `client_ref` with different contract terms. Choose a new reference for a new one-shot occurrence.
- `409 event_conflict`: reused `(source, id)` with a different evidence payload.
- `413 payload_too_large`: reduce JSON size; the default is 262144 bytes.
- `422 validation_error`: input does not match the strict schema; check required fields and timezone-aware dates.

Problem responses have `Content-Type: application/problem+json` and a short experimental `error` identifier. See [HTTP API](../protocol/http-api.md).

## My contract says `NOT_OBSERVED` even though the job ran

The observer evaluates **received evidence before the deadline**, not whether the underlying task ran. Check network connectivity, event `source`, `type`, `subject`, receiver clock, and deadline. An agent-generated `time` cannot make a late arrival on time.

## No evaluation in the outbox

Use operator credentials, query the correct sequence cursor, and ensure the observation is resolved. The periodic sweep runs every five seconds by default; check `VIGILACT_SWEEP_SECONDS`. At startup, pending overdue contracts are reconciled.

## A claimed command never finishes

The experimental observer does **not** automatically requeue claimed commands. Inspect the agent rather than creating a blind retry: the action may have executed even if its result was not reported.

## The website or GitHub Pages is missing

The source docs do not publish themselves. Merge the documentation workflow, choose **Settings → Pages → Build and deployment → GitHub Actions**, then inspect the `Docs` workflow logs. Before publication, the suggested `vigilact.atellaluca.com` URL is not a verified live website.
