"""
Date utilities for calendar-sse-mcp using dateparser and pydantic v2
"""
from datetime import datetime, timedelta
from typing import Optional, Union, Tuple, Dict, Any

import dateparser
from pydantic import BaseModel, field_validator, ConfigDict


class DateRange(BaseModel):
    """Model for a date range with validation using Pydantic v2"""
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


def parse_date_string(date_str: str) -> datetime:
    """
    Parse a date string using dateparser for more robust date handling
    
    Args:
        date_str: A string representing a date/time in various formats
        
    Returns:
        A datetime object
        
    Raises:
        ValueError: If the date string cannot be parsed
    """
    parsed_date = dateparser.parse(date_str)
    if not parsed_date:
        raise ValueError(f"Could not parse date: {date_str}")
    return parsed_date


def create_date_range(
    start_date: Optional[Union[str, datetime]] = None,
    end_date: Optional[Union[str, datetime]] = None,
    days: int = 7
) -> Tuple[datetime, datetime]:
    """
    Create a validated date range
    
    Args:
        start_date: Start date as string or datetime (defaults to today)
        end_date: End date as string or datetime (defaults to start_date + days)
        days: Number of days to include if end_date not provided (default: 7)
        
    Returns:
        Tuple of (start_date, end_date) as datetime objects
        
    Raises:
        ValueError: If dates cannot be parsed or end date is before start date
    """
    # Default start date is today
    if start_date is None:
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif isinstance(start_date, str):
        start = parse_date_string(start_date)
    else:
        start = start_date
    
    # Default end date is start date + days
    if end_date is None:
        end = start + timedelta(days=days)
    elif isinstance(end_date, str):
        end = parse_date_string(end_date)
    else:
        end = end_date
    
    # Validate with Pydantic model
    validated_range = DateRange(start_date=start, end_date=end)
    return validated_range.start_date, validated_range.end_date


def format_iso(dt: datetime) -> str:
    """
    Format a datetime as ISO 8601 string
    
    Args:
        dt: datetime object
        
    Returns:
        ISO 8601 formatted string
    """
    return dt.isoformat() 