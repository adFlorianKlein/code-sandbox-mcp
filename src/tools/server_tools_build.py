import subprocess

from fastmcp import FastMCP

import config
from utils import WORKSPACE, _resolve

# Executables that may be invoked via run_command.
# Extend this list when new runtimes/build tools are added to the container.
ALLOWED_EXECUTABLES = {
    # JVM
    "mvn", "mvnw", "./mvnw",
    "gradle", "gradlew", "./gradlew",
    "java", "javac",
    # Node / JS
    "node", "npm", "npx", "yarn", "pnpm",
    # Python
    "python", "python3", "pip", "pip3", "pytest",
    # Generic
    "make",
}


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    def run_command(
        executable: str,
        args: list[str],
        repo_name: str,
        timeout: int | None = None,
    ) -> str:
        """Runs a build/test command inside /workspace/<repo_name>.

        Only a fixed set of executables is allowed (mvn, gradle, npm, node, …).
        The working directory is always inside /workspace — path traversal is blocked.

        Args:
            executable: The program to run (e.g. 'mvn', 'npm', './gradlew').
            args: Arguments to pass (e.g. ['test', '-q'] or ['clean', 'install']).
            repo_name: Subdirectory of /workspace to use as working directory.
            timeout: Maximum runtime in seconds (falls back to RUN_COMMAND_TIMEOUT env var, default 120).
        """
        timeout = timeout or config.RUN_COMMAND_TIMEOUT
        if executable not in ALLOWED_EXECUTABLES:
            allowed = ", ".join(sorted(ALLOWED_EXECUTABLES))
            return f"Error: '{executable}' is not allowed. Permitted executables: {allowed}"

        try:
            workdir = _resolve(repo_name)
        except ValueError as e:
            return f"Error: {e}"

        if not workdir.exists():
            return f"Error: '{repo_name}' does not exist in /workspace"
        if not workdir.is_dir():
            return f"Error: '{repo_name}' is not a directory"

        try:
            result = subprocess.run(
                [executable] + args,
                capture_output=True,
                text=True,
                cwd=workdir,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return f"Error: command timed out after {timeout}s"
        except FileNotFoundError:
            return f"Error: '{executable}' not found — is it installed in the container?"

        output = "\n".join(filter(None, [result.stdout.strip(), result.stderr.strip()]))
        if result.returncode != 0:
            return f"Command failed (exit {result.returncode}):\n{output}"
        return output or "Command completed successfully (no output)."
