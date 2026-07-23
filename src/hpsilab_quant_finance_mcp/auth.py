"""Credential boundaries for HPSILab service access.

MCP authorization belongs to the HTTP transport. The local stdio server keeps
using an environment-provided API key, as recommended by the MCP specification.
This module deliberately separates service credentials from the MCP tool layer
so an HTTP resource-server token verifier can be added later without changing
the public tools or the quantitative service adapter.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


class CredentialProvider(Protocol):
    """Return the credential used by the downstream HPSILab API."""

    def get_api_key(self) -> str:
        """Return an API key, or an empty string when none is configured."""


@dataclass(frozen=True, slots=True)
class EnvironmentApiKeyProvider:
    """Read an HPSILab API key from a process environment variable."""

    variable_name: str = "HPSILAB_API_KEY"

    def get_api_key(self) -> str:
        return os.getenv(self.variable_name, "").strip()
