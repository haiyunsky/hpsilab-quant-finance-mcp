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

All financial research tools require a valid API key. Set `HPSILAB_API_KEY` in the process environment before calling the server. The public configuration is environment-based; there is no supported `server.api_key` assignment.

Tool functions return dictionaries with stable status and error fields. Research responses also include a research disclaimer. For normal MCP use, configure an MCP client and let it discover and invoke the tools through the protocol instead of calling Python functions directly.
