# Python installation and direct usage

Install the HPSILab Quant Finance MCP package:

```shell
pip install -U hpsilab-quant-finance-mcp
```

This installs the MCP server and its required `hpsilab-mcp` SDK dependency. Do not install the dependency in place of the MCP package when following this guide.

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

Tool functions return dictionaries with stable status and error fields. Research responses also include a research disclaimer. For normal MCP use, configure an MCP client and let it discover and invoke the tools through the protocol instead of calling Python functions directly.
