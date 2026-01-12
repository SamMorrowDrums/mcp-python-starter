# MCP Python Starter

A feature-complete Model Context Protocol (MCP) server template in Python using FastMCP. This starter demonstrates all major MCP features with clean, Pythonic code.

## 📚 Documentation

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Guide](https://modelcontextprotocol.io/docs/develop/build-server)

## ✨ Features

| Category | Feature | Description |
|----------|---------|-------------|
| **Tools** | `hello` | Basic tool with annotations |
| | `get_weather` | Tool returning structured data |
| | `ask_llm` | Tool that invokes LLM sampling |
| | `long_task` | Tool with 5-second progress updates |
| | `load_bonus_tool` | Dynamically loads a new tool |
| **Resources** | `info://about` | Static informational resource |
| | `file://example.md` | File-based markdown resource |
| **Templates** | `greeting://{name}` | Personalized greeting |
| | `data://items/{id}` | Data lookup by ID |
| **Prompts** | `greet` | Greeting in various styles |
| | `code_review` | Code review with focus areas |

## 🚀 Quick Start

### Prerequisites

- [Python 3.11+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/SamMorrowDrums/mcp-python-starter.git
cd mcp-python-starter

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### Running the Server

**stdio transport** (for local development):
```bash
uv run mcp-python-starter --stdio
```

**HTTP transport** (for remote/web deployment):
```bash
uv run mcp-python-starter --http --port 3000
```

## 🔧 VS Code Integration

This project includes VS Code configuration for seamless development:

1. Open the project in VS Code
2. The MCP configuration is in `.vscode/mcp.json`
3. Test the server using VS Code's MCP tools

### Using DevContainers

1. Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Open command palette: "Dev Containers: Reopen in Container"
3. Everything is pre-configured and ready to use!

## 📁 Project Structure

```
.
├── mcp_starter/
│   ├── __init__.py
│   ├── tools.py       # Tool definitions (hello, get_weather, ask_llm, etc.)
│   ├── resources.py   # Resource and template definitions
│   ├── prompts.py     # Prompt definitions
│   └── server.py      # Server orchestration (imports and wires modules)
├── .vscode/
│   ├── mcp.json       # MCP server configuration
│   ├── settings.json  # Python settings
│   └── extensions.json
├── .devcontainer/
│   └── devcontainer.json
├── pyproject.toml     # Project configuration (uv/pip, Ruff config)
└── .python-version
```

## 🛠️ Development

```bash
# Run the server (Python reloads automatically on changes)
uv run mcp-python-starter --stdio

# Use MCP Inspector for debugging
uv run mcp dev mcp_starter/server.py

# Format code
uv run ruff format .

# Lint
uv run ruff check .

# Lint with auto-fix
uv run ruff check --fix .

# Type check
uv run pyright
```

### Live Reload

Python scripts reload automatically when run with `uv run`. For enhanced debugging,
use `mcp dev` which provides the MCP Inspector UI.

## 🔍 MCP Inspector

The [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) is an essential development tool for testing and debugging MCP servers.

### Running Inspector

```bash
# Option 1: Use the built-in mcp dev command (recommended for Python)
uv run mcp dev mcp_starter/server.py

# Option 2: Use the npm-based inspector
npx @modelcontextprotocol/inspector uv run mcp-python-starter --stdio

# Option 3: Point to module directly
npx @modelcontextprotocol/inspector uv run python -m mcp_starter.server --stdio
```

### What Inspector Provides

- **Tools Tab**: List and invoke all registered tools with parameters
- **Resources Tab**: Browse and read resources and templates
- **Prompts Tab**: View and test prompt templates
- **Logs Tab**: See JSON-RPC messages between client and server
- **Schema Validation**: Verify tool input/output schemas

### Debugging Tips

1. Start Inspector before connecting your IDE/client
2. Use the "Logs" tab to see exact request/response payloads
3. Test tool annotations (ToolAnnotations) are exposed correctly
4. Verify progress notifications appear for `long_task`
5. Check that Context injection works for sampling tools

## 📖 Feature Examples

### Tool with Annotations (FastMCP decorator)

```python
@mcp.tool(
    title="Say Hello",
    description="A friendly greeting tool",
    annotations={"readOnlyHint": True},
)
def hello(name: str) -> str:
    """Say hello to someone.
    
    Args:
        name: The name to greet
    """
    return f"Hello, {name}!"
```

### Resource Template

```python
@mcp.resource("greeting://{name}")
def greeting_template(name: str) -> str:
    """Generate a personalized greeting."""
    return f"Hello, {name}!"
```

### Tool with Progress Updates

```python
@mcp.tool(title="Long Task")
async def long_task(
    task_name: str,
    ctx: Context[ServerSession, None],
) -> str:
    for i in range(5):
        await ctx.report_progress(
            progress=i / 5,
            total=1.0,
            message=f"Step {i + 1}/5",
        )
        await asyncio.sleep(1.0)
    return "Done!"
```

### Tool with Sampling

```python
@mcp.tool(title="Ask LLM")
async def ask_llm(
    prompt: str,
    ctx: Context[ServerSession, None],
) -> str:
    result = await ctx.session.create_message(
        messages=[{"role": "user", "content": {"type": "text", "text": prompt}}],
        max_tokens=100,
    )
    return result.content.text
```

## 🔐 Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

## 🤝 Contributing

Contributions welcome! Please ensure your changes maintain feature parity with other language starters.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
