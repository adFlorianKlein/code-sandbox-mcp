import tools.server_tools_build as server_tools_build
import tools.server_tools_filesystem as server_tools_filesystem
import tools.server_tools_git as server_tools_git
import config
from fastmcp import FastMCP
from logging_middleware import apply_logging


mcp = FastMCP("code-sandbox")

# Apply logging before any tools are registered so every tool is covered.
apply_logging(mcp)

server_tools_git.register(mcp)
server_tools_filesystem.register(mcp)
server_tools_build.register(mcp)

if __name__ == "__main__":
    mcp.run(
        transport=config.MCP_TRANSPORT,
        host=config.MCP_HOST,
        port=config.MCP_PORT,
        show_banner=False,
    )
