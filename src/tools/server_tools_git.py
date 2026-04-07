import os
import subprocess
from pathlib import Path

from fastmcp import FastMCP

import config
from utils import _git_auth_args


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    def git_clone_repo(url: str, api_key: str | None = None, username: str | None = None) -> str:
        """Clones a git repository into /workspace. Authenticates via Authorization header.
        api_key and username fall back to GIT_TOKEN / GIT_USER_NAME from the environment."""
        api_key = api_key or config.GIT_TOKEN
        username = username or config.GIT_USER_NAME
        if not api_key:
            return "Error: api_key not provided and GIT_TOKEN is not set"

        repo_name = Path(url.rstrip("/")).stem.removesuffix(".git")
        target = f"/workspace/{repo_name}"

        auth_args = _git_auth_args(url, api_key, username)
        if username:
            cmd = ["git", "clone", auth_args[0], target]
        else:
            cmd = ["git", "clone"] + auth_args + [url, target]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        return f"Cloned '{repo_name}' to {target}"

    @mcp.tool()
    def git_commit(
        repo_name: str,
        message: str,
        files: list[str],
        author_name: str | None = None,
        author_email: str | None = None,
    ) -> str:
        """Stages the given files and creates a local git commit in /workspace/<repo_name>.
        author_name and author_email fall back to GIT_USER_NAME / GIT_USER_EMAIL from the environment.

        Args:
            repo_name: Name of the repository directory inside /workspace.
            message: Commit message.
            files: List of file paths to stage (relative to the repo root). Pass ["."] to stage everything.
            author_name: Optional git author name (overrides env and repo/global config).
            author_email: Optional git author email (overrides env and repo/global config).
        """
        author_name = author_name or config.GIT_USER_NAME
        author_email = author_email or config.GIT_USER_EMAIL
        workdir = f"/workspace/{repo_name}"

        stage_result = subprocess.run(
            ["git", "add", "--"] + files,
            capture_output=True,
            text=True,
            cwd=workdir,
        )
        if stage_result.returncode != 0:
            return f"Error staging files: {stage_result.stderr}"

        env_overrides = {}
        if author_name:
            env_overrides["GIT_AUTHOR_NAME"] = author_name
            env_overrides["GIT_COMMITTER_NAME"] = author_name
        if author_email:
            env_overrides["GIT_AUTHOR_EMAIL"] = author_email
            env_overrides["GIT_COMMITTER_EMAIL"] = author_email

        commit_result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            cwd=workdir,
            env={**os.environ, **env_overrides},
        )
        if commit_result.returncode != 0:
            return f"Error committing: {commit_result.stderr}"
        return commit_result.stdout.strip()

    @mcp.tool()
    def git_push(
        repo_name: str,
        api_key: str | None = None,
        remote: str = "origin",
        branch: str | None = None,
        username: str | None = None,
        force: bool = False,
    ) -> str:
        """Pushes commits from /workspace/<repo_name> to the remote repository.
        api_key and username fall back to GIT_TOKEN / GIT_USER_NAME from the environment.

        Args:
            repo_name: Name of the repository directory inside /workspace.
            api_key: Personal access token (falls back to GIT_TOKEN env var).
            remote: Remote name to push to (default: "origin").
            branch: Branch to push. If omitted, pushes the current branch.
            username: Username for auth (falls back to GIT_USER_NAME env var).
            force: If True, adds --force-with-lease to the push command.
        """
        api_key = api_key or config.GIT_TOKEN
        username = username or config.GIT_USER_NAME
        if not api_key:
            return "Error: api_key not provided and GIT_TOKEN is not set"

        workdir = f"/workspace/{repo_name}"

        url_result = subprocess.run(
            ["git", "remote", "get-url", remote],
            capture_output=True,
            text=True,
            cwd=workdir,
        )
        if url_result.returncode != 0:
            return f"Error resolving remote URL: {url_result.stderr}"
        remote_url = url_result.stdout.strip()

        auth_args = _git_auth_args(remote_url, api_key, username)
        if username:
            push_cmd = ["git", "push"] + auth_args
        else:
            push_cmd = ["git", "push"] + auth_args + [remote]

        if branch:
            push_cmd.append(branch)
        if force:
            push_cmd.append("--force-with-lease")

        result = subprocess.run(push_cmd, capture_output=True, text=True, cwd=workdir)
        if result.returncode != 0:
            return f"Error pushing: {result.stderr}"
        return result.stdout.strip() or "Push successful."
