"""
EventKit-based calendar store for accessing macOS Calendar.app events.
"""
import os
import subprocess
import sys
import time
import datetime
import threading
from typing import List, Dict, Any, Optional, Tuple

from EventKit import (
    EKCalendarEventAvailabilityBusy,
    EKEntityTypeEvent,
    EKEventStore,
    EKEvent,
    EKCalendar,
    EKAlarm,
    EKSpanThisEvent
)
from Foundation import NSDate, NSDefaultRunLoopMode, NSRunLoop, NSURL


class CalendarStoreError(Exception):
    """Exception raised for errors in the CalendarStore."""
    pass


class CalendarStore:
    """Class to access macOS Calendar.app using EventKit."""

    def __init__(self, quiet: bool = False, port: int = 27212) -> None:
        """
        Initialize the calendar store.
        
        Args:
            quiet: If True, suppresses most console output
            port: Port to use for API requests (default: 27212)
        """
        self.event_store = EKEventStore.alloc().init()
        self.authorized = False
        self.quiet = quiet
        self.port = port
        self._last_health_check = 0
        self._auth_lock = threading.RLock()
        self.request_authorization()
        
        if not self.quiet:
            print(f"Using server on port {self.port}", file=sys.stderr)

    def is_healthy(self) -> bool:
        """
        Check if the calendar store is healthy and functional.
        
        This performs a lightweight health check that can detect:
        - Authorization expiration
        - EventKit store staleness (e.g., after system sleep)
        - General connectivity issues
        
        Returns:
            True if the store is healthy, False otherwise
        """
        try:
            with self._auth_lock:
                # Check authorization status first
                if not self.authorized:
                    return False
                
                # Try to access calendars - this will fail if EventKit is stale
                calendars = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)
                if calendars is None:
                    return False
                
                # Try to get calendar count to ensure we can enumerate them
                calendar_count = len(calendars)
                
                # Update last health check timestamp
                self._last_health_check = time.time()
                
                return True
                
        except Exception as e:
            if not self.quiet:
                print(f"Health check failed: {e}", file=sys.stderr)
            return False

    def refresh_if_needed(self) -> bool:
        """
        Refresh the EventKit store if it appears stale or unhealthy.
        
        This should be called before critical operations to ensure
        the store is in good condition, especially after potential
        system sleep or long idle periods.
        
        Returns:
            True if refresh was successful or not needed, False if failed
        """
        try:
            # Check if health check is recent (within last 30 seconds)
            current_time = time.time()
            if current_time - self._last_health_check < 30:
                return True
            
            # Perform health check
            if self.is_healthy():
                return True
            
            if not self.quiet:
                print("Calendar store appears stale, attempting refresh...", file=sys.stderr)
            
            # Try to refresh authorization
            with self._auth_lock:
                # Reset authorization state
                self.authorized = False
                
                # Create a new EventKit store
                self.event_store = EKEventStore.alloc().init()
                
                # Request authorization again
                return self.request_authorization()
                
        except Exception as e:
            if not self.quiet:
                print(f"Failed to refresh calendar store: {e}", file=sys.stderr)
            return False

    def request_authorization(self) -> bool:
        """
        Request access to calendars with improved error handling.
        
        Returns:
            True if authorization was granted, False otherwise
        """
        with self._auth_lock:
            if not self.quiet:
                print("Requesting access to your calendars...", file=sys.stderr)
            
            # Authorization result holder
            result = {"authorized": False, "complete": False}
            
            # Define callback
            def auth_callback(granted: bool, error: Any) -> None:
                result["authorized"] = granted
                result["complete"] = True
                if error and not self.quiet:
                    print(f"Calendar authorization error: {error}", file=sys.stderr)
            
            try:
                # Request access to calendars
                self.event_store.requestAccessToEntityType_completion_(EKEntityTypeEvent, auth_callback)
                
                # Wait for authorization callback to complete
                timeout = 15  # Increased timeout for better reliability
                start_time = time.time()
                
                while not result["complete"]:
                    # Run the run loop for a short time to process callbacks
                    NSRunLoop.currentRunLoop().runMode_beforeDate_(
                        NSDefaultRunLoopMode, NSDate.dateWithTimeIntervalSinceNow_(0.1)
                    )
                    
                    # Check for timeout
                    if time.time() - start_time > timeout:
                        if not self.quiet:
                            print("Timed out waiting for authorization", file=sys.stderr)
                        break
                
                self.authorized = result["authorized"]
                
                if self.authorized:
                    self._last_health_check = time.time()
                    if not self.quiet:
                        print("Calendar access authorized", file=sys.stderr)
                elif not self.quiet:
                    print("Calendar access denied", file=sys.stderr)
                
                return self.authorized
                
            except Exception as e:
                if not self.quiet:
                    print(f"Authorization request failed: {e}", file=sys.stderr)
                self.authorized = False
                return False

    def _check_authorization(self) -> None:
        """
        Check if the store is authorized and refresh if needed.
        
        This method now includes automatic refresh attempts before
        raising errors, making it more resilient to temporary issues.
        
        Raises:
            CalendarStoreError: If not authorized to access calendars
        """
        # Try to refresh if not authorized or unhealthy
        if not self.authorized or not self.is_healthy():
            if not self.refresh_if_needed():
                if not self.quiet:
                    print("Not authorized to access calendars", file=sys.stderr)
                raise CalendarStoreError("Not authorized to access calendars")

    def get_all_calendars(self) -> List[str]:
        """
        Get a list of all available calendars.
        
        Returns:
            List of calendar names
            
        Raises:
            CalendarStoreError: If not authorized to access calendars
        """
        self._check_authorization()
        
        try:
            calendars = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)
            return [calendar.title() for calendar in calendars]
        except Exception as e:
            # If operation fails, try refreshing once and retry
            if self.refresh_if_needed():
                try:
                    calendars = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)
                    return [calendar.title() for calendar in calendars]
                except Exception as retry_e:
                    raise CalendarStoreError(f"Failed to get calendars after refresh: {retry_e}")
            else:
                raise CalendarStoreError(f"Failed to get calendars: {e}")

    def _get_calendar_by_name(self, calendar_name: str) -> Optional[EKCalendar]:
        """
        Get a calendar by name.
        
        Args:
            calendar_name: Name of calendar to find
            
        Returns:
            Calendar object or None if not found
            
        Raises:
            CalendarStoreError: If not authorized to access calendars
        """
        self._check_authorization()
            
        calendars = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)
        for calendar in calendars:
            if calendar.title() == calendar_name:
                return calendar
                
        return None

    def _date_to_nsdate(self, date_str: Optional[str] = None, is_end_date: bool = False) -> NSDate:
        """
        Convert a date string to NSDate.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            is_end_date: Whether this is an end date (should be set to end of day)
            
        Returns:
            NSDate object
        """
        if not date_str:
            return NSDate.date()
            
        try:
            # Parse 'YYYY-MM-DD' format
            if "T" in date_str:
                # If date already has time component, parse as is
                if ":" in date_str:
                    # Has hours and minutes
                    if date_str.count(":") == 1:
                        # Only hours and minutes, add seconds
                        date_str = f"{date_str}:00"
                    date_format = "%Y-%m-%dT%H:%M:%S"
                else:
                    # Just the T separator, add time
                    if is_end_date:
                        date_str = f"{date_str}23:59:59"
                    else:
                        date_str = f"{date_str}00:00:00"
                    date_format = "%Y-%m-%dT%H:%M:%S"
            else:
                # Just date, no time component
                if is_end_date:
                    # For end dates, set to end of day
                    date_str = f"{date_str}T23:59:59"
                else:
                    # For start dates, set to beginning of day
                    date_str = f"{date_str}T00:00:00"
                date_format = "%Y-%m-%dT%H:%M:%S"
                
            date_obj = datetime.datetime.strptime(date_str, date_format)
            
            # Convert to NSDate (seconds since reference date)
            time_interval = date_obj.timestamp()
            return NSDate.dateWithTimeIntervalSince1970_(time_interval)
        except ValueError:
            # If parsing fails, return current date
            if not self.quiet:
                print(f"Invalid date format: {date_str}. Using current date.", file=sys.stderr)
            return NSDate.date()

    def get_events(
        self,
        calendar_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get events from a calendar.
        
        Args:
            calendar_name: Optional name of calendar to get events from
            start_date: Optional start date in format 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS'
            end_date: Optional end date in format 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS'
            
        Returns:
            List of event dictionaries
            
        Raises:
            CalendarStoreError: If not authorized or calendar not found
        """
        self._check_authorization()
        
        try:
            return self._get_events_impl(calendar_name, start_date, end_date)
        except CalendarStoreError:
            # Re-raise CalendarStoreError as-is
            raise
        except Exception as e:
            # For other exceptions, try refreshing once and retry
            if self.refresh_if_needed():
                try:
                    return self._get_events_impl(calendar_name, start_date, end_date)
                except Exception as retry_e:
                    raise CalendarStoreError(f"Failed to get events after refresh: {retry_e}")
            else:
                raise CalendarStoreError(f"Failed to get events: {e}")

    def _get_events_impl(
        self,
        calendar_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Internal implementation of get_events with the actual logic.
        
        Args:
            calendar_name: Optional name of calendar to get events from
            start_date: Optional start date in format 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS'
            end_date: Optional end date in format 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS'
            
        Returns:
            List of event dictionaries
            
        Raises:
            CalendarStoreError: If calendar not found
        """
        # Convert start date to NSDate
        ns_start_date = self._date_to_nsdate(start_date, is_end_date=False)
        
        # If no end date is provided, default to 7 days from start
        if not end_date:
            if start_date:
                # Try to parse the start date
                try:
                    # Get the date part only if it has a time component
                    date_part = start_date.split("T")[0] if "T" in start_date else start_date
                    date_obj = datetime.datetime.strptime(date_part, "%Y-%m-%d")
                    # Add 7 days and set to end of day
                    end_obj = date_obj + datetime.timedelta(days=7)
                    end_obj = end_obj.replace(hour=23, minute=59, second=59)
                    # Convert to NSDate
                    ns_end_date = NSDate.dateWithTimeIntervalSince1970_(end_obj.timestamp())
                except ValueError:
                    # Fallback to 7 days from now
                    time_interval = 7 * 24 * 60 * 60  # 7 days in seconds
                    ns_end_date = NSDate.dateWithTimeIntervalSinceNow_(time_interval)
            else:
                # 7 days from now
                time_interval = 7 * 24 * 60 * 60  # 7 days in seconds
                ns_end_date = NSDate.dateWithTimeIntervalSinceNow_(time_interval)
        else:
            # Use provided end date, making sure it's set to end of day
            ns_end_date = self._date_to_nsdate(end_date, is_end_date=True)
            
        # Get the specified calendar or all calendars
        calendar_obj = None
        if calendar_name:
            calendar_obj = self._get_calendar_by_name(calendar_name)
            if not calendar_obj:
                if not self.quiet:
                    print(f"Calendar '{calendar_name}' not found", file=sys.stderr)
                raise CalendarStoreError(f"Calendar '{calendar_name}' not found")
            calendars = [calendar_obj]
        else:
            calendars = None  # All calendars
            
        # Create predicate for events
        predicate = self.event_store.predicateForEventsWithStartDate_endDate_calendars_(
            ns_start_date, ns_end_date, calendars
        )
        
        # Get events matching the predicate
        events = self.event_store.eventsMatchingPredicate_(predicate)
        
        # Format the events as dictionaries
        result = []
        for event in events:
            result.append(self._format_event(event))
            
        return result

    def _format_event(self, event: EKEvent) -> Dict[str, Any]:
        """
        Format an EKEvent as a dictionary.
        
        Args:
            event: The Event object to format
            
        Returns:
            Dictionary representation of the event
        """
        start_time = None
        end_time = None
        
        if event.startDate():
            # Convert NSDate to ISO format string
            start_time = self._nsdate_to_iso(event.startDate())
        
        if event.endDate():
            end_time = self._nsdate_to_iso(event.endDate())
            
        # Get location, handling missing values
        location = event.location() if event.location() else ""
        
        # Get description, handling missing values
        description = event.notes() if event.notes() else ""
        
        return {
            "id": event.eventIdentifier(),
            "summary": event.title(),
            "start": start_time,
            "end": end_time,
            "location": location,
            "description": description,
            "calendar": event.calendar().title(),
            "all_day": event.isAllDay(),
            "availability": "busy" if event.availability() == EKCalendarEventAvailabilityBusy else "free"
        }
    
    def _nsdate_to_iso(self, date: NSDate) -> str:
        """
        Convert NSDate to ISO 8601 formatted string.
        
        Args:
            date: NSDate object to convert
            
        Returns:
            ISO 8601 formatted date string
        """
        time_interval = date.timeIntervalSince1970()
        dt = datetime.datetime.fromtimestamp(time_interval)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
        
    def _parse_iso_date(self, date_str: str) -> Tuple[NSDate, bool]:
        """
        Parse ISO 8601 date string to NSDate.
        
        Args:
            date_str: Date string in format "yyyy-MM-dd" or "yyyy-MM-ddTHH:mm:ss"
            
        Returns:
            Tuple of (NSDate object, success)
            
        Raises:
            ValueError: If date string is not in the correct format
        """
        try:
            # Check which format we're dealing with
            if "T" in date_str:
                # Has time component
                if ":" in date_str:
                    # Has hours and minutes
                    if date_str.count(":") == 1:
                        # Only hours and minutes, add seconds
                        date_str = f"{date_str}:00"
                    date_format = "%Y-%m-%dT%H:%M:%S"
                else:
                    # Just the T separator, add time
                    date_str = f"{date_str}00:00:00"
                    date_format = "%Y-%m-%dT%H:%M:%S"
            else:
                # Only date, no time - use beginning of day
                date_str = f"{date_str}T00:00:00"
                date_format = "%Y-%m-%dT%H:%M:%S"
                
            # Parse the appropriately formatted date
            dt = datetime.datetime.strptime(date_str, date_format)
            
            # Convert to NSDate
            ns_date = NSDate.dateWithTimeIntervalSince1970_(dt.timestamp())
            return ns_date, True
        except ValueError as e:
            if not self.quiet:
                print(f"Invalid date format: {date_str} - {e}", file=sys.stderr)
            raise ValueError(f"Invalid date format: {date_str} - {e}")

    def create_event(
        self,
        calendar_name: str,
        summary: str,
        start_date: str,
        end_date: str,
        location: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Create a new event in Calendar.app.
        
        Args:
            calendar_name: Name of the calendar to create the event in
            summary: Event title
            start_date: Start date in format "yyyy-MM-ddTHH:mm:ss"
            end_date: End date in format "yyyy-MM-ddTHH:mm:ss" 
            location: (Optional) Event location
            description: (Optional) Event description
            
        Returns:
            ID of the created event
            
        Raises:
            CalendarStoreError: If creation fails for any reason
        """
        self._check_authorization()
        
        try:
            return self._create_event_impl(calendar_name, summary, start_date, end_date, location, description)
        except CalendarStoreError:
            # Re-raise CalendarStoreError as-is
            raise
        except Exception as e:
            # For other exceptions, try refreshing once and retry
            if self.refresh_if_needed():
                try:
                    return self._create_event_impl(calendar_name, summary, start_date, end_date, location, description)
                except Exception as retry_e:
                    raise CalendarStoreError(f"Failed to create event after refresh: {retry_e}")
            else:
                raise CalendarStoreError(f"Failed to create event: {e}")

    def _create_event_impl(
        self,
        calendar_name: str,
        summary: str,
        start_date: str,
        end_date: str,
        location: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Internal implementation of create_event.
        """
        # Get the calendar
        calendar = self._get_calendar_by_name(calendar_name)
        if not calendar:
            raise CalendarStoreError(f"Calendar '{calendar_name}' not found")
            
        # Create a new event
        event = EKEvent.eventWithEventStore_(self.event_store)
        event.setTitle_(summary)
        event.setCalendar_(calendar)
        
        # Set dates
        try:
            start_nsdate, _ = self._parse_iso_date(start_date)
            end_nsdate, _ = self._parse_iso_date(end_date)
            
            event.setStartDate_(start_nsdate)
            event.setEndDate_(end_nsdate)
        except ValueError as e:
            raise CalendarStoreError(str(e))
        
        # Set optional properties
        if location:
            event.setLocation_(location)
            
        if description:
            event.setNotes_(description)
            
        # Save the event
        error = None
        success = self.event_store.saveEvent_span_error_(event, EKSpanThisEvent, error)
        
        if not success:
            error_str = error.localizedDescription() if error else "Unknown error"
            raise CalendarStoreError(f"Failed to create event: {error_str}")
            
        return event.eventIdentifier()

    def update_event(
        self,
        event_id: str,
        calendar_name: str,
        summary: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None, 
        location: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Update an existing event.
        
        Args:
            event_id: ID of the event to update
            calendar_name: Name of the calendar containing the event
            summary: (Optional) New event title
            start_date: (Optional) New start date in format "yyyy-MM-ddTHH:mm:ss"
            end_date: (Optional) New end date in format "yyyy-MM-ddTHH:mm:ss"
            location: (Optional) New event location
            description: (Optional) New event description
            
        Returns:
            True if update was successful
            
        Raises:
            CalendarStoreError: If update fails for any reason
        """
        self._check_authorization()
        
        try:
            return self._update_event_impl(event_id, calendar_name, summary, start_date, end_date, location, description)
        except CalendarStoreError:
            # Re-raise CalendarStoreError as-is
            raise
        except Exception as e:
            # For other exceptions, try refreshing once and retry
            if self.refresh_if_needed():
                try:
                    return self._update_event_impl(event_id, calendar_name, summary, start_date, end_date, location, description)
                except Exception as retry_e:
                    raise CalendarStoreError(f"Failed to update event after refresh: {retry_e}")
            else:
                raise CalendarStoreError(f"Failed to update event: {e}")

    def _update_event_impl(
        self,
        event_id: str,
        calendar_name: str,
        summary: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None, 
        location: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Internal implementation of update_event.
        """
        # Get the calendar
        calendar = self._get_calendar_by_name(calendar_name)
        if not calendar:
            raise CalendarStoreError(f"Calendar '{calendar_name}' not found")
            
        # Find the event
        event = self.event_store.eventWithIdentifier_(event_id)
        if not event:
            raise CalendarStoreError(f"Event with ID '{event_id}' not found")
            
        # Check that the event is in the specified calendar
        if event.calendar().title() != calendar_name:
            raise CalendarStoreError(f"Event is not in calendar '{calendar_name}'")
            
        # Update the event properties
        if summary:
            event.setTitle_(summary)
            
        if start_date:
            try:
                start_nsdate, _ = self._parse_iso_date(start_date)
                event.setStartDate_(start_nsdate)
            except ValueError as e:
                raise CalendarStoreError(str(e))
                
        if end_date:
            try:
                end_nsdate, _ = self._parse_iso_date(end_date)
                event.setEndDate_(end_nsdate)
            except ValueError as e:
                raise CalendarStoreError(str(e))
                
        if location is not None:  # Allow empty string to clear location
            event.setLocation_(location)
            
        if description is not None:  # Allow empty string to clear description
            event.setNotes_(description)
            
        # Save the updated event
        error = None
        success = self.event_store.saveEvent_span_error_(event, EKSpanThisEvent, error)
        
        if not success:
            error_str = error.localizedDescription() if error else "Unknown error"
            raise CalendarStoreError(f"Failed to update event: {error_str}")
            
        return True

    def delete_event(self, event_id: str, calendar_name: str) -> bool:
        """
        Delete an event.
        
        Args:
            event_id: ID of the event to delete
            calendar_name: Name of the calendar containing the event
            
        Returns:
            True if deletion was successful
            
        Raises:
            CalendarStoreError: If deletion fails for any reason
        """
        self._check_authorization()
        
        try:
            return self._delete_event_impl(event_id, calendar_name)
        except CalendarStoreError:
            # Re-raise CalendarStoreError as-is
            raise
        except Exception as e:
            # For other exceptions, try refreshing once and retry
            if self.refresh_if_needed():
                try:
                    return self._delete_event_impl(event_id, calendar_name)
                except Exception as retry_e:
                    raise CalendarStoreError(f"Failed to delete event after refresh: {retry_e}")
            else:
                raise CalendarStoreError(f"Failed to delete event: {e}")

    def _delete_event_impl(self, event_id: str, calendar_name: str) -> bool:
        """
        Internal implementation of delete_event.
        """
        # Get the calendar
        calendar = self._get_calendar_by_name(calendar_name)
        if not calendar:
            raise CalendarStoreError(f"Calendar '{calendar_name}' not found")
            
        # Find the event
        event = self.event_store.eventWithIdentifier_(event_id)
        if not event:
            raise CalendarStoreError(f"Event with ID '{event_id}' not found")
            
        # Check that the event is in the specified calendar
        if event.calendar().title() != calendar_name:
            raise CalendarStoreError(f"Event is not in calendar '{calendar_name}'")
            
        # Delete the event
        error = None
        success = self.event_store.removeEvent_span_error_(event, EKSpanThisEvent, error)
        
        if not success:
            error_str = error.localizedDescription() if error else "Unknown error"
            raise CalendarStoreError(f"Failed to delete event: {error_str}")
            
        return True 