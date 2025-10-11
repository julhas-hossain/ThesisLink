"""
LLM service for AI-powered template personalization using OpenAI.
"""
import openai
from typing import Dict, Optional
from ..config import settings
from ..models.contact import Contact
from ..models.template import Template
from ..utils.helpers import replace_placeholders

# Initialize OpenAI client
openai.api_key = settings.OPENAI_API_KEY


class LLMService:
    """Service class for LLM operations."""
    
    @staticmethod
    def get_contact_placeholders(contact: Contact) -> Dict[str, str]:
        """
        Generate placeholder dictionary from contact information.
        
        Args:
            contact: Contact object
            
        Returns:
            Dictionary of placeholders
        """
        return {
            "ProfName": contact.name,
            "ProfessorName": contact.name,
            "Name": contact.name,
            "Email": contact.email,
            "University": contact.university,
            "Department": contact.department or "your department",
            "ResearchInterest": contact.research_interest or "your research area",
            "ResearchTopic": contact.research_interest or "your research area",
            "Website": contact.website or "",
        }
    
    @staticmethod
    def personalize_with_placeholders(
        template: Template,
        contact: Contact
    ) -> Dict[str, str]:
        """
        Personalize template using simple placeholder replacement.
        
        Args:
            template: Template object
            contact: Contact object
            
        Returns:
            Dictionary with personalized subject and body
        """
        placeholders = LLMService.get_contact_placeholders(contact)
        
        personalized_subject = replace_placeholders(template.subject, placeholders)
        personalized_body = replace_placeholders(template.body, placeholders)
        
        return {
            "subject": personalized_subject,
            "body": personalized_body,
        }
    
    @staticmethod
    async def personalize_with_ai(
        template: Template,
        contact: Contact,
        additional_context: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Personalize template using AI (OpenAI GPT).
        
        Args:
            template: Template object
            contact: Contact object
            additional_context: Optional additional context for personalization
            
        Returns:
            Dictionary with AI-personalized subject and body
        """
        # First, do basic placeholder replacement
        base_personalization = LLMService.personalize_with_placeholders(template, contact)
        
        # Prepare context for AI
        context = f"""
        Contact Information:
        - Name: {contact.name}
        - University: {contact.university}
        - Department: {contact.department or 'Not specified'}
        - Research Interest: {contact.research_interest or 'Not specified'}
        """
        
        if additional_context:
            context += f"\n\nAdditional Context:\n{additional_context}"
        
        # Create AI prompt for subject
        subject_prompt = f"""
        You are helping a graduate student personalize an email subject line to a professor.
        
        {context}
        
        Original Subject: {base_personalization['subject']}
        
        Task: Improve and personalize this subject line to be more engaging and specific to the professor's research interests. Keep it professional, concise (under 100 characters), and attention-grabbing.
        
        Return ONLY the improved subject line, nothing else.
        """
        
        # Create AI prompt for body
        body_prompt = f"""
        You are helping a graduate student personalize an email to a professor.
        
        {context}
        
        Original Email Body:
        {base_personalization['body']}
        
        Task: Improve and personalize this email to be more engaging, specific to the professor's research, and professional. Make it feel genuine and tailored, not generic. Keep the same general structure and length.
        
        Return ONLY the improved email body, nothing else.
        """
        
        try:
            # Get AI-improved subject
            subject_response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a professional email writing assistant."},
                    {"role": "user", "content": subject_prompt}
                ],
                temperature=0.7,
                max_tokens=100,
            )
            
            personalized_subject = subject_response.choices[0].message.content.strip()
            
            # Get AI-improved body
            body_response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a professional email writing assistant."},
                    {"role": "user", "content": body_prompt}
                ],
                temperature=0.7,
                max_tokens=800,
            )
            
            personalized_body = body_response.choices[0].message.content.strip()
            
            return {
                "subject": personalized_subject,
                "body": personalized_body,
            }
            
        except Exception as e:
            # If AI fails, fall back to basic placeholder replacement
            print(f"AI personalization failed: {e}")
            return base_personalization
    
    @staticmethod
    async def personalize_template(
        template: Template,
        contact: Contact,
        use_ai: bool = False,
        additional_context: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Main method to personalize template (with or without AI).
        
        Args:
            template: Template object
            contact: Contact object
            use_ai: Whether to use AI personalization
            additional_context: Optional additional context
            
        Returns:
            Dictionary with personalized subject and body
        """
        if use_ai or template.use_ai_personalization:
            return await LLMService.personalize_with_ai(template, contact, additional_context)
        else:
            return LLMService.personalize_with_placeholders(template, contact)
