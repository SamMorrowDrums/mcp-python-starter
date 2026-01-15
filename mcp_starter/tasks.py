"""
MCP Tasks (Experimental) - Long-running asynchronous operations.

⚠️ EXPERIMENTAL: Tasks are an experimental feature that may change without notice.

Tasks enable asynchronous request handling in MCP. Instead of blocking until an
operation completes, the server creates a task, returns immediately, and the
client polls for the result.

## When to Use Tasks

Tasks are designed for operations that:
- Take significant time (seconds to minutes)
- Need progress updates during execution
- Require user input mid-execution (elicitation, sampling)
- Should run without blocking the requestor

## Important Notes

Tasks require the low-level Server API, not FastMCP. This file demonstrates
how to create a task-enabled server as an alternative to the FastMCP-based
main server.

To use this server instead:
    python -m mcp_starter.tasks_server

See: https://github.com/modelcontextprotocol/python-sdk/tree/main/docs/experimental
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import anyio
import mcp.types as types
from mcp.server.experimental.task_context import ServerTaskContext
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager


def create_task_server() -> Server:
    """Create and configure a task-enabled MCP server.

    This creates a low-level Server instance with experimental task support.
    Unlike FastMCP, this requires manual handler registration.
    """
    server = Server("mcp-python-starter-tasks")

    # Enable experimental task support
    # This auto-registers handlers for:
    # - tasks/get
    # - tasks/result
    # - tasks/list
    # - tasks/cancel
    server.experimental.enable_tasks()

    # Register tool list handler
    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        """List available tools with their task support level."""
        return [
            types.Tool(
                name="data_processing",
                description="Process data asynchronously with progress updates",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "data_size": {
                            "type": "integer",
                            "description": "Amount of data to process (simulated)",
                            "default": 5,
                        }
                    },
                },
                # TASK_REQUIRED means this tool MUST be called as a task
                execution=types.ToolExecution(taskSupport=types.TASK_REQUIRED),
            ),
            types.Tool(
                name="confirm_action",
                description="Demonstrates elicitation - requests user confirmation",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "The action to confirm",
                        }
                    },
                    "required": ["action"],
                },
                execution=types.ToolExecution(taskSupport=types.TASK_REQUIRED),
            ),
            types.Tool(
                name="generate_content",
                description="Generate content via LLM sampling within a task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt for content generation",
                        }
                    },
                    "required": ["prompt"],
                },
                execution=types.ToolExecution(taskSupport=types.TASK_REQUIRED),
            ),
        ]

    # Tool handlers
    async def handle_data_processing(arguments: dict[str, Any]) -> types.CreateTaskResult:
        """Process data with status updates - demonstrates task progress."""
        ctx = server.request_context
        ctx.experimental.validate_task_mode(types.TASK_REQUIRED)

        data_size = arguments.get("data_size", 5)

        async def work(task: ServerTaskContext) -> types.CallToolResult:
            await task.update_status("Initializing data processing...")
            await anyio.sleep(0.5)

            for i in range(data_size):
                if task.is_cancelled:
                    return types.CallToolResult(
                        content=[types.TextContent(type="text", text="Processing cancelled")]
                    )

                await task.update_status(f"Processing chunk {i + 1}/{data_size}...")
                await anyio.sleep(1)  # Simulate work

            await task.update_status("Finalizing results...")
            await anyio.sleep(0.5)

            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text", text=f"Successfully processed {data_size} chunks of data!"
                    )
                ]
            )

        return await ctx.experimental.run_task(work)

    async def handle_confirm_action(arguments: dict[str, Any]) -> types.CreateTaskResult:
        """Demonstrates elicitation - requests user confirmation."""
        ctx = server.request_context
        ctx.experimental.validate_task_mode(types.TASK_REQUIRED)

        action = arguments.get("action", "perform unknown action")

        async def work(task: ServerTaskContext) -> types.CallToolResult:
            await task.update_status("Waiting for user confirmation...")

            # Request user input via elicitation
            result = await task.elicit(
                message=f"Please confirm: {action}",
                requestedSchema={
                    "type": "object",
                    "properties": {
                        "confirm": {
                            "type": "boolean",
                            "description": "Confirm the action",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Optional reason for your choice",
                        },
                    },
                    "required": ["confirm"],
                },
            )

            if result.action == "accept" and result.content.get("confirm"):
                reason = result.content.get("reason", "No reason provided")
                return types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text", text=f"Action confirmed: {action}\nReason: {reason}"
                        )
                    ]
                )
            else:
                return types.CallToolResult(
                    content=[types.TextContent(type="text", text=f"Action declined: {action}")]
                )

        return await ctx.experimental.run_task(work)

    async def handle_generate_content(arguments: dict[str, Any]) -> types.CreateTaskResult:
        """Generate content via LLM sampling within a task."""
        ctx = server.request_context
        ctx.experimental.validate_task_mode(types.TASK_REQUIRED)

        prompt = arguments.get("prompt", "Write a short greeting")

        async def work(task: ServerTaskContext) -> types.CallToolResult:
            await task.update_status("Preparing to generate content...")
            await anyio.sleep(0.5)

            await task.update_status("Calling LLM for generation...")

            try:
                # Request LLM sampling from the client
                result = await task.create_message(
                    messages=[
                        types.SamplingMessage(
                            role="user",
                            content=types.TextContent(type="text", text=prompt),
                        )
                    ],
                    max_tokens=200,
                )

                if isinstance(result.content, types.TextContent):
                    generated_text = result.content.text
                else:
                    generated_text = "[Non-text response received]"

                return types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text", text=f"Generated content:\n\n{generated_text}"
                        )
                    ]
                )
            except Exception as e:
                return types.CallToolResult(
                    content=[
                        types.TextContent(type="text", text=f"Content generation failed: {e}")
                    ],
                    isError=True,
                )

        return await ctx.experimental.run_task(work)

    # Dispatch tool calls
    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any]
    ) -> types.CallToolResult | types.CreateTaskResult:
        """Route tool calls to appropriate handlers."""
        handlers = {
            "data_processing": handle_data_processing,
            "confirm_action": handle_confirm_action,
            "generate_content": handle_generate_content,
        }

        if name in handlers:
            return await handlers[name](arguments)
        else:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True,
            )

    return server


def run_task_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the task-enabled server with Streamable HTTP transport.

    Tasks require HTTP transport (not stdio) for proper operation.

    Args:
        host: Host to bind to
        port: Port to listen on
    """
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount

    server = create_task_server()
    session_manager = StreamableHTTPSessionManager(app=server)

    @asynccontextmanager
    async def app_lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            yield

    starlette_app = Starlette(
        routes=[Mount("/mcp", app=session_manager.handle_request)],
        lifespan=app_lifespan,
    )

    print(f"MCP Task Server starting on http://{host}:{port}/mcp")
    print("This server demonstrates experimental task support:")
    print("  - data_processing: Long-running task with progress updates")
    print("  - confirm_action: Task with user elicitation")
    print("  - generate_content: Task with LLM sampling")
    print()
    print("Note: Tasks require a compatible MCP client that supports task operations.")

    uvicorn.run(starlette_app, host=host, port=port)


if __name__ == "__main__":
    import sys

    host = "127.0.0.1"
    port = 8000

    # Simple arg parsing
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--host" and i < len(sys.argv):
            host = sys.argv[i + 1]
        elif arg == "--port" and i < len(sys.argv):
            port = int(sys.argv[i + 1])

    run_task_server(host=host, port=port)
