# Compatibility and protocol versions

Vigilact has **two independent version dimensions**:

- **Implementation version**: Python package version (PEP 440), currently
  `0.4.0a1`.
- **Protocol profile**: advertised in `GET /v1/info`, currently
  `vigilact/0.1-experimental` with the profile identifiers reported there.

The HTTP `/v1` route prefix is not a claim of a ratified v1 specification.
The full supported HTTP/JSON shapes and their semantic rules are described in
[PROTOCOL.md](PROTOCOL.md). The server MUST advertise the actual capabilities
it enables; in particular, remote command endpoints are disabled by default.

## Policy prior to protocol stabilization

- No backwards compatibility guarantee is made between experimental wire
  revisions. Every intentional breaking change must be documented in CHANGELOG.
- Implementations SHOULD perform feature discovery using `/v1/info` rather
  than assuming that an endpoint is enabled or that a proposed contract can
  be accepted.
- A client MUST handle rejection, disconnection, duplicate events, unknown
  errors and non-support for optional profiles.
- Unknown JSON input fields are rejected by the current reference server.
  Do not depend on implicit field extension or partial schema acceptance.
- Contract ownership and event receipt-time semantics are part of the current
  narrow profile and must not be inferred to extend to cross-party agreements.

## How changes become normative

1. Publish a design proposal defining new wire objects, meaning and failure cases.
2. Document independent implementation tests and security implications.
3. Add a versioned profile identifier and migration guidance where required.
4. Update OpenAPI/JSON Schema and shared conformance fixtures in the same change.
5. Demonstrate two independent implementations before advertising a stable profile.

The presence of an SDK does not make it normative; the written specification
and publicly observable conformance behavior take precedence.
