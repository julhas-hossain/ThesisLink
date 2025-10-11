"""
Email API endpoints for sending and managing emails.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
from ..database import get_db
from ..models.user import User
from ..models.contact import Contact, ContactStatus
from ..models.template import Template
from ..models.activity_log import ActivityLog, ActivityType
from ..services.email_service import EmailService
from ..services.llm_service import LLMService
from ..services.scheduler_service import SchedulerService
from ..api.deps import get_current_active_user

router = APIRouter(prefix="/email", tags=["Email"])


class SendEmailRequest(BaseModel):
    """Schema for sending a single email."""
    contact_id: int
    template_id: int
    use_ai: bool = False
    additional_context: Optional[str] = None


class BatchEmailRequest(BaseModel):
    """Schema for sending batch emails."""
    contact_ids: List[int]
    template_id: int
    use_ai: bool = False
    delay_seconds: Optional[int] = None


class ScheduleFollowupRequest(BaseModel):
    """Schema for scheduling a follow-up."""
    contact_id: int
    followup_date: datetime
    template_id: Optional[int] = None


@router.post("/send")
async def send_email(
    email_request: SendEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send a personalized email to a single contact.
    
    Args:
        email_request: Email send request
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message with email details
    """
    # Get template and contact
    template = db.query(Template).filter(
        Template.id == email_request.template_id,
        Template.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    contact = db.query(Contact).filter(
        Contact.id == email_request.contact_id,
        Contact.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Personalize template
    personalized = await LLMService.personalize_template(
        template=template,
        contact=contact,
        use_ai=email_request.use_ai,
        additional_context=email_request.additional_context
    )
    
    # Send email
    success = await EmailService.send_email_smtp(
        to_email=contact.email,
        subject=personalized["subject"],
        body=personalized["body"]
    )
    
    if not success:
        # Log failure
        activity = ActivityLog(
            user_id=current_user.id,
            contact_id=contact.id,
            activity_type=ActivityType.EMAIL_FAILED,
            title=f"Failed to send email to {contact.name}",
            description=f"Subject: {personalized['subject']}"
        )
        db.add(activity)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )
    
    # Update contact status
    contact.last_contacted_at = datetime.utcnow()
    contact.status = ContactStatus.CONTACTED
    
    # Log success
    activity = ActivityLog(
        user_id=current_user.id,
        contact_id=contact.id,
        activity_type=ActivityType.EMAIL_SENT,
        title=f"Email sent to {contact.name}",
        description=f"Subject: {personalized['subject']}",
        metadata={"template_id": template.id}
    )
    db.add(activity)
    db.commit()
    
    return {
        "success": True,
        "message": f"Email sent successfully to {contact.name}",
        "contact_email": contact.email,
        "subject": personalized["subject"]
    }


@router.post("/batch")
async def send_batch_emails(
    batch_request: BatchEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send personalized emails to multiple contacts.
    
    Args:
        batch_request: Batch email request
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch send results
    """
    # Get template
    template = db.query(Template).filter(
        Template.id == batch_request.template_id,
        Template.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Get contacts
    contacts = db.query(Contact).filter(
        Contact.id.in_(batch_request.contact_ids),
        Contact.user_id == current_user.id
    ).all()
    
    if len(contacts) != len(batch_request.contact_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more contacts not found"
        )
    
    # Prepare recipients list
    recipients = []
    for contact in contacts:
        personalized = await LLMService.personalize_template(
            template=template,
            contact=contact,
            use_ai=batch_request.use_ai
        )
        recipients.append({
            "email": contact.email,
            "subject": personalized["subject"],
            "body": personalized["body"],
            "contact_id": contact.id,
            "contact_name": contact.name
        })
    
    # Send batch emails
    results = await EmailService.send_batch_emails(
        recipients=recipients,
        subject_template=template.subject,
        body_template=template.body,
        delay_seconds=batch_request.delay_seconds
    )
    
    # Update contacts and log activities
    for recipient in recipients:
        contact = db.query(Contact).filter(Contact.id == recipient["contact_id"]).first()
        if recipient["email"] not in results["failed_emails"]:
            contact.last_contacted_at = datetime.utcnow()
            contact.status = ContactStatus.CONTACTED
            
            activity = ActivityLog(
                user_id=current_user.id,
                contact_id=contact.id,
                activity_type=ActivityType.EMAIL_SENT,
                title=f"Batch email sent to {contact.name}",
                description=f"Subject: {recipient['subject']}"
            )
        else:
            activity = ActivityLog(
                user_id=current_user.id,
                contact_id=contact.id,
                activity_type=ActivityType.EMAIL_FAILED,
                title=f"Failed to send batch email to {contact.name}",
                description=f"Subject: {recipient['subject']}"
            )
        db.add(activity)
    
    db.commit()
    
    return {
        "success": True,
        "results": results,
        "message": f"Sent {results['success']} emails successfully, {results['failed']} failed"
    }


@router.post("/schedule-followup")
async def schedule_followup(
    followup_request: ScheduleFollowupRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Schedule a follow-up email for a contact.
    
    Args:
        followup_request: Follow-up schedule request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    # Get contact
    contact = db.query(Contact).filter(
        Contact.id == followup_request.contact_id,
        Contact.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Schedule follow-up
    success = SchedulerService.schedule_followup(
        db=db,
        contact=contact,
        followup_date=followup_request.followup_date,
        template_id=followup_request.template_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule follow-up"
        )
    
    return {
        "success": True,
        "message": f"Follow-up scheduled for {contact.name}",
        "followup_date": followup_request.followup_date.isoformat()
    }
