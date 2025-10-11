"""
Activity Log schemas for request/response validation.
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from ..models.activity_log import ActivityType


class ActivityLogBase(BaseModel):
    """Base activity log schema."""
    activity_type: ActivityType
    title: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ActivityLogCreate(ActivityLogBase):
    """Schema for activity log creation."""
    contact_id: Optional[int] = None


class ActivityLogInDB(ActivityLogBase):
    """Schema for activity log in database."""
    id: int
    user_id: int
    contact_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActivityLog(ActivityLogInDB):
    """Schema for activity log response."""
    pass


class ActivityLogList(BaseModel):
    """Schema for paginated activity log list."""
    total: int
    logs: list[ActivityLog]
    page: int
    page_size: int
