# Contributing to HPSILab Quant Finance MCP

Thank you for helping make quantitative research through MCP more reliable and accessible. Contributions are especially welcome in interoperability, testing, documentation, error handling, and developer experience.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Before opening a change

- Search existing issues and pull requests.
- Use a discussion or issue before proposing a new tool, changing a schema, or altering authentication or transport behavior.
- Read [AGENTS.md](AGENTS.md), which defines the repository's design and compatibility contract.
- Report vulnerabilities privately according to [SECURITY.md](SECURITY.md).

Small documentation and test fixes can go directly to a pull request.

## Development setup

Requirements:

- Python 3.10, 3.11, or 3.12
- Git
- An HPSILab API key only for live integration testing

Create an isolated environment and install the package in editable mode:

```bash
python -m venv .venv
```

Activate it, then run:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

Never commit `.env` or a real `HPSILAB_API_KEY`.

## Running tests

The unit suite must not require live credentials:

```bash
python -m unittest discover -s tests
```

When changing packaging, also build and inspect the distributions in an isolated environment:

```bash
python -m pip install build
python -m build
```

Live checks are optional for contributors and must use a personal test account. Do not include private responses, account identifiers, or keys in issues or CI logs.

## Change guidelines

### MCP tools

- Do not rename released tools or parameters.
- Prefer optional, additive parameters with behavior-preserving defaults.
- Keep tool descriptions specific enough for autonomous selection.
- Document units, horizons, nullability, and side effects.
- Apply accurate MCP annotations and add regression coverage.
- Keep REST transport logic in the `hpsilab-mcp` SDK rather than duplicating it here.

### Documentation

- Use the canonical endpoint `https://hpsilab.com/mcp`.
- Distinguish hosted HTTP, local stdio, and the separate REST SDK.
- Test commands and JSON snippets before submitting them.
- Use placeholder credentials such as `hpsi_your_key`.
- Avoid performance, accuracy, coverage, or pricing claims that cannot be verified.
- Keep examples research-oriented and avoid guaranteed-return or personalized trading language.

## Commit and pull-request expectations

Keep commits focused and use an imperative summary, for example:

```text
docs: clarify Cursor authentication setup
test: cover invalid ticker normalization
fix: preserve structured timeout errors
```

A pull request should:

- explain the user problem and why the change belongs here;
- identify compatibility and security effects;
- include tests for observable runtime changes;
- update affected documentation and `CHANGELOG.md`;
- avoid unrelated formatting or refactoring;
- pass CI on every supported Python version.

Maintainers may ask for a smaller scope or a migration plan when a proposal affects the public MCP contract.

## Release responsibility

Only maintainers publish packages, Registry metadata, tags, or releases. The required sequence and verification steps are documented in [AGENTS.md](AGENTS.md#release-workflow).

