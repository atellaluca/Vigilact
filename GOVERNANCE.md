# Project governance

Vigilact is an independent, experimental open source project. **Luca Atella
([@atellaluca](https://github.com/atellaluca)) is its initial maintainer.**
No foundation, standards organization or third-party endorsement is claimed.

## Decisions and authority

- The maintainer merges contributions and approves releases. A review request is
  not a promise of merge, support, or a response within a fixed time.
- Changes affecting wire compatibility, authorization, observation semantics or
  required transports need a public design proposal and an architecture decision
  record (ADR) before stabilization.
- The project favors documented trade-offs, reproducible tests and independent
  implementations over feature count.
- In the absence of consensus, the maintainer records the decision and rationale
  publicly in the associated issue or ADR, except for private security reports.

## Contributions and intellectual property

Contributions are welcome under the repository's Apache-2.0 license.
Contributors retain the copyright to their contributions. No CLA, automatic
copyright assignment or exclusive licensing rights are requested at this time.
Contributors must have the right to submit their work; do not copy incompatible
code or confidential third-party specifications.

## Release model

Pre-1.0 versions are experimental. The reference server version and protocol
profile version are **separate**: an implementation update does not automatically
change the protocol's wire-level semantics. See [Compatibility](spec/COMPATIBILITY.md)
and [Releases](RELEASING.md).

## Security and behavior

Security reports follow [SECURITY.md](SECURITY.md). Community participation
follows [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Growing the project

If independent implementations and contributors emerge, governance can evolve
through a public proposal, including adding maintainers, review quorum and a
formal process for protocol decisions. No neutral standards body is asserted yet.
