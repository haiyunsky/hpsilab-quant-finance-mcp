# MCP Protocol Compatibility Review

Reviewed against MCP specification version **2025-11-25** and Official MCP Python SDK **1.27.2**.

## Summary

The project uses the Official MCP SDK for JSON-RPC framing, lifecycle negotiation, capability advertisement, validation, and standard transports. Phase 2 found one material interoperability issue: service failures were structured correctly but returned as successful tool results. The protocol adapter now preserves the structured payload and sets `isError: true`.

No public tool was renamed, removed, or split.

## Protocol surface

| Area | Status | Implementation and findings |
| --- | --- | --- |
| `initialize` | Compliant | SDK negotiates protocol version, returns server name/version/instructions and capabilities, then accepts `notifications/initialized`. Tests verify advertised package version over stdio and HTTP. |
| `tools/list` | Compliant | Nine stable tools, flat object inputs, parameter descriptions, valid JSON Schema, output schemas, and explicit boolean annotations. Catalog is static, so `listChanged` is false. |
| `tools/call` | Compliant | Successful dictionaries produce both serialized text and `structuredContent`. Structured service failures additionally return `isError: true`. Unknown tools and malformed inputs are handled by the SDK as protocol/tool validation errors. |
| `resources/list` | Compliant, empty | The SDK advertises the resources capability with `subscribe: false` and `listChanged: false`; the list is empty. No resource URI contract is currently needed. |
| `prompts/list` | Compliant, empty | The SDK advertises prompts with `listChanged: false`; the list is empty. Copy-ready user prompts remain documentation rather than a second runtime API. |
| Notifications | Compliant | The SDK handles lifecycle notifications. The server does not emit list-change notifications because tools, resources, and prompts do not change during a session. |
| Errors | Compliant | Request-shape and unknown-method failures use SDK JSON-RPC handling. Recoverable tool/service errors use `isError: true`, serialized text, and the existing machine-readable structured payload. |

## Transport review

### stdio

- Remains the default console transport.
- Uses newline-delimited UTF-8 JSON-RPC through the Official MCP SDK.
- Application code does not write banners or logs to stdout.
- Credentials come from `HPSILAB_API_KEY` rather than an MCP OAuth flow.
- CI starts a real subprocess, performs initialization, lists all protocol surfaces, and calls a tool.

### Streamable HTTP

- Uses the same `ProtocolFastMCP` instance and nine tool functions as stdio.
- Supports the standard `/mcp` POST/GET endpoint and SDK-managed sessions.
- Uses JSON responses where permitted while retaining SSE negotiation through the SDK.
- Defaults to `127.0.0.1:8000` for safe local execution.
- Uses SDK transport-security defaults for Host/Origin validation.
- Can be embedded using `create_http_app()` without duplicating tool or service code.

The public `https://hpsilab.com/mcp` deployment remains operationally separate from this repository's local runner. Its production TLS, proxy, rate-limit, and authorization configuration must be verified in deployment infrastructure.

## Tool schema review

- All inputs are top-level JSON objects.
- No tool uses a nested `request`, `params`, or `input` wrapper.
- Existing names and parameter defaults are unchanged.
- `generate_stock_images.types` has an explicit enum and remains optional.
- `force` and `types` now have schema-level descriptions.
- Every tool publishes an object `outputSchema`. It intentionally allows additional service fields because the hosted quantitative API is additive and client compatibility takes priority over falsely strict schemas.
- Artifact tools remain non-destructive but non-idempotent; the other seven tools remain read-only and idempotent.

Splitting a tool was not appropriate: each current tool represents one coherent research capability, and splitting would expand the selection surface without removing a nested request or an incompatible schema.

## Non-standard extensions

Tool `_meta` values such as `x-tier` and `x-access` are application metadata carried in the protocol's extensible metadata field. Clients must treat them as optional and must rely on standard annotations for safety behavior. No client is required to understand these values.

## Automated enforcement

`scripts/validate_project.py` checks:

- the exact nine public names;
- flat, valid input schemas and valid output schemas;
- parameter descriptions;
- explicit safety annotations;
- empty resources/prompts assumptions;
- transport declarations and canonical endpoint;
- version synchronization across package and manifests.

The protocol tests separately exercise initialize, list operations, tool errors, stdio, and Streamable HTTP.

## Specification references

- [MCP 2025-11-25 specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [Lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)
- [Transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)
- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

