"""
Calendar SSE MCP - A Model Context Protocol server for macOS Calendar.app
"""

from .date_utils import parse_date_string, create_date_range, format_iso
from .models import (
    CalendarEvent, EventCreate, EventUpdate, 
    CalendarList, EventList, ApiResponse
)

__version__ = "0.1.0" 