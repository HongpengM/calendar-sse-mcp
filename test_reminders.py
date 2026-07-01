"""
Unit tests for Reminders integration.

These tests mock CalendarStore so they do not require real EventKit data or permissions.
"""
import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.calendar_http_mcp import server


class TestReminderTools(unittest.TestCase):
    """Tests for MCP reminder tools in server.py"""

    def _mock_store(self, **methods):
        """Helper to build a mocked CalendarStore with given return values."""
        store = MagicMock()
        for name, value in methods.items():
            getattr(store, name).return_value = value
        return store

    def test_list_all_reminder_lists(self):
        mock_store = self._mock_store(
            get_all_reminder_lists=[
                {
                    "qualified_name": "reminders:iCloud/Tasks",
                    "title": "Tasks",
                    "source": "iCloud",
                    "calendar_identifier": "cal-1",
                    "allows_content_modifications": True,
                }
            ]
        )
        with patch.object(server, "get_calendar_store", return_value=mock_store):
            result = json.loads(server.list_all_reminder_lists())
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["reminder_lists"][0]["qualified_name"], "reminders:iCloud/Tasks")

    def test_search_reminders(self):
        mock_store = self._mock_store(
            get_reminders=[
                {
                    "id": "r1",
                    "title": "Buy milk",
                    "list_name": "Tasks",
                    "source": "iCloud",
                    "qualified_name": "reminders:iCloud/Tasks",
                    "due_date": "2026-07-01T10:00:00",
                    "start_date": None,
                    "completed": False,
                    "completion_date": None,
                    "notes": "",
                    "priority": 0,
                },
                {
                    "id": "r2",
                    "title": "Call mom",
                    "list_name": "Tasks",
                    "source": "iCloud",
                    "qualified_name": "reminders:iCloud/Tasks",
                    "due_date": None,
                    "start_date": None,
                    "completed": True,
                    "completion_date": None,
                    "notes": "",
                    "priority": 0,
                },
            ]
        )
        with patch.object(server, "get_calendar_store", return_value=mock_store):
            result = json.loads(server.search_reminders(query="milk"))
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["reminders"][0]["id"], "r1")

    def test_create_reminder(self):
        mock_store = self._mock_store(create_reminder="new-reminder-id")
        with patch.object(server, "get_calendar_store", return_value=mock_store):
            result = json.loads(
                server.create_reminder(
                    calendar_name="reminders:iCloud/Tasks",
                    title="Buy milk",
                    due_date="tomorrow 10am",
                    notes="Whole milk",
                    priority=5,
                )
            )
        self.assertTrue(result["success"])
        self.assertEqual(result["reminder_id"], "new-reminder-id")
        mock_store.create_reminder.assert_called_once()
        call_kwargs = mock_store.create_reminder.call_args.kwargs
        self.assertEqual(call_kwargs["calendar_name"], "reminders:iCloud/Tasks")
        self.assertEqual(call_kwargs["title"], "Buy milk")
        self.assertEqual(call_kwargs["notes"], "Whole milk")
        self.assertEqual(call_kwargs["priority"], 5)
        self.assertIsInstance(call_kwargs["due_date"], str)

    def test_complete_reminder(self):
        mock_store = self._mock_store(complete_reminder=True)
        with patch.object(server, "get_calendar_store", return_value=mock_store):
            result = json.loads(
                server.complete_reminder(
                    reminder_id="r1",
                    calendar_name="reminders:iCloud/Tasks",
                )
            )
        self.assertTrue(result["success"])
        mock_store.complete_reminder.assert_called_once_with(
            reminder_id="r1", calendar_name="reminders:iCloud/Tasks"
        )

    def test_delete_reminder(self):
        mock_store = self._mock_store(delete_reminder=True)
        with patch.object(server, "get_calendar_store", return_value=mock_store):
            result = json.loads(
                server.delete_reminder(
                    reminder_id="r1",
                    calendar_name="reminders:iCloud/Tasks",
                )
            )
        self.assertTrue(result["success"])
        mock_store.delete_reminder.assert_called_once_with(
            reminder_id="r1", calendar_name="reminders:iCloud/Tasks"
        )

    def test_search_reminders_date_error(self):
        with patch.object(server, "get_calendar_store"):
            result = json.loads(server.search_reminders(query="", start_date="not-a-date"))
        self.assertIn("error", result)


class TestReminderModels(unittest.TestCase):
    """Tests for Reminder Pydantic models"""

    def test_reminder_model(self):
        from src.calendar_http_mcp.models import Reminder

        reminder = Reminder(
            id="r1",
            title="Buy milk",
            list_name="Tasks",
            source="iCloud",
            qualified_name="reminders:iCloud/Tasks",
            due_date=datetime(2026, 7, 1, 10, 0, 0),
            completed=False,
        )
        data = reminder.to_dict()
        self.assertEqual(data["title"], "Buy milk")
        self.assertEqual(data["due_date"], "2026-07-01T10:00:00")

    def test_reminder_create_model(self):
        from src.calendar_http_mcp.models import ReminderCreate

        request = ReminderCreate(
            calendar_name="reminders:iCloud/Tasks",
            title="Buy milk",
            due_date="tomorrow 10am",
            priority=5,
        )
        self.assertEqual(request.title, "Buy milk")
        self.assertIsInstance(request.due_date, datetime)


class TestCalendarStoreHelpers(unittest.TestCase):
    """Tests for small CalendarStore helpers that do not need EventKit"""

    def test_parse_datetime(self):
        from src.calendar_http_mcp.calendar_store import CalendarStore

        store = CalendarStore.__new__(CalendarStore)
        self.assertIsNone(store._parse_datetime(None))
        dt = datetime(2026, 7, 1, 10, 0, 0)
        self.assertEqual(store._parse_datetime(dt), dt)
        self.assertEqual(
            store._parse_datetime("2026-07-01T10:00:00"),
            datetime(2026, 7, 1, 10, 0, 0),
        )
        self.assertIsNone(store._parse_datetime("not-a-date"))


if __name__ == "__main__":
    unittest.main()
