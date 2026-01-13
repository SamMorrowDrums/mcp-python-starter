"""
MCP Tools - All tool definitions for the server.

## Tool Annotations

Every tool MUST have annotations to help AI assistants understand behavior:
- readOnlyHint: Tool only reads data, doesn't modify state
- destructiveHint: Tool can permanently delete or modify data
- idempotentHint: Repeated calls with same args have same effect
- openWorldHint: Tool accesses external systems (web, APIs, etc.)

See: https://modelcontextprotocol.io/docs/concepts/tools
"""

from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING, Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.session import ServerSession
from mcp.types import Icon, ToolAnnotations

from .icons import (
    ABACUS_ICON,
    HOURGLASS_ICON,
    PACKAGE_ICON,
    ROBOT_ICON,
    SUN_BEHIND_CLOUD_ICON,
    WAVING_HAND_ICON,
)

if TYPE_CHECKING:
    from mcp.server.fastmcp import Context

# Enum type for calculator operations
Operation = Literal["add", "subtract", "multiply", "divide"]

# Track if bonus tool is loaded
_bonus_tool_loaded = False

# =============================================================================
# Common annotation patterns for reuse across tools
# =============================================================================

# Read-only tool that doesn't modify any state
ANNOTATIONS_READ_ONLY = ToolAnnotations(
    title="Read Only",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

# Tool that simulates external data (weather, APIs, etc.)
ANNOTATIONS_SIMULATED_EXTERNAL = ToolAnnotations(
    title="Simulated External Data",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=False,  # Results vary due to simulation
    openWorldHint=False,  # Simulated, not real external calls
)

# Tool that invokes LLM sampling
ANNOTATIONS_SAMPLING = ToolAnnotations(
    title="LLM Sampling",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=False,  # LLM responses vary
    openWorldHint=False,  # Uses connected client, not external
)

# Tool that mutates server state
ANNOTATIONS_STATE_MUTATING = ToolAnnotations(
    title="State Mutating",
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=True,  # Loading twice is safe
    openWorldHint=False,
)

# Pure computation tool
ANNOTATIONS_PURE_COMPUTATION = ToolAnnotations(
    title="Pure Computation",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


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
    def hello(name: str) -> str:
        """A friendly greeting tool that says hello to someone.

        Args:
            name: The name to greet
        """
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
    def get_weather(location: str) -> dict[str, Any]:
        """Get current weather for a location (simulated).

        Args:
            location: City name or coordinates
        """
        conditions = ["sunny", "cloudy", "rainy", "windy"]
        return {
            "location": location,
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
        prompt: str,
        ctx: Context[ServerSession, None],
        max_tokens: int = 100,
    ) -> str:
        """Ask the connected LLM a question using sampling.

        Args:
            prompt: The question or prompt for the LLM
            max_tokens: Maximum tokens in response
        """
        try:
            result = await ctx.session.create_message(
                messages=[
                    {
                        "role": "user",
                        "content": {"type": "text", "text": prompt},
                    }
                ],
                max_tokens=max_tokens,
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
        task_name: str,
        ctx: Context[ServerSession, None],
    ) -> str:
        """A task that takes 5 seconds and reports progress along the way.

        Args:
            task_name: Name for this task
        """
        steps = 5

        await ctx.info(f"Starting task: {task_name}")

        for i in range(steps):
            await ctx.report_progress(
                progress=i / steps,
                total=1.0,
                message=f"Step {i + 1}/{steps}",
            )
            await asyncio.sleep(1.0)

        await ctx.report_progress(progress=1.0, total=1.0, message="Complete!")

        return f'Task "{task_name}" completed successfully after {steps} steps!'

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
    def load_bonus_tool() -> str:
        """Dynamically loads a bonus tool that wasn't available at startup."""
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
        return "Bonus tool 'bonus_calculator' has been loaded! Refresh your tools list to see it."

    # =========================================================================
    # Elicitation Tools - Demonstrate requesting user input during tool execution
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
        action: str,
        ctx: Context[ServerSession, None],
    ) -> str:
        """Demonstrates elicitation - requests user confirmation before proceeding.

        Args:
            action: The action to confirm with the user
        """
        try:
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
        ctx: Context[ServerSession, None],
        topic: str = "",
    ) -> str:
        """Demonstrates URL elicitation - opens a feedback form in the browser.

        Args:
            topic: Optional topic for the feedback
        """
        feedback_url = "https://github.com/SamMorrowDrums/mcp-starters/issues/new?template=workshop-feedback.yml"
        if topic:
            feedback_url += f"&title={topic}"

        try:
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
