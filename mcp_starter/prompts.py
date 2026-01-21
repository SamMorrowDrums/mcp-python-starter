"""MCP Prompts - All prompt definitions for the server."""

from __future__ import annotations

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field


def register_prompts(mcp: FastMCP) -> None:
    """Register all prompts with the MCP server.

    Note: The Python MCP SDK's PromptArgument model does not support a 'title' field,
    only 'name', 'description', and 'required'. This is a limitation of the SDK compared
    to the canonical MCP interface. The 'description' field is used for both purposes.
    """

    @mcp.prompt(
        title="Greeting Prompt",
        description="Generate a greeting message",
    )
    def greet(
        name: Annotated[str, Field(title="Name", description="Name of the person to greet")],
        style: Annotated[
            str,
            Field(title="Style", description="Greeting style (formal/casual)"),
        ] = "casual",
    ) -> str:
        """Generate a greeting prompt.

        Args:
            name: Name of the person to greet
            style: The greeting style (formal, casual, or enthusiastic)
        """
        styles = {
            "formal": f"Please compose a formal, professional greeting for {name}.",
            "casual": f"Write a casual, friendly hello to {name}.",
            "enthusiastic": f"Create an excited, enthusiastic greeting for {name}!",
        }
        return styles.get(style, styles["casual"])

    @mcp.prompt(
        title="Code Review",
        description="Review code for potential improvements",
    )
    def code_review(
        code: Annotated[str, Field(title="Code", description="The code to review")],
        language: Annotated[
            str,
            Field(title="Language", description="Programming language of the code"),
        ] = "python",
        focus: Annotated[
            str,
            Field(
                title="Focus",
                description="What to focus on (security, performance, readability, or all)",
            ),
        ] = "all",
    ) -> str:
        """Generate a code review prompt.

        Args:
            code: The code to review
            language: Programming language
            focus: What to focus on (security, performance, readability, or all)
        """
        focus_instructions = {
            "security": "Focus on security vulnerabilities and potential exploits.",
            "performance": "Focus on performance optimizations and efficiency issues.",
            "readability": "Focus on code clarity, naming, and maintainability.",
            "all": "Provide a comprehensive review covering security, performance, and readability.",
        }

        instruction = focus_instructions.get(focus, focus_instructions["all"])
        return f"""Please review the following {language} code. {instruction}

```{language}
{code}
```"""
