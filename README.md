# Calendar SSE MCP

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server for interacting with macOS Calendar.app through AppleScript.

## Features

- List all calendars from macOS Calendar.app
- Get events from specific calendars
- Filter events by date range
- Create, update, and delete calendar events
- Search for events by text query
- Provides both MCP resources and tools for AI assistants
- Includes prompt templates for common operations
- Comprehensive command-line interface for all operations
- Built-in launch agent support for background operation
- JSON API endpoints for programmatic access
- Robust date parsing using dateparser library
- Data validation with Pydantic v2
- Dynamic launch agent detection and installation

## Requirements

- macOS (tested on macOS 14 Sonoma and above)
- Python 3.12 or newer
- Calendar.app with at least one calendar set up

## Installation

### From Source

Clone the repository and install:

```bash
git clone https://github.com/yourusername/calendar-sse-mcp.git
cd calendar-sse-mcp
pip install -e .
```

### Using uv

You can install directly using [uv](https://github.com/astral-sh/uv), a fast Python package installer:

```bash
uv pip install git+https://github.com/HongpengM/calendar-sse-mcp.git
```

Note: This package will be available on PyPI in the future.

```bash 
uv pip install calendar-sse-mcp
```

## Claude Configuration

To add this calendar service to Claude, create the following JSON configuration:

```json
{
  "schema_version": "v1",
  "name": "Calendar",
  "description": "Access and manage events in macOS Calendar.app",
  "provider_uri": "http://localhost:3000",
  "provider_type": "mcp_server",
  "tools": [
    {
      "name": "list_all_calendars",
      "description": "List all available calendars in Calendar.app"
    },
    {
      "name": "search_events",
      "description": "Search for events in Calendar.app by query, calendar name, and date range"
    },
    {
      "name": "create_calendar_event",
      "description": "Create a new event in Calendar.app"
    },
    {
      "name": "update_calendar_event",
      "description": "Update an existing event in Calendar.app"
    },
    {
      "name": "delete_calendar_event",
      "description": "Delete an event from Calendar.app"
    }
  ]
}
```

Save this as `calendar-mcp.json` and add it to Claude in your settings.

## Command-line Usage

The package provides a comprehensive command-line interface:

```bash
# Using the installed script
calendar-mcp [command] [options]

# Or directly with the module
python -m calendar_sse_mcp [command] [options]
```

### Running the server

```bash
# Start the MCP server
calendar-mcp server

# Specify host and port
calendar-mcp server --host 0.0.0.0 --port 5000
```

### Installing as a Claude MCP server

```bash
# Install as a Claude MCP server
calendar-mcp install

# With a custom name
calendar-mcp install --name "My Calendar"
```

### Setting up as a Launch Agent (background service)

The package includes a built-in command to create and install a Launch Agent:

```bash
# Create and install the Launch Agent
calendar-mcp agent create

# Create, install, and immediately load the Agent
calendar-mcp agent create --load

# Customize port and log directory
calendar-mcp agent create --port 5000 --logdir ~/logs

# Check the status of the Launch Agent
calendar-mcp agent check

# Show logs
calendar-mcp agent check --show-logs

# Uninstall the Launch Agent
calendar-mcp agent uninstall

# Reinstall the Launch Agent (uninstall and create again)
calendar-mcp agent uninstall && calendar-mcp agent create --load
```

### Managing Calendar Events

```bash
# List all calendars
calendar-mcp calendars

# Get events from a calendar
calendar-mcp events "Work"

# Create a new event
calendar-mcp create "Work" "Team Meeting" --start-time 10:00

# Update an event
calendar-mcp update "Work" "EVENT_ID" --summary "Updated Meeting"

# Delete an event
calendar-mcp delete "Work" "EVENT_ID"

# Search for events
calendar-mcp search "meeting" --calendar "Work"
```

For more details, see the [CLI Tools Documentation](docs/cli_tools.md).

## Calendar.app Permissions

The first time you run the server and it attempts to access Calendar.app, macOS will prompt you to grant permissions. You must grant these permissions for the script to work.

1. When prompted, click "OK" to allow access
2. To check or modify permissions later, go to:
   - System Settings > Privacy & Security > Automation
   - Ensure Python/Terminal has permissions to control Calendar.app

## Privacy Warning and Disclaimer

**IMPORTANT**: This software requires full access to your macOS Calendar.app and all its data. Please be aware of the following:

- When you run this software, macOS will prompt you to grant Calendar.app access to `uv`, Python, or your terminal application
- Granting this permission gives the application complete read and write access to ALL your calendar data
- All calendar events, including potentially sensitive information (meetings, appointments, personal events), will be accessible to this software
- Any application given this access could potentially read, modify, or delete your calendar events

By installing and using this software, you acknowledge:

1. You understand the scope of permissions being granted
2. You accept the potential privacy and security risks involved
3. You are responsible for reviewing the source code or trusting the developer
4. No warranty is provided regarding security, privacy, or data integrity

If you're uncomfortable with these permissions, please do not proceed with installation.

## API Reference

### MCP Resources

- `calendars://list` - List all available calendars
- `calendar://{name}` - Get information about a specific calendar
- `events://{calendar_name}` - Get all events in a calendar
- `events://{calendar_name}/{start_date}/{end_date}` - Get events in a date range
- `event://{calendar_name}/{event_id}` - Get a specific event by ID

### JSON API Endpoints

See [API Endpoints Documentation](docs/api_endpoints.md) for detailed information.

- `api://calendars` - Get all calendars as a standardized JSON response
- `api://events/{calendar_name}` - Get events from a calendar as JSON
- `api://events/{calendar_name}/{start_date}/{end_date}` - Get events in a date range
- `api://events/create/{calendar_name}/{summary}/{start_date}/{end_date}` - Create a new event
- `api://events/update/{event_id}/{calendar_name}` - Update an event
- `api://events/delete/{event_id}/{calendar_name}` - Delete an event

### MCP Tools

- `list_all_calendars()` - List all available calendars
- `search_events(query, calendar_name?, start_date?, end_date?)` - Search for events
- `create_calendar_event(calendar_name, summary, start_date, end_date, location?, description?)` - Create a new event
- `update_calendar_event(event_id, calendar_name, summary?, start_date?, end_date?, location?, description?)` - Update an event
- `delete_calendar_event(event_id, calendar_name)` - Delete an event

### MCP Prompts

- `create_event_prompt(calendar_name, summary, date?, start_time?, end_time?, duration_minutes?, location?, description?)` - Prompt to create a new event
- `search_events_prompt(query, calendar_name?, start_date?, end_date?)` - Prompt to search for events

## Documentation

- [Launch Agent Setup](docs/launch_agent_setup.md) - How to run the server as a background service
- [CLI Tools](docs/cli_tools.md) - Comprehensive command-line tool reference
- [Date Handling](docs/date_handling.md) - Information about flexible date parsing with dateparser

## Date Parsing

This package uses the `dateparser` library for robust date parsing, which provides:

- Natural language date parsing ("tomorrow", "next week", etc.)
- Support for relative dates ("3 days from now")
- Multiple date formats (MM/DD/YYYY, YYYY-MM-DD, etc.)
- Time zone awareness

Example date formats supported:
- "2023-05-15" (ISO format)
- "May 15, 2023" (Natural language)
- "tomorrow at 3pm" (Relative with time)
- "next Monday" (Weekday reference)
- "05/15/2023" (US format)
- "15/05/2023" (European format)

## Data Validation

The package uses Pydantic v2 for data validation, providing:

- Type checking and validation
- Custom validators
- JSON schema generation
- Serialization/deserialization
- Proper error messages for validation failures

## Future Enhancements

- CalDAV support for accessing remote calendars
- Recurring event support
- Calendar sharing features
- Support for attendees and invitations
- Notifications for upcoming events

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.