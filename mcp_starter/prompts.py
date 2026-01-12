"""MCP Prompts - All prompt definitions for the server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register all prompts with the MCP server."""

    @mcp.prompt(
        title="Greeting Prompt",
        description="Generate a greeting in a specific style",
    )
    def greet(name: str, style: str = "casual") -> str:
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
        description="Request a code review with specific focus areas",
    )
    def code_review(code: str, language: str, focus: str = "all") -> str:
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
