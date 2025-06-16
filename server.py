import json
import multiprocessing
import socket
import time
from collections.abc import Generator
from typing import Any
from unittest import result
import uvicorn
from pydantic import AnyUrl
from starlette.applications import Starlette
from starlette.requests import Request

import mcp.types as types
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.resources import FunctionResource
from mcp.shared.context import RequestContext
from mcp.server.fastmcp import Context
from mcp.types import (
    CreateMessageRequestParams,
    CreateMessageResult,
    GetPromptResult,
    InitializeResult,
    ReadResourceResult,
    SamplingMessage,
    TextContent,
    TextResourceContents,
)
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

# Tool: hello sampling
@mcp.tool()
async def say_hello_sampling(name: str,  ctx: Context) -> str:
    """Say hello to a user with a configurable greeting - with sampling to improve the response."""
    greeting = os.environ.get("MCP_GREETING", "Hello")
    await ctx.info(f"Requesting sampling for greeting: {greeting}")

    result = await ctx.session.create_message(
        messages=[SamplingMessage(role="user", content=TextContent(type="text", text=f"write a letter with the greeting: {greeting} addressed to: {name}!"))],
        max_tokens=800,
        temperature=0.7,
    )
    return result.content.text


if __name__ == "__main__":
    mcp.run()

