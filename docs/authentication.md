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
on the first authentication or authorization failure, on an empty Credit
balance, and on an unresolved payment settlement.

An empty balance arrives as HTTP 402 with `error: "insufficient_credits"` and
is reported under its own error code. It is not an authentication failure: the
key is valid, nothing was charged (`credits_charged: 0`), and the call made
after Credits are added is sent rather than refused locally.

The package also enforces one process-local limit: 10 requests per rolling
minute per API key. It is burst protection for the hosted API, not a quota —
entitlement is measured in Credits, and only the hosted service knows the
balance and the plan.
