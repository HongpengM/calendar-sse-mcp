# ADR 0001: Three Entry Commands

Date: 2026-06-08

## Status

Accepted

## Context

The project originally had one `[project.scripts]` entry point (`calendar-mcp`) that served all purposes: CLI calendar operations, HTTP server management, and MCP server invocation. This forced every consumer (human terminal users, MCP clients, background services) to navigate a nested subcommand hierarchy.

Adding STDIO transport support exposed the need to separate concerns:

- MCP clients that spawn subprocesses need a zero-argument command (`calendar-stdio`)
- Terminal users doing quick calendar lookups want a flat CLI without server subcommands mixed in (`calendar-cli`)
- Server operators need the full management CLI (`calendar-mcp`)

## Decision

Add two new `[project.scripts]` entry points alongside the existing one:

1. **`calendar-stdio`** — Zero-argument entry that immediately starts the MCP server with STDIO transport. Designed for MCP client configs (Claude Desktop, etc.) where the command is spawned as a subprocess.

2. **`calendar-cli`** — Flattened CLI that exposes calendar operations directly (`calendars`, `events`, `create`, `update`, `delete`, `search`) without the `cli` subcommand prefix or any server management commands.

3. **`calendar-mcp`** (existing, retained) — Full management CLI with `cli` and `server` subcommands. Not deprecated; remains available for backward compatibility.

## Consequences

- Three entry points instead of one, but each has a clear, narrow purpose
- `calendar-mcp` retains all existing behavior — no breakage for LaunchAgent installations or scripts
- `calendar-stdio` and `calendar-cli` have minimal surface area, reducing confusion
- Removed dead `--dev` flag from `calendar-mcp cli` during this cleanup
