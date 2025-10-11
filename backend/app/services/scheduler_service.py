"""
Scheduler service for managing follow-up emails and scheduled tasks.
This uses Celery for task scheduling with Redis as the broker.
"""
from celery import Celery
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from ..config import settings
from ..database import SessionLocal
from ..models.contact import Contact, ContactStatus
from ..models.activity_log import ActivityLog, ActivityType

# Initialize Celery
celery_app = Celery(
    "thesislink",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'check-followups-every-hour': {
            'task': 'app.services.scheduler_service.check_pending_followups',
            'schedule': 3600.0,  # Every hour
        },
    },
)


@celery_app.task(name="app.services.scheduler_service.send_followup_email")
def send_followup_email_task(contact_id: int, user_id: int, template_id: Optional[int] = None):
    """
    Celery task to send a follow-up email.
    
    Args:
        contact_id: Contact ID to follow up with
        user_id: User ID
        template_id: Optional template ID to use
    """
    from ..services.email_service import EmailService
    from ..services.llm_service import LLMService
    from ..models.template import Template
    
    db = SessionLocal()
    try:
        # Get contact
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            print(f"Contact {contact_id} not found")
            return
        
        # Get template
        if template_id:
            template = db.query(Template).filter(
                Template.id == template_id,
                Template.user_id == user_id
            ).first()
        else:
            # Get default template
            template = db.query(Template).filter(
                Template.user_id == user_id,
                Template.is_default == True
            ).first()
        
        if not template:
            print(f"No template found for user {user_id}")
            return
        
        # Personalize email
        personalized = LLMService.personalize_with_placeholders(template, contact)
        
        # Send email (using synchronous version for Celery task)
        import asyncio
        success = asyncio.run(EmailService.send_email_smtp(
            to_email=contact.email,
            subject=f"Follow-up: {personalized['subject']}",
            body=personalized['body']
        ))
        
        if success:
            # Update contact
            contact.last_contacted_at = datetime.utcnow()
            contact.status = ContactStatus.CONTACTED
            
            # Log activity
            activity = ActivityLog(
                user_id=user_id,
                contact_id=contact_id,
                activity_type=ActivityType.EMAIL_SENT,
                title=f"Follow-up email sent to {contact.name}",
                description=f"Subject: {personalized['subject']}"
            )
            db.add(activity)
            db.commit()
            
            print(f"Follow-up email sent successfully to {contact.email}")
        else:
            # Log failure
            activity = ActivityLog(
                user_id=user_id,
                contact_id=contact_id,
                activity_type=ActivityType.EMAIL_FAILED,
                title=f"Failed to send follow-up email to {contact.name}",
                description="Email sending failed"
            )
            db.add(activity)
            db.commit()
            
            print(f"Failed to send follow-up email to {contact.email}")
    
    except Exception as e:
        print(f"Error in send_followup_email_task: {e}")
        db.rollback()
    finally:
        db.close()


@celery_app.task(name="app.services.scheduler_service.check_pending_followups")
def check_pending_followups():
    """
    Celery periodic task to check for pending follow-ups.
    Runs every hour to check if any contacts need follow-up emails.
    """
    db = SessionLocal()
    try:
        # Find contacts with follow_up_date in the past and status FOLLOW_UP_SCHEDULED
        now = datetime.utcnow()
        pending_contacts = db.query(Contact).filter(
            Contact.follow_up_date <= now,
            Contact.status == ContactStatus.FOLLOW_UP_SCHEDULED
        ).all()
        
        print(f"Found {len(pending_contacts)} contacts pending follow-up")
        
        for contact in pending_contacts:
            # Schedule follow-up email task
            send_followup_email_task.delay(
                contact_id=contact.id,
                user_id=contact.user_id
            )
        
    except Exception as e:
        print(f"Error in check_pending_followups: {e}")
    finally:
        db.close()


class SchedulerService:
    """Service class for scheduling operations."""
    
    @staticmethod
    def schedule_followup(
        db: Session,
        contact: Contact,
        followup_date: datetime,
        template_id: Optional[int] = None
    ) -> bool:
        """
        Schedule a follow-up email for a contact.
        
        Args:
            db: Database session
            contact: Contact object
            followup_date: When to send follow-up
            template_id: Optional template ID
            
        Returns:
            bool: True if scheduled successfully
        """
        try:
            # Update contact
            contact.follow_up_date = followup_date
            contact.status = ContactStatus.FOLLOW_UP_SCHEDULED
            
            # Log activity
            activity = ActivityLog(
                user_id=contact.user_id,
                contact_id=contact.id,
                activity_type=ActivityType.FOLLOW_UP_SCHEDULED,
                title=f"Follow-up scheduled for {contact.name}",
                description=f"Scheduled for {followup_date.isoformat()}",
                metadata={"template_id": template_id} if template_id else None
            )
            db.add(activity)
            db.commit()
            
            # If follow-up is due within next hour, schedule task immediately
            if followup_date <= datetime.utcnow() + timedelta(hours=1):
                send_followup_email_task.apply_async(
                    args=[contact.id, contact.user_id, template_id],
                    eta=followup_date
                )
            
            return True
            
        except Exception as e:
            print(f"Error scheduling follow-up: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def cancel_followup(db: Session, contact: Contact) -> bool:
        """
        Cancel a scheduled follow-up.
        
        Args:
            db: Database session
            contact: Contact object
            
        Returns:
            bool: True if cancelled successfully
        """
        try:
            contact.follow_up_date = None
            if contact.status == ContactStatus.FOLLOW_UP_SCHEDULED:
                contact.status = ContactStatus.CONTACTED
            
            db.commit()
            return True
            
        except Exception as e:
            print(f"Error cancelling follow-up: {e}")
            db.rollback()
            return False
