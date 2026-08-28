# Python installation and direct usage

Install the HPSILab Quant Finance MCP package:

```shell
pip install -U hpsilab-quant-finance-mcp
```

This installs the MCP server and its required `hpsilab-mcp` SDK dependency. Do not install the dependency in place of the MCP package when following this guide.

The current package and server release is `0.10.0`. Direct execution from an
unpackaged source checkout reports `0.10.0+source`.

## Direct Python usage

The MCP package exposes its registered tool functions through the server module:

```python
from hpsilab_quant_finance_mcp import server

result = server.get_iv_radar("NVDA")
print(result)
```

All SDK calls require a valid API key. Set `HPSILAB_API_KEY` in the process environment before calling the server. The public configuration is environment-based; there is no supported `server.api_key` assignment. If the key is absent, the call stops locally before constructing the downstream client and returns only:

```json
{
  "error": "api_key_required",
  "message": "A free API key is required.",
  "register_url": "https://hpsilab.com/register",
  "docs_url": "https://hpsilab.com/developer/v2"
}
```

The adapter never retries 401 or 402 responses. A 429 is retried only when a
valid `Retry-After` value is available. Read-only calls use a finite retry
budget for timeouts and recoverable 500/502/503/504 responses; artifact
generation calls are not automatically retried because they are non-idempotent.

## Local burst protection

The adapter enforces one process-local limit per configured API key: 10
requests per rolling 60 seconds. Anonymous callers receive zero tool requests.
Every actual downstream attempt, including a retry, consumes one allowance. A
locally rejected request returns status code 429 without constructing the
downstream client.

This is burst protection, not a quota. Day-scoped local gates were removed in
0.9.0: entitlement is measured in Credits, and a process that cannot see a
balance or a plan was refusing Developer and Pro keys at the Free tier's
numbers for the rest of the UTC day.

A 429 says only that the caller is going too fast, so the refusal this package
raises locally carries no registration or upgrade guidance of its own. The
action it does carry is the one that resolves it:

```python
if result.get("error") == "rate_limit_exceeded":
    wait_seconds = result["retry_after_seconds"]  # also in next_actions
```

When a 429 originates from the hosted API, the adapter preserves its safe
metadata, including `tool`, `limit`, `window`, `reset_at`, `next_actions`, and
the plan guidance the service attached (`upgrade_available`, `upgrade_message`,
`upgrade_url`), when present. Only the hosted service can see the plan behind
the key, so what it says about this caller is passed through rather than
rebuilt or withheld.

## Credits, payment, and settlement

An empty Credit balance is HTTP 402 with `error: "insufficient_credits"`. It
is reported as `error_code: "insufficient_credits"` — never as a rate limit,
which waiting would resolve, and never as a generic HTTP error, which would
discard the numbers a caller needs:

```python
if result.get("error") == "insufficient_credits":
    needed = result["credits_required"]
    have = result["credits_remaining"]  # credits_charged is always 0 here
    actions = result["next_actions"]  # register, or upgrade — never both
```

`next_actions` is the canonical machine-readable list. Entries carry a `type`
(`register`, `verify_email`, `upgrade`, `retry_after`), a label, and a URL
where one applies. `register` appears only for a caller with no account.

A caller that has not identified itself gets a fourth possibility on the same
status. The free evaluation allowance is HTTP 402 with `error:
"anonymous_allowance_exhausted"`, reported as `error_code:
"allowance_exhausted"` — never as `payment_required`, which would ask someone
who owes nothing to configure a wallet, and never as a generic HTTP error,
which would discard the ceiling itself:

```python
if result.get("error_code") == "allowance_exhausted":
    used = result["calls_used"]  # cached results count toward this
    ceiling = result["calls_allowed"]  # per result["window_days"] days
    actions = result["next_actions"]  # register_account first — free, one call
```

`calls_allowed_next` names the ceiling registering would raise it to, and is
absent for a caller already on that rung; those callers get `verify_email`
rather than `register`. Requires `hpsilab-mcp` 0.14.0 or later, which is the
release that stopped raising this refusal as a payment error.

If a payment was sent and the API cannot confirm whether it settled, the
result is `error_code: "settlement_unknown"` with `x402_status:
"settlement_unknown"`, an empty `next_actions`, and a `call_id`. **Do not
retry that call and do not pay for it again** — a retry signs a second
authorization for one logical call. Keep the `call_id`: it is what
reconciliation needs to determine whether the money moved.

Tool functions return dictionaries with stable status and error fields. Research responses also include a research disclaimer. For normal MCP use, configure an MCP client and let it discover and invoke the tools through the protocol instead of calling Python functions directly.
