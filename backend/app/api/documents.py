"""
Documents API endpoints for file upload and management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..models.document import Document
from ..models.activity_log import ActivityLog, ActivityType
from ..schemas.document import Document as DocumentSchema, DocumentUploadResponse
from ..services.file_service import FileService
from ..api.deps import get_current_active_user
import os

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    contact_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document file.
    
    Args:
        file: File to upload
        contact_id: Optional contact ID to link document to
        description: Optional description
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Uploaded document information
    """
    # Upload file
    document = await FileService.upload_document(
        db=db,
        user=current_user,
        file=file,
        contact_id=contact_id,
        description=description
    )
    
    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        contact_id=contact_id,
        activity_type=ActivityType.DOCUMENT_UPLOADED,
        title=f"Uploaded document: {document.original_filename}",
        description=f"File size: {document.file_size} bytes"
    )
    db.add(activity)
    db.commit()
    
    return {
        "id": document.id,
        "filename": document.filename,
        "original_filename": document.original_filename,
        "file_size": document.file_size,
        "file_type": document.file_type,
        "message": "File uploaded successfully"
    }


@router.get("/", response_model=List[DocumentSchema])
async def list_documents(
    contact_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List documents for current user.
    
    Args:
        contact_id: Optional filter by contact ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of documents
    """
    query = db.query(Document).filter(Document.user_id == current_user.id)
    
    if contact_id:
        query = query.filter(Document.contact_id == contact_id)
    
    documents = query.order_by(Document.created_at.desc()).all()
    
    return documents


@router.get("/{document_id}", response_model=DocumentSchema)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get document information.
    
    Args:
        document_id: Document ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Document object
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Download a document file.
    
    Args:
        document_id: Document ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        File response
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not FileService.document_exists(document):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    return FileResponse(
        path=document.file_path,
        filename=document.original_filename,
        media_type=document.mime_type
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document.
    
    Args:
        document_id: Document ID
        current_user: Current authenticated user
        db: Database session
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    success = FileService.delete_document(db, document)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )
    
    return None
