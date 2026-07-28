# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.4] - 2026-07-29

### Added

- Repository-wide guidance for AI coding assistants in `AGENTS.md`.
- Dedicated setup and troubleshooting guides for ChatGPT, Claude, VS Code, GitHub Copilot, and Cursor.
- Copy-ready prompt libraries for stock, options, earnings, portfolio, and pre-trade risk workflows.
- Contributor, security, conduct, issue, and pull-request documentation.
- A shared `QuantFinanceService` and credential-provider boundary used by every MCP transport.
- Local Streamable HTTP startup and an ASGI app factory alongside the existing stdio transport.
- Protocol, transport, schema, output, and service-layer regression tests.
- Automated MCP contract and release-manifest validation.
- Architecture, protocol audit, and Phase 2 migration documentation.
- MCP initialization instructions for cross-tool safety and workflow guidance.
- Native Streamable HTTP setup examples for Kimi Code, Codex, and GitHub Copilot CLI.
- An explicit enum for `generate_stock_images.types` and consistent `force` and `types` parameters in the self-hosted server.

### Changed

- Reorganized the README around a hosted-MCP-first installation path, clear product value, client compatibility, architecture, FAQ, and contribution guidance.
- Raised the minimum Official MCP Python SDK version to 1.27.2 and constrained it below version 2.
- Added schema-level parameter descriptions and object output schemas to all tools.
- Added `status` and `disclaimer` fields to successful object responses when absent.
- Marked structured service failures as MCP tool execution errors while preserving their existing payload.
- Expanded CI with Ruff lint/format checks, protocol validation, schema validation, and the Python version test matrix.

## [0.5.3] - 2026-07-23

### Added

- Explicit boolean `idempotentHint` annotations to all nine MCP tools for client and app-review compatibility.
- Regression tests that reject missing, null, or non-boolean tool annotation hints.

### Changed

- Corrected `generate_stock_images` and `generate_stock_research_report` annotations: both create non-destructive, non-idempotent external artifacts and may consume metered quota.
- Standardized the official remote endpoint as `https://hpsilab.com/mcp` across manifests, examples, and documentation.

## [0.5.2]

### Added

- Package-level `__version__` derived from installed metadata.

## [0.5.1]

### Added

- Official MCP Registry manifest.
- Improved tool descriptions for agent tool selection.
- Explicit response schemas and input validation.
- Consistent error handling for authentication, rate limiting, payment, timeout, connection, HTTP, and JSON failures.

## [0.5.0]

### Added

- `readOnlyHint`, `destructiveHint`, and `openWorldHint` annotations for all nine MCP tools.

## [0.4.1]

### Added

- `get_pretrade_risk_scan`.

[Unreleased]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/compare/v0.5.4...HEAD
[0.5.4]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/releases/tag/v0.5.4
[0.5.3]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/releases/tag/v0.5.3
[0.5.2]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/releases/tag/v0.5.2
[0.5.1]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/releases/tag/v0.5.1
[0.5.0]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/releases/tag/v0.5.0
[0.4.1]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/releases/tag/v0.4.1
