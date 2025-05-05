#!/usr/bin/env python3
"""
Calendar MCP Server - An MCP server for interacting with macOS Calendar.app
"""
import datetime
import json
import os
from typing import Dict, List, Optional, Union, Any

from mcp.server.fastmcp import FastMCP

from .calendar_store import CalendarStore, CalendarStoreError
from .models import ApiResponse, CalendarEvent, EventCreate, EventUpdate, EventList, CalendarList
from .date_utils import create_date_range, format_iso


# Get port from environment or use default
port = int(os.environ.get("SERVER_PORT", "3000"))

# Create the MCP server with port setting
mcp = FastMCP("Calendar MCP", port=port)


# Resources -----------------------------------------------------------------

@mcp.resource("calendars://list")
def list_calendars() -> str:
    """
    List all available calendars in Calendar.app
    
    Returns:
        JSON string containing calendar names
    """
    try:
        store = CalendarStore(quiet=True)
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
        store = CalendarStore(quiet=True)
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
        store = CalendarStore(quiet=True)
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
        store = CalendarStore(quiet=True)
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
        store = CalendarStore(quiet=True)
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
        store = CalendarStore(quiet=True)
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
    end_date: Optional[str] = None
) -> str:
    """
    Search for events in Calendar.app
    
    Args:
        query: Search query (case-insensitive substring match)
        calendar_name: (Optional) Specific calendar to search in
        start_date: (Optional) Start date in format "yyyy-MM-dd"
        end_date: (Optional) End date in format "yyyy-MM-dd"
        
    Returns:
        JSON string containing matching events
    """
    try:
        store = CalendarStore(quiet=True)
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
        
        return json.dumps({
            "events": matching_events,
            "count": len(matching_events)
        }, ensure_ascii=False)
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
        store = CalendarStore(quiet=True)
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
        store = CalendarStore(quiet=True)
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
        store = CalendarStore(quiet=True)
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


# Prompts ------------------------------------------------------------------

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
        store = CalendarStore(quiet=True)
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
        store = CalendarStore(quiet=True)
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
        store = CalendarStore(quiet=True)
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
        
        store = CalendarStore(quiet=True)
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
        
        # Format dates as ISO strings for the calendar store
        start_iso = format_iso(start_dt)
        end_iso = format_iso(end_dt)
        
        store = CalendarStore(quiet=True)
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
        
        store = CalendarStore(quiet=True)
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
        
        store = CalendarStore(quiet=True)
        
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
        store = CalendarStore(quiet=True)
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


# Main entry point ---------------------------------------------------------

if __name__ == "__main__":
    mcp.run() 