# Calendar SSE MCP Command-line Tools

This document describes the comprehensive command-line interface included with the Calendar SSE MCP package.

## Usage

Once installed, you can access the CLI through either:

```bash
# Via uvx (recommended for tools from packages)
uvx --from calendar-sse-mcp calendar-sse [command] [options]

# Directly (if installed in your environment)
calendar-sse [command] [options]

# Or through the Python module
python -m calendar_sse_mcp [command] [options]
```

## Command Structure

The `calendar-sse` command provides two main subcommands:

- `cli`: For direct calendar operations (creating events, searching, etc.)
- `server`: For server management operations (install, start, stop, etc.)

## CLI Subcommand

The `cli` subcommand provides direct access to Calendar.app functionality:

```bash
calendar-sse cli [operation] [options]
```

**Global Options:**
- `--dev` - Connect to the development server on port 27213 instead of the standard server on port 27212

### Available Calendar Operations

| Operation    | Description                         |
|--------------|-------------------------------------|
| `calendars`  | List all available calendars        |
| `events`     | Get events from a calendar          |
| `create`     | Create a new event                  |
| `update`     | Update an existing event            |
| `delete`     | Delete an event                     |
| `search`     | Search for events                   |

### `cli calendars` - List Calendars

List all available calendars in Calendar.app:

```bash
calendar-sse cli calendars [options]
```

**Options:**
- `--json` - Output in JSON format

### `cli events` - Get Events

Get events from a specific calendar:

```bash
calendar-sse cli events CALENDAR [options]
```

**Arguments:**
- `CALENDAR` - Name of the calendar to get events from

**Options:**
- `--start-date DATE` - Start date in flexible format (e.g., 'yesterday', '2023-01-01')
- `--end-date DATE` - End date in flexible format (e.g., 'tomorrow', '2023-12-31')
- `--json` - Output in JSON format

### `cli create` - Create Event

Create a new event in a calendar:

```bash
calendar-sse cli create [options]
```

**Options:**
- `--event TEXT`, `--summary TEXT` - Event title/summary (required)
- `--cal CALENDAR`, `--calendar CALENDAR` - Name of the calendar (default from .env DEFAULT_CALENDAR)
- `--date DATE` - Event date in flexible format (default: today)
- `--start TIME`, `--start-time TIME` - Start time in flexible format (default: current time)
- `--end TIME`, `--end-time TIME` - End time in flexible format
- `--duration DURATION` - Duration in flexible format (e.g., '60min', '1h', '1.5 hours') (default: 60min if end time not specified)
- `--location LOCATION` - Event location
- `--description TEXT` - Event description
- `--json` - Output in JSON format

### `cli update` - Update Event

Update an existing event:

```bash
calendar-sse cli update CALENDAR EVENT_ID [options]
```

**Arguments:**
- `CALENDAR` - Name of the calendar containing the event
- `EVENT_ID` - ID of the event to update

**Options:**
- `--summary TEXT` - New event title/summary
- `--date DATE` - New event date in flexible format
- `--start-time TIME` - New start time in flexible format
- `--end-time TIME` - New end time in flexible format
- `--location LOCATION` - New event location
- `--description TEXT` - New event description
- `--json` - Output in JSON format

### `cli delete` - Delete Event

Delete an event:

```bash
calendar-sse cli delete CALENDAR EVENT_ID [options]
```

**Arguments:**
- `CALENDAR` - Name of the calendar containing the event
- `EVENT_ID` - ID of the event to delete

**Options:**
- `--json` - Output in JSON format

### `cli search` - Search Events

Search for events:

```bash
calendar-sse cli search QUERY [options]
```

**Arguments:**
- `QUERY` - Search term (case-insensitive)

**Options:**
- `--calendar CALENDAR` - Specific calendar to search in
- `--start-date DATE` - Start date in flexible format
- `--end-date DATE` - End date in flexible format
- `--duration DURATION` - Duration from start date (e.g., '3d', '1 week', '2 months')
- `--json` - Output in JSON format

## Server Subcommand

The `server` subcommand manages the server as a background service:

```bash
calendar-sse server [operation] [options]
```

### Available Server Operations

| Operation    | Description                                      |
|--------------|--------------------------------------------------|
| `install`    | Install the server as a LaunchAgent              |
| `uninstall`  | Uninstall the server LaunchAgent                 |
| `start`      | Start the server                                 |
| `stop`       | Stop the server                                  |
| `restart`    | Restart the server                               |
| `logs`       | Display server logs                              |
| `run`        | Run the server directly in the foreground        |

### `server install` - Install Server

Install the server as a LaunchAgent:

```bash
calendar-sse server install [options]
```

**Options:**
- `--port PORT` - Server port (default: 27212)
- `--logdir DIR` - Log directory (default: /tmp)
- `--name NAME` - LaunchAgent name (default: com.calendar-sse-mcp)
- `--no-load` - Don't start the server after installation
- `--dev` - Install as a development server on port 27213 (overrides --port)

### `server uninstall` - Uninstall Server

Uninstall the server LaunchAgent:

```bash
calendar-sse server uninstall [options]
```

**Options:**
- `--name NAME` - LaunchAgent name (default: com.calendar-sse-mcp)

### `server start` - Start Server

Start the server:

```bash
calendar-sse server start [options]
```

**Options:**
- `--name NAME` - LaunchAgent name (default: com.calendar-sse-mcp)

### `server stop` - Stop Server

Stop the server:

```bash
calendar-sse server stop [options]
```

**Options:**
- `--name NAME` - LaunchAgent name (default: com.calendar-sse-mcp)

### `server restart` - Restart Server

Restart the server:

```bash
calendar-sse server restart [options]
```

**Options:**
- `--name NAME` - LaunchAgent name (default: com.calendar-sse-mcp)

### `server logs` - View Logs

View server logs:

```bash
calendar-sse server logs [options]
```

**Options:**
- `--name NAME` - LaunchAgent name (default: com.calendar-sse-mcp)
- `--level {info,error,all}` - Log level to display (default: all)
- `--lines N` - Number of log lines to show (default: 10)

### `server run` - Run in Foreground

Run the server directly in the foreground:

```bash
calendar-sse server run [options]
```

**Options:**
- `--host HOST` - Host to bind to (default: 127.0.0.1)
- `--port PORT` - Port to bind to (default: 27212)

## Examples

### List Available Calendars

```bash
calendar-sse cli calendars
```

### Create a New Event

```bash
# Create a meeting at 10:00 AM today for 1 hour
calendar-sse cli create --event "Team Meeting" --cal "Work" --start "10:00" --duration "1h"

# Create an event on a specific date with human-readable times
calendar-sse cli create --event "Dinner with Friends" --cal "Personal" \
  --date "next Friday" --start "7:30 PM" --duration "2 hours" \
  --location "Joe's Restaurant" --description "Reservation for 4 people"
```

### Update an Event

```bash
# Update the event title
calendar-sse cli update "Work" "CA0C1456-F7C8-4FD5-B8C3-8A2F9D3CE7B9" --summary "Team Sync"

# Update multiple fields
calendar-sse cli update "Work" "CA0C1456-F7C8-4FD5-B8C3-8A2F9D3CE7B9" \
  --start-time "2:30 PM" --end-time "3:30 PM" \
  --location "Conference Room B"
```

### Search for Events

```bash
# Search for events containing "meeting"
calendar-sse cli search "meeting"

# Search in a specific calendar and date range
calendar-sse cli search "lunch" --calendar "Personal" --start-date "2023-09-01" --end-date "2023-09-30"

# Search for events in the next week
calendar-sse cli search "appointment" --duration "7d"
```

### Managing the Server

```bash
# Install and start the server
calendar-sse server install --port 5000 --logdir ~/logs

# View server logs
calendar-sse server logs --level error

# Restart the server
calendar-sse server restart

# Uninstall the server
calendar-sse server uninstall
```

## JSON Output

Most commands support a `--json` flag that outputs the results in JSON format, which is useful for scripting and integration with other tools. 