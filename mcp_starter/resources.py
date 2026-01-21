"""MCP Resources - All resource and template definitions for the server."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

# Example data for resources
ITEMS_DATA: dict[str, dict[str, str]] = {
    "1": {"name": "Widget", "description": "A useful widget"},
    "2": {"name": "Gadget", "description": "A fancy gadget"},
    "3": {"name": "Gizmo", "description": "A mysterious gizmo"},
}


def register_resources(mcp: FastMCP) -> None:
    """Register all resources and templates with the MCP server."""

    @mcp.resource("about://server", name="About", description="Information about this MCP server")
    def about_resource() -> str:
        """Information about this MCP server."""
        return """MCP Python Starter v1.0.0

This is a feature-complete MCP server demonstrating:
- Tools with annotations and structured output
- Resources (static and dynamic)
- Resource templates
- Prompts with completions
- Sampling, progress updates, and dynamic tool loading

For more information, visit: https://modelcontextprotocol.io"""

    @mcp.resource(
        "doc://example", name="Example Document", description="An example document resource"
    )
    def example_file() -> str:
        """An example markdown document."""
        return """# Example Document

This is an example markdown document served as an MCP resource.

## Features

- **Bold text** and *italic text*
- Lists and formatting
- Code blocks

```python
hello = "world"
```

## Links

- [MCP Documentation](https://modelcontextprotocol.io)
- [Python SDK](https://github.com/modelcontextprotocol/python-sdk)
"""

    @mcp.resource(
        "greeting://{name}",
        name="Personalized Greeting",
        description="A personalized greeting for a specific person",
    )
    def greeting_template(name: str) -> str:
        """Generate a personalized greeting.

        Args:
            name: Name to include in greeting
        """
        return f"Hello, {name}! This greeting was generated just for you."

    @mcp.resource(
        "item://{id}",
        name="Item Data",
        description="Data for a specific item by ID",
    )
    def item_data(id: str) -> str:
        """Get data for a specific item by ID.

        Args:
            id: The item ID to look up
        """
        item = ITEMS_DATA.get(id)
        if not item:
            raise ValueError(f"Item not found: {id}")
        return json.dumps({"id": id, **item}, indent=2)
