"""
Central configuration — all values are read from environment variables.
Copy example.env to .env and set your values there (or pass them via docker-compose).
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT_TYPE", "streamable-http")
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))

# ---------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------
GIT_TOKEN = os.getenv("GIT_TOKEN")           # Personal access token
GIT_USER_NAME = os.getenv("GIT_USER_NAME")   # Used as username in auth and as git author name
GIT_USER_EMAIL = os.getenv("GIT_USER_EMAIL") # Used as git author email

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_PATH = Path(os.getenv("LOG_PATH", "/app/logs/mcp_tools.jsonl"))
LOG_MAX_ENTRIES = int(os.getenv("LOG_MAX_ENTRIES", "1000"))

# ---------------------------------------------------------------------------
# Build / run_command
# ---------------------------------------------------------------------------
RUN_COMMAND_TIMEOUT = int(os.getenv("RUN_COMMAND_TIMEOUT", "120"))
