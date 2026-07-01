# MCP Client Configuration Guide

This guide shows how to connect to the Calendar HTTP MCP server from various MCP clients.

## Server Information

- **URL**: `http://localhost:27212`
- **Transport**: HTTP (Streamable HTTP)
- **Port**: 27212 (default)

## Claude Desktop Configuration

For Claude Desktop, add this to your MCP settings file:

**Location**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "calendar": {
      "url": "http://localhost:27212",
      "transport": "http"
    }
  }
}
```

Or if Claude Desktop uses a different format:

```json
{
  "mcpServers": {
    "calendar": {
      "command": "curl",
      "args": [
        "-X", "GET",
        "http://localhost:27212/sse"
      ]
    }
  }
}
```

## Generic MCP Client Configuration

For other MCP clients that support HTTP/SSE transport:

```json
{
  "mcpServers": {
    "calendar": {
      "url": "http://localhost:27212",
      "transport": "http",
      "headers": {}
    }
  }
}
```

## Testing the Connection

You can test if the server is running and accessible:

```bash
# Check if server is running (HTTP transport)
curl http://localhost:27212/health 2>&1 || echo "Server is running (may not have /health endpoint)"

# Or use the CLI tool
uv run -m calendar_http_mcp cli calendars
```

## Available Tools

Once connected, the following MCP tools are available:

### Calendar tools

- `list_all_calendars()` - List all available calendars
- `search_events(query, calendar_name?, start_date?, end_date?)` - Search for events
- `create_calendar_event(calendar_name, summary, start_date, end_date, location?, description?)` - Create a new event
- `update_calendar_event(event_id, calendar_name, summary?, start_date?, end_date?, location?, description?)` - Update an event
- `delete_calendar_event(event_id, calendar_name)` - Delete an event

### Reminder tools

- `list_all_reminder_lists()` - List all available reminder lists
- `search_reminders(query, calendar_name?, start_date?, end_date?)` - Search for reminders
- `create_reminder(calendar_name, title, due_date?, notes?, priority?)` - Create a new reminder
- `update_reminder(reminder_id, calendar_name, title?, due_date?, notes?, priority?, completed?)` - Update a reminder
- `complete_reminder(reminder_id, calendar_name)` - Mark a reminder as completed
- `delete_reminder(reminder_id, calendar_name)` - Delete a reminder

## Available Resources

### Calendar resources

- `calendars://list` - List all calendars
- `calendar://{name}` - Get calendar info
- `events://{calendar_name}` - Get all events
- `events://{calendar_name}/{start_date}/{end_date}` - Get events in date range
- `event://{calendar_name}/{event_id}` - Get specific event

### Reminder resources

- `reminder-lists://list` - List all reminder lists
- `reminders://{calendar_name}` - Get reminders from a specific list

## Troubleshooting

1. **Server not running**: Start it with `launchctl start com.calendar-mcp` or `uv run -m calendar_http_mcp server start`

2. **Port conflict**: Check if port 27212 is in use: `lsof -i :27212`

3. **Check logs**: View server logs with `uv run -m calendar_http_mcp server logs`

4. **Verify server**: Test with `curl http://localhost:27212/sse -H "Accept: text/event-stream"`
