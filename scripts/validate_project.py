"""Validate MCP tool schemas and cross-file release metadata."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema.validators import validator_for

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hpsilab_quant_finance_mcp import __version__
from hpsilab_quant_finance_mcp.server import mcp

EXPECTED_TOOLS = {
    "analyze_stock",
    "get_ai_prediction",
    "get_iv_radar",
    "get_option_pressure",
    "get_monte_carlo",
    "get_equity_curve",
    "get_pretrade_risk_scan",
    "generate_stock_images",
    "generate_stock_research_report",
}
REQUIRED_ANNOTATIONS = ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint")


def load_json(name: str) -> dict[str, Any]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def validate_release_metadata() -> None:
    registry = load_json("server.json")
    manifest = load_json("manifest.json")

    versions = {
        "package": __version__,
        "server.json": registry["version"],
        "server.json package": registry["packages"][0]["version"],
        "manifest.json": manifest["version"],
    }
    if len(set(versions.values())) != 1:
        raise ValueError(f"Release versions are not synchronized: {versions}")

    if registry["packages"][0]["transport"]["type"] != "stdio":
        raise ValueError("The Official MCP Registry package must advertise stdio")
    if registry["remotes"][0]["type"] != "streamable-http":
        raise ValueError("The Official MCP Registry remote must advertise Streamable HTTP")
    if registry["remotes"][0]["url"] != "https://hpsilab.com/mcp":
        raise ValueError("Unexpected canonical remote endpoint")

    manifest_tools = {tool["name"] for tool in manifest["tools"]}
    if manifest_tools != EXPECTED_TOOLS:
        raise ValueError(f"manifest.json tool mismatch: {manifest_tools ^ EXPECTED_TOOLS}")


async def validate_mcp_contract() -> None:
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    if names != EXPECTED_TOOLS:
        raise ValueError(f"Registered tool mismatch: {names ^ EXPECTED_TOOLS}")

    for tool in tools:
        if not tool.description:
            raise ValueError(f"{tool.name} has no description")
        if tool.inputSchema.get("type") != "object":
            raise ValueError(f"{tool.name} input schema is not an object")
        if {"request", "input"} & tool.inputSchema.get("properties", {}).keys():
            raise ValueError(f"{tool.name} uses a nested request wrapper")
        if tool.outputSchema is None:
            raise ValueError(f"{tool.name} has no output schema")

        validator_for(tool.inputSchema).check_schema(tool.inputSchema)
        validator_for(tool.outputSchema).check_schema(tool.outputSchema)

        if tool.annotations is None:
            raise ValueError(f"{tool.name} has no annotations")
        for hint in REQUIRED_ANNOTATIONS:
            value = getattr(tool.annotations, hint)
            if type(value) is not bool:
                raise ValueError(f"{tool.name}.{hint} must be an explicit boolean")

        for name, schema in tool.inputSchema.get("properties", {}).items():
            branches = schema.get("anyOf", [schema])
            if not schema.get("description") and not any(branch.get("description") for branch in branches):
                raise ValueError(f"{tool.name}.{name} has no parameter description")

    if await mcp.list_resources():
        raise ValueError("Resources were added without updating the protocol capability review")
    if await mcp.list_prompts():
        raise ValueError("Prompts were added without updating the protocol capability review")


def main() -> None:
    validate_release_metadata()
    asyncio.run(validate_mcp_contract())
    print("MCP schemas, annotations, capabilities, manifests, and versions are valid.")


if __name__ == "__main__":
    main()
