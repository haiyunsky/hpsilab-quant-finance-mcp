# Authentication

## Official Remote MCP

[Register a free HPSILab account](https://hpsilab.com/register), sign in, and generate an API key from the Settings page. Send that key on every hosted MCP connection as a bearer credential:

```text
Authorization: Bearer hpsi_your_key
```

The official endpoint is `https://hpsilab.com/mcp`. All financial research tools require a valid API key. Do not configure the research credential as optional.

## Local stdio

The local package reads exactly one environment variable:

```text
HPSILAB_API_KEY
```

Set it through the MCP client's private environment or secret configuration. Do not add a real key to repository files, examples, command history, logs, screenshots, issue reports, or chat prompts.

## Key generation and handling

New users must register through [https://hpsilab.com/register](https://hpsilab.com/register). After signing in, use Settings to generate, replace, and manage API keys before configuring an MCP client.

If a key is exposed, revoke or replace it in Settings and update the private client configuration. Authentication failures should be returned as structured errors; clients must not echo credentials while troubleshooting.
