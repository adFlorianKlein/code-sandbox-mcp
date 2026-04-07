import fnmatch
import re
import shutil
import subprocess

from fastmcp import FastMCP

from utils import WORKSPACE, _resolve


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    def ls(path: str = ".") -> str:
        """Lists the contents of a directory inside /workspace.

        Args:
            path: Directory path relative to /workspace (default: workspace root).
        """
        try:
            target = _resolve(path)
        except ValueError as e:
            return f"Error: {e}"

        if not target.exists():
            return f"Error: '{path}' does not exist"
        if not target.is_dir():
            return f"Error: '{path}' is not a directory"

        entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name))
        lines = [f"{e.name}{'/' if e.is_dir() else ''}" for e in entries]
        return "\n".join(lines) if lines else "(empty)"

    @mcp.tool()
    def read_file(path: str) -> str:
        """Returns the content of a file inside /workspace.

        Args:
            path: File path relative to /workspace.
        """
        try:
            target = _resolve(path)
        except ValueError as e:
            return f"Error: {e}"

        if not target.exists():
            return f"Error: '{path}' does not exist"
        if not target.is_file():
            return f"Error: '{path}' is not a file"

        return target.read_text(encoding="utf-8", errors="replace")

    @mcp.tool()
    def write_file(path: str, content: str) -> str:
        """Creates or overwrites a file inside /workspace with the given content.

        Args:
            path: File path relative to /workspace.
            content: Text content to write.
        """
        try:
            target = _resolve(path)
        except ValueError as e:
            return f"Error: {e}"

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Written {len(content)} characters to '{path}'"

    @mcp.tool()
    def edit_file(path: str, old_string: str, new_string: str) -> str:
        """Replaces the first occurrence of *old_string* with *new_string* in a file.
        Returns an error if *old_string* is not found or is ambiguous (multiple matches).

        Args:
            path: File path relative to /workspace.
            old_string: Exact string to search for (must match exactly once).
            new_string: Replacement string.
        """
        try:
            target = _resolve(path)
        except ValueError as e:
            return f"Error: {e}"

        if not target.exists():
            return f"Error: '{path}' does not exist"

        original = target.read_text(encoding="utf-8", errors="replace")
        count = original.count(old_string)
        if count == 0:
            return "Error: old_string not found in file"
        if count > 1:
            return f"Error: old_string found {count} times — provide more context to make it unique"

        target.write_text(original.replace(old_string, new_string, 1), encoding="utf-8")
        return f"Replaced 1 occurrence in '{path}'"

    @mcp.tool()
    def glob(pattern: str, path: str = ".") -> str:
        """Returns all files matching a glob pattern inside /workspace.

        Args:
            pattern: Glob pattern (e.g. '**/*.py', '*.txt').
            path: Directory to search in, relative to /workspace (default: workspace root).
        """
        try:
            base = _resolve(path)
        except ValueError as e:
            return f"Error: {e}"

        matches = []
        for match in sorted(base.rglob("*")):
            if not match.is_file():
                continue
            if fnmatch.fnmatch(match.name, pattern.split("/")[-1]) or match.match(pattern):
                try:
                    matches.append(str(match.relative_to(WORKSPACE)))
                except ValueError:
                    pass

        return "\n".join(matches) if matches else "(no matches)"

    @mcp.tool()
    def grep(pattern: str, path: str = ".", glob_pattern: str = "*") -> str:
        """Searches for a regex pattern in files inside /workspace and returns matching lines.

        Args:
            pattern: Regular expression to search for.
            path: Directory to search in, relative to /workspace (default: workspace root).
            glob_pattern: Only search files whose name matches this glob (e.g. '*.py').
        """
        try:
            base = _resolve(path)
        except ValueError as e:
            return f"Error: {e}"

        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"Error: invalid regex — {e}"

        results = []
        for file in sorted(base.rglob("*")):
            if not file.is_file():
                continue
            if not fnmatch.fnmatch(file.name, glob_pattern):
                continue
            try:
                for lineno, line in enumerate(file.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if regex.search(line):
                        results.append(f"{file.relative_to(WORKSPACE)}:{lineno}: {line}")
            except OSError:
                continue

        return "\n".join(results) if results else "(no matches)"

    @mcp.tool()
    def delete_file(path: str) -> str:
        """Deletes a single file inside /workspace.

        Args:
            path: File path relative to /workspace.
        """
        try:
            target = _resolve(path)
        except ValueError as e:
            return f"Error: {e}"

        if not target.exists():
            return f"Error: '{path}' does not exist"
        if not target.is_file():
            return f"Error: '{path}' is not a file — use delete_project to remove directories"

        target.unlink()
        return f"Deleted '{path}'"

    @mcp.tool()
    def delete_project(repo_name: str) -> str:
        """Deletes a project directory from /workspace.

        If the directory is a git repository, deletion is blocked when:
        - there are uncommitted changes (staged or unstaged), or
        - there are local commits not yet pushed to the remote.

        Non-git directories are deleted without checks.

        Args:
            repo_name: Name of the project directory inside /workspace.
        """
        try:
            target = _resolve(repo_name)
        except ValueError as e:
            return f"Error: {e}"

        if not target.exists():
            return f"Error: '{repo_name}' does not exist"
        if not target.is_dir():
            return f"Error: '{repo_name}' is not a directory"

        # Only run git checks when the directory is actually a git repo.
        is_git = (target / ".git").exists()
        if is_git:
            # Uncommitted changes (staged or unstaged)
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=target,
            )
            if status.returncode != 0:
                return f"Error checking git status: {status.stderr.strip()}"
            if status.stdout.strip():
                return (
                    "Error: repository has uncommitted changes — "
                    "commit or stash them before deleting"
                )

            # Unpushed commits — try tracking branch first, fall back to any remote branch
            unpushed = subprocess.run(
                ["git", "log", "@{u}..HEAD", "--oneline"],
                capture_output=True, text=True, cwd=target,
            )
            if unpushed.returncode != 0:
                # No upstream configured — check if there are commits and no remote at all
                has_commits = subprocess.run(
                    ["git", "log", "--oneline", "-1"],
                    capture_output=True, text=True, cwd=target,
                )
                has_remote = subprocess.run(
                    ["git", "remote"],
                    capture_output=True, text=True, cwd=target,
                )
                if has_commits.stdout.strip() and not has_remote.stdout.strip():
                    return (
                        "Error: repository has commits but no remote configured — "
                        "push to a remote before deleting"
                    )
            elif unpushed.stdout.strip():
                count = len(unpushed.stdout.strip().splitlines())
                return (
                    f"Error: repository has {count} unpushed commit(s) — "
                    "push them before deleting"
                )

        shutil.rmtree(target)
        return f"Deleted project '{repo_name}'"
