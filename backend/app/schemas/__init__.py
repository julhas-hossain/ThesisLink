"""
Initialize schemas package.
"""
from .user import User, UserCreate, UserUpdate, UserInDB, Token, TokenData
from .contact import Contact, ContactCreate, ContactUpdate, ContactInDB, ContactList
from .template import (
    Template,
    TemplateCreate,
    TemplateUpdate,
    TemplateInDB,
    TemplatePersonalize,
    PersonalizedTemplate,
)
from .document import Document, DocumentCreate, DocumentInDB, DocumentUploadResponse
from .activity_log import ActivityLog, ActivityLogCreate, ActivityLogInDB, ActivityLogList

__all__ = [
    "User",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "Token",
    "TokenData",
    "Contact",
    "ContactCreate",
    "ContactUpdate",
    "ContactInDB",
    "ContactList",
    "Template",
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateInDB",
    "TemplatePersonalize",
    "PersonalizedTemplate",
    "Document",
    "DocumentCreate",
    "DocumentInDB",
    "DocumentUploadResponse",
    "ActivityLog",
    "ActivityLogCreate",
    "ActivityLogInDB",
    "ActivityLogList",
]
