# AGENTS.md

This file provides context for AI coding agents working in this repository.

## Project Overview

**MCP Python Starter** is a feature-complete Model Context Protocol (MCP) server template in Python using FastMCP. It demonstrates all major MCP features including tools, resources, resource templates, prompts, sampling, progress updates, and dynamic tool loading.

**Purpose**: Workshop starter template for learning MCP server development.

## Technology Stack

- **Runtime**: Python 3.11+
- **MCP SDK**: `mcp` (FastMCP)
- **HTTP Server**: uvicorn
- **CLI**: Click
- **Package Manager**: uv (recommended) or pip

## Project Structure

```
mcp_starter/
├── __init__.py
└── server.py       # Main server with all MCP features

.vscode/
├── mcp.json            # MCP server configuration for VS Code
├── tasks.json          # Build/run tasks
├── launch.json         # Debug configurations
└── extensions.json     # Recommended extensions

.devcontainer/
└── devcontainer.json   # DevContainer configuration

pyproject.toml          # Package configuration and tool settings
```

## Build & Run Commands

```bash
# Using uv (recommended)
uv sync                      # Install dependencies
uv run mcp-python-starter    # Run server (stdio)
uv run mcp-python-starter --http  # Run server (HTTP)

# Using pip
pip install -e ".[dev]"      # Install with dev dependencies
python -m mcp_starter.server # Run server (stdio)
python -m mcp_starter.server --http  # Run server (HTTP)
```

## Linting & Formatting

```bash
# Using uv
uv run ruff check .          # Lint code
uv run ruff check --fix .    # Fix lint issues
uv run ruff format .         # Format code

# Using pip (after installing dev deps)
ruff check .
ruff check --fix .
ruff format .

# Type checking
uv run pyright
# or
pyright
```

## Testing

```bash
uv run pytest
# or
pytest
```

## Key Files to Modify

- **Add/modify tools**: `mcp_starter/server.py` → functions with `@mcp.tool()` decorator
- **Add/modify resources**: `mcp_starter/server.py` → functions with `@mcp.resource()` decorator
- **Add/modify prompts**: `mcp_starter/server.py` → functions with `@mcp.prompt()` decorator
- **Package config**: `pyproject.toml`
- **HTTP port/config**: `mcp_starter/server.py` → `main()` function

## MCP Features Implemented

| Feature | Location | Description |
|---------|----------|-------------|
| `hello` tool | `server.py` | Basic tool with annotations |
| `get_weather` tool | `server.py` | Structured JSON output |
| `ask_llm` tool | `server.py` | Sampling/LLM invocation |
| `long_task` tool | `server.py` | Progress updates |
| `load_bonus_tool` | `server.py` | Dynamic tool loading |
| Resources | `server.py` | Static `info://about`, `file://example.md` |
| Templates | `server.py` | `greeting://{name}`, `data://items/{id}` |
| Prompts | `server.py` | `greet`, `code_review` with arguments |

## Environment Variables

- `PORT` - HTTP server port (default: 3000)

## Conventions

- Use FastMCP decorators (`@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`)
- Type hints on all functions
- Docstrings for tools (used as MCP descriptions)
- Use Ruff for linting and formatting
- Follow PEP 8 style guide

## Code Quality Tools

All configured in `pyproject.toml`:
- **Ruff**: Linting + formatting (replaces Black, isort, flake8)
- **Pyright**: Type checking

## Documentation Links

- [MCP Specification](https://modelcontextprotocol.io/)
- [Python SDK (FastMCP)](https://github.com/modelcontextprotocol/python-sdk)
- [Building Servers](https://modelcontextprotocol.io/docs/develop/build-server)
- [uv Package Manager](https://docs.astral.sh/uv/)
