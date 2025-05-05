"""
Pydantic models for calendar-sse-mcp using Pydantic v2
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

from pydantic import BaseModel, Field, field_validator, ConfigDict

from .date_utils import parse_date_string


class CalendarEvent(BaseModel):
    """Model for a calendar event"""
    model_config = ConfigDict(extra="allow")
    
    id: str
    summary: str
    start_date: datetime
    end_date: datetime
    calendar_name: str
    all_day: bool = False
    location: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    availability: str = "busy"
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_date(cls, value: Union[str, datetime]) -> datetime:
        """Parse dates from various formats"""
        if isinstance(value, datetime):
            return value
            
        try:
            return parse_date_string(value)
        except ValueError:
            raise ValueError(f"Invalid date format: {value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dict with ISO formatted dates"""
        result = self.model_dump()
        result["start_date"] = self.start_date.isoformat()
        result["end_date"] = self.end_date.isoformat()
        return result


class EventCreate(BaseModel):
    """Model for creating a calendar event"""
    model_config = ConfigDict(extra="ignore")
    
    calendar_name: str
    summary: str
    start_date: datetime
    end_date: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    all_day: bool = False
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_date(cls, value: Union[str, datetime]) -> datetime:
        """Parse dates from various formats"""
        if isinstance(value, datetime):
            return value
            
        try:
            return parse_date_string(value)
        except ValueError:
            raise ValueError(f"Invalid date format: {value}")
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, end_date: datetime, info: Dict[str, Any]) -> datetime:
        """Validate that end_date is not before start_date"""
        start_date = info.data.get('start_date')
        if start_date and end_date < start_date:
            raise ValueError("End date cannot be before start date")
        return end_date


class EventUpdate(BaseModel):
    """Model for updating a calendar event"""
    model_config = ConfigDict(extra="ignore")
    
    event_id: str
    calendar_name: str
    summary: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_date(cls, value: Optional[Union[str, datetime]]) -> Optional[datetime]:
        """Parse dates from various formats"""
        if value is None or isinstance(value, datetime):
            return value
            
        try:
            return parse_date_string(value)
        except ValueError:
            raise ValueError(f"Invalid date format: {value}")


class CalendarList(BaseModel):
    """Model for a list of calendars"""
    calendars: List[str]
    count: int = Field(..., description="Number of calendars")


class EventSearchParams(BaseModel):
    """Model for event search parameters"""
    query: str
    calendar_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_date(cls, value: Optional[Union[str, datetime]]) -> Optional[datetime]:
        """Parse dates from various formats"""
        if value is None or isinstance(value, datetime):
            return value
            
        try:
            return parse_date_string(value)
        except ValueError:
            raise ValueError(f"Invalid date format: {value}")


class EventList(BaseModel):
    """Model for a list of events"""
    events: List[CalendarEvent]
    count: int = Field(..., description="Number of events")


class ApiResponse(BaseModel):
    """Model for API responses"""
    status: str = "success"
    data: Optional[Any] = None
    message: Optional[str] = None
    
    @classmethod
    def success(cls, data: Any = None, message: Optional[str] = None) -> "ApiResponse":
        """Create a success response"""
        return cls(status="success", data=data, message=message)
    
    @classmethod
    def error(cls, message: str) -> "ApiResponse":
        """Create an error response"""
        return cls(status="error", message=message) 