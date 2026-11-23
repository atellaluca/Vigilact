# Help improve Vigilact

Vigilact needs **protocol scrutiny** more than feature count. Reviews of failure semantics, idempotency boundaries and security are especially valuable.

## Good first contributions

- Test contradictory or duplicate evidence under reconnects.
- Add transport-neutral conformance fixtures.
- Improve examples in another language.
- Report ambiguous contract semantics with a failing test.
- Expand documentation with verified reproduction steps.

## Documentation workflow

```bash
poetry sync --all-groups --all-extras
poetry run python scripts/check_docs.py
poetry run mkdocs build --strict
poetry run mkdocs serve
```

Edit pages under `docs/`; `mkdocs.yml` owns the navigation. Follow the [maintainer documentation workflow](../maintainers/docs-workflow.md). For behavior claims, compare the page with source code, the protocol draft and the generated OpenAPI document. Avoid presenting planned features as implemented.

## Proposing protocol changes

Start with a GitHub issue using the *Protocol proposal* template. Include motivation, concrete example, error semantics, security impact, compatibility costs, negative test cases and how an independent implementation could validate the behavior.

The repository also includes contributor conduct guidelines, governance decisions, a support policy and release procedures:

- [CONTRIBUTING.md](https://github.com/atellaluca/vigilact/blob/main/CONTRIBUTING.md)
- [GOVERNANCE.md](https://github.com/atellaluca/vigilact/blob/main/GOVERNANCE.md)
- [CODE_OF_CONDUCT.md](https://github.com/atellaluca/vigilact/blob/main/CODE_OF_CONDUCT.md)
- [ROADMAP.md](https://github.com/atellaluca/vigilact/blob/main/ROADMAP.md)

## Release and compatibility

Documentation changes that affect wire semantics should update the normative spec, API/JSON Schemas, conformance tests and changelog in the **same pull request**. Current releases remain alpha and may break compatibility.

For disclosure of a security vulnerability, follow [Security and limitations](security.md) rather than filing a public exploit issue.
