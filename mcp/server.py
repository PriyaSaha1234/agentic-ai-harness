from mcp.server import MCPServer
from datetime import datetime
import os
import asyncio
import sys


server = MCPServer(
    name="agent-harness-tools",
    version="1.0.0",
)


@server.tool()
def get_time() -> str:
    """Get the current local date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@server.tool()
def list_workspace_files() -> str:
    """List files available in the workspace folder."""

    workspace = "workspace"

    if not os.path.exists(workspace):
        return "Workspace folder does not exist."

    files = os.listdir(workspace)

    if not files:
        return "Workspace is empty."

    return "\n".join(files)


async def main():

    print(
        "MCP server starting...",
        file=sys.stderr,
        flush=True
    )

    print(
        "Available tools: get_time, list_workspace_files",
        file=sys.stderr,
        flush=True
    )

    await server.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())