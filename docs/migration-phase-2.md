# Phase 2 Migration Notes

Phase 2 is backward compatible. No public tool, parameter, console command, package name, environment variable, or response field was removed or renamed.

## What changed

### SDK requirement

The minimum Official MCP Python SDK version is now `1.27.2`, with major version 2 excluded. Reinstall or upgrade before running the server:

```bash
python -m pip install --upgrade hpsilab-quant-finance-mcp
```

### Successful output

Successful object responses now include these fields when the downstream service did not already provide them:

```json
{
  "status": "success",
  "disclaimer": "Research and educational output only. ..."
}
```

This is additive. Existing service fields and their nesting are unchanged. Consumers should continue ignoring unknown fields.

### Error output

The current missing-credential contract supersedes the earlier Phase 2
`missing_api_key` envelope. No downstream request is sent:

```json
{
  "error": "api_key_required",
  "message": "A free API key is required.",
  "register_url": "https://hpsilab.com/register",
  "docs_url": "https://hpsilab.com/developer/v2"
}
```

At the MCP protocol layer, the result also sets `isError: true`. Consumers
should detect `structuredContent.error == "api_key_required"`.

### Transport options

The original command still starts stdio:

```bash
hpsilab-quant-finance-mcp
```

Local Streamable HTTP is now available without a second implementation:

```bash
hpsilab-quant-finance-mcp --transport streamable-http
```

This local HTTP mode uses the process-level `HPSILAB_API_KEY` and is intended for development or controlled deployment. It is not a replacement for the authenticated hosted endpoint.

### Python internals

Input validation, SDK dispatch, and output/error normalization moved to `QuantFinanceService`. The historical private helpers in `server.py` remain as compatibility aliases, but integrations should use MCP rather than importing private functions.

## No action required

Existing ChatGPT, Claude, VS Code, GitHub Copilot, Cursor, Continue, and Kimi configurations using `https://hpsilab.com/mcp` require no change.
