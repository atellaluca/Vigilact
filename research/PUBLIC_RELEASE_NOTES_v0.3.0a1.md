# Release notes draft — Vigilact 0.3.0a1

**First multi-implementation Core alpha — not production-ready**

Vigilact lets a client propose a time-bounded operational commitment to an
observer, then publish evidence that the observer evaluates. The observer
records a durable outcome and a transport-neutral CloudEvents-style evaluation
event without providing a notification service.

### What's new

- **Independent Go HTTP observer** implementing `core.expected_event/0.1`
  using only the Go standard library.
- **Two implementations / one black-box suite:** 15 passing HTTP and restart
  checks per observer in local tests.
- Startup recovery, detection of missing events, deduplication and append-only
  outbox verified for both implementations.
- New behavior-profile draft, implementation guide and CI publication gate.
- Python API and optional commands remain experimental and versioned separately
  from the protocol identifier.

### Run the demonstration

```bash
python -m pip install -e '.[dev]'
python scripts/test_observers.py
```

Requires Go 1.23+ installed. Read `spec/CORE_EXPECTED_EVENT.md` and
`SECURITY.md` before trying the observer on your own systems.

### What this is not

This is **not** a universal contract language, not a notification dispatcher,
not a workflow engine, and not suitable for public internet or production
networks. The Go implementation is single-process JSON-snapshot storage.
Please open issues for protocol design review and concrete integration needs.
