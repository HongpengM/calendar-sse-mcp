# Calendar MCP API Endpoints

This document describes the JSON API endpoints available in the Calendar MCP service.

## URL Format Requirements

The Calendar MCP service implements API endpoints using the MCP resource model. All endpoints must use a URL scheme format like `api://path`. Simple path formats like `/api/path` will result in validation errors.

## Available Endpoints

### List Calendars

```
api://calendars
```

Returns a list of all available calendars.

### Get Events (All)

```
api://events/{calendar_name}
```

Returns all events from the specified calendar.

### Get Events (Date Range)

```
api://events/{calendar_name}/{start_date}/{end_date}
```

Returns events from the specified calendar within the date range.

- `start_date` and `end_date` can be in any format parseable by dateparser

### Create Event

```
api://events/create/{calendar_name}/{summary}/{start_date}/{end_date}
```

Creates a new event in the specified calendar.

### Update Event

```
api://events/update/{event_id}/{calendar_name}
```

Updates the specified event.

### Delete Event

```
api://events/delete/{event_id}/{calendar_name}
```

Deletes the specified event.

## Response Format

All API endpoints return a standardized JSON response with the following structure:

```json
{
  "status": "success",
  "data": { ... },
  "message": "Optional message"
}
```

Or in case of errors:

```json
{
  "status": "error",
  "message": "Error message"
}
```

## Implementation Notes

1. The MCP framework used in this service requires path parameters instead of query parameters for route definitions.
2. All date string inputs are processed through the `date_utils.py` module, which supports flexible date formats.
3. All responses are validated using Pydantic models before being returned. 