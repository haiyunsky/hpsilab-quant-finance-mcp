# Python installation and direct usage

Install the HPSILab Quant Finance MCP package:

```shell
pip install -U hpsilab-quant-finance-mcp
```

This installs the MCP server and its required `hpsilab-mcp` SDK dependency. Do not install the dependency in place of the MCP package when following this guide.

The current package and server release is `0.8.12`. Direct execution from an
unpackaged source checkout reports `0.8.12+source`.

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

## Local Free-tier quotas

The adapter enforces all three limits for each configured API key:

- 20 requests per tool per UTC day;
- 100 total SDK requests per UTC day;
- 10 total SDK requests per rolling 60 seconds.

Anonymous callers receive zero tool requests. Every actual downstream attempt,
including a retry, consumes one allowance. A locally rejected request returns
status code 429 without constructing the downstream client. Counters are kept
in memory for the current process; hosted enforcement remains authoritative
across restarts and multiple machines.

Tool functions return dictionaries with stable status and error fields. Research responses also include a research disclaimer. For normal MCP use, configure an MCP client and let it discover and invoke the tools through the protocol instead of calling Python functions directly.
