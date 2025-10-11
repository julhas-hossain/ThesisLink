"""
Document schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DocumentBase(BaseModel):
    """Base document schema."""
    description: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Schema for document creation."""
    contact_id: Optional[int] = None


class DocumentInDB(DocumentBase):
    """Schema for document in database."""
    id: int
    user_id: int
    contact_id: Optional[int] = None
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    mime_type: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Document(DocumentInDB):
    """Schema for document response."""
    pass


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    message: str = "File uploaded successfully"
