"""
Templates API endpoints for managing email templates.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..models.template import Template
from ..models.contact import Contact
from ..models.activity_log import ActivityLog, ActivityType
from ..schemas.template import (
    Template as TemplateSchema,
    TemplateCreate,
    TemplateUpdate,
    TemplatePersonalize,
    PersonalizedTemplate
)
from ..services.llm_service import LLMService
from ..api.deps import get_current_active_user

router = APIRouter(prefix="/templates", tags=["Templates"])


@router.post("/", response_model=TemplateSchema, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new email template.
    
    Args:
        template_data: Template creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created template object
    """
    # If this is marked as default, unset other defaults
    if template_data.is_default:
        db.query(Template).filter(
            Template.user_id == current_user.id,
            Template.is_default == True
        ).update({"is_default": False})
    
    # Create template
    template = Template(
        **template_data.model_dump(),
        user_id=current_user.id
    )
    db.add(template)
    
    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        activity_type=ActivityType.TEMPLATE_CREATED,
        title=f"Created template: {template.name}",
        description=f"Template created with {len(template.body)} characters"
    )
    db.add(activity)
    
    db.commit()
    db.refresh(template)
    
    return template


@router.get("/", response_model=List[TemplateSchema])
async def list_templates(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all templates for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of templates
    """
    templates = db.query(Template).filter(
        Template.user_id == current_user.id
    ).order_by(Template.is_default.desc(), Template.created_at.desc()).all()
    
    return templates


@router.get("/{template_id}", response_model=TemplateSchema)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific template by ID.
    
    Args:
        template_id: Template ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Template object
    """
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template


@router.put("/{template_id}", response_model=TemplateSchema)
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a template.
    
    Args:
        template_id: Template ID
        template_data: Template update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated template object
    """
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # If setting as default, unset other defaults
    if template_data.is_default:
        db.query(Template).filter(
            Template.user_id == current_user.id,
            Template.id != template_id,
            Template.is_default == True
        ).update({"is_default": False})
    
    # Update fields
    update_data = template_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a template.
    
    Args:
        template_id: Template ID
        current_user: Current authenticated user
        db: Database session
    """
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    db.delete(template)
    db.commit()
    
    return None


@router.post("/personalize", response_model=PersonalizedTemplate)
async def personalize_template(
    personalize_data: TemplatePersonalize,
    use_ai: bool = Query(False, description="Use AI for personalization"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Personalize a template for a specific contact.
    
    Args:
        personalize_data: Personalization request data
        use_ai: Whether to use AI personalization
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Personalized template with subject and body
    """
    # Get template
    template = db.query(Template).filter(
        Template.id == personalize_data.template_id,
        Template.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Get contact
    contact = db.query(Contact).filter(
        Contact.id == personalize_data.contact_id,
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
        use_ai=use_ai,
        additional_context=personalize_data.additional_context
    )
    
    return {
        "subject": personalized["subject"],
        "body": personalized["body"],
        "original_subject": template.subject,
        "original_body": template.body
    }
