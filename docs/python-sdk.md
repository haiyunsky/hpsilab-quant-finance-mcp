# Python SDK and direct Python usage

The MCP server and Python REST SDK are related but distinct packages.

| Use case | Package |
| --- | --- |
| Connect ChatGPT, Claude, Cursor, or another MCP client | `hpsilab-quant-finance-mcp` |
| Call HPSILab directly from Python through the REST SDK | `hpsilab-mcp` |

## Direct REST SDK

Install the published SDK:

```bash
pip install -U hpsilab-mcp
```

Use the SDK's documented `HpsiMcpClient` interface for direct Python integrations. The SDK is the source of truth for hosted REST paths, methods, authentication, and transport behavior: [hpsilab-mcp on PyPI](https://pypi.org/project/hpsilab-mcp/).

## Calling the MCP package from Python

The MCP package exposes its registered tool functions through the server module:

```python
from hpsilab_quant_finance_mcp import server

result = server.get_iv_radar("NVDA")
print(result)
```

Set `HPSILAB_API_KEY` in the process environment before importing and calling the server. The public configuration is environment-based; there is no supported `server.api_key` assignment.

Tool functions return dictionaries with stable status and error fields. Research responses also include a research disclaimer. Prefer MCP when an assistant or MCP host manages tool discovery; prefer the SDK when application code needs direct REST access.
