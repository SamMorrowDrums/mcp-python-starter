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
from uuid import uuid4

from mcp.server.mcpserver import Context, MCPServer
from mcp.types import (
    CreateMessageRequest,
    CreateMessageRequestParams,
    CreateMessageResult,
    CreateMessageResultWithTools,
    ElicitRequest,
    ElicitRequestFormParams,
    ElicitRequestURLParams,
    ElicitResult,
    Icon,
    InputRequiredResult,
    SamplingMessage,
    TextContent,
    ToolAnnotations,
)
from mcp_types.version import MODERN_PROTOCOL_VERSIONS
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


def register_tools(mcp: MCPServer) -> None:
    """Register all tools with the MCP server."""

    @mcp.tool(
        title="Say Hello",
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
        icons=[
            Icon(
                src=WAVING_HAND_ICON,
                mime_type="image/png",
                sizes=["256x256"],
            ),
        ],
    )
    def hello(
        name: Annotated[str, Field(description="Name of the person to greet")],
    ) -> str:
        """Say hello to a person"""
        return f"Hello, {name}! Welcome to MCP."

    @mcp.tool(
        title="Get Weather",
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=False,  # Simulated - results vary
            open_world_hint=False,  # Not real external call
        ),
        icons=[
            Icon(
                src=SUN_BEHIND_CLOUD_ICON,
                mime_type="image/png",
                sizes=["256x256"],
            ),
        ],
    )
    def get_weather(
        city: Annotated[str, Field(description="City name to get weather for")],
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
        title="Ask LLM",
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=False,  # LLM responses vary
            open_world_hint=False,
        ),
        icons=[
            Icon(
                src=ROBOT_ICON,
                mime_type="image/png",
                sizes=["256x256"],
            ),
        ],
    )
    async def ask_llm(
        prompt: Annotated[str, Field(description="The question or prompt to send to the LLM")],
        ctx: Context,
        maxTokens: Annotated[int, Field(description="Maximum tokens in response")] = 100,
    ) -> str | InputRequiredResult:
        """Ask the connected LLM a question using sampling"""
        try:
            messages = [SamplingMessage(role="user", content=TextContent(text=prompt))]
            if ctx.protocol_version in MODERN_PROTOCOL_VERSIONS:
                result = (ctx.input_responses or {}).get("sampling")
                if result is None:
                    return InputRequiredResult(
                        input_requests={
                            "sampling": CreateMessageRequest(
                                params=CreateMessageRequestParams(
                                    messages=messages, max_tokens=maxTokens
                                )
                            )
                        },
                        request_state="ask_llm",
                    )
                if ctx.request_state != "ask_llm":
                    raise ValueError("Missing or invalid sampling request state")
                if not isinstance(result, (CreateMessageResult, CreateMessageResultWithTools)):
                    raise ValueError("Invalid sampling response")
            else:
                result = await ctx.session.create_message(messages=messages, max_tokens=maxTokens)
            if isinstance(result.content, TextContent):
                return f"LLM Response: {result.content.text}"
            return "LLM Response: [non-text response]"
        except Exception as e:
            return f"Sampling not supported or failed: {e}"

    @mcp.tool(
        title="Long Running Task",
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        ),
        icons=[
            Icon(
                src=HOURGLASS_ICON,
                mime_type="image/png",
                sizes=["256x256"],
            ),
        ],
    )
    async def long_task(
        taskName: Annotated[str, Field(description="Name for this task")],
        ctx: Context,
        steps: Annotated[int, Field(description="Number of steps to simulate")] = 5,
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
        title="Load Bonus Tool",
        annotations=ToolAnnotations(
            read_only_hint=False,  # Modifies server state
            destructive_hint=False,
            idempotent_hint=True,  # Safe to call multiple times
            open_world_hint=False,
        ),
        icons=[
            Icon(
                src=PACKAGE_ICON,
                mime_type="image/png",
                sizes=["256x256"],
            ),
        ],
    )
    async def load_bonus_tool(ctx: Context) -> str:
        """Dynamically register a new bonus tool"""
        global _bonus_tool_loaded

        if _bonus_tool_loaded:
            return "Bonus tool is already loaded! Try calling 'bonus_calculator'."

        @mcp.tool(
            title="Bonus Calculator",
            annotations=ToolAnnotations(
                read_only_hint=True,
                destructive_hint=False,
                idempotent_hint=True,  # Pure computation
                open_world_hint=False,
            ),
            icons=[
                Icon(
                    src=ABACUS_ICON,
                    mime_type="image/png",
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

        await ctx.notify_tools_changed()
        if ctx.protocol_version != "2026-07-28":
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
        title="Confirm Action",
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=False,  # User response varies
            open_world_hint=False,
        ),
    )
    async def confirm_action(
        action: Annotated[str, Field(description="Description of the action to confirm")],
        ctx: Context,
        destructive: Annotated[
            bool,
            Field(description="Whether the action is destructive"),
        ] = False,
    ) -> str | InputRequiredResult:
        """Request user confirmation before proceeding"""
        try:
            # Form elicitation: Display a structured form with typed fields
            # The client renders this as a dialog/form based on the JSON schema
            message = f"Please confirm: {action}"
            schema = {
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
            }
            if ctx.protocol_version in MODERN_PROTOCOL_VERSIONS:
                result = (ctx.input_responses or {}).get("confirmation")
                if result is None:
                    return InputRequiredResult(
                        input_requests={
                            "confirmation": ElicitRequest(
                                params=ElicitRequestFormParams(
                                    message=message, requested_schema=schema
                                )
                            )
                        },
                        request_state="confirm_action",
                    )
                if ctx.request_state != "confirm_action":
                    raise ValueError("Missing or invalid confirmation request state")
                if not isinstance(result, ElicitResult):
                    raise ValueError("Invalid elicitation response")
            else:
                result = await ctx.session.elicit_form(message=message, requested_schema=schema)

            if result.action == "accept":
                content = result.content or {}
                if not isinstance(content.get("confirm"), bool) or (
                    "reason" in content and not isinstance(content["reason"], str)
                ):
                    raise ValueError("Invalid confirmation response")
                if content["confirm"]:
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
        title="Get Feedback",
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=False,  # User response varies
            open_world_hint=True,  # Opens external URL
        ),
    )
    async def get_feedback(
        question: Annotated[str, Field(description="The question to ask the user")],
        ctx: Context,
    ) -> str | InputRequiredResult:
        """Request feedback from the user"""
        feedback_url = "https://github.com/SamMorrowDrums/mcp-starters/issues/new?template=workshop-feedback.yml"
        if question:
            feedback_url += f"&title={question}"

        try:
            # URL elicitation: Open a web page in the user's browser
            # Useful for OAuth flows, external forms, documentation links, etc.
            message = (
                "Please provide feedback on MCP Starters by completing the form at the URL below:"
            )
            if ctx.protocol_version in MODERN_PROTOCOL_VERSIONS:
                result = (ctx.input_responses or {}).get("feedback")
                if result is None:
                    return InputRequiredResult(
                        input_requests={
                            "feedback": ElicitRequest(
                                params=ElicitRequestURLParams(message=message, url=feedback_url)
                            )
                        },
                        request_state="get_feedback",
                    )
                if ctx.request_state != "get_feedback":
                    raise ValueError("Missing or invalid feedback request state")
                if not isinstance(result, ElicitResult):
                    raise ValueError("Invalid elicitation response")
            else:
                result = await ctx.session.elicit_url(
                    message=message, url=feedback_url, elicitation_id=str(uuid4())
                )

            if result.action == "accept":
                return "Thank you for providing feedback! Your input helps improve MCP Starters."
            elif result.action == "decline":
                return f"No problem! Feel free to provide feedback anytime at: {feedback_url}"
            else:  # cancel
                return "Feedback request cancelled."
        except Exception as e:
            return f"URL elicitation not supported or failed: {e}\n\nYou can still provide feedback at: {feedback_url}"
