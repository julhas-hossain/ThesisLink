"""
Template schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TemplateBase(BaseModel):
    """Base template schema with common fields."""
    name: str = Field(..., min_length=1, max_length=200)
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    description: Optional[str] = None
    is_default: Optional[bool] = False
    use_ai_personalization: Optional[bool] = False


class TemplateCreate(TemplateBase):
    """Schema for template creation."""
    pass


class TemplateUpdate(BaseModel):
    """Schema for template updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    body: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    use_ai_personalization: Optional[bool] = None


class TemplateInDB(TemplateBase):
    """Schema for template in database."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Template(TemplateInDB):
    """Schema for template response."""
    pass


class TemplatePersonalize(BaseModel):
    """Schema for AI personalization request."""
    template_id: int
    contact_id: int
    additional_context: Optional[str] = None


class PersonalizedTemplate(BaseModel):
    """Schema for personalized template response."""
    subject: str
    body: str
    original_subject: str
    original_body: str
