# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.9.0] - 2026-08-09

Alignment with the hosted error contract that took effect on 2026-08-08, when
Credits became the unit of entitlement. Three responses this package could not
previously tell apart — "wait", "top up", and "pay for this call" — now arrive
as three error codes with three different remedies.

### Fixed

- **Every non-2xx response was being reported as an untyped `http_error`** for
  anyone running `hpsilab-mcp` 0.13.0 or later, which the previous dependency
  floor (`>=0.12.2`) allowed. `QuantFinanceClient._raise_for_status` restated
  the signature it was overriding, so the `payment_refusal=` argument the SDK
  began passing in 0.13.0 raised `TypeError` before the response could be
  classified: no status code, no typed exception, and no bounded retry on 429.
  The override now forwards whatever the SDK passes.
- A payment challenge no longer latches the whole process shut. A 402 offer is
  a price, not a bad credential — the SDK stopped treating it as an
  authentication failure in 0.13.0, and mirroring that failure here locked a
  caller with a valid key out of every free tool after it touched a priced one.

### Added

- `insufficient_credits` — an empty Credit balance (HTTP 402,
  `error: "insufficient_credits"`) is reported under its own error code with
  `credits_required`, `credits_remaining`, `credits_charged: 0`, and a
  `next_actions` list. It never trips the local authentication circuit: the key
  is valid, and the call made right after Credits are added has to reach the
  network instead of being refused locally.
- `settlement_unknown` — a payment the API cannot confirm is reported with
  `x402_status: "settlement_unknown"`, the `call_id` a reconciliation run
  needs, and a deliberately empty `next_actions`. It is not retried and no
  offer is attached: a retry signs a second authorization for one logical call.
- `next_actions`, the canonical machine-readable conversion layer, on local
  refusals and passed through from the hosted API.

### Changed

- **429 responses no longer carry registration or upgrade guidance.** The
  `upgrade` and `next_action` objects added in 0.8.10–0.8.13 are gone from
  locally generated rate limits. A 429 is resolved by waiting; selling a plan
  to a caller whose problem clears itself inside a minute points at the wrong
  remedy. The hosted API removed the same fields from its own 429 on
  2026-08-08. Hosted 429 bodies are still passed through unchanged.
- **Day-scoped local quotas are removed** (100 requests per UTC day, 20 per
  tool per UTC day). They copied the requests-per-day gates the hosted API
  retired on 2026-08-08, in the one place that can see neither a balance nor a
  plan: a Developer key (60 rpm) or a Pro key (300 rpm, 15,000 Credits) was
  refused at the Free tier's numbers for the rest of the UTC day without a
  request ever leaving the process. What remains is burst protection: 10
  requests per rolling minute per API key.
- `FreeTierQuotaLimiter` is now `BurstRateLimiter`, `QuotaExceeded` is
  `RateLimited`, and `FREE_REQUESTS_PER_MINUTE` is `LOCAL_REQUESTS_PER_MINUTE`.
  The removed day-scoped constants have no replacement.
- Batch calls stop on an empty balance and on an unresolved settlement, not
  only on authentication failures. The second may arrive with no status code
  at all, so it is matched by error code.
- Minimum `hpsilab-mcp` raised to 0.13.5 for `HpsiMcpInsufficientCreditsError`,
  `HpsiMcpSettlementUnknownError`, and one `X-Request-Id` per logical call.

## [0.8.13] - 2026-08-08

### Fixed

- Preserved backend quota metadata and additive registration/Pro upgrade
  guidance when translating downstream HTTP 429 responses into MCP results.
- Fixed the test import ordering required by the GitHub Actions Ruff check.

## [0.8.12] - 2026-08-07

### Changed

- Synchronized package, source-checkout, documentation, and registry manifest
  version metadata for the 0.8.12 patch release.
- Added additive `next_action` registration and Pro upgrade guidance to local
  rate-limit responses while preserving the existing error contract.

## [0.8.11] - 2026-08-07

### Fixed

- All MCP tools now share one downstream SDK client per authentication
  configuration. The first HTTP 401/402 opens a process-local authentication
  circuit, so later calls are rejected locally until the API key changes or
  the service process is recreated.
- Raised the minimum `hpsilab-mcp` dependency to 0.12.2 so the shared client
  also enforces its instance-level 401/402 circuit breaker.

## [0.8.10] - 2026-08-07

### Changed

- Local quota rejections now include additive `used`, `remaining`, `reset_at`,
  registration guidance, and paid-plan upgrade guidance while preserving the
  existing structured error envelope.

## [0.8.9] - 2026-08-07

### Changed

- Synchronized package, source-checkout, documentation, and registry manifest
  version metadata for the 0.8.9 patch release.

## [0.8.8] - 2026-08-05

### Configure and Check the `.env` File

## [0.8.7] - 2026-08-05

### Added

- Added process-local Free SDK quota safeguards per API-key digest: 20
  requests per tool per UTC day, 100 total requests per UTC day, and 10 total
  requests per rolling minute. Anonymous calls remain blocked before dispatch,
  retries consume allowance, and local quota rejections send no request.

## [0.8.6] - 2026-08-05

### Fixed

- Missing API keys now stop locally before downstream client construction and
  return the exact `api_key_required` registration payload without x402
  payment details.
- Added bounded retries for read-only calls: 401/402 and ordinary request
  failures are never retried, 429 follows a valid `Retry-After`, and only
  timeouts plus recoverable 500/502/503/504 responses use the finite retry
  budget. Batch service calls stop on the first authentication failure.
- Source checkouts now advertise `0.8.6+source` instead of `0.0.0`, and the
  downstream User-Agent uses that real package version.

## [0.8.5] - 2026-08-05

### Fixed

- Normalized supported `get_ai_prediction` SDK responses before applying the
  shared object-response check, preventing valid prediction data from being
  returned as `invalid_response`.

### Changed

- Simplified `README.md` around the recommended Official Remote MCP setup,
  local stdio installation, tool discovery, and copy-ready verification.
- Standardized new-user registration on `https://hpsilab.com/register`; users
  generate and manage API keys in Settings, and every MCP connection requires
  a valid bearer credential.
- Corrected Python installation guidance to use
  `pip install -U hpsilab-quant-finance-mcp` and removed the unsupported
  `server.api_key` configuration pattern.
- Public documentation describes nine financial research tools. The retained
  `register_account` compatibility tool now directs new users to
  `https://hpsilab.com/register`; users generate and manage keys in Settings.

## [0.8.2] - 2026-08-04

### Added

- Added a Python SDK example showing how to configure `server.api_key` and call `get_iv_radar()`.

## [0.8.1] - 2026-08-03

### Fixed

- **Importing `server` no longer leaks httpx request logs to stderr.**
  Constructing `FastMCP` (module import time, not just when actually running
  as a server) calls the SDK's `configure_logging()`, which puts a
  `RichHandler` on the *root* logger at `INFO` — a side effect of importing
  the module, not something opt-in. httpx logs `HTTP Request: GET
  https://.../api/...` at `INFO` for every call, so anyone who does
  `from hpsilab_quant_finance_mcp import server` to call a tool directly in a
  script (rather than running the MCP process) got that printed for every
  call. Quieted the `httpx`/`httpcore` loggers to `WARNING` specifically,
  leaving FastMCP's own operational logging untouched for the real
  server-process case where it's genuinely useful.

## [0.8.0] - 2026-08-03

### Fixed

- **`register_account` was broken for the exact case it exists to handle.**
  `hpsilab-mcp` 0.11.0 made API key mandatory: `HpsiMcpClient()` now refuses
  to construct with an empty `api_key`, since anonymous access was retired
  server-side. This package's `register_account` used to always build a
  client with `api_key=<whatever HPSILAB_API_KEY resolves to, including "">`
  and call `client.register_account(...)` on it — with no key configured
  (the tool's entire reason to exist), that construction now raised instead
  of running, and every call failed with a generic `http_error`.

  Fixed by using the SDK's new standalone `hpsilab_mcp.register(email=...)`
  function when no key is configured, and only falling back to the
  client-instance path when a key already exists (e.g. re-registering the
  same address to recover a lost key). No change to the tool's public
  signature or return shape.

### Changed

- Bumped the `hpsilab-mcp` dependency floor to `>=0.11.0` (was `>=0.8.2`) —
  the version that added `hpsilab_mcp.register()`, which the fix above
  depends on.
- `register_account`'s documented return shape no longer lists `user_id`.
  The backend stopped including it (internal database primary key, not
  something a caller has a use for) — this package never read it either, so
  the only change is removing the now-inaccurate docstring line.

## [0.7.3] - 2026-07-31

### Changed

- Bumped the `hpsilab-mcp` dependency floor to `>=0.8.2` to pick up its
  simplified anonymous-quota warning: 429/402 rejections for a caller with no
  account and no key now surface one unified message ("Free API key required.
  Register at https://hpsilab.com/register, or call
  `client.register_account(email=...)`") instead of separate keyed/unkeyed
  wording. This package has no copy of that text itself — it delegates to the
  SDK — so there is no other source change here.

## [0.7.2] - 2026-07-31

### Fixed

- Restored the MCP Registry ownership marker in `README.md`. The registry
  proves PyPI ownership by looking for `<!-- mcp-name: ... -->` inside the
  *published package's* README; it was dropped in the 2026-07-24 documentation
  refactor, and `mcp-publisher publish` has failed with a 400 ever since.

  Nothing surfaced the loss: builds, tests and PyPI releases were all unaffected,
  so 0.6.0, 0.7.0 and 0.7.1 shipped normally while the registry silently stayed
  on 0.5.3. Because PyPI releases are immutable, restoring the marker requires a
  new version — hence this release.

### Added

- `scripts/validate_project.py` now fails when that marker is missing, so it
  cannot be lost again without CI saying so.

## [0.7.1] - 2026-07-31

### Fixed

- Documentation stated that `register_account` belonged to the hosted endpoint.
  It ships in this package too, as of 0.7.0 — the FAQ told local-stdio users
  that the one feature added for them was somewhere else. The README also still
  said a valid API key was needed before installing, which stopped being true
  in 0.7.0.

### Changed

- The `missing_api_key` error now names `register_account` as the way to obtain
  a key. Previously it said only "Set HPSILAB_API_KEY", which is a dead end for
  a caller that has no key and no way to get one — while the tool that hands
  one over sat unmentioned in the same tool list.

## [0.7.0] - 2026-07-31

### Added

- `register_account` tool — create a free HPSILab account and receive an API
  key without a password, a wallet, or a web form. This is the only tool that
  works *without* `HPSILAB_API_KEY`: every other tool returns `missing_api_key`
  without one, and this is how a caller obtains one. The account is created
  unverified (keeping the anonymous daily allowance) until the emailed link is
  confirmed, and it is also bound to the caller server-side, so an MCP client
  that cannot rewrite its own `Authorization` header is still recognised.

  Calling it again returns the same account with a fresh key rather than
  creating a second one. An address already belonging to a different account is
  refused, so an agent cannot attach itself to someone else's account.

### Changed

- Minimum `hpsilab-mcp` is now 0.8.0, which provides the underlying
  `register_account()` client method.

## [0.6.0] - 2026-07-30

Recorded retrospectively — this release shipped without a changelog entry.

### Changed

- **Breaking:** `get_equity_curves` renamed to `get_equity_curve` for
  consistency with the other singular tool names.

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

[Unreleased]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/compare/v0.8.13...HEAD
[0.8.13]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/compare/v0.8.12...v0.8.13
[0.8.12]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/compare/v0.8.11...v0.8.12
[0.8.11]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/compare/v0.8.10...v0.8.11
[0.8.10]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/compare/v0.8.9...v0.8.10
[0.5.4]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/releases/tag/v0.5.4
[0.5.3]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/releases/tag/v0.5.3
[0.5.2]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/releases/tag/v0.5.2
[0.5.1]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/releases/tag/v0.5.1
[0.5.0]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/releases/tag/v0.5.0
[0.4.1]: https://github.com/haiyunsky/hpsilab-quant-finance-mcp/releases/tag/v0.4.1
