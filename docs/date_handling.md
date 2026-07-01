# Date Handling in calendar-http-mcp

This document explains how dates are handled in the calendar-http-mcp using the dateparser library and Pydantic v2.

## Overview

The calendar-http-mcp uses the [dateparser](https://dateparser.readthedocs.io/en/latest/) library to provide flexible date parsing capabilities. This allows users to input dates in a variety of formats, including:

- Natural language ("tomorrow", "next week", "in 3 days")
- Standard formats ("2023-05-15", "15/05/2023", "May 15, 2023")
- Relative dates ("3 days ago", "yesterday", "today")

## Supported Date Formats

### ISO Format

- `2023-05-15` - Date only
- `2023-05-15T14:30:00` - Date and time

### Natural Language

- `today`, `tomorrow`, `yesterday`
- `next Monday`, `last Friday`
- `in 3 days`, `3 days ago`
- `next week`, `last month`

### Regional Formats

- `05/15/2023` - US format (MM/DD/YYYY)
- `15/05/2023` - European format (DD/MM/YYYY)
- `May 15, 2023` - Written format
- `15 May 2023` - Alternative written format

### With Time

- `tomorrow at 3pm`
- `next Monday at 14:30`
- `2023-05-15 14:30`

## Date Validation

Dates are validated using Pydantic v2 models to ensure:

1. **Format correctness** - Dates must be parseable
2. **Logical consistency** - End dates cannot be before start dates
3. **Type safety** - All dates are converted to Python datetime objects

## Duration Parsing

When searching for events, you can specify durations using flexible formats:

- `3d` or `3 days` - 3 days
- `1w` or `1 week` - 1 week
- `2m` or `2 months` - 2 months (approximated as 60 days)

## Implementation Details

The date handling is implemented in two main files:

1. **`date_utils.py`** - Core date parsing and validation functions
2. **`models.py`** - Pydantic models with date validators

### Key Functions

- `parse_date_string()` - Parse a single date string
- `create_date_range()` - Create a validated date range
- `format_iso()` - Format a datetime as ISO 8601 string

### Error Handling

When dates cannot be parsed, the system raises `ValueError` with descriptive messages. These are caught and returned as JSON error responses in the API.

## Examples

### CLI Usage

```bash
# Create an event for tomorrow
calendar-mcp cli create --event "Meeting" --cal "Work" --date "tomorrow" --start "10:00"

# Search for events in the next week
calendar-mcp cli search "project" --duration "1 week"

# Get events from next Monday to next Friday
calendar-mcp cli events "Work" --start-date "next Monday" --end-date "next Friday"
```

### API Usage

Dates can be passed to API endpoints in any supported format:

```
api://events/Work/next%20Monday/next%20Friday
```

The URL-encoded date strings are parsed on the server side.

## Time Zone Handling

Currently, all dates are handled in the local system time zone. Future versions may add support for explicit time zone handling.

## Best Practices

1. **Use ISO format for scripts** - When writing scripts, use `YYYY-MM-DD` format for reliability
2. **Use natural language for CLI** - When using the CLI interactively, natural language is more convenient
3. **Be specific with times** - Always include a time component when creating events to avoid ambiguity
4. **Check date parsing** - If a date isn't being parsed as expected, try a more explicit format
