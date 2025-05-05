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

from . import calendar_store
from .calendar_store import CalendarStoreError
from .server import mcp
from .launch_agent import create_launch_agent, check_launch_agent, uninstall_launch_agent
from .date_utils import create_date_range, format_iso


# Load environment variables from .env file if it exists
dotenv.load_dotenv()


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with fallback to default."""
    return os.environ.get(key, default)


def run_server_command(args: argparse.Namespace) -> None:
    """Run the MCP server"""
    host = args.host or get_env("SERVER_HOST", "127.0.0.1")
    port = args.port or get_env("SERVER_PORT", "3000")
    
    # FastMCP doesn't accept host or port as parameters directly
    # Set them through environment variables
    os.environ["SERVER_PORT"] = str(port)
    
    # Run the server with SSE transport
    mcp.run(transport="sse")


def install_server_command(args: argparse.Namespace) -> None:
    """Install the MCP server in Claude"""
    script_path = Path(__file__).parent / "server.py"
    cmd = ["mcp", "install", str(script_path)]
    
    if args.name:
        cmd.extend(["--name", args.name])
    
    if args.env_file:
        cmd.extend(["-f", args.env_file])
    
    if args.env_vars:
        for var in args.env_vars:
            cmd.extend(["-v", var])
    
    subprocess.run(cmd, check=True)


def create_launch_agent_command(args: argparse.Namespace) -> None:
    """Create and install a Launch Agent plist"""
    # Get arguments or defaults
    port = args.port or int(os.environ.get("SERVER_PORT", "3000"))
    logdir = args.logdir or os.environ.get("LOG_DIR", "/tmp")
    agent_name = args.name or os.environ.get("LAUNCH_AGENT_NAME", "com.calendar-sse-mcp")
    auto_load = args.load or os.environ.get("AUTO_LOAD_AGENT", "").lower() == "true"
    
    # Use the dynamic launch agent creation function
    success, message, plist_path = create_launch_agent(
        agent_name=agent_name,
        port=port,
        log_dir=logdir,
        auto_load=auto_load
    )
    
    print(message)
    
    if not success:
        sys.exit(1)


def check_launch_agent_command(args: argparse.Namespace) -> None:
    """Check the status of installed launch agents"""
    agent_name = args.name or os.environ.get("LAUNCH_AGENT_NAME", "com.calendar-sse-mcp")
    show_logs = args.show_logs
    
    is_loaded, status = check_launch_agent(agent_name=agent_name, show_logs=show_logs)
    
    if not status["installed"]:
        print(f"Launch Agent not installed at: {status['plist_path']}")
        sys.exit(1)
    
    print(f"Launch Agent installed at: {status['plist_path']}")
    
    if status["loaded"]:
        print("Launch Agent is loaded and running")
        if status["process_info"]:
            print(f"Status details:\n{status['process_info']}")
    else:
        print("Launch Agent is installed but not currently loaded")
    
    if status["stdout_log"]:
        print(f"\nStdout log exists at: {status['stdout_log']}")
        if show_logs and status["stdout_content"]:
            print("\nLast 10 lines of stdout log:")
            for line in status["stdout_content"]:
                print(line.rstrip())
    else:
        print("\nStdout log does not exist")
    
    if status["stderr_log"]:
        print(f"Stderr log exists at: {status['stderr_log']}")
        if show_logs and status["stderr_content"]:
            print("\nLast 10 lines of stderr log:")
            for line in status["stderr_content"]:
                print(line.rstrip())
    else:
        print("Stderr log does not exist")


def uninstall_launch_agent_command(args: argparse.Namespace) -> None:
    """Uninstall a Launch Agent"""
    agent_name = args.name or os.environ.get("LAUNCH_AGENT_NAME", "com.calendar-sse-mcp")
    
    success, message = uninstall_launch_agent(agent_name=agent_name)
    print(message)
    
    if not success:
        sys.exit(1)


def list_calendars_command(args: argparse.Namespace) -> None:
    """List all available calendars"""
    try:
        # Create a CalendarStore instance
        store = calendar_store.CalendarStore(quiet=args.json)
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
        # Create a CalendarStore instance
        store = calendar_store.CalendarStore(quiet=args.json)
        events = store.get_events(
            calendar_name=args.calendar,
            start_date=args.start_date,
            end_date=args.end_date
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


def create_event_command(args: argparse.Namespace) -> None:
    """Create a new event"""
    try:
        # Get calendar from args or env
        calendar = args.calendar or get_env("DEFAULT_CALENDAR")
        if not calendar:
            print("Error: No calendar specified. Please provide a calendar name or set DEFAULT_CALENDAR in .env", file=sys.stderr)
            sys.exit(1)
            
        # Parse start and end times
        duration = args.duration or int(get_env("EVENT_DURATION_MINUTES", "60"))
        
        if args.duration and not args.end_time:
            # Calculate end time based on duration
            start = datetime.datetime.strptime(f"{args.date}T{args.start_time}", "%Y-%m-%dT%H:%M")
            end = start + datetime.timedelta(minutes=duration)
            end_time = end.strftime("%H:%M")
        else:
            end_time = args.end_time
        
        # Format ISO8601 dates
        start_date = f"{args.date}T{args.start_time}:00"
        end_date = f"{args.date}T{end_time}:00"
        
        # Create a CalendarStore instance
        store = calendar_store.CalendarStore(quiet=args.json)
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
            print(f"Event created successfully! Event ID: {event_id}")
    except CalendarStoreError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def update_event_command(args: argparse.Namespace) -> None:
    """Update an existing event"""
    try:
        # Format ISO8601 dates if provided
        start_date = None
        if args.date and args.start_time:
            start_date = f"{args.date}T{args.start_time}:00"
        
        end_date = None
        if args.date and args.end_time:
            end_date = f"{args.date}T{args.end_time}:00"
        
        # Create a CalendarStore instance
        store = calendar_store.CalendarStore(quiet=args.json)
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
        # Create a CalendarStore instance
        store = calendar_store.CalendarStore(quiet=args.json)
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
        # Get calendar from args or env if not provided
        calendar_name = args.calendar or get_env("DEFAULT_CALENDAR", None)
        
        # Create a CalendarStore instance
        store = calendar_store.CalendarStore(quiet=args.json)
        events = store.get_events(
            calendar_name=calendar_name,
            start_date=args.start_date,
            end_date=args.end_date
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


def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(description="Calendar MCP Server CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Run the MCP server")
    server_parser.add_argument("--host", help="Server host")
    server_parser.add_argument("--port", type=int, help="Server port")
    server_parser.set_defaults(func=run_server_command)
    
    # Install server command
    install_parser = subparsers.add_parser("install", help="Install the server in Claude")
    install_parser.add_argument("--name", help="Custom name for the server")
    install_parser.add_argument("--env-file", help="Environment file to use")
    install_parser.add_argument("--env-vars", nargs="+", help="Environment variables to set")
    install_parser.set_defaults(func=install_server_command)
    
    # Launch agent commands
    agent_parser = subparsers.add_parser("agent", help="Manage Launch Agent")
    agent_subparsers = agent_parser.add_subparsers(dest="agent_command", help="Agent command to run", required=True)
    
    # Create launch agent command
    create_agent_parser = agent_subparsers.add_parser("create", help="Create a Launch Agent")
    create_agent_parser.add_argument("--name", help="Launch Agent name")
    create_agent_parser.add_argument("--port", type=int, help="Server port")
    create_agent_parser.add_argument("--logdir", help="Log directory")
    create_agent_parser.add_argument("--load", action="store_true", help="Auto-load the agent")
    create_agent_parser.set_defaults(func=create_launch_agent_command)
    
    # Check launch agent command
    check_agent_parser = agent_subparsers.add_parser("check", help="Check Launch Agent status")
    check_agent_parser.add_argument("--name", help="Launch Agent name")
    check_agent_parser.add_argument("--show-logs", action="store_true", help="Show log contents")
    check_agent_parser.set_defaults(func=check_launch_agent_command)
    
    # Uninstall launch agent command
    uninstall_agent_parser = agent_subparsers.add_parser("uninstall", help="Uninstall Launch Agent")
    uninstall_agent_parser.add_argument("--name", help="Launch Agent name")
    uninstall_agent_parser.set_defaults(func=uninstall_launch_agent_command)
    
    # Calendars command
    calendars_parser = subparsers.add_parser('calendars', help='List all available calendars')
    calendars_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    calendars_parser.set_defaults(func=list_calendars_command)
    
    # Events command
    events_parser = subparsers.add_parser('events', help='Get events from a calendar')
    events_parser.add_argument(
        "calendar",
        help="Name of the calendar"
    )
    events_parser.add_argument(
        "--start-date",
        help="Start date in format YYYY-MM-DD"
    )
    events_parser.add_argument(
        "--end-date",
        help="End date in format YYYY-MM-DD"
    )
    events_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    events_parser.set_defaults(func=get_events_command)
    
    # Create event command
    create_parser = subparsers.add_parser('create', help='Create a new event')
    create_parser.add_argument(
        "calendar",
        nargs='?',
        help="Name of the calendar (default from .env DEFAULT_CALENDAR)"
    )
    create_parser.add_argument(
        "summary",
        help="Event title/summary"
    )
    create_parser.add_argument(
        "--date",
        default=datetime.datetime.now().strftime("%Y-%m-%d"),
        help="Event date in format YYYY-MM-DD (default: today)"
    )
    create_parser.add_argument(
        "--start-time",
        default=datetime.datetime.now().strftime("%H:%M"),
        help="Start time in format HH:MM (default: current time)"
    )
    create_parser.add_argument(
        "--end-time",
        help="End time in format HH:MM (calculated from duration if not provided)"
    )
    create_parser.add_argument(
        "--duration",
        type=int,
        help="Duration in minutes (default from .env or 60)"
    )
    create_parser.add_argument(
        "--location",
        help="Event location"
    )
    create_parser.add_argument(
        "--description",
        help="Event description"
    )
    create_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    create_parser.set_defaults(func=create_event_command)
    
    # Update event command
    update_parser = subparsers.add_parser('update', help='Update an existing event')
    update_parser.add_argument(
        "calendar",
        help="Name of the calendar"
    )
    update_parser.add_argument(
        "event_id",
        help="ID of the event to update"
    )
    update_parser.add_argument(
        "--summary",
        help="New event title/summary"
    )
    update_parser.add_argument(
        "--date",
        help="New event date in format YYYY-MM-DD"
    )
    update_parser.add_argument(
        "--start-time",
        help="New start time in format HH:MM"
    )
    update_parser.add_argument(
        "--end-time",
        help="New end time in format HH:MM"
    )
    update_parser.add_argument(
        "--location",
        help="New event location"
    )
    update_parser.add_argument(
        "--description",
        help="New event description"
    )
    update_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    update_parser.set_defaults(func=update_event_command)
    
    # Delete event command
    delete_parser = subparsers.add_parser('delete', help='Delete an event')
    delete_parser.add_argument(
        "calendar",
        help="Name of the calendar"
    )
    delete_parser.add_argument(
        "event_id",
        help="ID of the event to delete"
    )
    delete_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    delete_parser.set_defaults(func=delete_event_command)
    
    # Search events command
    search_parser = subparsers.add_parser('search', help='Search for events')
    search_parser.add_argument(
        "query",
        help="Search query"
    )
    search_parser.add_argument(
        "--calendar",
        help="Name of the calendar (default from .env DEFAULT_CALENDAR)"
    )
    search_parser.add_argument(
        "--start-date",
        help="Start date in format YYYY-MM-DD"
    )
    search_parser.add_argument(
        "--end-date",
        help="End date in format YYYY-MM-DD"
    )
    search_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    search_parser.set_defaults(func=search_events_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no command is provided
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    # Run the appropriate function
    args.func(args)


if __name__ == "__main__":
    main() 