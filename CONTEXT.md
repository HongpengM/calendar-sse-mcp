# CONTEXT — calendar-http-mcp

Domain glossary. No implementation details.

## Entry Commands

Three `[project.scripts]` entry points serve different consumers:

| Command | Consumer | Transport | Intent |
|---|---|---|---|
| `calendar-mcp` | Humans in terminal | HTTP + CLI subcommands | Full management CLI (install, run, debug, direct calendar ops) |
| `calendar-stdio` | MCP clients (Claude Desktop, etc.) | STDIO | Zero-argument MCP server; client spawns process, communicates via stdin/stdout |
| `calendar-cli` | Humans in terminal | None (local EventKit) | Flat calendar operations CLI; no server subcommands |

**Distinction rule**: If a command needs HTTP transport management (install/start/stop/logs), it belongs to `calendar-mcp`. If it's a direct calendar operation (create/search/delete), it belongs to `calendar-cli`. If it's an MCP client spawning a server, use `calendar-stdio`.

## Transport Modes

- **STDIO**: Server reads JSON-RPC from stdin, writes to stdout. No network port. Used by MCP clients that spawn subprocesses.
- **Streamable HTTP**: Server listens on a TCP port. Used by LaunchAgent (background service) and HTTP-based MCP clients.

## Calendar Operations

All calendar operations go through `CalendarStore` (EventKit wrapper). They never go through the HTTP server — even the `calendar-mcp cli` commands call `CalendarStore` directly.

## Deprecated / Dead

- `--dev` flag on `calendar-mcp cli`: removed. It assigned a port variable that was never consumed. CLI commands talk to EventKit directly, not via the HTTP server.
