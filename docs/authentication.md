# Authentication

## Official Remote MCP

[Register a free HPSILab account](https://hpsilab.com/register), sign in, and generate an API key from the Settings page. Send that key on every hosted MCP connection as a bearer credential:

```text
Authorization: Bearer hpsi_your_key
```

The official endpoint is `https://hpsilab.com/mcp`. All financial research tools require a valid API key. Do not configure the research credential as optional.

When no key is configured, the local Python package does not send a request or
offer an x402 payment quote. It returns exactly:

```json
{
  "error": "api_key_required",
  "message": "A free API key is required.",
  "register_url": "https://hpsilab.com/register",
  "docs_url": "https://hpsilab.com/developer/v2"
}
```

## Local stdio

The local package reads exactly one environment variable:

```text
HPSILAB_API_KEY
```

Set it through the MCP client's private environment or secret configuration. Do not add a real key to repository files, examples, command history, logs, screenshots, issue reports, or chat prompts.

## Key generation and handling

New users must register through [https://hpsilab.com/register](https://hpsilab.com/register). After signing in, use Settings to generate, replace, and manage API keys before configuring an MCP client.

If a key is exposed, revoke or replace it in Settings and update the private client configuration. Authentication failures should be returned as structured errors; clients must not echo credentials while troubleshooting.

The package never retries 401, 402, or 403 responses. Batch service calls stop
on the first authentication or authorization failure.

For a configured Free-user key, the local SDK also enforces 20 requests per
tool per UTC day, 100 total requests per UTC day, and 10 total requests per
rolling minute. These process-local counters are a client-side safeguard; the
hosted service remains the authoritative quota source.
