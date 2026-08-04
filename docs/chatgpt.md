# Use HPSILab with ChatGPT

ChatGPT connects to the hosted HPSILab Streamable HTTP server. It does not launch the local Python stdio package directly.

> ChatGPT MCP app availability, labels, and administrator permissions vary by plan and can change while the feature is in beta. See OpenAI's current [developer mode and MCP apps documentation](https://help.openai.com/en/articles/12584461-developer-mode-apps-and-full-mcp-connectors-in-chatgpt-beta).

## Installation

1. Use ChatGPT on the web with a plan and workspace that supports custom MCP apps.
2. Ask a workspace administrator to enable developer mode if your account does not expose it.
3. [Register a HPSILab account](https://hpsilab.com/register), sign in, and generate an API key in Settings.

## Configuration

1. Open **Settings → Apps → Advanced Settings** and enable developer mode, or use the equivalent workspace-admin path.
2. Choose **Apps → Create**.
3. Enter a recognizable name such as `HPSILab Quant Finance`.
4. Set the MCP endpoint to:

   ```text
   https://hpsilab.com/mcp
   ```

5. Select the authentication option supported by your workspace. If the form permits a static bearer token, use the HPSILab API key as the bearer credential. Never paste it into a chat message.
6. Select **Scan Tools**, review the publicly documented financial research tools and their annotations, then create the app.
7. Open a new chat and enable the draft/custom HPSILab app from the tools menu.

A valid HPSILab API key is required. Configure it as the bearer credential and never paste it into a chat message.

## Example prompts

```text
Use HPSILab to analyze NVDA. Summarize the overall signal, confidence, IV regime,
options pressure, 30-day Monte Carlo range, and major risks. Cite the tool outputs
and distinguish observed data from your interpretation.
```

```text
Use the HPSILab IV and option-pressure tools for AAPL. Explain whether implied
volatility is elevated relative to history and identify the most important strikes.
Do not recommend a trade.
```

```text
Run the HPSILab pre-trade risk scan for MSFT. Surface every failed or warning
check and explain any unavailable portfolio fields using the reason returned.
```

## Troubleshooting

### The Create button or developer mode is missing

Custom MCP apps may require a supported plan, web access, an administrator setting, or an Enterprise/Edu role. Check the current OpenAI documentation and ask the workspace administrator to confirm access.

### Tool scanning fails

- Confirm the endpoint is exactly `https://hpsilab.com/mcp`.
- Confirm the credential is a bearer token and does not include extra quotes or whitespace.
- Confirm that a valid HPSILab API key is configured as the bearer credential.
- Ask the administrator whether workspace networking or app policies block third-party MCP servers.

### ChatGPT does not call HPSILab

- Start a new chat after enabling the app.
- Select HPSILab in the tools/apps menu.
- Explicitly say “Use HPSILab” and name the desired analysis.
- If the tool list changed after the app was created, refresh/re-scan the app according to workspace policy.

### A report or image call asks for confirmation

`generate_stock_images` and `generate_stock_research_report` create hosted artifacts and are non-idempotent. Review the action and quota implications before approving or retrying.
