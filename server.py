from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("MCP Python Starter")

# Tool: hello
@mcp.tool()
def say_hello(name: str) -> str:
    """Say hello to a user with a configurable greeting."""
    greeting = os.environ.get("MCP_GREETING", "Hello")
    return f"{greeting}, {name}!"

# Resource: example markdown
@mcp.resource("example://md")
def example_md() -> str:
    """Serve the example markdown file as a resource."""
    with open("resources/example.md", "r", encoding="utf-8") as f:
        return f.read()

# Prompt: greeting
@mcp.prompt()
def greeting_prompt(name: str = "friend") -> str:
    return f"Say hello to {name}!"

if __name__ == "__main__":
    mcp.run()
