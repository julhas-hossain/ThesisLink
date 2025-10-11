"""
Contact schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional
from datetime import datetime
from ..models.contact import ContactStatus


class ContactBase(BaseModel):
    """Base contact schema with common fields."""
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    university: str = Field(..., min_length=1, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    research_interest: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    """Schema for contact creation."""
    status: Optional[ContactStatus] = ContactStatus.NEW


class ContactUpdate(BaseModel):
    """Schema for contact updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    university: Optional[str] = Field(None, min_length=1, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    research_interest: Optional[str] = None
    website: Optional[str] = None
    status: Optional[ContactStatus] = None
    notes: Optional[str] = None
    follow_up_date: Optional[datetime] = None


class ContactInDB(ContactBase):
    """Schema for contact in database."""
    id: int
    user_id: int
    status: ContactStatus
    last_contacted_at: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    reply_received: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Contact(ContactInDB):
    """Schema for contact response."""
    pass


class ContactList(BaseModel):
    """Schema for paginated contact list."""
    total: int
    contacts: list[Contact]
    page: int
    page_size: int
