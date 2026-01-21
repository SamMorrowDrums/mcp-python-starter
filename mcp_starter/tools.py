"""
MCP Tools - All tool definitions for the server.

## Tool Annotations

Every tool SHOULD have annotations to help AI assistants understand behavior.

WHY ANNOTATIONS MATTER:
Annotations enable MCP client applications to understand the risk level of
tool calls. Clients can use these hints to implement safety policies, such as:
  - Prompting users for confirmation before executing destructive operations
  - Auto-approving read-only tools while requiring approval for writes
  - Warning users when tools access external systems (openWorldHint)
  - Optimizing retry logic for idempotent operations

ANNOTATION FIELDS:
- readOnlyHint: Tool only reads data, doesn't modify state
- destructiveHint: Tool can permanently delete or modify data
- idempotentHint: Repeated calls with same args have same effect
- openWorldHint: Tool accesses external systems (web, APIs, etc.)

See: https://modelcontextprotocol.io/docs/concepts/tools
"""

from __future__ import annotations

import asyncio
import random
from typing import Annotated, Any, Literal

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession
from mcp.types import Icon, ToolAnnotations
from pydantic import Field

from .icons import (
    ABACUS_ICON,
    HOURGLASS_ICON,
    PACKAGE_ICON,
    ROBOT_ICON,
    SUN_BEHIND_CLOUD_ICON,
    WAVING_HAND_ICON,
)

# Enum type for calculator operations
Operation = Literal["add", "subtract", "multiply", "divide"]

# Track if bonus tool is loaded
_bonus_tool_loaded = False


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server."""

    @mcp.tool(
        annotations=ToolAnnotations(
            title="Say Hello",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
        icons=[
            Icon(
                src=WAVING_HAND_ICON,
                mimeType="image/png",
                sizes=["256x256"],
            ),
        ],
    )
    def hello(
        name: Annotated[str, Field(title="Name", description="Name of the person to greet")],
    ) -> str:
        """Say hello to a person"""
        return f"Hello, {name}! Welcome to MCP."

    @mcp.tool(
        annotations=ToolAnnotations(
            title="Get Weather",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=False,  # Simulated - results vary
            openWorldHint=False,  # Not real external call
        ),
        icons=[
            Icon(
                src=SUN_BEHIND_CLOUD_ICON,
                mimeType="image/png",
                sizes=["256x256"],
            ),
        ],
    )
    def get_weather(
        city: Annotated[str, Field(title="City", description="City name to get weather for")],
    ) -> dict[str, Any]:
        """Get the current weather for a city"""
        conditions = ["sunny", "cloudy", "rainy", "windy"]
        return {
            "location": city,
            "temperature": round(15 + random.random() * 20),
            "unit": "celsius",
            "conditions": random.choice(conditions),
            "humidity": round(40 + random.random() * 40),
        }

    @mcp.tool(
        annotations=ToolAnnotations(
            title="Ask LLM",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=False,  # LLM responses vary
            openWorldHint=False,
        ),
        icons=[
            Icon(
                src=ROBOT_ICON,
                mimeType="image/png",
                sizes=["256x256"],
            ),
        ],
    )
    async def ask_llm(
        prompt: Annotated[
            str, Field(title="Prompt", description="The question or prompt to send to the LLM")
        ],
        ctx: Context[ServerSession, None],
        maxTokens: Annotated[
            int, Field(title="Max Tokens", description="Maximum tokens in response")
        ] = 100,
    ) -> str:
        """Ask the connected LLM a question using sampling"""
        try:
            result = await ctx.session.create_message(
                messages=[
                    {
                        "role": "user",
                        "content": {"type": "text", "text": prompt},
                    }
                ],
                max_tokens=maxTokens,
            )
            if result.content.type == "text":
                return f"LLM Response: {result.content.text}"
            return "LLM Response: [non-text response]"
        except Exception as e:
            return f"Sampling not supported or failed: {e}"

    @mcp.tool(
        annotations=ToolAnnotations(
            title="Long Running Task",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
        icons=[
            Icon(
                src=HOURGLASS_ICON,
                mimeType="image/png",
                sizes=["256x256"],
            ),
        ],
    )
    async def long_task(
        taskName: Annotated[str, Field(title="Task Name", description="Name for this task")],
        ctx: Context[ServerSession, None],
        steps: Annotated[int, Field(title="Steps", description="Number of steps to simulate")] = 5,
    ) -> str:
        """Simulate a long-running task with progress updates"""
        await ctx.info(f"Starting task: {taskName}")

        for i in range(steps):
            await ctx.report_progress(
                progress=i / steps,
                total=1.0,
                message=f"Step {i + 1}/{steps}",
            )
            await asyncio.sleep(1.0)

        await ctx.report_progress(progress=1.0, total=1.0, message="Complete!")

        return f'Task "{taskName}" completed successfully after {steps} steps!'

    @mcp.tool(
        annotations=ToolAnnotations(
            title="Load Bonus Tool",
            readOnlyHint=False,  # Modifies server state
            destructiveHint=False,
            idempotentHint=True,  # Safe to call multiple times
            openWorldHint=False,
        ),
        icons=[
            Icon(
                src=PACKAGE_ICON,
                mimeType="image/png",
                sizes=["256x256"],
            ),
        ],
    )
    async def load_bonus_tool(ctx: Context[ServerSession, None]) -> str:
        """Dynamically register a new bonus tool"""
        global _bonus_tool_loaded

        if _bonus_tool_loaded:
            return "Bonus tool is already loaded! Try calling 'bonus_calculator'."

        @mcp.tool(
            annotations=ToolAnnotations(
                title="Bonus Calculator",
                readOnlyHint=True,
                destructiveHint=False,
                idempotentHint=True,  # Pure computation
                openWorldHint=False,
            ),
            icons=[
                Icon(
                    src=ABACUS_ICON,
                    mimeType="image/png",
                    sizes=["256x256"],
                ),
            ],
        )
        def bonus_calculator(a: float, b: float, operation: Operation) -> str:
            """A calculator that was dynamically loaded.

            Args:
                a: First number
                b: Second number
                operation: Mathematical operation to perform
            """
            ops = {
                "add": a + b,
                "subtract": a - b,
                "multiply": a * b,
                "divide": a / b if b != 0 else float("nan"),
            }
            result = ops.get(operation, float("nan"))
            return f"{a} {operation} {b} = {result}"

        _bonus_tool_loaded = True

        # Notify clients that the tools list has changed
        await ctx.session.send_tool_list_changed()

        return "Bonus tool 'bonus_calculator' has been loaded! The tools list has been updated."

    # =========================================================================
    # Elicitation Tools - Request user input during tool execution
    #
    # WHY ELICITATION MATTERS:
    # Elicitation allows tools to request additional information from users
    # mid-execution, enabling interactive workflows. This is essential for:
    #   - Confirming destructive actions before they happen
    #   - Gathering missing parameters that weren't provided upfront
    #   - Implementing approval workflows for sensitive operations
    #   - Collecting feedback or additional context during execution
    #
    # TWO ELICITATION MODES:
    # - Form (elicit_form): Display a structured form with typed fields
    # - URL (elicit_url): Open a web page (OAuth, feedback form, docs, etc.)
    #
    # RESPONSE ACTIONS:
    # - "accept": User provided the requested information
    # - "decline": User explicitly refused to provide information
    # - "cancel": User dismissed the request without responding
    # =========================================================================

    @mcp.tool(
        annotations=ToolAnnotations(
            title="Confirm Action",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=False,  # User response varies
            openWorldHint=False,
        ),
    )
    async def confirm_action(
        action: Annotated[
            str, Field(title="Action", description="Description of the action to confirm")
        ],
        ctx: Context[ServerSession, None],
        destructive: Annotated[
            bool,
            Field(title="Destructive", description="Whether the action is destructive"),
        ] = False,
    ) -> str:
        """Request user confirmation before proceeding"""
        try:
            # Form elicitation: Display a structured form with typed fields
            # The client renders this as a dialog/form based on the JSON schema
            result = await ctx.session.elicit_form(
                message=f"Please confirm: {action}",
                requestedSchema={
                    "type": "object",
                    "properties": {
                        "confirm": {
                            "type": "boolean",
                            "title": "Confirm",
                            "description": "Confirm the action",
                        },
                        "reason": {
                            "type": "string",
                            "title": "Reason",
                            "description": "Optional reason for your choice",
                        },
                    },
                    "required": ["confirm"],
                },
            )

            if result.action == "accept":
                content = result.content or {}
                if content.get("confirm"):
                    reason = content.get("reason", "No reason provided")
                    return f"Action confirmed: {action}\nReason: {reason}"
                return f"Action declined by user: {action}"
            elif result.action == "decline":
                return f"User declined to respond for: {action}"
            else:  # cancel
                return f"User cancelled elicitation for: {action}"
        except Exception as e:
            return f"Elicitation not supported or failed: {e}"

    @mcp.tool(
        annotations=ToolAnnotations(
            title="Get Feedback",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=False,  # User response varies
            openWorldHint=True,  # Opens external URL
        ),
    )
    async def get_feedback(
        question: Annotated[
            str, Field(title="Question", description="The question to ask the user")
        ],
        ctx: Context[ServerSession, None],
    ) -> str:
        """Request feedback from the user"""
        feedback_url = "https://github.com/SamMorrowDrums/mcp-starters/issues/new?template=workshop-feedback.yml"
        if question:
            feedback_url += f"&title={question}"

        try:
            # URL elicitation: Open a web page in the user's browser
            # Useful for OAuth flows, external forms, documentation links, etc.
            result = await ctx.session.elicit_url(
                message="Please provide feedback on MCP Starters by completing the form at the URL below:",
                url=feedback_url,
            )

            if result.action == "accept":
                return "Thank you for providing feedback! Your input helps improve MCP Starters."
            elif result.action == "decline":
                return f"No problem! Feel free to provide feedback anytime at: {feedback_url}"
            else:  # cancel
                return "Feedback request cancelled."
        except Exception as e:
            return f"URL elicitation not supported or failed: {e}\n\nYou can still provide feedback at: {feedback_url}"
