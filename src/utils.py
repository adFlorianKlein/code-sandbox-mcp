from pathlib import Path

WORKSPACE = Path("/workspace")


def _resolve(path: str) -> Path:
    """Resolves *path* relative to WORKSPACE and raises ValueError if it escapes."""
    resolved = (WORKSPACE / path).resolve()
    if not resolved.is_relative_to(WORKSPACE):
        raise ValueError(f"Path '{path}' is outside /workspace")
    return resolved


def _auth_header(url: str, api_key: str) -> str:
    """Returns the appropriate HTTP auth header value for the given remote URL."""
    is_gitlab = "gitlab" in url.lower()
    return f"PRIVATE-TOKEN: {api_key}" if is_gitlab else f"Authorization: Bearer {api_key}"


def _embed_credentials(url: str, username: str, api_key: str) -> str:
    """Embeds username + api_key into a URL, stripping any existing credentials."""
    scheme, rest = url.split("://", 1)
    if "@" in rest:
        rest = rest.split("@", 1)[1]
    return f"{scheme}://{username}:{api_key}@{rest}"


def _git_auth_args(url: str, api_key: str, username: str | None) -> list[str]:
    """Returns the git CLI arguments needed to authenticate against *url*.

    With username  → credentials are embedded in the URL itself.
    Without        → an http.extraHeader config flag is returned instead.
    """
    if username:
        return [_embed_credentials(url, username, api_key)]
    return ["-c", f"http.extraHeader={_auth_header(url, api_key)}"]
