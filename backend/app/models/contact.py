"""
Contact model for managing professor/supervisor information.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..database import Base


class ContactStatus(str, enum.Enum):
    """Enum for contact status tracking."""
    NEW = "new"
    CONTACTED = "contacted"
    REPLIED = "replied"
    FOLLOW_UP_SCHEDULED = "follow_up_scheduled"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NO_RESPONSE = "no_response"


class Contact(Base):
    """Contact model for professor/supervisor information."""
    
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic Information
    name = Column(String, nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    university = Column(String, nullable=False)
    department = Column(String, nullable=True)
    research_interest = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    
    # Status and Notes
    status = Column(Enum(ContactStatus), default=ContactStatus.NEW, index=True)
    notes = Column(Text, nullable=True)
    
    # Tracking
    last_contacted_at = Column(DateTime, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    reply_received = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="contacts")
    documents = relationship("Document", back_populates="contact", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="contact", cascade="all, delete-orphan")
