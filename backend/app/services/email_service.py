"""
Email service for sending emails via SMTP or Gmail API.
"""
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict
from datetime import datetime
import aiosmtplib
from ..config import settings


class EmailService:
    """Service class for email operations."""
    
    @staticmethod
    async def send_email_smtp(
        to_email: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        is_html: bool = False
    ) -> bool:
        """
        Send email using SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            attachments: List of file paths to attach
            is_html: Whether body is HTML
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add body
            body_type = "html" if is_html else "plain"
            message.attach(MIMEText(body, body_type))
            
            # Add attachments if any
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        filename = file_path.split("/")[-1].split("\\")[-1]
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename= {filename}",
                        )
                        message.attach(part)
                    except Exception as e:
                        print(f"Failed to attach file {file_path}: {e}")
            
            # Send email using aiosmtplib for async support
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False
    
    @staticmethod
    async def send_batch_emails(
        recipients: List[Dict[str, str]],
        subject_template: str,
        body_template: str,
        delay_seconds: int = None,
        attachments: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Send batch emails with delay between each.
        
        Args:
            recipients: List of dicts with 'email', 'subject', 'body'
            subject_template: Subject template (fallback)
            body_template: Body template (fallback)
            delay_seconds: Delay between emails
            attachments: List of file paths to attach
            
        Returns:
            Dictionary with success count, failed count, and failed emails
        """
        if delay_seconds is None:
            delay_seconds = settings.BATCH_EMAIL_DELAY_SECONDS
        
        success_count = 0
        failed_count = 0
        failed_emails = []
        
        for recipient in recipients:
            email = recipient.get("email")
            subject = recipient.get("subject", subject_template)
            body = recipient.get("body", body_template)
            
            # Send email
            success = await EmailService.send_email_smtp(
                to_email=email,
                subject=subject,
                body=body,
                attachments=attachments
            )
            
            if success:
                success_count += 1
            else:
                failed_count += 1
                failed_emails.append(email)
            
            # Delay between emails (except after last email)
            if recipient != recipients[-1]:
                await asyncio.sleep(delay_seconds)
        
        return {
            "total": len(recipients),
            "success": success_count,
            "failed": failed_count,
            "failed_emails": failed_emails,
            "sent_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def validate_email_format(email: str) -> bool:
        """
        Basic email format validation.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if valid format
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


# Gmail API implementation (optional - can be extended later)
class GmailAPIService:
    """Service for Gmail API integration (placeholder for future implementation)."""
    
    @staticmethod
    async def send_email_gmail_api(
        to_email: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send email using Gmail API.
        
        Note: This is a placeholder. Full implementation requires:
        - Google OAuth2 flow
        - Gmail API credentials setup
        - User authorization
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body
            attachments: File attachments
            
        Returns:
            bool: True if successful
        """
        # TODO: Implement Gmail API integration
        raise NotImplementedError("Gmail API integration not yet implemented")
