"""
File service for handling file uploads and storage.
"""
import os
import shutil
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from ..config import settings
from ..models.document import Document
from ..models.user import User
from ..utils.helpers import (
    sanitize_filename,
    get_file_extension,
    generate_unique_filename
)


class FileService:
    """Service class for file operations."""
    
    @staticmethod
    def validate_file_type(filename: str) -> bool:
        """
        Validate file type against allowed types.
        
        Args:
            filename: Name of the file
            
        Returns:
            bool: True if file type is allowed
        """
        file_ext = get_file_extension(filename)
        allowed_types = settings.ALLOWED_FILE_TYPES.split(',')
        return file_ext in allowed_types
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """
        Validate file size against maximum allowed size.
        
        Args:
            file_size: Size of file in bytes
            
        Returns:
            bool: True if file size is within limits
        """
        return file_size <= settings.MAX_UPLOAD_SIZE
    
    @staticmethod
    async def save_upload_file(
        upload_file: UploadFile,
        destination: str
    ) -> int:
        """
        Save uploaded file to destination.
        
        Args:
            upload_file: FastAPI UploadFile object
            destination: Destination file path
            
        Returns:
            int: File size in bytes
        """
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        file_size = 0
        with open(destination, "wb") as buffer:
            while chunk := await upload_file.read(8192):  # Read in 8KB chunks
                file_size += len(chunk)
                buffer.write(chunk)
        
        return file_size
    
    @staticmethod
    async def upload_document(
        db: Session,
        user: User,
        file: UploadFile,
        contact_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> Document:
        """
        Upload and store a document.
        
        Args:
            db: Database session
            user: Current user
            file: Uploaded file
            contact_id: Optional contact ID to link document to
            description: Optional description
            
        Returns:
            Document object
            
        Raises:
            HTTPException: If file validation fails
        """
        # Validate file type
        if not FileService.validate_file_type(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {settings.ALLOWED_FILE_TYPES}"
            )
        
        # Generate unique filename
        original_filename = sanitize_filename(file.filename)
        unique_filename = generate_unique_filename(original_filename)
        
        # Create user-specific upload directory
        user_upload_dir = os.path.join(settings.UPLOAD_DIR, str(user.id))
        file_path = os.path.join(user_upload_dir, unique_filename)
        
        # Save file
        file_size = await FileService.save_upload_file(file, file_path)
        
        # Validate file size
        if not FileService.validate_file_size(file_size):
            # Delete the file if it exceeds size limit
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
            )
        
        # Create document record
        document = Document(
            user_id=user.id,
            contact_id=contact_id,
            filename=unique_filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=get_file_extension(original_filename),
            mime_type=file.content_type or "application/octet-stream",
            description=description
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return document
    
    @staticmethod
    def delete_document(db: Session, document: Document) -> bool:
        """
        Delete a document from database and filesystem.
        
        Args:
            db: Database session
            document: Document object to delete
            
        Returns:
            bool: True if successful
        """
        try:
            # Delete file from filesystem
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # Delete database record
            db.delete(document)
            db.commit()
            
            return True
        except Exception as e:
            print(f"Error deleting document: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_document_path(document: Document) -> str:
        """
        Get the full file path for a document.
        
        Args:
            document: Document object
            
        Returns:
            str: Full file path
        """
        return document.file_path
    
    @staticmethod
    def document_exists(document: Document) -> bool:
        """
        Check if document file exists on filesystem.
        
        Args:
            document: Document object
            
        Returns:
            bool: True if file exists
        """
        return os.path.exists(document.file_path)
