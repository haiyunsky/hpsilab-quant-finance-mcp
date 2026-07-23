# Security Policy

## Supported versions

Security fixes are applied to the latest published release. Users should upgrade before reporting an issue that is already fixed on the default branch.

| Version | Supported |
| --- | --- |
| Latest release | Yes |
| Older releases | No |

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability or include secrets, tokens, account identifiers, private market data, or exploit details in public discussions.

Preferred reporting path:

1. Open a private report through the repository's **Security → Report a vulnerability** workflow: `https://github.com/haiyunsky/hpsilab-quant-finance-mcp/security/advisories/new`.
2. Include the affected version, environment, impact, reproduction steps, and a minimal proof of concept.
3. Remove or redact all real API keys and personal data.

If private vulnerability reporting is unavailable, contact the maintainer through the GitHub profile without disclosing technical details publicly, and request a private reporting channel.

You can expect an initial acknowledgement within seven calendar days. Validation, remediation, and disclosure timing depend on severity and whether a coordinated release across the MCP package, SDK, and hosted API is required.

## Scope

Reports are useful when they concern:

- leakage or mishandling of `HPSILAB_API_KEY` or authorization headers;
- authentication or authorization bypass;
- command or argument injection in local stdio setup;
- unsafe MCP input-schema handling;
- exposure of private account or portfolio data;
- server-side request forgery, arbitrary code execution, or dependency compromise;
- misleading tool annotations that could cause unsafe automatic execution.

The following are generally out of scope unless they demonstrate a concrete security boundary failure:

- financial losses based on research output;
- model accuracy or market-prediction quality;
- rate limits or account quotas working as documented;
- vulnerabilities that require an already compromised local machine;
- reports generated only by automated scanners without a reproducible impact.

## Operational guidance

- Never commit API keys to source control or client configuration shared with a team.
- Prefer secret inputs or environment variables supported by the MCP client.
- Rotate a key immediately if it appears in a log, screenshot, issue, or commit.
- Review non-idempotent artifact calls before approving retries.
- Install releases only from the linked PyPI project and verify the package name carefully.

