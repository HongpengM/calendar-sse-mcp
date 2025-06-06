#!/usr/bin/env python3
"""
Calendar MCP Server - An MCP server for interacting with macOS Calendar.app

This server provides an interface to Calendar.app on macOS, allowing you to:
- List available calendars
- View, create, update, and delete events
- Search for events by date range
- Get detailed information about calendars and events

The server uses FastMCP to expose both resources and tools that can be used
by AI assistants to interact with the user's calendar.
"""
import datetime
import json
import os
from typing import Dict, List, Optional, Union, Any
import dateparser
from datetime import datetime, timedelta
import sys

from mcp.server.fastmcp import FastMCP

from .calendar_store import CalendarStore, CalendarStoreError
from .models import ApiResponse, CalendarEvent, EventCreate, EventUpdate, EventList, CalendarList
from .date_utils import create_date_range, format_iso


# Create the MCP server - settings can be passed to the constructor
mcp = FastMCP(
    "Calendar MCP",
    port=int(os.environ.get("SERVER_PORT", "27212")),
    host=os.environ.get("SERVER_HOST", "127.0.0.1")
)

# Initialize a global calendar store instance to avoid authorization conflicts
# This prevents the "Received request before initialization was complete" error
# by ensuring calendar authorization is completed before the server accepts requests
_global_calendar_store: Optional[CalendarStore] = None
_store_lock = None  # Will be initialized as threading.RLock() when needed

def get_calendar_store() -> CalendarStore:
    """
    Get the global calendar store instance with health checking and auto-recreation.
    
    This function implements robust maintenance of the EventKit instance:
    - Health checks on each access to detect stale/invalid stores
    - Auto-recreation when authorization expires or system resumes from sleep
    - Thread-safe access with proper locking
    
    Returns:
        The global CalendarStore instance
        
    Raises:
        CalendarStoreError: If unable to create or authorize calendar access
    """
    global _global_calendar_store, _store_lock
    
    # Initialize the lock on first use (avoids import order issues)
    if _store_lock is None:
        import threading
        _store_lock = threading.RLock()
    
    with _store_lock:
        # Check if we need to create or recreate the store
        needs_recreation = False
        
        if _global_calendar_store is None:
            needs_recreation = True
        else:
            # Perform health check on existing store
            try:
                # Quick health check: try to get calendars list
                # This will fail if authorization expired or EventKit is stale
                calendars = _global_calendar_store.get_all_calendars()
                
                # Additional check: verify the store is still authorized
                if not _global_calendar_store.authorized:
                    print("Calendar store authorization expired, recreating...", file=sys.stderr)
                    needs_recreation = True
                    
            except CalendarStoreError as e:
                print(f"Calendar store health check failed: {e}, recreating...", file=sys.stderr)
                needs_recreation = True
            except Exception as e:
                print(f"Calendar store health check error: {e}, recreating...", file=sys.stderr)
                needs_recreation = True
        
        # Create or recreate the store if needed
        if needs_recreation:
            try:
                print("Creating new calendar store instance...", file=sys.stderr)
                _global_calendar_store = CalendarStore(quiet=True)
                
                # Verify the new store is working
                if not _global_calendar_store.authorized:
                    raise CalendarStoreError("Failed to authorize calendar access")
                
                # Test basic functionality
                calendars = _global_calendar_store.get_all_calendars()
                print(f"Calendar store created successfully with {len(calendars)} calendars", file=sys.stderr)
                
            except Exception as e:
                _global_calendar_store = None
                raise CalendarStoreError(f"Failed to create calendar store: {e}")
        
        return _global_calendar_store

# Main entry point ---------------------------------------------------------

if __name__ == "__main__":
    # Get the port from environment variables
    port = int(os.environ.get("SERVER_PORT", "27212"))
    transport = os.environ.get("SERVER_TRANSPORT", "sse")
    
    print(f"Server configured with port={port}, transport={transport}")
    
    # Initialize the calendar store early to handle authorization
    print("Initializing calendar access...")
    get_calendar_store()
    print("Calendar access initialized.")
    
    # Run the server with the specified transport
    mcp.run(transport=transport)


# Resources -----------------------------------------------------------------

@mcp.resource("calendars://list")
def list_calendars() -> str:
    """
    List all available calendars in Calendar.app
    
    Returns:
        JSON string containing calendar names
    """
    try:
        store = get_calendar_store()
        calendars = store.get_all_calendars()
        return json.dumps(calendars, ensure_ascii=False)
    except CalendarStoreError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"}, ensure_ascii=False)


@mcp.resource("calendar://{name}")
def get_calendar_info(name: str) -> str:
    """
    Get information about a specific calendar
    
    Args:
        name: The name of the calendar
        
    Returns:
        JSON string with calendar information
    """
    # For now, we just return basic information
    try:
        store = get_calendar_store()
        calendars = store.get_all_calendars()
        
        if name not in calendars:
            return json.dumps({"error": f"Calendar '{name}' not found"}, ensure_ascii=False)
        
        return json.dumps({
            "name": name,
            "exists": True
        }, ensure_ascii=False)
    except CalendarStoreError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"}, ensure_ascii=False)


@mcp.resource("events://{calendar_name}")
def get_calendar_events(calendar_name: str) -> str:
    """
    Get events from a specific calendar
    
    Args:
        calendar_name: The name of the calendar
        
    Returns:
        JSON string containing events
    """
    try:
        store = get_calendar_store()
        events = store.get_events(calendar_name=calendar_name)
        return json.dumps(events, ensure_ascii=False)
    except CalendarStoreError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"}, ensure_ascii=False)


@mcp.resource("events://{calendar_name}/{start_date}/{end_date}")
def get_calendar_events_by_date_range(
    calendar_name: str, 
    start_date: str, 
    end_date: str
) -> str:
    """
    Get events from a specific calendar within a date range
    
    Args:
        calendar_name: The name of the calendar
        start_date: Start date in format "yyyy-MM-dd"
        end_date: End date in format "yyyy-MM-dd"
        
    Returns:
        JSON string containing events
    """
    try:
        if start_date == end_date: # Shift end_date to the end of the day
            end_date = f"{end_date}T23:59:59"
            
        
        # Handle date ranges by adjusting time components
        if start_date and len(start_date) == 10:  # YYYY-MM-DD format (10 chars)
            start_date = f"{start_date}T00:00:00"
            
        if end_date and len(end_date) == 10:  # YYYY-MM-DD format (10 chars)
            end_date = f"{end_date}T23:59:59"
        
        
        store = get_calendar_store()
        events = store.get_events(
            calendar_name=calendar_name,
            start_date=start_date,
            end_date=end_date
        )
        return json.dumps(events, ensure_ascii=False)
    except CalendarStoreError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"}, ensure_ascii=False)


@mcp.resource("event://{calendar_name}/{event_id}")
def get_event(calendar_name: str, event_id: str) -> str:
    """
    Get a specific event by ID
    
    Args:
        calendar_name: The name of the calendar
        event_id: The ID of the event
        
    Returns:
        JSON string containing event details
    """
    try:
        # Get all events and filter by ID
        store = get_calendar_store()
        events = store.get_events(calendar_name=calendar_name)
        event = next((e for e in events if e["id"] == event_id), None)
        
        if event:
            return json.dumps(event, ensure_ascii=False)
        else:
            return json.dumps({"error": f"Event with ID '{event_id}' not found"}, ensure_ascii=False)
    except CalendarStoreError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"}, ensure_ascii=False)


# Tools --------------------------------------------------------------------

@mcp.tool()
def list_all_calendars() -> str:
    """
    List all available calendars in Calendar.app
    
    Returns:
        JSON string containing calendar names
    """
    try:
        store = get_calendar_store()
        calendars = store.get_all_calendars()
        return json.dumps({
            "calendars": calendars,
            "count": len(calendars)
        }, ensure_ascii=False)
    except CalendarStoreError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"}, ensure_ascii=False)


@mcp.tool()
def search_events(
    query: str,
    calendar_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    duration: Optional[str] = None
) -> str:
    """
    Search for events in Calendar.app, optionally within a flexible date range.
    
    Args:
        query: Search query (case-insensitive substring match).
               If empty, returns all events matching other criteria.
        calendar_name: (Optional) Specific calendar to search in.
        start_date: (Optional) Starting date in any format parseable by dateparser.
                    Defaults to today if no end_date and no duration given for start_date logic.
        end_date: (Optional) Ending date in any format parseable by dateparser.
        duration: (Optional) Duration from start date or before end date,
                  e.g., "3d", "1 week", "1 month".
                  Default is "3d" if only start_date is given or if neither start_date nor end_date is given.
                  See date parsing logic for details on how start_date, end_date, and duration interact.
    
    Examples:
        # Basic search - searches next 3 days (default duration)
        search_events("meeting")
        
        # Search in specific calendar
        search_events("dentist", calendar_name="Personal")
        
        # Search with custom duration from today
        search_events("workout", duration="1 week")
        search_events("birthday", duration="1 month")
        search_events("deadline", duration="7d")
        
        # Search from specific start date (uses default 3-day duration)
        search_events("conference", start_date="2024-01-15")
        
        # Search from start date with custom duration
        search_events("vacation", start_date="2024-06-01", duration="2 weeks")
        
        # Search within specific date range
        search_events("project", start_date="2024-01-01", end_date="2024-01-31")
        search_events("appointment", start_date="next Monday", end_date="next Friday")
        
        # Search backwards from end date (duration before end_date)
        search_events("review", end_date="2024-12-31", duration="1 month")
        
        # Get all events in date range (empty query matches all)
        search_events("", start_date="today", end_date="tomorrow")
        
        # Flexible date formats supported by dateparser
        search_events("lunch", start_date="tomorrow", end_date="next week")
        search_events("call", start_date="Jan 15 2024", end_date="Jan 20 2024")
        search_events("event", start_date="2024-01-15 09:00", end_date="2024-01-15 17:00")
        
    Date Logic:
        - No dates: today + 3 days (default)
        - Only start_date: start_date + duration (default 3d)
        - Only end_date: end_date - duration (default 3d) to end_date
        - Both dates: exact range (if same date, end extends to 23:59:59)
        - Duration formats: "3d", "1 week", "2 months", "7 days"
        
    Returns:
        JSON string containing matching events with count
    """
    try:
        # Date parsing and duration logic from get_events_date_range
        days = 3  # Default duration is 3 days
        if duration:
            duration_lower = duration.lower().strip()
            num_str = ''.join(c for c in duration_lower if c.isdigit())
            if num_str:
                num = int(num_str)
                if duration_lower.endswith('d') or 'day' in duration_lower:
                    days = num
                elif duration_lower.endswith('w') or 'week' in duration_lower:
                    days = num * 7
                elif duration_lower.endswith('m') or 'month' in duration_lower:
                    days = num * 30  # Approximation for months
        
        start_dt: Optional[datetime] = None
        end_dt: Optional[datetime] = None

        if end_date and not start_date: # Only end_date provided
            parsed_end_dt = dateparser.parse(end_date)
            if not parsed_end_dt:
                raise ValueError(f"Could not parse end date: {end_date}")
            end_dt = parsed_end_dt
            start_dt = end_dt - timedelta(days=days)
        else:
            if not start_date: # No start_date and no end date
                # Default to today if start_date is not provided
                start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            else: 
                parsed_start_dt = dateparser.parse(start_date)
                if not parsed_start_dt:
                    raise ValueError(f"Could not parse start date: {start_date}")
                start_dt = parsed_start_dt
    
                if end_date: # If start_date and end_date provided
                    parsed_end_dt = dateparser.parse(end_date)
                    if not parsed_end_dt:
                        raise ValueError(f"Could not parse end date: {end_date}")
                    end_dt = parsed_end_dt
                    
                    # Handle same-day searches: if dates are the same and appear to be date-only inputs,
                    # set start to beginning of day and end to end of day
                    if start_dt.date() == end_dt.date():
                        # Check if inputs were likely date-only (both parsed to midnight)
                        if (start_dt.hour == 0 and start_dt.minute == 0 and start_dt.second == 0 and
                            end_dt.hour == 0 and end_dt.minute == 0 and end_dt.second == 0):
                            # Set start to beginning of day and end to end of day
                            start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999)
                else: # If only start date provided
                    # Use duration if no end_date is provided
                    end_dt = start_dt + timedelta(days=days)
        
        if start_dt and end_dt and end_dt < start_dt:
            raise ValueError("End date cannot be before start date")

        start_iso_for_store = format_iso(start_dt) if start_dt else None
        end_iso_for_store = format_iso(end_dt) if end_dt else None

        # If after all logic, start_iso_for_store or end_iso_for_store is None,
        # it means store.get_events will use its default (e.g. all future events)
        # However, the logic above tries to ensure they are set, e.g. default 3 day window.
        # If start_date, end_date, and duration are all None, this results in:
        # start_dt = now, end_dt = start_dt + 3 days.

        store = get_calendar_store()
        events = store.get_events(
            calendar_name=calendar_name,
            start_date=start_iso_for_store,
            end_date=end_iso_for_store
        )
        
        # Filter events by query (case-insensitive)
        # An empty query string will match all events due to '"" in event_field.lower()' being true
        query_lower = query.lower()
        matching_events = [
            event for event in events
            if (
                query_lower in event["summary"].lower() or
                query_lower in (event["description"] or "").lower() or
                query_lower in (event["location"] or "").lower()
            )
        ]
        
        return json.dumps({
            "events": matching_events,
            "count": len(matching_events)
        }, ensure_ascii=False)
    except ValueError as e:
        return json.dumps({"error": f"Date error: {str(e)}"}, ensure_ascii=False)
    except CalendarStoreError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"}, ensure_ascii=False)


@mcp.tool()
def create_calendar_event(
    calendar_name: str,
    summary: str,
    start_date: str,
    end_date: str,
    location: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    Create a new event in Calendar.app
    
    Args:
        calendar_name: Name of the calendar to create the event in
        summary: Event title
        start_date: Start date in format "yyyy-MM-ddTHH:mm:ss"
        end_date: End date in format "yyyy-MM-ddTHH:mm:ss"
        location: (Optional) Event location
        description: (Optional) Event description
        
    Returns:
        JSON string containing the result
    """
    try:
        store = get_calendar_store()
        event_id = store.create_event(
            calendar_name=calendar_name,
            summary=summary,
            start_date=start_date,
            end_date=end_date,
            location=location,
            description=description
        )
        
        return json.dumps({
            "success": True,
            "event_id": event_id
        }, ensure_ascii=False)
    except CalendarStoreError as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "success": False, 
            "error": f"Unexpected error: {str(e)}"
        }, ensure_ascii=False)


@mcp.tool()
def update_calendar_event(
    event_id: str,
    calendar_name: str,
    summary: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    location: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    Update an existing event in Calendar.app
    
    Args:
        event_id: ID of the event to update
        calendar_name: Name of the calendar containing the event
        summary: (Optional) New event title
        start_date: (Optional) New start date in format "yyyy-MM-ddTHH:mm:ss"
        end_date: (Optional) New end date in format "yyyy-MM-ddTHH:mm:ss"
        location: (Optional) New event location
        description: (Optional) New event description
        
    Returns:
        JSON string containing the result
    """
    try:
        store = get_calendar_store()
        success = store.update_event(
            event_id=event_id,
            calendar_name=calendar_name,
            summary=summary,
            start_date=start_date,
            end_date=end_date,
            location=location,
            description=description
        )
        
        return json.dumps({
            "success": success
        }, ensure_ascii=False)
    except CalendarStoreError as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }, ensure_ascii=False)


@mcp.tool()
def delete_calendar_event(event_id: str, calendar_name: str) -> str:
    """
    Delete an event from Calendar.app
    
    Args:
        event_id: ID of the event to delete
        calendar_name: Name of the calendar containing the event
        
    Returns:
        JSON string containing the result
    """
    try:
        store = get_calendar_store()
        success = store.delete_event(
            event_id=event_id,
            calendar_name=calendar_name
        )
        
        return json.dumps({
            "success": success
        }, ensure_ascii=False)
    except CalendarStoreError as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }, ensure_ascii=False)


@mcp.prompt()
def create_event_prompt(
    calendar_name: str,
    summary: str,
    date: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    duration_minutes: Optional[int] = 60,
    location: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    Create a new event with simplified parameters
    
    Args:
        calendar_name: Name of the calendar to create the event in
        summary: Event title
        date: (Optional) Event date in format "yyyy-MM-dd", defaults to today
        start_time: (Optional) Start time in format "HH:mm", defaults to now
        end_time: (Optional) End time in format "HH:mm"
        duration_minutes: (Optional) Duration in minutes, used if end_time not provided
        location: (Optional) Event location
        description: (Optional) Event description
    """
    # Get current date and time if not provided
    now = datetime.datetime.now()
    
    if not date:
        date = now.strftime("%Y-%m-%d")
        
    if not start_time:
        start_time = now.strftime("%H:%M")
    
    # Calculate end time if not provided
    if not end_time:
        start_dt = datetime.datetime.strptime(f"{date}T{start_time}", "%Y-%m-%dT%H:%M")
        end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
        end_time = end_dt.strftime("%H:%M")
    
    # Format ISO8601 dates
    start_date = f"{date}T{start_time}:00"
    end_date = f"{date}T{end_time}:00"
    
    # Create the event
    try:
        store = get_calendar_store()
        event_id = store.create_event(
            calendar_name=calendar_name,
            summary=summary,
            start_date=start_date,
            end_date=end_date,
            location=location,
            description=description
        )
        
        return f"Event '{summary}' created successfully in calendar '{calendar_name}' on {date} from {start_time} to {end_time}."
    except CalendarStoreError as e:
        return f"Failed to create event: {e}"
    except Exception as e:
        return f"Failed to create event: Unexpected error: {e}"


@mcp.prompt()
def search_events_prompt(
    query: str,
    calendar_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    """
    Search for events with a user-friendly response
    
    Args:
        query: Search query
        calendar_name: (Optional) Specific calendar to search in
        start_date: (Optional) Start date in format "yyyy-MM-dd"
        end_date: (Optional) End date in format "yyyy-MM-dd"
    """
    try:
        # Handle date ranges by adjusting time components
        if start_date and len(start_date) == 10:  # YYYY-MM-DD format (10 chars)
            start_date = f"{start_date}T00:00:00"
            
        if end_date and len(end_date) == 10:  # YYYY-MM-DD format (10 chars)
            end_date = f"{end_date}T23:59:59"
            
        store = get_calendar_store()
        events = store.get_events(
            calendar_name=calendar_name,
            start_date=start_date,
            end_date=end_date
        )
        
        # Filter events by query (case-insensitive)
        query = query.lower()
        matching_events = [
            event for event in events
            if (
                query in event["summary"].lower() or
                query in (event["description"] or "").lower() or
                query in (event["location"] or "").lower()
            )
        ]
        
        # Format a human-readable response
        if not matching_events:
            return f"No events found matching '{query}'."
            
        response = f"Found {len(matching_events)} events matching '{query}':\n\n"
        
        for event in matching_events:
            date = event["start"].split("T")[0]
            time = event["start"].split("T")[1][:5]  # Extract HH:MM
            response += f"- {date} {time}: {event['summary']} (in calendar '{event['calendar']}')\n"
            
        return response
    except CalendarStoreError as e:
        return f"Failed to search events: {e}"
    except Exception as e:
        return f"Failed to search events: Unexpected error: {e}"


# JSON API endpoints -------------------------------------------------------

@mcp.resource("api://calendars")
def api_list_calendars() -> str:
    """
    API endpoint to list all available calendars with JSON response
    
    Returns:
        JSON response with calendars
    """
    try:
        store = get_calendar_store()
        calendars = store.get_all_calendars()
        
        response = ApiResponse.success(
            data=CalendarList(calendars=calendars, count=len(calendars))
        )
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except CalendarStoreError as e:
        response = ApiResponse.error(message=str(e))
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except Exception as e:
        response = ApiResponse.error(message=f"Unexpected error: {str(e)}")
        return json.dumps(response.model_dump(), ensure_ascii=False)


@mcp.resource("api://events/{calendar_name}")
def api_get_events(calendar_name: str) -> str:
    """
    API endpoint to get events from a calendar with JSON response
    
    Args:
        calendar_name: The name of the calendar
        
    Returns:
        JSON response with events
    """
    try:
        # Use current date range if not specified
        start_dt, end_dt = create_date_range(None, None)
        
        # Format dates as ISO strings for the calendar store
        start_iso = format_iso(start_dt)
        end_iso = format_iso(end_dt)
        
        store = get_calendar_store()
        raw_events = store.get_events(
            calendar_name=calendar_name,
            start_date=start_iso,
            end_date=end_iso
        )
        
        # Convert to validated CalendarEvent objects
        events = []
        for raw_event in raw_events:
            # Add calendar name to each event
            raw_event["calendar_name"] = calendar_name
            event = CalendarEvent(**raw_event)
            events.append(event)
        
        response = ApiResponse.success(
            data=EventList(events=events, count=len(events))
        )
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except ValueError as e:
        response = ApiResponse.error(message=f"Date error: {str(e)}")
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except CalendarStoreError as e:
        response = ApiResponse.error(message=str(e))
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except Exception as e:
        response = ApiResponse.error(message=f"Unexpected error: {str(e)}")
        return json.dumps(response.model_dump(), ensure_ascii=False)


@mcp.resource("api://events/{calendar_name}/{start_date}/{end_date}")
def api_get_events_with_dates(calendar_name: str, start_date: str, end_date: str) -> str:
    """
    API endpoint to get events from a calendar within a date range with JSON response
    
    Args:
        calendar_name: The name of the calendar
        start_date: Start date in any format parseable by dateparser
        end_date: End date in any format parseable by dateparser
        
    Returns:
        JSON response with events
    """
    try:
        # Parse and validate date range
        start_dt, end_dt = create_date_range(start_date, end_date)
        
        # Ensure end_dt is set to end of day (23:59:59) if only date is provided
        # This is especially important for same-day searches
        if start_dt.hour == 0 and start_dt.minute == 0 and start_dt.second == 0:
            # Only modify if it's at the beginning of the day (likely just date was provided)
            start_dt = start_dt.replace(hour=0, minute=0, second=0)
            
        if end_dt.hour == 0 and end_dt.minute == 0 and end_dt.second == 0:
            # Only modify if it's at the beginning of the day (likely just date was provided)
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
        
        # Format dates as ISO strings for the calendar store
        start_iso = format_iso(start_dt)
        end_iso = format_iso(end_dt)
        
        store = get_calendar_store()
        raw_events = store.get_events(
            calendar_name=calendar_name,
            start_date=start_iso,
            end_date=end_iso
        )
        
        # Convert to validated CalendarEvent objects
        events = []
        for raw_event in raw_events:
            # Add calendar name to each event
            raw_event["calendar_name"] = calendar_name
            event = CalendarEvent(**raw_event)
            events.append(event)
        
        response = ApiResponse.success(
            data=EventList(events=events, count=len(events))
        )
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except ValueError as e:
        response = ApiResponse.error(message=f"Date error: {str(e)}")
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except CalendarStoreError as e:
        response = ApiResponse.error(message=str(e))
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except Exception as e:
        response = ApiResponse.error(message=f"Unexpected error: {str(e)}")
        return json.dumps(response.model_dump(), ensure_ascii=False)


@mcp.resource("api://events/create/{calendar_name}/{summary}/{start_date}/{end_date}")
def api_create_event_path(calendar_name: str, summary: str, start_date: str, end_date: str) -> str:
    """
    API endpoint to create a new event with JSON response using path parameters
    
    Args:
        calendar_name: Name of the calendar
        summary: Event title
        start_date: Start date in any format parseable by dateparser
        end_date: End date in any format parseable by dateparser
        
    Returns:
        JSON response with result
    """
    try:
        # Validate input with Pydantic model
        event_data = EventCreate(
            calendar_name=calendar_name,
            summary=summary,
            start_date=start_date,
            end_date=end_date,
            location=None,
            description=None,
            all_day=False
        )
        
        store = get_calendar_store()
        event_id = store.create_event(
            calendar_name=event_data.calendar_name,
            summary=event_data.summary,
            start_date=format_iso(event_data.start_date),
            end_date=format_iso(event_data.end_date),
            location=None,
            description=None
        )
        
        response = ApiResponse.success(
            data={"event_id": event_id},
            message="Event created successfully"
        )
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except ValueError as e:
        response = ApiResponse.error(message=f"Validation error: {str(e)}")
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except CalendarStoreError as e:
        response = ApiResponse.error(message=str(e))
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except Exception as e:
        response = ApiResponse.error(message=f"Unexpected error: {str(e)}")
        return json.dumps(response.model_dump(), ensure_ascii=False)


@mcp.resource("api://events/update/{event_id}/{calendar_name}")
def api_update_event_path(event_id: str, calendar_name: str) -> str:
    """
    API endpoint to update an event with JSON response using path parameters
    
    Args:
        event_id: ID of the event to update
        calendar_name: Name of the calendar
        
    Returns:
        JSON response with result
    """
    try:
        # Use only the path parameters (no optional updates)
        event_data = EventUpdate(
            event_id=event_id,
            calendar_name=calendar_name
        )
        
        store = get_calendar_store()
        
        success = store.update_event(
            event_id=event_data.event_id,
            calendar_name=event_data.calendar_name,
            summary=None,
            start_date=None,
            end_date=None,
            location=None,
            description=None
        )
        
        if success:
            response = ApiResponse.success(message="Event updated successfully")
        else:
            response = ApiResponse.error(message="Failed to update event")
        
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except ValueError as e:
        response = ApiResponse.error(message=f"Validation error: {str(e)}")
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except CalendarStoreError as e:
        response = ApiResponse.error(message=str(e))
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except Exception as e:
        response = ApiResponse.error(message=f"Unexpected error: {str(e)}")
        return json.dumps(response.model_dump(), ensure_ascii=False)


@mcp.resource("api://events/delete/{event_id}/{calendar_name}")
def api_delete_event_path(event_id: str, calendar_name: str) -> str:
    """
    API endpoint to delete an event with JSON response using path parameters
    
    Args:
        event_id: ID of the event to delete
        calendar_name: Name of the calendar
        
    Returns:
        JSON response with result
    """
    try:
        store = get_calendar_store()
        success = store.delete_event(event_id=event_id, calendar_name=calendar_name)
        
        if success:
            response = ApiResponse.success(message="Event deleted successfully")
        else:
            response = ApiResponse.error(message="Failed to delete event")
        
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except CalendarStoreError as e:
        response = ApiResponse.error(message=str(e))
        return json.dumps(response.model_dump(), ensure_ascii=False)
    except Exception as e:
        response = ApiResponse.error(message=f"Unexpected error: {str(e)}")
        return json.dumps(response.model_dump(), ensure_ascii=False) 