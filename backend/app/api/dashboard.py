"""
Dashboard API endpoints for analytics and activity logs.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from ..database import get_db
from ..models.user import User
from ..models.contact import Contact, ContactStatus
from ..models.activity_log import ActivityLog, ActivityType
from ..models.template import Template
from ..models.document import Document
from ..schemas.activity_log import ActivityLog as ActivityLogSchema, ActivityLogList
from ..api.deps import get_current_active_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics summary.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dashboard statistics
    """
    # Contact statistics
    total_contacts = db.query(func.count(Contact.id)).filter(
        Contact.user_id == current_user.id
    ).scalar()
    
    contacted = db.query(func.count(Contact.id)).filter(
        Contact.user_id == current_user.id,
        Contact.status.in_([ContactStatus.CONTACTED, ContactStatus.REPLIED])
    ).scalar()
    
    replied = db.query(func.count(Contact.id)).filter(
        Contact.user_id == current_user.id,
        Contact.status == ContactStatus.REPLIED
    ).scalar()
    
    pending = db.query(func.count(Contact.id)).filter(
        Contact.user_id == current_user.id,
        Contact.status == ContactStatus.NEW
    ).scalar()
    
    follow_ups_scheduled = db.query(func.count(Contact.id)).filter(
        Contact.user_id == current_user.id,
        Contact.status == ContactStatus.FOLLOW_UP_SCHEDULED
    ).scalar()
    
    # Recent activity (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_emails = db.query(func.count(ActivityLog.id)).filter(
        ActivityLog.user_id == current_user.id,
        ActivityLog.activity_type == ActivityType.EMAIL_SENT,
        ActivityLog.created_at >= seven_days_ago
    ).scalar()
    
    # Templates count
    templates_count = db.query(func.count(Template.id)).filter(
        Template.user_id == current_user.id
    ).scalar()
    
    # Documents count
    documents_count = db.query(func.count(Document.id)).filter(
        Document.user_id == current_user.id
    ).scalar()
    
    # Response rate
    response_rate = (replied / contacted * 100) if contacted > 0 else 0
    
    return {
        "contacts": {
            "total": total_contacts,
            "contacted": contacted,
            "replied": replied,
            "pending": pending,
            "follow_ups_scheduled": follow_ups_scheduled,
            "response_rate": round(response_rate, 2)
        },
        "activity": {
            "emails_sent_last_7_days": recent_emails
        },
        "resources": {
            "templates": templates_count,
            "documents": documents_count
        }
    }


@router.get("/activity", response_model=ActivityLogList)
async def get_activity_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    activity_type: Optional[ActivityType] = None,
    contact_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get activity logs with pagination and filtering.
    
    Args:
        page: Page number
        page_size: Items per page
        activity_type: Optional filter by activity type
        contact_id: Optional filter by contact
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Paginated activity logs
    """
    query = db.query(ActivityLog).filter(ActivityLog.user_id == current_user.id)
    
    if activity_type:
        query = query.filter(ActivityLog.activity_type == activity_type)
    
    if contact_id:
        query = query.filter(ActivityLog.contact_id == contact_id)
    
    total = query.count()
    
    offset = (page - 1) * page_size
    logs = query.order_by(ActivityLog.created_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "total": total,
        "logs": logs,
        "page": page,
        "page_size": page_size
    }


@router.get("/pipeline")
async def get_pipeline_overview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get outreach pipeline overview.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Pipeline stages with contact counts
    """
    pipeline = []
    
    for status in ContactStatus:
        count = db.query(func.count(Contact.id)).filter(
            Contact.user_id == current_user.id,
            Contact.status == status
        ).scalar()
        
        # Get sample contacts for this stage
        contacts = db.query(Contact).filter(
            Contact.user_id == current_user.id,
            Contact.status == status
        ).order_by(Contact.updated_at.desc()).limit(5).all()
        
        pipeline.append({
            "status": status.value,
            "count": count,
            "contacts": [
                {
                    "id": c.id,
                    "name": c.name,
                    "university": c.university,
                    "last_contacted": c.last_contacted_at.isoformat() if c.last_contacted_at else None
                }
                for c in contacts
            ]
        })
    
    return {
        "pipeline": pipeline
    }


@router.get("/upcoming-followups")
async def get_upcoming_followups(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get upcoming follow-ups within specified days.
    
    Args:
        days: Number of days to look ahead
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of upcoming follow-ups
    """
    future_date = datetime.utcnow() + timedelta(days=days)
    
    followups = db.query(Contact).filter(
        Contact.user_id == current_user.id,
        Contact.follow_up_date.isnot(None),
        Contact.follow_up_date <= future_date,
        Contact.follow_up_date >= datetime.utcnow()
    ).order_by(Contact.follow_up_date.asc()).all()
    
    return {
        "count": len(followups),
        "followups": [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "university": c.university,
                "follow_up_date": c.follow_up_date.isoformat(),
                "status": c.status.value
            }
            for c in followups
        ]
    }
