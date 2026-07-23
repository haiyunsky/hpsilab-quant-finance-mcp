# Repository Guidance for AI Coding Assistants

## Project mission

HPSILab Quant Finance MCP gives MCP-compatible assistants a stable, auditable interface for quantitative research on US equities and options. The project should make sophisticated analysis easier to access without presenting research output as investment advice or enabling trade execution.

Production quality means more than adding tools. Favor correctness, interoperability, predictable schemas, clear documentation, safe failure modes, and a low-friction installation experience.

## Scope and architecture

- `src/hpsilab_quant_finance_mcp/server.py` defines the MCP tool surface and delegates API calls to the published `hpsilab-mcp` Python SDK.
- The SDK is the source of truth for hosted REST paths and methods. Do not duplicate its HTTP implementation here.
- `server.json` is the publication manifest for the Official MCP Registry.
- `manifest.json` and `glama.json` serve other MCP catalogs.
- `README.md`, `docs/`, and `examples/` are user-facing product surfaces and must match the released behavior.

## Design principles

1. Prefer a small, coherent, well-documented tool surface over feature count.
2. Preserve structured outputs. Clients and agents must be able to consume results without parsing prose.
3. Make safe behavior explicit. This server performs research and does not execute trades.
4. Fail predictably with actionable, machine-readable errors.
5. Keep the remote Streamable HTTP service and local stdio package behavior clearly distinguished.
6. Treat interoperability as a release requirement, not a best-effort feature.
7. Avoid claims that cannot be verified from the implementation, tests, or published service.

## Coding standards

- Support the Python versions declared in `pyproject.toml`.
- Use type annotations for public functions and MCP tool parameters.
- Validate user input at the MCP boundary. Ticker symbols must use the existing normalization and validation path.
- Reuse shared helpers for authentication, errors, API dispatch, and annotations.
- Keep tool functions thin; API transport belongs in `hpsilab-mcp`.
- Do not log API keys, authorization headers, account data, or full sensitive responses.
- Use descriptive names and concise docstrings. Document units, ranges, time horizons, and nullable fields.
- Add or update tests for every observable behavior change.
- Run `python -m unittest discover -s tests` before requesting review.
- Do not reformat or rewrite unrelated files in a focused change.

## MCP compatibility requirements

- Remain compatible with the Official MCP Python SDK and its supported protocol version.
- Preserve both published transports: Streamable HTTP for the hosted endpoint and stdio for the PyPI package.
- Keep `server.json` valid against its declared Official MCP Registry schema.
- Tool input schemas must be valid JSON Schema and usable by ChatGPT, Claude, VS Code, GitHub Copilot, Cursor, Continue, and Kimi.
- Every tool must have accurate boolean `readOnlyHint`, `destructiveHint`, `idempotentHint`, and `openWorldHint` annotations.
- Tools that create hosted artifacts or consume quota must not be described as read-only or idempotent.
- Initialization metadata, advertised package version, manifests, and documentation must agree.
- Never depend on client-specific prompt syntax for core functionality.

## Tool design guidelines

- Do not add a tool when an existing tool can express the use case with a backward-compatible optional parameter.
- Each tool description must state when to use it, when to prefer another tool, required inputs, output semantics, and relevant side effects.
- Use stable snake_case tool names and parameter names.
- Prefer one ticker per call unless a separately reviewed batch contract is introduced.
- Return dictionaries with stable keys. Additive optional fields are preferred over shape changes.
- Include units and horizons in field names or documentation.
- Return the shared research disclaimer where appropriate.
- Do not implement brokerage connectivity, order entry, or autonomous trade execution in this repository.

## Documentation requirements

- The README first screen must state the product value, supported market scope, remote endpoint, and fastest setup path.
- Every supported client guide must include installation, configuration, a verification prompt, and troubleshooting.
- Examples must be realistic, copy-ready, and must not promise unavailable data or guaranteed returns.
- Use `https://hpsilab.com/mcp` as the canonical remote endpoint.
- Clearly distinguish remote MCP setup, local stdio installation, and the separate REST SDK.
- Never commit real API keys. Use `hpsi_your_key` or environment-variable placeholders.
- Keep tool names, package names, versions, pricing/access statements, and tool counts synchronized across all documentation and manifests.
- Link to canonical detailed guides instead of duplicating large, client-specific sections in the README.

## Backward compatibility rules

- Do not rename or remove a released tool, parameter, response field, console script, environment variable, package, or registry identifier in a minor or patch release.
- Do not change a parameter's meaning, default, accepted unit, or required status without a major-version migration plan.
- New response fields must be additive and safe for clients that ignore unknown keys.
- New parameters should be optional and have behavior-preserving defaults.
- Deprecations require documentation, a changelog entry, runtime guidance where appropriate, and at least one minor release before removal.
- Authentication, transport, and endpoint changes require explicit migration documentation and compatibility testing.

## Release workflow

1. Start from a clean branch and record the intended user-visible change.
2. Update implementation and tests together when behavior changes.
3. Run the full test suite and validate `server.json` with the current MCP publisher.
4. Verify local stdio initialization, `tools/list`, and representative tool calls.
5. Smoke-test the hosted endpoint and the documented setup for affected clients.
6. Update `README.md`, relevant files in `docs/` and `examples/`, and `CHANGELOG.md`.
7. Keep the version synchronized in `pyproject.toml`, `server.json`, and `manifest.json`.
8. Build and inspect the Python source distribution and wheel.
9. Publish the Python package before publishing matching metadata to the Official MCP Registry.
10. Create a signed or otherwise auditable Git tag and GitHub release from the changelog entry.
11. Verify the released PyPI package, registry listing, remote endpoint, and installation instructions after publication.

Patch releases are for backward-compatible fixes and documentation. Minor releases may add backward-compatible capability. Breaking changes require a major release and a documented migration path.

