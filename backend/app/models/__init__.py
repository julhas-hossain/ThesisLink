"""
Initialize models package.
Import all models here for easy access.
"""
from .user import User
from .contact import Contact, ContactStatus
from .template import Template
from .document import Document
from .activity_log import ActivityLog, ActivityType

__all__ = [
    "User",
    "Contact",
    "ContactStatus",
    "Template",
    "Document",
    "ActivityLog",
    "ActivityType",
]
