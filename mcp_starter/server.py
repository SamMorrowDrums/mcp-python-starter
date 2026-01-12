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

from .prompts import register_prompts
from .resources import register_resources
from .tools import register_tools

# =============================================================================
# Server Instructions for AI Assistants
# =============================================================================

SERVER_INSTRUCTIONS = """
# MCP Python Starter Server

A demonstration MCP server showcasing Python/FastMCP capabilities.

## Available Tools

### Greeting & Demos
- **hello**: Simple greeting - use to test connectivity
- **get_weather**: Returns simulated weather data
- **long_task**: Demonstrates progress reporting (takes ~5 seconds)

### LLM Interaction
- **ask_llm**: Invoke LLM sampling to ask questions (requires client support)

### Dynamic Features
- **load_bonus_tool**: Dynamically adds a calculator tool at runtime
- **bonus_calculator**: Available after calling load_bonus_tool

## Available Resources

- **config://settings**: Server configuration as JSON
- **status://server**: Current server status
- **notes://{name}**: Dynamic notes by name (e.g., notes://example)

## Available Prompts

- **greeting**: Generates a personalized greeting
- **code_review**: Structured code review prompt

## Recommended Workflows

1. **Testing Connection**: Call `hello` with your name to verify the server is responding
2. **Weather Demo**: Call `get_weather` with a location to see structured output
3. **Progress Demo**: Call `long_task` to see progress notifications
4. **Dynamic Loading**: Call `load_bonus_tool`, then refresh tools to see `bonus_calculator`

## Tool Annotations

All tools include annotations indicating:
- Whether they modify state (readOnlyHint)
- If they're safe to retry (idempotentHint)
- Whether they access external systems (openWorldHint)

Use these hints to make informed decisions about tool usage.
""".strip()

# Initialize FastMCP server with instructions
mcp = FastMCP(
    "mcp-python-starter",
    version="1.0.0",
    instructions=SERVER_INSTRUCTIONS,
)

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
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
