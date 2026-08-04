# Local installation and self-hosting

Use Official Remote MCP unless the client requires stdio or you are developing the server. All financial research tools require a valid API key. The local package calls the hosted HPSILab API through the `hpsilab-mcp` SDK and needs network access.

## Local stdio with uvx

For clients whose stdio schema uses `mcpServers` and that can launch `uvx`:

```json
{
  "mcpServers": {
    "hpsilab": {
      "command": "uvx",
      "args": ["hpsilab-quant-finance-mcp"],
      "env": {
        "HPSILAB_API_KEY": "hpsi_your_key"
      }
    }
  }
}
```

Store the real key in private user-level configuration.

## Install from PyPI

```bash
pip install -U hpsilab-quant-finance-mcp
hpsilab-quant-finance-mcp
```

The console command starts stdio by default and reads `HPSILAB_API_KEY` from the process environment.

## Install from source

```bash
git clone https://github.com/haiyunsky/hpsilab-quant-finance-mcp.git
cd hpsilab-quant-finance-mcp
python -m venv .venv
python -m pip install -e .
hpsilab-quant-finance-mcp
```

## Local Streamable HTTP development

```bash
hpsilab-quant-finance-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

The local endpoint is `http://127.0.0.1:8000/mcp`. The built-in runner only accepts loopback hosts and uses the process-level `HPSILAB_API_KEY`. This is a development mode, not the Official Remote MCP service.

For external hosting, import `create_http_app()` from `hpsilab_quant_finance_mcp.server` and supply production TLS, authentication, allowed-host/origin, proxy, observability, and secret-management controls in the hosting layer. Do not expose the built-in development runner publicly.

## Verification

After configuration, inspect the client's MCP tool list and call a publicly documented read-only tool such as `analyze_stock` with `AAPL`.
