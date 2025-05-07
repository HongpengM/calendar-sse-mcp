# Managing Calendar SSE MCP as a Launch Agent

This document explains how to install, run, and manage the Calendar SSE MCP server as a background service on macOS using the `calendar-sse server` commands.

## Overview

The `calendar-sse server` subcommand provides comprehensive tools for managing the Calendar SSE MCP server as a background service (Launch Agent) on macOS. This allows the server to:

- Run in the background without keeping a terminal window open
- Start automatically when you log in
- Be easily monitored, started, stopped, and restarted

## Installation

To install the server as a Launch Agent:

```bash
# Basic installation with default settings
calendar-sse server install

# Customize the port and log directory
calendar-sse server install --port 5000 --logdir ~/logs

# Install without auto-starting the server
calendar-sse server install --no-load

# Install as a development server on port 27213
calendar-sse server install --dev
```

This creates a property list file (`plist`) in your `~/Library/LaunchAgents/` directory that tells macOS how to run the server.

### What the installation does

1. Creates a plist file in `~/Library/LaunchAgents/com.calendar-sse-mcp.plist` (or with your custom name)
2. Configures it to run the server on the specified port
3. Sets up logging to the specified directory
4. Automatically loads the agent (unless `--no-load` is specified)

> **Note:** When using via `uvx`, you can update to the latest version and reinstall in one step with:
> ```bash
> uvx --refresh --from calendar-sse-mcp calendar-sse server install
> ```

## Managing the Server

### Starting the Server

If the server isn't already running or was installed with `--no-load`:

```bash
calendar-sse server start
```

### Stopping the Server

```bash
calendar-sse server stop
```

### Restarting the Server

Useful after making configuration changes:

```bash
calendar-sse server restart
```

### Checking Status and Viewing Logs

```bash
# View all logs
calendar-sse server logs

# View only error logs
calendar-sse server logs --level error

# View only info logs
calendar-sse server logs --level info

# View more log lines
calendar-sse server logs --lines 50
```

### Uninstalling the Server

To completely remove the Launch Agent:

```bash
calendar-sse server uninstall
```

This will:
1. Stop the running server (if it's running)
2. Remove the plist file from `~/Library/LaunchAgents/`

## Running the Server Directly (for Testing)

To run the server directly in the foreground (useful for testing or debugging):

```bash
calendar-sse server run

# Customize the host and port
calendar-sse server run --host 0.0.0.0 --port 5000
```

When running this way, the server will run until you press `Ctrl+C` to stop it, or close the terminal window.

## Troubleshooting

If you encounter issues with the Launch Agent:

1. Check the server logs:
   ```bash
   calendar-sse server logs --level error
   ```

2. Try uninstalling and reinstalling the Launch Agent:
   ```bash
   calendar-sse server uninstall
   calendar-sse server install
   ```

3. Make sure the port you're trying to use isn't already in use:
   ```bash
   lsof -i :27212  # Replace with your port number
   ```

4. Try running the server directly to see any immediate errors:
   ```bash
   calendar-sse server run
   ```

## Advanced Configuration

### Custom Launch Agent Name

You can customize the Launch Agent name:

```bash
calendar-sse server install --name com.mycompany.calendar-mcp
```

When using a custom name, you'll need to specify it for other operations:

```bash
calendar-sse server start --name com.mycompany.calendar-mcp
calendar-sse server logs --name com.mycompany.calendar-mcp
``` 