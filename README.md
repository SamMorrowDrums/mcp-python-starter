# MCP Python Starter

A minimal Model Context Protocol (MCP) server implemented in Python, matching the features and structure of the TypeScript starter.

## Features
- **Hello Tool**: Returns a greeting using the `MCP_GREETING` environment variable.
- **Markdown Resource**: Serves a static markdown file from `resources/example.md`.
- **Prompt**: Simple prompt handler example.
- **Environment-based configuration**: Reads greeting and secret from environment variables.
- **VS Code integration**: `.vscode/mcp.json` for easy server launch with input prompts.
- **Devcontainer support**: (Optional, add `.devcontainer` if needed)
- **Tests**: (Add tests as needed)

## Quickstart

1. **Install dependencies**

   ```sh
   pip install .
   ```

2. **Run the server**

   ```sh
   python server.py stdio
   ```

3. **Use with MCP client or VS Code**

   Use the provided `.vscode/mcp.json` to launch the server with custom inputs.

## Project Structure

- `server.py` — Main MCP server implementation
- `resources/example.md` — Example markdown resource
- `.vscode/mcp.json` — VS Code MCP server config
- `.gitignore` — Standard Python ignores

## License

MIT
