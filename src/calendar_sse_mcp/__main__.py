#!/usr/bin/env python3
"""
Command-line interface for the Calendar MCP Server
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, NoReturn, Callable, Union

import dotenv
import dateparser
import re

from . import calendar_store, __version__
from .calendar_store import CalendarStoreError
from .server import mcp, get_calendar_store
from .launch_agent import create_launch_agent, check_launch_agent, uninstall_launch_agent
from .date_utils import create_date_range, format_iso


# Load environment variables from .env file if it exists
dotenv.load_dotenv()


# ----- Utility functions -----

def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with fallback to default."""
    return os.environ.get(key, default)


def show_version():
    """Display the package version and exit"""
    print(f"calendar-sse-mcp version {__version__}")
    sys.exit(0)


def _get_launch_agent_plist_path(agent_name: str) -> Path:
    """Get the path to the launch agent plist file"""
    home_dir = Path.home()
    return home_dir / "Library" / "LaunchAgents" / f"{agent_name}.plist"


def _run_launchctl_command(operation: str, plist_path: Path) -> bool:
    """Run a launchctl command (load/unload) on a plist file"""
    try:
        result = subprocess.run(
            ["launchctl", operation, str(plist_path)],
            check=False,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running launchctl {operation}: {e}", file=sys.stderr)
        return False


# ----- CLI Command Parsers -----

def add_calendars_parser(subparsers):
    """Add the calendars command parser"""
    parser = subparsers.add_parser("calendars", help="List all available calendars")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.set_defaults(func=list_calendars_command)
    return parser


def add_events_parser(subparsers):
    """Add the events command parser"""
    parser = subparsers.add_parser("events", help="Get events from a calendar")
    parser.add_argument("calendar", help="Name of the calendar")
    parser.add_argument("--start-date", help="Start date in flexible format (e.g. 'yesterday', '2023-01-01')")
    parser.add_argument("--end-date", help="End date in flexible format (e.g. 'tomorrow', '2023-12-31')")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.set_defaults(func=get_events_command)
    return parser


def add_create_parser(subparsers):
    """Add the create command parser"""
    parser = subparsers.add_parser("create", help="Create a new event")
    parser.add_argument("--cal", "--calendar", dest="calendar", help="Name of the calendar (default from .env DEFAULT_CALENDAR)")
    parser.add_argument("--event", "--summary", dest="summary", required=True, help="Event title/summary")
    parser.add_argument("--date", default=datetime.datetime.now().strftime("%Y-%m-%d"), 
                        help="Event date in flexible format (default: today)")
    parser.add_argument("--start", "--start-time", dest="start_time", 
                        default=datetime.datetime.now().strftime("%H:%M"),
                        help="Start time in flexible format (default: current time)")
    parser.add_argument("--end", "--end-time", dest="end_time", 
                        help="End time in flexible format (calculated from duration if not provided)")
    parser.add_argument("--duration", type=str, help="Duration (e.g. '60min', '1h', '1.5 hours', default: 60min)")
    parser.add_argument("--location", help="Event location")
    parser.add_argument("--description", help="Event description")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.set_defaults(func=create_event_command_v2)
    return parser


def add_update_parser(subparsers):
    """Add the update command parser"""
    parser = subparsers.add_parser("update", help="Update an existing event")
    parser.add_argument("calendar", help="Name of the calendar")
    parser.add_argument("event_id", help="ID of the event to update")
    parser.add_argument("--summary", help="New event title/summary")
    parser.add_argument("--date", help="New event date in flexible format")
    parser.add_argument("--start-time", help="New start time in flexible format")
    parser.add_argument("--end-time", help="New end time in flexible format")
    parser.add_argument("--location", help="New event location")
    parser.add_argument("--description", help="New event description")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.set_defaults(func=update_event_command)
    return parser


def add_delete_parser(subparsers):
    """Add the delete command parser"""
    parser = subparsers.add_parser("delete", help="Delete an event")
    parser.add_argument("calendar", help="Name of the calendar")
    parser.add_argument("event_id", help="ID of the event to delete")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.set_defaults(func=delete_event_command)
    return parser


def add_search_parser(subparsers):
    """Add the search command parser"""
    parser = subparsers.add_parser("search", help="Search for events")
    parser.add_argument("query", help="Search term (case-insensitive)")
    parser.add_argument("--calendar", help="Specific calendar to search in")
    parser.add_argument("--start-date", help="Start date in flexible format")
    parser.add_argument("--end-date", help="End date in flexible format")
    parser.add_argument("--duration", help="Duration from start date (e.g., '3d', '1 week')")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.set_defaults(func=search_events_command)
    return parser


def create_cli_parser(subparsers):
    """Create the CLI command parser"""
    cli_parser = subparsers.add_parser("cli", help="Direct calendar operations")
    cli_parser.add_argument("--dev", action="store_true", help="Connect to development server (port 27213)")
    cli_subparsers = cli_parser.add_subparsers(dest="cli_command", help="Calendar operation", required=True)
    
    # Add calendar operations to cli_subparsers
    add_calendars_parser(cli_subparsers)
    add_events_parser(cli_subparsers)
    add_create_parser(cli_subparsers)
    add_update_parser(cli_subparsers)
    add_delete_parser(cli_subparsers)
    add_search_parser(cli_subparsers)
    
    return cli_parser


# ----- Server Command Parsers -----

def add_start_parser(subparsers):
    """Add the start command parser"""
    parser = subparsers.add_parser("start", help="Start the server")
    parser.add_argument("--name", default="com.calendar-sse-mcp", help="Launch Agent name")
    parser.set_defaults(func=server_start_command)
    return parser


def add_stop_parser(subparsers):
    """Add the stop command parser"""
    parser = subparsers.add_parser("stop", help="Stop the server")
    parser.add_argument("--name", default="com.calendar-sse-mcp", help="Launch Agent name")
    parser.set_defaults(func=server_stop_command)
    return parser


def add_restart_parser(subparsers):
    """Add the restart command parser"""
    parser = subparsers.add_parser("restart", help="Restart the server")
    parser.add_argument("--name", default="com.calendar-sse-mcp", help="Launch Agent name")
    parser.set_defaults(func=server_restart_command)
    return parser


def add_install_parser(subparsers):
    """Add the install command parser"""
    parser = subparsers.add_parser("install", help="Install the server as a LaunchAgent")
    # Basic options
    parser.add_argument("--port", type=int, default=27212, help="Server port (default: 27212)")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--logdir", default="/tmp", help="Log directory (default: /tmp)")
    parser.add_argument("--name", default="com.calendar-sse-mcp", help="Launch Agent name")
    
    # Installation options
    parser.add_argument("--no-load", action="store_true", help="Don't load the agent after creation")
    parser.add_argument("--dev", action="store_true", help="Install as development server on port 27213")
    parser.add_argument("--working-dir", help="Working directory for the server (default: current directory)")
    parser.add_argument("--python-path", help="Path to Python executable (default: auto-detect)")
    
    # Environment variables
    parser.add_argument("--env", "-e", action="append", help="Additional environment variables in the format KEY=VALUE")
    
    # Auto-start options
    parser.add_argument("--run-at-login", action="store_true", default=True, help="Run the server at login (default: True)")
    parser.add_argument("--no-run-at-login", action="store_false", dest="run_at_login", help="Don't run the server at login")
    parser.add_argument("--keep-alive", action="store_true", default=True, help="Keep the server alive (restart on crash, default: True)")
    parser.add_argument("--no-keep-alive", action="store_false", dest="keep_alive", help="Don't restart the server on crash")
    
    parser.set_defaults(func=server_install_command)
    return parser


def add_uninstall_parser(subparsers):
    """Add the uninstall command parser"""
    parser = subparsers.add_parser("uninstall", help="Uninstall the server LaunchAgent")
    parser.add_argument("--name", default="com.calendar-sse-mcp", help="Launch Agent name")
    parser.add_argument("--dev", action="store_true", help="Uninstall development server (on port 27213)")
    parser.set_defaults(func=server_uninstall_command)
    return parser


def add_uninstall_dev_parser(subparsers):
    """Add the uninstall-dev command parser"""
    parser = subparsers.add_parser("uninstall-dev", help="Uninstall the development server LaunchAgent")
    parser.set_defaults(func=server_uninstall_dev_command)
    return parser


def add_logs_parser(subparsers):
    """Add the logs command parser"""
    parser = subparsers.add_parser("logs", help="Display server logs")
    parser.add_argument("--name", default="com.calendar-sse-mcp", help="Launch Agent name")
    parser.add_argument("--level", choices=["info", "error", "all"], default="all", 
                       help="Log level to display (info=stdout, error=stderr, all=both)")
    parser.add_argument("--lines", type=int, default=10, help="Number of log lines to show")
    parser.set_defaults(func=server_logs_command)
    return parser


def add_run_parser(subparsers):
    """Add the run command parser"""
    parser = subparsers.add_parser("run", help="Run the server directly in the foreground")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=27212, help="Port to bind to")
    parser.add_argument("--dev", action="store_true", help="Run on development port (27213)")
    parser.set_defaults(func=run_server_command)
    return parser


def create_server_parser(subparsers):
    """Create the server command parser"""
    server_parser = subparsers.add_parser("server", help="Server management operations")
    server_subparsers = server_parser.add_subparsers(dest="server_command", help="Server operation", required=True)
    
    add_start_parser(server_subparsers)
    add_stop_parser(server_subparsers)
    add_restart_parser(server_subparsers)
    add_install_parser(server_subparsers)
    add_uninstall_parser(server_subparsers)
    add_uninstall_dev_parser(server_subparsers)
    add_logs_parser(server_subparsers)
    add_run_parser(server_subparsers)
    
    return server_parser


# ----- CLI Command Handlers -----

def list_calendars_command(args: argparse.Namespace) -> None:
    """List all available calendars"""
    try:
        # Get server port - use dev port if specified
        port = 27213 if hasattr(args, 'dev') and args.dev else 27212
        
        # Use the global calendar store instance instead of creating a new one
        store = get_calendar_store()
        calendars = store.get_all_calendars()
        
        if args.json:
            print(json.dumps(calendars, indent=2, ensure_ascii=False))
        else:
            print("Available calendars:")
            for calendar in calendars:
                print(f"- {calendar}")
    except CalendarStoreError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def get_events_command(args: argparse.Namespace) -> None:
    """Get events from a calendar"""
    try:
        # Get server port - use dev port if specified
        port = 27213 if hasattr(args, 'dev') and args.dev else 27212
        
        # Handle date ranges by adjusting time components
        start_date = args.start_date
        end_date = args.end_date
        
        # If start_date is provided and doesn't have time component, add beginning of day
        if start_date and len(start_date) == 10:  # YYYY-MM-DD format (10 chars)
            start_date = f"{start_date}T00:00:00"
            
        # If end_date is provided and doesn't have time component, add end of day
        if end_date and len(end_date) == 10:  # YYYY-MM-DD format (10 chars)
            end_date = f"{end_date}T23:59:59"
            
        # Create a CalendarStore instance
        store = get_calendar_store()
        events = store.get_events(
            calendar_name=args.calendar,
            start_date=start_date,
            end_date=end_date
        )
        
        if args.json:
            print(json.dumps(events, indent=2, ensure_ascii=False))
        else:
            print(f"Events in calendar '{args.calendar}':")
            for event in events:
                start_time = event["start"].split("T")[1][:5]  # Extract HH:MM
                print(f"- {start_time} | {event['summary']} (ID: {event['id']})")
    except CalendarStoreError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def create_event_command_v2(args: argparse.Namespace) -> None:
    """Create a new event with flexible time parsing"""
    try:
        # Get server port - use dev port if specified
        port = 27213 if hasattr(args, 'dev') and args.dev else 27212
        
        # Get calendar from args or env
        calendar = args.calendar or get_env("DEFAULT_CALENDAR")
        if not calendar:
            print("Error: No calendar specified. Please provide a calendar name with --cal or set DEFAULT_CALENDAR in .env", 
                  file=sys.stderr)
            sys.exit(1)
            
        # Parse date
        date_str = args.date
        parsed_date = dateparser.parse(date_str)
        if not parsed_date:
            print(f"Error: Could not parse date '{date_str}'", file=sys.stderr)
            sys.exit(1)
        date_only = parsed_date.strftime("%Y-%m-%d")
        
        # Parse start time
        start_time_str = args.start_time
        parsed_start = dateparser.parse(f"{date_only} {start_time_str}")
        if not parsed_start:
            print(f"Error: Could not parse start time '{start_time_str}'", file=sys.stderr)
            sys.exit(1)
        start_time = parsed_start.strftime("%H:%M")
        
        # Parse end time or duration
        if args.end_time:
            # End time is provided directly
            parsed_end = dateparser.parse(f"{date_only} {args.end_time}")
            if not parsed_end:
                print(f"Error: Could not parse end time '{args.end_time}'", file=sys.stderr)
                sys.exit(1)
            end_time = parsed_end.strftime("%H:%M")
        else:
            # Calculate end time from duration
            duration_minutes = 60  # Default duration
            
            if args.duration:
                # Try to parse the duration string
                duration_str = args.duration.lower()
                
                # First try to extract numeric part and unit
                match = re.search(r'(\d+\.?\d*)\s*([a-zA-Z]+)', duration_str)
                if match:
                    value = float(match.group(1))
                    unit = match.group(2)
                    
                    if 'hour' in unit or unit.startswith('h'):
                        duration_minutes = int(value * 60)
                    elif 'min' in unit or unit.startswith('m'):
                        duration_minutes = int(value)
                    else:
                        print(f"Warning: Unrecognized duration unit '{unit}', using default 60 minutes", file=sys.stderr)
                else:
                    # Try to interpret as a pure number (minutes)
                    try:
                        duration_minutes = int(float(duration_str))
                    except ValueError:
                        print(f"Warning: Could not parse duration '{duration_str}', using default 60 minutes", 
                              file=sys.stderr)
            
            # Calculate end time
            start_dt = datetime.datetime.strptime(f"{date_only}T{start_time}", "%Y-%m-%dT%H:%M")
            end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
            end_time = end_dt.strftime("%H:%M")
        
        # Format ISO8601 dates
        start_date = f"{date_only}T{start_time}:00"
        end_date = f"{date_only}T{end_time}:00"
        
        # Create the event
        store = get_calendar_store()
        event_id = store.create_event(
            calendar_name=calendar,
            summary=args.summary,
            start_date=start_date,
            end_date=end_date,
            location=args.location,
            description=args.description
        )
        
        if args.json:
            print(json.dumps({"success": True, "event_id": event_id}, ensure_ascii=False))
        else:
            print(f"Event '{args.summary}' created successfully in calendar '{calendar}'")
            print(f"  Date: {date_only}")
            print(f"  Time: {start_time} - {end_time}")
            print(f"  Event ID: {event_id}")
    except CalendarStoreError as e:
        if args.json:
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.json:
            print(json.dumps({"success": False, "error": f"Unexpected error: {e}"}, ensure_ascii=False))
        else:
            print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def update_event_command(args: argparse.Namespace) -> None:
    """Update an existing event"""
    try:
        # Get server port - use dev port if specified
        port = 27213 if hasattr(args, 'dev') and args.dev else 27212
        
        # Format ISO8601 dates if provided
        start_date = None
        if args.date and args.start_time:
            start_date = f"{args.date}T{args.start_time}:00"
        
        end_date = None
        if args.date and args.end_time:
            end_date = f"{args.date}T{args.end_time}:00"
        
        # Create a CalendarStore instance
        store = get_calendar_store()
        success = store.update_event(
            event_id=args.event_id,
            calendar_name=args.calendar,
            summary=args.summary,
            start_date=start_date,
            end_date=end_date,
            location=args.location,
            description=args.description
        )
        
        if args.json:
            print(json.dumps({"success": success}, ensure_ascii=False))
        else:
            print("Event updated successfully!")
    except CalendarStoreError as e:
        if args.json:
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.json:
            print(json.dumps({"success": False, "error": f"Unexpected error: {e}"}, ensure_ascii=False))
        else:
            print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def delete_event_command(args: argparse.Namespace) -> None:
    """Delete an event"""
    try:
        # Get server port - use dev port if specified
        port = 27213 if hasattr(args, 'dev') and args.dev else 27212
        
        # Create a CalendarStore instance
        store = get_calendar_store()
        success = store.delete_event(
            event_id=args.event_id,
            calendar_name=args.calendar
        )
        
        if args.json:
            print(json.dumps({"success": success}, ensure_ascii=False))
        else:
            print("Event deleted successfully!")
    except CalendarStoreError as e:
        if args.json:
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.json:
            print(json.dumps({"success": False, "error": f"Unexpected error: {e}"}, ensure_ascii=False))
        else:
            print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def search_events_command(args: argparse.Namespace) -> None:
    """Search for events"""
    try:
        # Get server port - use dev port if specified
        port = 27213 if hasattr(args, 'dev') and args.dev else 27212
        
        # Get calendar from args, but don't default to DEFAULT_CALENDAR
        # This allows searching across all calendars when not specified
        calendar_name = args.calendar
        
        # Handle date ranges by adjusting time components
        start_date = args.start_date
        end_date = args.end_date
        
        # If start_date is provided and doesn't have time component, add beginning of day
        if start_date and len(start_date) == 10:  # YYYY-MM-DD format (10 chars)
            start_date = f"{start_date}T00:00:00"
            
        # If end_date is provided and doesn't have time component, add end of day
        if end_date and len(end_date) == 10:  # YYYY-MM-DD format (10 chars)
            end_date = f"{end_date}T23:59:59"
        
        # Create a CalendarStore instance
        store = get_calendar_store()
        events = store.get_events(
            calendar_name=calendar_name,
            start_date=start_date,
            end_date=end_date
        )
        
        # Filter events by query
        query = args.query.lower()
        matching_events = [
            event for event in events
            if (
                query in event["summary"].lower() or
                query in (event["description"] or "").lower() or
                query in (event["location"] or "").lower()
            )
        ]
        
        if args.json:
            print(json.dumps(matching_events, indent=2, ensure_ascii=False))
        else:
            print(f"Found {len(matching_events)} matching events:")
            for event in matching_events:
                start_time = event["start"].split("T")[1][:5]  # Extract HH:MM
                date = event["start"].split("T")[0]
                print(f"- {date} {start_time} | {event['summary']} (ID: {event['id']})")
    except CalendarStoreError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


# ----- Server Command Handlers -----

def run_server_command(args: argparse.Namespace) -> None:
    """Run the MCP server"""
    # Get server port - use dev port if specified
    port = 27213 if hasattr(args, 'dev') and args.dev else args.port or get_env("SERVER_PORT", "27212")
    host = args.host or get_env("SERVER_HOST", "127.0.0.1")
    
    # Set environment variables for the server
    os.environ["SERVER_HOST"] = str(host)
    os.environ["SERVER_PORT"] = str(port)
    
    print(f"Starting server on {host}:{port}...")
    
    # Set the settings directly on the mcp object
    mcp.settings.port = port
    mcp.settings.host = host
    
    # Run the server with SSE transport
    mcp.run(transport="sse")


def server_install_command(args: argparse.Namespace) -> None:
    """Install the server as a Launch Agent"""
    agent_name = args.name
    plist_path = _get_launch_agent_plist_path(agent_name)
    
    # If --dev is specified, override the port to 27213
    if args.dev:
        port = 27213
        print(f"Installing in DEVELOPMENT mode on port {port}")
    else:
        port = args.port
    
    # Check if the agent is already installed
    if plist_path.exists():
        print(f"Launch Agent '{agent_name}' is already installed. Removing first...")
        _run_launchctl_command("unload", plist_path)
        try:
            plist_path.unlink()
            print(f"Existing Launch Agent plist removed: {plist_path}")
        except Exception as e:
            print(f"Error removing existing plist: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Create and install the Launch Agent
    print(f"Installing Launch Agent '{agent_name}' with port {port}...")
    success, message, new_plist_path = create_launch_agent(
        agent_name=agent_name,
        port=port,
        log_dir=args.logdir,
        auto_load=not args.no_load
    )
    
    print(message)
    
    if not success:
        sys.exit(1)
    
    if not args.no_load:
        print(f"Launch Agent started. Server is running at http://localhost:{port}")
        print(f"Log files: {args.logdir}/{agent_name}-stdout.log and {args.logdir}/{agent_name}-stderr.log")


def server_uninstall_command(args: argparse.Namespace) -> None:
    """Uninstall the server Launch Agent"""
    # If --dev is specified, use the dev agent name
    if hasattr(args, 'dev') and args.dev:
        agent_name = "com.calendar-sse-mcp.dev"
        print(f"Uninstalling DEVELOPMENT server agent '{agent_name}'...")
    else:
        agent_name = args.name
        print(f"Uninstalling server agent '{agent_name}'...")
    
    success, message = uninstall_launch_agent(agent_name=agent_name)
    print(message)
    
    if not success:
        sys.exit(1)


def server_start_command(args: argparse.Namespace) -> None:
    """Start the server Launch Agent"""
    agent_name = args.name
    plist_path = _get_launch_agent_plist_path(agent_name)
    
    if not plist_path.exists():
        print(f"Error: Launch Agent '{agent_name}' is not installed. Install it first with 'calendar-sse server install'", 
              file=sys.stderr)
        sys.exit(1)
    
    # Check if already loaded
    loaded = False
    try:
        result = subprocess.run(
            ["launchctl", "list"],
            check=True,
            capture_output=True,
            text=True
        )
        loaded = agent_name in result.stdout
    except Exception:
        # Can't determine if it's loaded, so we'll try to load it anyway
        pass
    
    if loaded:
        print(f"Launch Agent '{agent_name}' is already running.")
        return
    
    print(f"Starting Launch Agent '{agent_name}'...")
    if _run_launchctl_command("load", plist_path):
        print(f"Launch Agent '{agent_name}' started successfully.")
    else:
        print(f"Failed to start Launch Agent '{agent_name}'", file=sys.stderr)
        sys.exit(1)


def server_stop_command(args: argparse.Namespace) -> None:
    """Stop the server Launch Agent"""
    agent_name = args.name
    plist_path = _get_launch_agent_plist_path(agent_name)
    
    if not plist_path.exists():
        print(f"Error: Launch Agent '{agent_name}' is not installed.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Stopping Launch Agent '{agent_name}'...")
    if _run_launchctl_command("unload", plist_path):
        print(f"Launch Agent '{agent_name}' stopped successfully.")
    else:
        print(f"Failed to stop Launch Agent '{agent_name}'", file=sys.stderr)
        sys.exit(1)


def server_restart_command(args: argparse.Namespace) -> None:
    """Restart the server Launch Agent"""
    agent_name = args.name
    server_stop_command(args)
    server_start_command(args)


def server_logs_command(args: argparse.Namespace) -> None:
    """Display server logs"""
    agent_name = args.name
    is_loaded, status = check_launch_agent(agent_name=agent_name, show_logs=True)
    
    if not status["installed"]:
        print(f"Launch Agent '{agent_name}' is not installed.", file=sys.stderr)
        sys.exit(1)
    
    # Display status information
    print(f"Launch Agent '{agent_name}' status: {'running' if status['loaded'] else 'stopped'}")
    
    # Display logs based on level
    if args.level in ["all", "info"] and status["stdout_log"]:
        print(f"\n--- Last {args.lines} lines of stdout log ({status['stdout_log']}) ---")
        if status["stdout_content"]:
            for line in status["stdout_content"][-args.lines:]:
                print(line.rstrip())
        else:
            print("(No stdout content)")
    
    if args.level in ["all", "error"] and status["stderr_log"]:
        print(f"\n--- Last {args.lines} lines of stderr log ({status['stderr_log']}) ---")
        if status["stderr_content"]:
            for line in status["stderr_content"][-args.lines:]:
                print(line.rstrip())
        else:
            print("(No stderr content)")
    
    if not status["stdout_log"] and not status["stderr_log"]:
        print("No log files found.")


def server_uninstall_dev_command(args: argparse.Namespace) -> None:
    """Uninstall the development server Launch Agent"""
    agent_name = "com.calendar-sse-mcp.dev"
    print(f"Uninstalling development server agent '{agent_name}'...")
    
    success, message = uninstall_launch_agent(agent_name=agent_name)
    print(message)
    
    if not success:
        sys.exit(1)


# ----- Main Entry Point -----

def main():
    """Main entry point for the calendar-sse CLI"""
    parser = argparse.ArgumentParser(description="Calendar SSE MCP Tool")
    parser.add_argument("--version", action="store_true", help="Show version information and exit")
    
    # Add subparsers for "cli" and "server" commands
    subparsers = parser.add_subparsers(dest="command", help="Command category", required=False)
    
    # Setup CLI and Server parsers
    create_cli_parser(subparsers)
    create_server_parser(subparsers)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show version and exit if --version is provided
    if hasattr(args, 'version') and args.version:
        show_version()
    
    # If no command was provided
    if not hasattr(args, 'command') or not args.command:
        parser.print_help()
        sys.exit(1)
    
    # If command is provided but no subcommand function
    if not hasattr(args, 'func'):
        if args.command == "cli":
            subparsers.choices["cli"].print_help()
        elif args.command == "server":
            subparsers.choices["server"].print_help()
        sys.exit(1)
    
    # Run the corresponding function for the command
    args.func(args)


# For backward compatibility with existing entry points
cli_main = main


if __name__ == "__main__":
    main()
