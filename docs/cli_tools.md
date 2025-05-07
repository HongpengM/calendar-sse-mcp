# Calendar SSE MCP Command-line Tools

This document describes the command-line interface for directly interacting with calendars and the MCP server using the `calendar-mcp` script. For managing the server as a background Launch Agent (installing, starting, stopping, viewing logs, etc.), please refer to the [Launch Agent Setup Guide](launch_agent_setup.md) which details the `server` command.

## Accessing the `calendar-mcp` CLI

Once the package is installed, you can access this CLI through:

```bash
# Via uvx (recommended for tools from packages)
uvx --from calendar-sse-mcp calendar-mcp [command] [options]

# Or directly if your environment is set up for it
# python -m calendar_sse_mcp [command] [options]
# calendar-mcp [command] [options] (if bin scripts are on PATH)
```

## Available `calendar-mcp` Commands

| Command     | Description                                          |
|-------------|------------------------------------------------------|
| `server`    | Run the MCP server in the foreground.                  |
| `install`   | Install the server for use with Claude.              |
| `calendars` | List all available calendars.                        |
| `events`    | Get events from a calendar.                          |
| `create`    | Create a new event.                                  |
| `update`    | Update an existing event.                            |
| `delete`    | Delete an event.                                     |
| `search`    | Search for events.                                   |
| `--version` | Show version information.                            |

## `calendar-mcp server` Command

Run the MCP server directly in the foreground. This is useful for testing or if you don't want to use a Launch Agent.

```bash
calendar-mcp server [options]
# or via uvx
uvx --from calendar-sse-mcp calendar-mcp server [options]
```

**Options:**
- `--host HOST` - Host to bind server to (default: 127.0.0.1)
- `--port PORT` - Port to bind server to (default: 27212)

## `calendar-mcp install` Command

Install the MCP server for use with an AI assistant like Claude. This command typically registers the server with the MCP tooling.

```bash
calendar-mcp install [options]
# or via uvx
uvx --from calendar-sse-mcp calendar-mcp install [options]
```

**Options:**
- `--name NAME` - Custom name for the server in the AI assistant.
- `--env-file FILE, -f FILE` - Environment file to load variables from when the AI assistant calls the server.
- `--env-vars VAR, -v VAR` - Environment variables in KEY=VALUE format (can be repeated) for the AI assistant.

## `calendar-mcp calendars` Command

List all available calendars in Calendar.app:

```bash
calendar-mcp calendars [options]
# or via uvx
uvx --from calendar-sse-mcp calendar-mcp calendars [options]
```

**Options:**
- `--json` - Output in JSON format

## `calendar-mcp events` Command

Get events from a specific calendar:

```bash
calendar-mcp events CALENDAR [options]
# or via uvx
uvx --from calendar-sse-mcp calendar-mcp events CALENDAR [options]
```

**Arguments:**
- `CALENDAR` - Name of the calendar to get events from

**Options:**
- `--start-date DATE` - Start date in format YYYY-MM-DD
- `--end-date DATE` - End date in format YYYY-MM-DD
- `--json` - Output in JSON format

## `calendar-mcp create` Command

Create a new event in a calendar:

```bash
calendar-mcp create CALENDAR SUMMARY [options]
# or via uvx
uvx --from calendar-sse-mcp calendar-mcp create CALENDAR SUMMARY [options]
```

**Arguments:**
- `CALENDAR` - Name of the calendar to create the event in (can be omitted if `DEFAULT_CALENDAR` is in `.env`).
- `SUMMARY` - Event title/summary

**Options:**
- `--date DATE` - Event date in format YYYY-MM-DD (default: today)
- `--start-time TIME` - Start time in format HH:MM (default: current time)
- `--end-time TIME` - End time in format HH:MM (calculated from duration if not provided)
- `--duration MINUTES` - Duration in minutes (default: 60, or from `.env` `EVENT_DURATION_MINUTES`)
- `--location LOCATION` - Event location
- `--description TEXT` - Event description
- `--json` - Output in JSON format

## `calendar-mcp update` Command

Update an existing event:

```bash
calendar-mcp update CALENDAR EVENT_ID [options]
# or via uvx
uvx --from calendar-sse-mcp calendar-mcp update CALENDAR EVENT_ID [options]
```

**Arguments:**
- `CALENDAR` - Name of the calendar containing the event
- `EVENT_ID` - ID of the event to update

**Options:**
- `--summary TEXT` - New event title/summary
- `--date DATE` - New event date in format YYYY-MM-DD
- `--start-time TIME` - New start time in format HH:MM
- `--end-time TIME` - New end time in format HH:MM
- `--location LOCATION` - New event location
- `--description TEXT` - New event description
- `--json` - Output in JSON format

## `calendar-mcp delete` Command

Delete an event:

```bash
calendar-mcp delete CALENDAR EVENT_ID [options]
# or via uvx
uvx --from calendar-sse-mcp calendar-mcp delete CALENDAR EVENT_ID [options]
```

**Arguments:**
- `CALENDAR` - Name of the calendar containing the event
- `EVENT_ID` - ID of the event to delete

**Options:**
- `--json` - Output in JSON format

## `calendar-mcp search` Command

Search for events:

```bash
calendar-mcp search QUERY [options]
# or via uvx
uvx --from calendar-sse-mcp calendar-mcp search QUERY [options]
```

**Arguments:**
- `QUERY` - Search term (case-insensitive)

**Options:**
- `--calendar CALENDAR` - Specific calendar to search in (optional, searches all if omitted).
- `--start-date DATE` - Start date in format YYYY-MM-DD
- `--end-date DATE` - End date in format YYYY-MM-DD
- `--json` - Output in JSON format

## JSON Output

Most `calendar-mcp` commands support a `--json` flag that outputs the results in JSON format, which is useful for scripting and integration with other tools.

## Examples

### List all calendars

```bash
uvx --from calendar-sse-mcp calendar-mcp calendars
```

### Create a new event

```bash
# Create a meeting at 10:00 AM today for 1 hour in "Work" calendar
uvx --from calendar-sse-mcp calendar-mcp create "Work" "Team Meeting" --start-time 10:00

# Create a detailed event in "Personal" calendar
uvx --from calendar-sse-mcp calendar-mcp create "Personal" "Dinner with Friends" \
  --date 2023-09-15 \
  --start-time 19:30 \
  --end-time 22:00 \
  --location "Joe's Restaurant" \
  --description "Reservation for 4 people"
```

### Update an event

```bash
# Update the event title in "Work" calendar
uvx --from calendar-sse-mcp calendar-mcp update "Work" "CA0C1456-..." --summary "Team Sync"

# Update multiple fields
uvx --from calendar-sse-mcp calendar-mcp update "Work" "CA0C1456-..." \
  --start-time 14:30 \
  --end-time 15:30 \
  --location "Conference Room B"
```

### Search for events

```bash
# Search for events containing "meeting" across all calendars
uvx --from calendar-sse-mcp calendar-mcp search "meeting"

# Search in a specific calendar and date range
uvx --from calendar-sse-mcp calendar-mcp search "lunch" --calendar "Personal" --start-date 2023-09-01 --end-date 2023-09-30
``` 