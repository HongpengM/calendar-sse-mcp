# Calendar SSE MCP Command-line Tools

This document describes the comprehensive command-line interface included with the Calendar SSE MCP package.

## Installation

Once installed, you can access the CLI through either:

```bash
# If installed with pip
calendar-mcp [command] [options]

# Or directly with the module
python -m calendar_sse_mcp [command] [options]
```

## Available Commands

| Command | Description |
|---------|-------------|
| `server` | Run the MCP server |
| `install` | Install as an MCP server in Claude |
| `launchagent` | Create and install a macOS Launch Agent |
| `calendars` | List all available calendars |
| `events` | Get events from a calendar |
| `create` | Create a new event |
| `update` | Update an existing event |
| `delete` | Delete an event |
| `search` | Search for events |

## Server Command

Run the MCP server:

```bash
calendar-mcp server [options]
```

Options:
- `--host HOST` - Host to bind server to (default: 127.0.0.1)
- `--port PORT` - Port to bind server to (default: 27212)

## Install Command

Install the MCP server in Claude:

```bash
calendar-mcp install [options]
```

Options:
- `--name NAME` - Custom name for the server
- `--env-file FILE, -f FILE` - Environment file to load variables from
- `--env-vars VAR, -v VAR` - Environment variables in KEY=VALUE format (can be repeated)

## Launch Agent Command

Create and install a macOS Launch Agent for running the service in the background:

```bash
calendar-mcp launchagent [options]
```

Options:
- `--host HOST` - Host to bind server to (default: 127.0.0.1)
- `--port PORT` - Port to bind server to (default: 27212)
- `--logdir DIR` - Directory for log files (default: /tmp)
- `--load` - Automatically load the Launch Agent after creation

### What the Launch Agent Tool Does

When you run the launchagent command, it:

1. Finds the `uv` executable in your PATH
2. Creates a properly formatted plist file that uses `uv run` to run the server
3. Places it in your user's `~/Library/LaunchAgents/` directory
4. Configures the service to start automatically when you log in
5. Sets up appropriate logging in the specified directory
6. Optionally loads the Launch Agent immediately if `--load` is specified

## Calendars Command

List all available calendars in Calendar.app:

```bash
calendar-mcp calendars [options]
```

Options:
- `--json` - Output in JSON format

## Events Command

Get events from a specific calendar:

```bash
calendar-mcp events CALENDAR [options]
```

Arguments:
- `CALENDAR` - Name of the calendar to get events from

Options:
- `--start-date DATE` - Start date in format YYYY-MM-DD
- `--end-date DATE` - End date in format YYYY-MM-DD
- `--json` - Output in JSON format

## Create Command

Create a new event in a calendar:

```bash
calendar-mcp create CALENDAR SUMMARY [options]
```

Arguments:
- `CALENDAR` - Name of the calendar to create the event in
- `SUMMARY` - Event title/summary

Options:
- `--date DATE` - Event date in format YYYY-MM-DD (default: today)
- `--start-time TIME` - Start time in format HH:MM (default: current time)
- `--end-time TIME` - End time in format HH:MM (calculated from duration if not provided)
- `--duration MINUTES` - Duration in minutes (default: 60)
- `--location LOCATION` - Event location
- `--description TEXT` - Event description
- `--json` - Output in JSON format

## Update Command

Update an existing event:

```bash
calendar-mcp update CALENDAR EVENT_ID [options]
```

Arguments:
- `CALENDAR` - Name of the calendar containing the event
- `EVENT_ID` - ID of the event to update

Options:
- `--summary TEXT` - New event title/summary
- `--date DATE` - New event date in format YYYY-MM-DD
- `--start-time TIME` - New start time in format HH:MM
- `--end-time TIME` - New end time in format HH:MM
- `--location LOCATION` - New event location
- `--description TEXT` - New event description
- `--json` - Output in JSON format

## Delete Command

Delete an event:

```bash
calendar-mcp delete CALENDAR EVENT_ID [options]
```

Arguments:
- `CALENDAR` - Name of the calendar containing the event
- `EVENT_ID` - ID of the event to delete

Options:
- `--json` - Output in JSON format

## Search Command

Search for events:

```bash
calendar-mcp search QUERY [options]
```

Arguments:
- `QUERY` - Search term (case-insensitive)

Options:
- `--calendar CALENDAR` - Specific calendar to search in (optional)
- `--start-date DATE` - Start date in format YYYY-MM-DD
- `--end-date DATE` - End date in format YYYY-MM-DD
- `--json` - Output in JSON format

## JSON Output

All commands support a `--json` flag that outputs the results in JSON format, which is useful for scripting and integration with other tools.

## Examples

### List all calendars

```bash
calendar-mcp calendars
```

### Create a new event

```bash
# Create a meeting at 10:00 AM today for 1 hour
calendar-mcp create "Work" "Team Meeting" --start-time 10:00

# Create a detailed event
calendar-mcp create "Personal" "Dinner with Friends" \
  --date 2023-09-15 \
  --start-time 19:30 \
  --end-time 22:00 \
  --location "Joe's Restaurant" \
  --description "Reservation for 4 people"
```

### Update an event

```bash
# Update the event title
calendar-mcp update "Work" "CA0C1456-F7C8-4FD5-B8C3-8A2F9D3CE7B9" --summary "Team Sync"

# Update multiple fields
calendar-mcp update "Work" "CA0C1456-F7C8-4FD5-B8C3-8A2F9D3CE7B9" \
  --start-time 14:30 \
  --end-time 15:30 \
  --location "Conference Room B"
```

### Search for events

```bash
# Search for events containing "meeting"
calendar-mcp search "meeting"

# Search in a specific calendar and date range
calendar-mcp search "lunch" --calendar "Personal" --start-date 2023-09-01 --end-date 2023-09-30
``` 