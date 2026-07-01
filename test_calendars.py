"""
Unit tests for source-qualified calendar handling.

These tests mock CalendarStore so they do not require real EventKit data or
permissions. They verify that same-named calendars from different accounts stay
distinguishable in MCP output (mirroring the Reminders behaviour).
"""
import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.calendar_http_mcp import server


class TestCalendarTools(unittest.TestCase):
    """Tests for MCP calendar tools in server.py"""

    def _mock_store(self, **methods):
        """Helper to build a mocked CalendarStore with given return values."""
        store = MagicMock()
        for name, value in methods.items():
            getattr(store, name).return_value = value
        return store

    def test_list_all_calendars_distinguishes_same_name(self):
        """Two accounts each with a 'Work' calendar must produce distinct entries."""
        mock_store = self._mock_store(
            get_all_calendars_detailed=[
                {
                    "qualified_name": "calendars:iCloud/Work",
                    "title": "Work",
                    "source": "iCloud",
                    "calendar_identifier": "cal-icloud-1",
                    "allows_content_modifications": True,
                },
                {
                    "qualified_name": "calendars:Google/Work",
                    "title": "Work",
                    "source": "Google",
                    "calendar_identifier": "cal-google-1",
                    "allows_content_modifications": True,
                },
            ]
        )
        with patch.object(server, "get_calendar_store", return_value=mock_store):
            result = json.loads(server.list_all_calendars())

        self.assertEqual(result["count"], 2)
        qualified = {c["qualified_name"] for c in result["calendars"]}
        self.assertEqual(qualified, {"calendars:iCloud/Work", "calendars:Google/Work"})
        # Same plain title, different sources
        self.assertEqual({c["title"] for c in result["calendars"]}, {"Work"})
        self.assertEqual({c["source"] for c in result["calendars"]}, {"iCloud", "Google"})

    def test_search_events_passes_through_source(self):
        """Events returned by the store must carry source/qualified_name to the client."""
        mock_store = self._mock_store(
            get_events=[
                {
                    "id": "e1",
                    "summary": "Standup",
                    "start": "2026-07-01T09:00:00",
                    "end": "2026-07-01T09:30:00",
                    "location": "",
                    "description": "",
                    "calendar": "Work",
                    "source": "Google",
                    "qualified_name": "calendars:Google/Work",
                    "all_day": False,
                    "availability": "busy",
                }
            ]
        )
        with patch.object(server, "get_calendar_store", return_value=mock_store):
            result = json.loads(server.search_events(query="standup"))

        self.assertEqual(result["count"], 1)
        event = result["events"][0]
        self.assertEqual(event["source"], "Google")
        self.assertEqual(event["qualified_name"], "calendars:Google/Work")

    def test_create_calendar_event_forwards_qualified_name(self):
        """A qualified calendar_name must be forwarded verbatim to the store."""
        mock_store = self._mock_store(create_event="new-event-id")
        with patch.object(server, "get_calendar_store", return_value=mock_store):
            result = json.loads(
                server.create_calendar_event(
                    calendar_name="calendars:Google/Work",
                    summary="Sync",
                    start_date="2026-07-01T10:00:00",
                    end_date="2026-07-01T11:00:00",
                )
            )
        self.assertTrue(result["success"])
        self.assertEqual(result["event_id"], "new-event-id")
        call_kwargs = mock_store.create_event.call_args.kwargs
        self.assertEqual(call_kwargs["calendar_name"], "calendars:Google/Work")


class TestCalendarModels(unittest.TestCase):
    """Tests for the new calendar Pydantic models"""

    def test_calendar_info_model(self):
        from src.calendar_http_mcp.models import CalendarInfo

        info = CalendarInfo(
            qualified_name="calendars:iCloud/Work",
            title="Work",
            source="iCloud",
            calendar_identifier="cal-1",
            allows_content_modifications=True,
        )
        self.assertEqual(info.qualified_name, "calendars:iCloud/Work")
        self.assertEqual(info.source, "iCloud")

    def test_calendar_event_roundtrips_source(self):
        from src.calendar_http_mcp.models import CalendarEvent

        event = CalendarEvent(
            id="e1",
            summary="Standup",
            start_date=datetime(2026, 7, 1, 9, 0, 0),
            end_date=datetime(2026, 7, 1, 9, 30, 0),
            calendar_name="Work",
            source="Google",
            qualified_name="calendars:Google/Work",
        )
        data = event.to_dict()
        self.assertEqual(data["source"], "Google")
        self.assertEqual(data["qualified_name"], "calendars:Google/Work")


class TestFindCalendar(unittest.TestCase):
    """Tests for CalendarStore._find_calendar matching without EventKit access."""

    def _fake_calendar(self, title, source_title):
        cal = MagicMock()
        cal.title.return_value = title
        source = MagicMock()
        source.title.return_value = source_title
        cal.source.return_value = source
        return cal

    def test_find_calendar_prefers_qualified_then_title(self):
        from src.calendar_http_mcp.calendar_store import CalendarStore

        store = CalendarStore.__new__(CalendarStore)
        icloud_work = self._fake_calendar("Work", "iCloud")
        google_work = self._fake_calendar("Work", "Google")

        store.event_store = MagicMock()
        store.event_store.calendarsForEntityType_.return_value = [icloud_work, google_work]

        with patch.object(CalendarStore, "_check_authorization", lambda self: None):
            # Qualified name resolves to the exact account, not the first match
            self.assertIs(store._find_calendar("calendars:Google/Work"), google_work)
            # Plain title falls back to the first match (backward compatible)
            self.assertIs(store._find_calendar("Work"), icloud_work)
            # Unknown name returns None
            self.assertIsNone(store._find_calendar("calendars:Nope/Missing"))


if __name__ == "__main__":
    unittest.main()
