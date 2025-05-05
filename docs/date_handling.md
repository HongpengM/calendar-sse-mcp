# Date Handling in Calendar SSE MCP

This document explains how dates are handled in the Calendar SSE MCP using the dateparser library and Pydantic v2.

## Dateparser Integration

The Calendar SSE MCP uses the [dateparser](https://dateparser.readthedocs.io/en/latest/) library to provide flexible date parsing capabilities. This allows users to input dates in a variety of formats, including:

- ISO 8601 format (`YYYY-MM-DD`, `YYYY-MM-DDTHH:MM:SS`)
- Natural language dates ("tomorrow", "next week", "in 3 days")
- Various date formats (US, European, etc.)
- Relative dates with specific times ("tomorrow at 3pm")

### Example Date Formats

The following date formats are supported:

| Input | Interpretation |
|-------|----------------|
| `2023-12-25` | December 25, 2023 (00:00:00) |
| `25/12/2023` | December 25, 2023 (00:00:00) |
| `12/25/2023` | December 25, 2023 (00:00:00) |
| `Dec 25, 2023` | December 25, 2023 (00:00:00) |
| `tomorrow` | Next day (00:00:00) |
| `tomorrow at 3pm` | Next day (15:00:00) |
| `next Monday` | Next Monday (00:00:00) |
| `in 2 days` | 2 days from now |
| `yesterday` | Previous day (00:00:00) |
| `now` | Current date and time |

## Pydantic v2 Validation

The application uses [Pydantic v2](https://docs.pydantic.dev/latest/) for data validation and parsing. This ensures that all date inputs are properly validated and converted to the correct format.

### DateRange Model

The `DateRange` model is used to validate date ranges:

```python
class DateRange(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    start_date: datetime
    end_date: datetime
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_date(cls, value: Union[str, datetime]) -> datetime:
        """Parse dates using dateparser for flexible input formats"""
        if isinstance(value, datetime):
            return value
        
        parsed_date = dateparser.parse(value)
        if not parsed_date:
            raise ValueError(f"Could not parse date: {value}")
        return parsed_date
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, end_date: datetime, info: Dict[str, Any]) -> datetime:
        """Validate that end_date is not before start_date"""
        start_date = info.data.get('start_date')
        if start_date and end_date < start_date:
            raise ValueError("End date cannot be before start date")
        return end_date
```

This model:
1. Accepts both string and datetime objects
2. Uses dateparser to parse string dates
3. Validates that the end date is not before the start date
4. Returns properly formatted datetime objects

### Date Utility Functions

The following utility functions simplify date handling in the application:

- `parse_date_string(date_str)`: Parse a single date string using dateparser
- `create_date_range(start_date, end_date, days)`: Create a validated date range with proper defaults
- `format_iso(dt)`: Format a datetime as an ISO 8601 string

## Usage in API Endpoints

The JSON API endpoints use these date handling capabilities to provide a flexible interface:

```python
@mcp.resource("api/events/{calendar_name}")
def api_get_events(calendar_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    API endpoint to get events from a calendar with JSON response
    
    Args:
        calendar_name: The name of the calendar
        start_date: Optional start date in any format parseable by dateparser
        end_date: Optional end date in any format parseable by dateparser
        
    Returns:
        JSON response with events
    """
    try:
        # Parse and validate date range
        start_dt, end_dt = create_date_range(start_date, end_date)
        
        # Format dates as ISO strings for the calendar store
        start_iso = format_iso(start_dt)
        end_iso = format_iso(end_dt)
        
        # ...
```

## Default Behavior

When dates are not specified:

- Default start date is today (00:00:00)
- Default end date is 7 days from the start date
- All times are in the local timezone unless specified otherwise

## Error Handling

When date parsing fails:

1. A clear error message is returned, including the unparseable date string
2. The error is wrapped in the API response for proper client handling
3. The error message will indicate if the issue was with the date format or range validation 