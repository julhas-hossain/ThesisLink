"""
Contacts API endpoints for managing professor/supervisor contacts.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from ..database import get_db
from ..models.user import User
from ..models.contact import Contact, ContactStatus
from ..models.activity_log import ActivityLog, ActivityType
from ..schemas.contact import Contact as ContactSchema, ContactCreate, ContactUpdate, ContactList
from ..api.deps import get_current_active_user

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.post("/", response_model=ContactSchema, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new contact.
    
    Args:
        contact_data: Contact creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created contact object
    """
    # Create contact
    contact = Contact(
        **contact_data.model_dump(),
        user_id=current_user.id
    )
    db.add(contact)
    
    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        contact_id=None,  # Will be set after commit
        activity_type=ActivityType.CONTACT_CREATED,
        title=f"Created contact: {contact.name}",
        description=f"Added {contact.name} from {contact.university}"
    )
    
    db.commit()
    db.refresh(contact)
    
    # Update activity with contact_id
    activity.contact_id = contact.id
    db.add(activity)
    db.commit()
    
    return contact


@router.get("/", response_model=ContactList)
async def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ContactStatus] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List contacts with pagination and filtering.
    
    Args:
        page: Page number (starts at 1)
        page_size: Number of items per page
        status: Optional status filter
        search: Optional search query (searches name, email, university)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Paginated list of contacts
    """
    # Build query
    query = db.query(Contact).filter(Contact.user_id == current_user.id)
    
    # Apply status filter
    if status:
        query = query.filter(Contact.status == status)
    
    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Contact.name.ilike(search_pattern),
                Contact.email.ilike(search_pattern),
                Contact.university.ilike(search_pattern),
                Contact.research_interest.ilike(search_pattern)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    contacts = query.order_by(Contact.created_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "total": total,
        "contacts": contacts,
        "page": page,
        "page_size": page_size
    }


@router.get("/{contact_id}", response_model=ContactSchema)
async def get_contact(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific contact by ID.
    
    Args:
        contact_id: Contact ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Contact object
    """
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    return contact


@router.put("/{contact_id}", response_model=ContactSchema)
async def update_contact(
    contact_id: int,
    contact_data: ContactUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a contact.
    
    Args:
        contact_id: Contact ID
        contact_data: Contact update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated contact object
    """
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Update fields
    update_data = contact_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)
    
    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        contact_id=contact.id,
        activity_type=ActivityType.CONTACT_UPDATED,
        title=f"Updated contact: {contact.name}",
        description="Contact information updated"
    )
    db.add(activity)
    
    db.commit()
    db.refresh(contact)
    
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a contact.
    
    Args:
        contact_id: Contact ID
        current_user: Current authenticated user
        db: Database session
    """
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    contact_name = contact.name
    db.delete(contact)
    db.commit()
    
    return None


@router.get("/stats/summary")
async def get_contact_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get contact statistics summary.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dictionary with contact statistics
    """
    # Count by status
    stats = {}
    for status_enum in ContactStatus:
        count = db.query(func.count(Contact.id)).filter(
            Contact.user_id == current_user.id,
            Contact.status == status_enum
        ).scalar()
        stats[status_enum.value] = count
    
    # Total contacts
    total = db.query(func.count(Contact.id)).filter(
        Contact.user_id == current_user.id
    ).scalar()
    stats["total"] = total
    
    return stats
