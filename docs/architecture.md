# Architecture

## Design goals

The server has one public MCP tool surface, one reusable service adapter, and two standard transports. Transport selection must never duplicate quantitative logic or change tool schemas.

```mermaid
flowchart LR
    C["MCP clients"]
    STDIO["stdio transport"]
    HTTP["Streamable HTTP transport"]
    MCP["ProtocolFastMCP<br/>10 registered tools; 9 publicly documented"]
    SERVICE["QuantFinanceService<br/>validation · errors · output normalization"]
    CREDS["CredentialProvider"]
    ENV["Environment API key"]
    FUTURE["Future OAuth token context"]
    SDK["hpsilab-mcp SDK"]
    API["HPSILab API"]

    C --> STDIO --> MCP
    C --> HTTP --> MCP
    MCP --> SERVICE --> SDK --> API
    SERVICE --> CREDS
    ENV --> CREDS
    FUTURE -. future adapter .-> CREDS
```

## Module responsibilities

### `server.py`

- owns MCP server metadata and tool registration;
- exposes the nine stable public tool functions;
- converts structured service errors into MCP `CallToolResult` objects with `isError: true`;
- selects stdio or Streamable HTTP at process startup;
- exposes an ASGI app factory for external HTTP hosting.

Tool functions remain thin and call `_service.call(...)`. They do not construct REST URLs or duplicate downstream transport code.

### `service.py`

- validates and normalizes ticker symbols;
- obtains credentials through a provider interface;
- delegates every operation to the official `hpsilab-mcp` SDK;
- maps SDK exceptions into a stable structured error shape;
- adds the backward-compatible `status` and `disclaimer` fields to successful objects.

This service is independent of MCP transport and can be unit-tested without starting a protocol session.

### `auth.py`

`CredentialProvider` is the boundary between service access and credential acquisition. The current implementation reads `HPSILAB_API_KEY`, which is appropriate for stdio and local development.

For production HTTP OAuth, the MCP server should become an OAuth 2.1 resource server using the Official MCP SDK's token-verifier and authorization settings. A future implementation should:

1. publish RFC 9728 Protected Resource Metadata;
2. discover or reference an OAuth authorization server;
3. validate audience, issuer, expiry, and scopes on every HTTP request;
4. translate the validated subject/account context into an account-scoped downstream credential;
5. support Client ID Metadata Documents where available and DCR as a compatibility fallback;
6. leave stdio API-key behavior unchanged.

**This plan is still future work for this package.** The hosted deployment at `https://hpsilab.com/mcp` already supports OAuth 2.1 Authorization Code + PKCE with Dynamic Client Registration (added 2026-07-24) — but that is a separate, internally-hosted code path independent of this PyPI package's `auth.py`. If this package's own local Streamable HTTP mode is ever given OAuth support, it would follow the plan above; it does not inherit the hosted deployment's implementation.

OAuth access tokens must never be accepted in query parameters or treated as a process-global API key.

## Transport selection

The console command remains backward compatible:

```bash
hpsilab-quant-finance-mcp
```

It starts stdio and writes only MCP JSON-RPC messages to stdout.

Local Streamable HTTP can be started with:

```bash
hpsilab-quant-finance-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

Equivalent environment variables are `HPSILAB_MCP_TRANSPORT`, `HPSILAB_MCP_HOST`, and `HPSILAB_MCP_PORT`. The built-in runner accepts loopback hosts only. The Official MCP SDK supplies session management, protocol-version handling, JSON/SSE negotiation, Origin/Host protection, and lifecycle processing.

`create_http_app()` returns the same server as an ASGI application for deployment behind an approved production host. Production hosting must configure TLS, accepted hosts/origins, authentication, request limits, and trusted proxy behavior explicitly.

## Compatibility contract

- Public tool names and existing parameters are stable.
- Inputs remain flat JSON objects.
- Successful responses retain all SDK fields and add only `status` and `disclaimer` when absent.
- Errors retain the existing structured fields and are also marked `isError: true` at the MCP layer.
- Resources and prompts are currently empty; no finance functionality is duplicated into those surfaces.
- Tool, resource, and prompt catalogs are static, so change notifications are not advertised.
