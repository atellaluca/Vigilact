# Run the independent Go observer

Vigilact has two independent HTTP observers for the experimental
`core.expected_event/0.1` profile. The Go implementation does **not** import
any Python code and uses only Go's standard library.

See [Go implementation notes](https://github.com/atellaluca/vigilact/blob/main/implementations/go-observer/README.md)
for installation and limitations, or run the project-wide publication gate:

```bash
poetry sync --all-groups --all-extras
poetry run python scripts/test_observers.py
```

This command compiles the Go implementation, starts both servers on local
loopback addresses, executes the *same* black-box contract/event/outbox test
suite and verifies that their state survives a process restart.

Each implementation should pass 15 checks: 11 HTTP conformance checks,
plus 4 recovery/late-event checks. The gate does not test optional agent
capability and remote-command endpoints, which the Go server does not expose.

## Verify the Go source independently

```bash
cd implementations/go-observer
go test -race ./...
go build ./...
```

The observer is intentionally single-process and file-backed. It is a research
reference, not a service recommended for public or production exposure.
The [Core profile draft](../concepts/core-profile.md) explains the guaranteed
behavior and the limits of this claim.
