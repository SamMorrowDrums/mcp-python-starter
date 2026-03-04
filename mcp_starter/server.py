"""
MCP Python Starter - FastMCP Server

A feature-complete Model Context Protocol server demonstrating:
- Tools with annotations, sampling, progress, and dynamic loading
- Resources (static and dynamic) and templates
- Prompts with completions

Usage:
    uv run mcp-python-starter --stdio     # stdio transport
    uv run mcp-python-starter --http      # HTTP transport (default port 3000)

Documentation: https://modelcontextprotocol.io/
"""

from __future__ import annotations

import click
from mcp.server.fastmcp import FastMCP
from mcp.server.lowlevel.server import NotificationOptions

from .prompts import register_prompts
from .resources import register_resources
from .tools import register_tools

# =============================================================================
# Server Instructions for AI Assistants
# =============================================================================

SERVER_INSTRUCTIONS = """
# MCP Python Starter Server

A demonstration MCP server showcasing Python/FastMCP capabilities.

## Recommended Workflows

1. **Test connectivity** → Call `hello` to verify the server responds
2. **Structured output** → Call `get_weather` to see typed response data
3. **Progress reporting** → Call `long_task` to observe real-time progress notifications
4. **Dynamic tools** → Call `load_bonus_tool`, then re-list tools to see `bonus_calculator` appear
5. **LLM sampling** → Call `ask_llm` to have the server request a completion from the client
6. **Elicitation** → Call `confirm_action` (form-based) or `get_feedback` (URL-based) to request user input

## Multi-Tool Flows

- **Full demo**: `hello` → `get_weather` → `long_task` → `load_bonus_tool` → `bonus_calculator`
- **Dynamic loading**: `load_bonus_tool` triggers a `tools/list_changed` notification — refresh your tool list to see `bonus_calculator`
- **User interaction**: `confirm_action` demonstrates schema elicitation, `get_feedback` demonstrates URL elicitation

## Notes

- All tools include annotations (readOnlyHint, idempotentHint, openWorldHint) to guide safe usage
- Resources and prompts are available for context and templating — use `resources/list` and `prompts/list` to discover them
""".strip()

# Initialize FastMCP server with instructions
mcp = FastMCP(
    "mcp-python-starter",
    instructions=SERVER_INSTRUCTIONS,
)
mcp._mcp_server.version = "1.0.0"

# Enable listChanged notifications for dynamic tool loading (load_bonus_tool).
# FastMCP calls create_initialization_options() without args, which defaults to
# NotificationOptions() with all fields False. Override to inject tools_changed=True.
_original_create_init_options = mcp._mcp_server.create_initialization_options


def _patched_create_init_options(notification_options=None, experimental_capabilities=None):
    if notification_options is None:
        notification_options = NotificationOptions(tools_changed=True)
    return _original_create_init_options(
        notification_options=notification_options,
        experimental_capabilities=experimental_capabilities or {},
    )


mcp._mcp_server.create_initialization_options = _patched_create_init_options

# Register all components
register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)


@click.command()
@click.option("--stdio", is_flag=True, help="Run with stdio transport")
@click.option("--http", is_flag=True, help="Run with HTTP transport")
@click.option("--port", default=3000, help="Port for HTTP transport")
def main(stdio: bool, http: bool, port: int) -> None:
    """MCP Python Starter Server.

    Run with either stdio or HTTP transport.
    """
    if stdio or (not stdio and not http):
        mcp.run(transport="stdio")
    elif http:
        # Port must be set via settings, not run() parameter
        mcp.settings.port = port
        mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
