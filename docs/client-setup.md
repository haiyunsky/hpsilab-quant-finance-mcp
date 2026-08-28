# MCP client setup

Official Remote MCP is recommended for every client that supports Streamable HTTP.

## Remote connection parameters

These values are shared, but the surrounding configuration syntax is client-specific. Do not paste one client's JSON into another client.

| Setting | Value |
| --- | --- |
| Name | `hpsilab` |
| Transport | Streamable HTTP |
| URL | `https://hpsilab.com/mcp` |
| Header | `Authorization: Bearer hpsi_your_key` |

All financial research tools require a valid API key. [Register](https://hpsilab.com/register), sign in, generate the key in Settings, and keep the real value in a private user-level configuration or the client's secret store.

## Claude

Claude Code can add the hosted server directly:

```bash
claude mcp add --transport http --scope user hpsilab https://hpsilab.com/mcp --header "Authorization: Bearer hpsi_your_key"
```

Verify with `claude mcp get hpsilab`. See [claude.md](claude.md) for additional Claude surfaces and local stdio.

## Cursor

Add this in Cursor's supported private MCP configuration:

```json
{
  "mcpServers": {
    "hpsilab": {
      "url": "https://hpsilab.com/mcp",
      "headers": {
        "Authorization": "Bearer hpsi_your_key"
      }
    }
  }
}
```

See [cursor.md](cursor.md) for local stdio and troubleshooting.

## ChatGPT

ChatGPT uses the hosted server rather than the local stdio package:

1. In a workspace that supports custom MCP apps, enable developer mode.
2. Create an app named `HPSILab Quant Finance`.
3. Enter `https://hpsilab.com/mcp` as the endpoint.
4. Configure the valid HPSILab API key as the bearer credential.
5. Scan the tools, review their annotations, enable the app, and open a new chat.

Availability and labels vary by ChatGPT plan and workspace policy. See [chatgpt.md](chatgpt.md) for current UI guidance.

## VS Code and GitHub Copilot

Use the hosted URL and required bearer header in the MCP configuration supported by your installed version. Detailed copy-ready configurations are in [vscode.md](vscode.md) and [copilot.md](copilot.md).

## Continue and Kimi

If the installed client version supports Streamable HTTP with custom bearer headers, enter the remote parameters above using that client's own configuration UI or schema. Otherwise use its documented stdio support with [self-hosting.md](self-hosting.md). This repository does not contain versioned Continue or Kimi configuration schemas.

## Verification

After connecting, confirm all 10 tools are available — the 9 financial research tools plus `register_account` — then run:

```text
Use HPSILab to analyze AAPL. Return the overall signal, confidence, strongest
bullish and bearish evidence, and a concise risk summary.
```

## Troubleshooting

- **Authentication error:** confirm the header name is `Authorization` and its value begins with `Bearer `.
- **No tools discovered:** confirm the URL is exactly `https://hpsilab.com/mcp` and that the client supports Streamable HTTP.
- **Configuration rejected:** validate the JSON and use the schema expected by the installed client version.
- **Tool not called:** enable HPSILab in the client's tools menu and explicitly ask it to use HPSILab.
- **Artifact retry prompt:** review before approving; image and report tools are non-idempotent and may consume quota.
