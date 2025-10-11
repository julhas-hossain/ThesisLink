"""
Activity Log model for tracking user actions and email activities.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..database import Base


class ActivityType(str, enum.Enum):
    """Enum for activity types."""
    CONTACT_CREATED = "contact_created"
    CONTACT_UPDATED = "contact_updated"
    CONTACT_DELETED = "contact_deleted"
    EMAIL_SENT = "email_sent"
    EMAIL_FAILED = "email_failed"
    FOLLOW_UP_SCHEDULED = "follow_up_scheduled"
    REPLY_RECEIVED = "reply_received"
    DOCUMENT_UPLOADED = "document_uploaded"
    TEMPLATE_CREATED = "template_created"
    TEMPLATE_USED = "template_used"


class ActivityLog(Base):
    """Activity Log model for tracking user actions."""
    
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    
    # Activity Information
    activity_type = Column(Enum(ActivityType), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Additional Data (JSON field for flexible storage)
    metadata = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")
    contact = relationship("Contact", back_populates="activity_logs")
    
    def __repr__(self):
        return f"<ActivityLog(type='{self.activity_type}', id={self.id})>"
