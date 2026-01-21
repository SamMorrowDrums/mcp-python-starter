# MCP Python Starter - Copilot Coding Agent Instructions

## Building and Testing

- **Install dependencies:**
  ```bash
  uv sync --all-extras
  ```

- **Run the server:**
  ```bash
  uv run mcp-python-starter
  ```

- **Run tests:**
  ```bash
  uv run pytest
  ```

- **Format code:**
  ```bash
  uv run ruff format .
  ```

- **Lint code:**
  ```bash
  uv run ruff check .
  ```

- **Auto-fix lint issues:**
  ```bash
  uv run ruff check --fix .
  ```

## Before Committing Checklist

1. ✅ Run `uv run ruff format .`
2. ✅ Run `uv run ruff check .` and fix any errors
3. ✅ Run `uv run pytest` to verify tests pass
4. ✅ Test the server with `uv run mcp-python-starter`

