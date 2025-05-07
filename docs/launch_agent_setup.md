# Managing Calendar-SSE-MCP as a Launch Agent

This document explains how to install, run, and manage the Calendar SSE MCP server as a background service on macOS using the `server` command-line tool.

## Overview of the `server` command

The `server` script is the primary tool for managing the Calendar SSE MCP as a background Launch Agent. It provides subcommands to handle the lifecycle of the service.

Usage:
```bash
# Via uvx (recommended)
uvx --from calendar-sse-mcp server [subcommand] [options]

# Directly (if installed in current environment)
# python -m calendar_sse_mcp.server_cli_main [subcommand] [options] 
# Note: The exact direct command depends on how you have your Python environment and PATH set up.
# Using uvx is generally more reliable for CLI tools from packages.
```

## Available Subcommands

| Subcommand  | Description                                                     |
|-------------|-----------------------------------------------------------------|
| `install`   | Installs the server as a Launch Agent and starts it.            |
| `uninstall` | Stops and uninstalls the Launch Agent.                          |
| `start`     | Starts the Launch Agent if it's not already running.            |
| `stop`      | Stops the Launch Agent if it's running.                         |
| `restart`   | Stops and then restarts the Launch Agent.                       |
| `update`    | Reinstalls the package and then reinstalls and restarts the agent.|
| `logs`      | Displays logs from the Launch Agent.                            |

## Detailed Subcommand Usage

### `server install`

Installs and configures the Calendar SSE MCP as a Launch Agent. This will also attempt to start the agent immediately after installation.

```bash
# Install with default settings
uvx --from calendar-sse-mcp server install

# Install with custom port and log directory
uvx --from calendar-sse-mcp server install --port 5001 --logdir ~/calendar_mcp_logs

# Install with a custom agent name (advanced)
uvx --from calendar-sse-mcp server install --name com.my.custom.calendar.mcp
```

**Options for `install`:**
- `--port PORT`: Port for the server to listen on (default: 27212).
- `--logdir DIR`: Directory to store log files (default: `/tmp`).
- `--name AGENT_NAME`: Custom name for the Launch Agent plist (default: `com.calendar-sse-mcp`).
- `--no-load`: Install the agent but do not automatically start it.

### `server uninstall`

Stops the Launch Agent (if running) and removes its plist file from `~/Library/LaunchAgents/`.

```bash
# Uninstall with default agent name
uvx --from calendar-sse-mcp server uninstall

# Uninstall with a custom agent name
uvx --from calendar-sse-mcp server uninstall --name com.my.custom.calendar.mcp
```

**Options for `uninstall`:**
- `--name AGENT_NAME`: Name of the Launch Agent to uninstall (important if a custom name was used during install).

### `server start`

Starts the Launch Agent. If the agent is already loaded, it may indicate that.

```bash
# Start the default agent
uvx --from calendar-sse-mcp server start

# Start a custom named agent
uvx --from calendar-sse-mcp server start --name com.my.custom.calendar.mcp
```

**Options for `start`:**
- `--name AGENT_NAME`: Name of the Launch Agent to start.

### `server stop`

Stops the Launch Agent.

```bash
# Stop the default agent
uvx --from calendar-sse-mcp server stop

# Stop a custom named agent
uvx --from calendar-sse-mcp server stop --name com.my.custom.calendar.mcp
```

**Options for `stop`:**
- `--name AGENT_NAME`: Name of the Launch Agent to stop.

### `server restart`

Effectively stops and then starts the Launch Agent. Useful for applying configuration changes that require a full service restart.

```bash
# Restart the default agent
uvx --from calendar-sse-mcp server restart

# Restart a custom named agent
uvx --from calendar-sse-mcp server restart --name com.my.custom.calendar.mcp
```

**Options for `restart`:**
- `--name AGENT_NAME`: Name of the Launch Agent to restart.

### `server update`

This command first attempts to uninstall any existing Launch Agent with the specified name. Then, it uses `uv pip install --force-reinstall calendar-sse-mcp` to update the package from PyPI. Finally, it runs the `install` process for the Launch Agent with the provided (or default) options.

```bash
# Update the package and reinstall the default agent
uvx --refresh --from calendar-sse-mcp server update

# Update and specify custom settings for the reinstalled agent
uvx --refresh --from calendar-sse-mcp server update --port 5002 --logdir ~/new_logs
```

**Options for `update`:**
- `--port PORT`, `--logdir DIR`, `--name AGENT_NAME`, `--no-load`: Same as for `install`, applied to the reinstallation of the agent.
- The `--refresh` flag for `uvx` is recommended to ensure it fetches the latest package information before reinstalling.

### `server logs`

Displays the standard output and standard error logs for the Launch Agent. By default, it shows the last 10 lines of each.

```bash
# Show logs for the default agent
uvx --from calendar-sse-mcp server logs

# Show only error logs
uvx --from calendar-sse-mcp server logs --level error

# Show all available info logs (stdout)
uvx --from calendar-sse-mcp server logs --level info

# Show logs for a custom named agent
uvx --from calendar-sse-mcp server logs --name com.my.custom.calendar.mcp

# Show more lines (e.g., last 50 lines)
uvx --from calendar-sse-mcp server logs --lines 50
```

**Options for `logs`:**
- `--level {all,info,error}`: Specifies which logs to display (default: `all`). `info` shows stdout, `error` shows stderr.
- `--name AGENT_NAME`: Name of the Launch Agent whose logs to show.
- `--lines N`: Number of recent lines to show from each log file (default: 10).

## What the `server install` Command Does

When you run `server install`, it:
1. Determines the path to the Python interpreter (or `uv` if available and configured for use).
2. Determines the path to the `calendar_sse_mcp.server` module.
3. Creates a properly formatted `.plist` file for `launchd`.
   - This plist file is configured to run the server, typically using a command like `uv run calendar_sse_mcp.server` or `python -m calendar_sse_mcp.server`.
   - It includes specified port and environment variables for logging.
4. Places the plist file in your user's `~/Library/LaunchAgents/` directory (e.g., `~/Library/LaunchAgents/com.calendar-sse-mcp.plist`).
5. Sets up the service to start automatically when you log in.
6. Configures logging to the specified directory (e.g., `/tmp/com.calendar-sse-mcp-stdout.log` and `/tmp/com.calendar-sse-mcp-stderr.log`).
7. Unless `--no-load` is specified, it attempts to load (start) the Launch Agent immediately using `launchctl load`.

## Manual `launchctl` Management (Advanced)

While the `server` command provides a user-friendly interface, you can also manage the Launch Agent directly using macOS's `launchctl` command. This can be useful for advanced troubleshooting.

The typical name for the agent is `com.calendar-sse-mcp`, and its plist file is located at `~/Library/LaunchAgents/com.calendar-sse-mcp.plist` (unless a custom name was used).

### Check if the service is running
```bash
launchctl list | grep com.calendar-sse-mcp # Replace with custom name if used
```

### Unload (stop) the service
```bash
launchctl unload ~/Library/LaunchAgents/com.calendar-sse-mcp.plist
```

### Load (start) the service
```bash
launchctl load ~/Library/LaunchAgents/com.calendar-sse-mcp.plist
```

## Troubleshooting

- **Use `server logs`**: This is the first step to check for errors.
  ```bash
  uvx --from calendar-sse-mcp server logs --level error
  ```
- **Permissions**: Ensure Calendar.app permissions are granted.
  1. If the server has never run successfully, try running it directly in the foreground once to trigger the permission dialog: `uvx --from calendar-sse-mcp calendar-mcp server`
  2. Go to System Settings > Privacy & Security > Automation.
  3. Verify that your terminal application (e.g., Terminal, iTerm2) or Python/uv has permission to control Calendar.app.
- **Plist file**: Check the content of `~/Library/LaunchAgents/com.calendar-sse-mcp.plist` (or your custom named file) to ensure paths and commands are correct.
- **`launchctl` errors**: If `server start` or `server stop` fail, try the manual `launchctl load -w <plist_path>` or `launchctl unload -w <plist_path>` commands and observe any direct error messages.

## Important Notes

- The Launch Agent runs in the user's context, so it will only run when the user is logged in.
- If you change your Python environment significantly (e.g., switch to a different Python version or move `uv`), you may need to reinstall the Launch Agent using `server update` or `server uninstall` followed by `server install`. 