# code-sandbox-mcp

An MCP server that gives AI agents a sandboxed environment to clone, edit, build, and push code — all isolated inside a Docker container.

## Tools

| Category | Tools |
|---|---|
| **Git** | `git_clone_repo`, `git_commit`, `git_push` |
| **Filesystem** | `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `delete_file`, `delete_project` |
| **Build** | `run_command` (mvn, gradle, npm, node, python, …) |

All filesystem and build tools are sandboxed to `/workspace`. Path traversal is blocked. `delete_project` is blocked when there are uncommitted or unpushed changes.

## Images

| Image | Contents |
|---|---|
| `code-sandbox-base` | Python 3.12, git |
| `code-sandbox-java` | + Maven |
| `code-sandbox-full` | + Maven, Node.js, npm |

## Quick Start

```bash
# 1. Configure
cp example.env .env
# Edit .env — set GIT_TOKEN, GIT_USER_NAME, etc.

# 2. Build
./build.sh v0.0.1

# 3. Run
docker compose up
```

The server is available at `http://localhost:8075/mcp` (configurable via `MCP_PORT`).

## Configuration

All settings are read from environment variables (see `example.env`):

| Variable | Default | Description |
|---|---|---|
| `MCP_PORT` | `8000` | Server port |
| `GIT_TOKEN` | — | Git personal access token (fallback for all git tools) |
| `GIT_USER_NAME` | — | Git username / author name |
| `GIT_USER_EMAIL` | — | Git author email |
| `RUN_COMMAND_TIMEOUT` | `120` | Max seconds for `run_command` |
| `LOG_MAX_ENTRIES` | `1000` | Max tool call log entries kept |

## Logging

Every tool call is logged to `/app/logs/mcp_tools.jsonl` (mounted to `.dcs/code_sandbox/logs/`). The log is capped at `LOG_MAX_ENTRIES` entries. Sensitive values (`api_key`, `token`, …) are automatically redacted.
