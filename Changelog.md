# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- The README rendered wrong wherever it is actually read. The three badges sat
  on the line directly below a blockquote with no blank line between them, so
  Markdown's lazy continuation pulled them inside the quote. The example image
  and the `LICENSE`, `AGENTS.md`, and `CONTRIBUTING.md` links were relative,
  which resolves on GitHub and breaks on PyPI, where this file is the package
  long description. The `docs/tools.md#get_monte_carlo` anchor has never
  existed — tool names live in table cells, and anchors come from headings.
- The documented tool surface was one short. `tools/list` and `manifest.json`
  both advertise 10 tools; README, `docs/tools.md`, and `docs/client-setup.md`
  described 9 and omitted `register_account` entirely. `docs/tools.md` now has
  a section for it, and `docs/architecture.md` no longer calls it
  compatibility-only — it is the first entry in an `allowance_exhausted`
  refusal's `next_actions`.
- `manifest.json` still described `register_account` as a "Legacy
  compatibility operation", which stopped being true in 0.10.0.

### Changed

- Reorganized the README around what a registry or catalog visitor needs
  first: a facts table (registry name, version, transports, endpoint, install,
  auth, tool count), then the two transports, then tools. The error-contract
  reference that had accumulated inside the hosted quick start is now a
  five-row table at the end, pointing at `docs/authentication.md` and
  `docs/python-sdk.md`, which carry the same material in full.

## [0.10.0] - 2026-08-28

The hosted API began answering a third refusal on HTTP 402 on 2026-08-27, and
this package could not tell it from the other two. Registering — free, and the
one thing that resolves it — was never named.

### Fixed

- **A spent free evaluation allowance was reported as an untyped `http_error`**
  for anyone running `hpsilab-mcp` 0.14.0 or later, and as `payment_required`
  on the releases before it. The refusal (`error:
  "anonymous_allowance_exhausted"`) has no `accepts` and never will, because
  there is nothing to sell a caller who has not said who it is; read as a
  payment challenge it told that caller to configure a wallet, and read as a
  generic HTTP error it discarded `calls_used`, `calls_allowed`,
  `window_days`, and the `next_actions` list carrying the free remedy. Both
  reached the exact population the ceiling exists to convert.

### Added

- `allowance_exhausted` — the free evaluation ceiling is reported under its own
  error code with `calls_used`, `calls_allowed`, `calls_allowed_next`,
  `window_days`, `credits_charged: 0`, and `next_actions`. The API's own remedy
  list is passed through untouched; only it knows whether this caller should
  register or verify an address it has already given us. The local fallback
  leads with the `register_account` tool rather than the signup URL, so an
  agent can take the remedy in one call with no browser and no human.
- No `upgrade` action and no `upgrade_url` appear in this payload, even though
  the hosted body carries them. Money buys an unidentified caller no further
  anonymous calls, and a price listed ahead of a free remedy is what the API's
  `next_actions` ordering exists to prevent.
- `call_batch` stops on it by error code as well as by status: the ceiling is
  not per-symbol, so every remaining symbol would spend a request rediscovering
  it.
- A hosted 429 now preserves `upgrade_available`, `upgrade_message`, and
  `upgrade_url` alongside the quota metadata it already passed through. The
  burst refusal this package raises locally still carries no upsell of its own
  — waiting is what resolves that one — but only the hosted service can see the
  plan behind the key, and dropping a field it chose to send is not this
  layer's decision. README and `docs/python-sdk.md` said a 429 carries no
  upgrade guidance at all; both now distinguish the two.

### Changed

- Raised the minimum `hpsilab-mcp` REST SDK version to 0.14.0, the release that
  raises `HpsiMcpAllowanceExhaustedError` instead of a payment error. This
  package now imports that class directly.
- The allowance refusal deliberately opens **no** local circuit, unlike the
  Credits refusal. Its remedy is a tool this same process exposes, and
  `register_account` lifts the ceiling for the API key already configured — a
  60-second latch would refuse the very next call, which is the one that would
  now succeed, and make registering look like it did nothing.

### Known issues

- `verify_email` is read from the response body rather than from the SDK's
  sanitized `HpsiMcpAllowanceExhaustedError.verify_email_url`. That attribute
  is always `None` in `hpsilab-mcp` 0.14.0: the verification link is the
  hpsilab.com site root, and the SDK's public-URL allowlist admits only
  `/register` and `/pricing`. The same URL rides in `next_actions` untouched
  regardless, so withholding the top-level field would have hidden a remedy the
  payload publishes two lines further down.

## [0.9.2] - 2026-08-11

### Fixed

- Made the `insufficient_credits` breaker atomic per API-key identity. The
  breaker check, downstream SDK call, and breaker update now share one
  identity-specific lock, so a concurrent fan-out reaches the backend once
  and every waiting call is refused locally after the first 402. Different
  identities do not block one another.

### Changed

- Raised the minimum `hpsilab-mcp` REST SDK version to 0.13.11, which applies
  the same atomic Credits breaker to direct SDK calls.

## [0.9.1] - 2026-08-10

### Added

- A 60-second, per-API-key `insufficient_credits` circuit breaker. After the
  first hosted 402, calls across all symbols and tools return the cached
  structured refusal locally with `circuit_open` and `retry_after_seconds`.
  The circuit expires automatically and embeddings can clear it immediately
  after a top-up with `clear_insufficient_credits_circuit()`.

### Changed

- Raised the minimum `hpsilab-mcp` REST SDK version to 0.13.10 and synchronized
  package, source fallback, MCP Registry manifest, catalog manifest, and
  user-facing version documentation for this patch release.

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
