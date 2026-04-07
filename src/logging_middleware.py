"""
Logging middleware for the MCP server.

Patches mcp.tool() so that every registered tool is automatically wrapped
with a logging layer. Each invocation appends one JSON line to LOG_PATH.

Log entry schema (all fields always present):
{
    "timestamp":     str   — ISO 8601 UTC
    "tool":          str   — tool function name
    "args":          dict  — bound arguments (sensitive fields redacted)
    "success":       bool  — false when an exception was raised OR result starts with "Error"
    "error":         str|null — first 300 chars of the error, null on success
    "duration_ms":   float — wall-clock time of the tool call
    "result_length": int   — character length of the return value
}
"""

import functools
import inspect
import json
import threading
import time
from datetime import datetime, timezone
from fastmcp import FastMCP

import config

LOG_PATH = config.LOG_PATH
MAX_ENTRIES = config.LOG_MAX_ENTRIES

# Argument names whose values are replaced with "[REDACTED]" in the log.
REDACTED_FIELDS = {"api_key", "password", "token", "secret", "access_token"}

_lock = threading.Lock()


def _redact(arguments: dict) -> dict:
    return {
        k: "[REDACTED]" if k in REDACTED_FIELDS else v
        for k, v in arguments.items()
    }


def _write_entry(entry: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False, default=str)
    with _lock:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        _trim_log()


def _trim_log() -> None:
    """Keeps only the last MAX_ENTRIES lines in the log file (called under _lock)."""
    lines = LOG_PATH.read_text(encoding="utf-8").splitlines(keepends=True)
    if len(lines) > MAX_ENTRIES:
        LOG_PATH.write_text("".join(lines[-MAX_ENTRIES:]), encoding="utf-8")


def _build_entry(
    fn_name: str,
    arguments: dict,
    success: bool,
    error: str | None,
    duration_ms: float,
    result_length: int,
) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": fn_name,
        "args": _redact(arguments),
        "success": success,
        "error": error[:300] if error else None,
        "duration_ms": duration_ms,
        "result_length": result_length,
    }


def _wrap(fn):
    """Wraps a tool function with logging. Preserves the original signature."""

    @functools.wraps(fn)
    def logged(*args, **kwargs):
        sig = inspect.signature(fn)
        try:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            arguments = dict(bound.arguments)
        except TypeError:
            arguments = {"_args": args, "_kwargs": kwargs}

        start = time.perf_counter()
        error: str | None = None
        success = True
        result = None

        try:
            result = fn(*args, **kwargs)

            # Tools signal errors via return strings rather than exceptions.
            if isinstance(result, str) and result.startswith("Error"):
                success = False
                error = result

            return result

        except Exception as e:
            success = False
            error = f"{type(e).__name__}: {e}"
            raise

        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            result_length = len(str(result)) if result is not None else 0
            entry = _build_entry(fn.__name__, arguments, success, error, duration_ms, result_length)
            _write_entry(entry)

    return logged


def apply_logging(mcp: FastMCP) -> None:
    """Patches mcp.tool so that all subsequently registered tools are logged."""
    original_tool = mcp.tool

    def logging_tool(*deco_args, **deco_kwargs):
        decorator = original_tool(*deco_args, **deco_kwargs)

        def wrapper(fn):
            return decorator(_wrap(fn))

        return wrapper

    mcp.tool = logging_tool
