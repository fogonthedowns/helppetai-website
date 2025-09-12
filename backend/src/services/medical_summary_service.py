"""
Medical Summary Service for generating AI-powered veterinary visit summaries.
Integrates with OpenAI to create contextual medical record summaries.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from openai import AsyncOpenAI

from ..config import settings

logger = logging.getLogger(__name__)


class MedicalSummaryService:
    """Service for generating AI-powered medical summaries from visit transcripts."""
    
    def __init__(self):
        """Initialize the medical summary service."""
        self._openai_client = None
        
    async def _get_openai_client(self):
        """Lazy initialization of OpenAI client."""
        if self._openai_client is None:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required for medical summary functionality")
            
            self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("Connected to OpenAI API for medical summaries")
            
        return self._openai_client
    
    async def generate_medical_summary(
        self,
        current_visit_transcript: str,
        previous_visit_transcript: Optional[str] = None,
        current_medical_record_description: Optional[str] = None,
        pet_name: str = "the pet",
        pet_species: str = "animal"
    ) -> str:
        """
        Generate a veterinary medical summary comparing current visit to previous visits and medical history.
        
        Args:
            current_visit_transcript: Transcript from the current visit
            previous_visit_transcript: Transcript from the most recent previous visit (optional)
            current_medical_record_description: Current medical record description (optional)
            pet_name: Name of the pet for personalization
            pet_species: Species of the pet (dog, cat, etc.)
            
        Returns:
            AI-generated medical summary from veterinary perspective
        """
        try:
            openai_client = await self._get_openai_client()
            
            # Build context for the AI prompt
            context_parts = []
            
            if current_medical_record_description:
                context_parts.append(f"EXISTING MEDICAL RECORD:\n{current_medical_record_description}")
            
            if previous_visit_transcript:
                context_parts.append(f"PREVIOUS VISIT TRANSCRIPT:\n{previous_visit_transcript}")
            
            context_parts.append(f"CURRENT VISIT TRANSCRIPT:\n{current_visit_transcript}")
            
            context_text = "\n\n" + "\n\n".join(context_parts)
            
            # Create the veterinary-focused prompt
            system_prompt = f"""You are an experienced veterinarian reviewing medical records and visit transcripts for {pet_name}, a {pet_species}. Your task is to create a concise medical summary that will help other veterinarians understand this pet's condition and what to watch for.

Instructions:
- Write from a veterinary professional perspective
- Focus on medical significance and clinical observations
- Highlight any changes from previous visits or ongoing conditions
- Include key diagnostic findings, treatments, and recommendations
- Note any red flags or conditions that require monitoring
- Keep the summary concise but comprehensive (2-4 sentences)
- Use professional veterinary terminology
- Focus on actionable clinical information

Format your response as a brief medical summary that would be useful for the pet's ongoing care."""

            user_prompt = f"""Please analyze the following information for {pet_name} and create a veterinary medical summary:

{context_text}

Create a concise medical summary focusing on:
1. Current condition and any changes from previous visits
2. Key findings and treatments from this visit
3. Important conditions to monitor or watch for
4. Clinical significance for ongoing care

Provide a professional veterinary summary in 2-4 sentences."""

            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Low temperature for consistent, professional medical summaries
                max_tokens=300    # Keep summaries concise
            )
            
            summary = response.choices[0].message.content.strip()
            
            logger.info(f"Generated medical summary for {pet_name} ({len(summary)} characters)")
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate medical summary: {e}")
            # Return a fallback summary instead of raising an exception
            return f"Medical summary generation failed. Current visit processed on {datetime.utcnow().strftime('%Y-%m-%d')}. Please review transcript manually for clinical details."
    
    async def update_medical_record_with_summary(
        self,
        current_visit_transcript: str,
        previous_visit_transcript: Optional[str] = None,
        current_medical_record_description: Optional[str] = None,
        pet_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate and format a medical summary for updating medical records.
        
        Args:
            current_visit_transcript: Current visit transcript
            previous_visit_transcript: Previous visit transcript (optional)
            current_medical_record_description: Existing medical record description
            pet_info: Dictionary with pet information (name, species, etc.)
            
        Returns:
            Updated medical record description with new summary
        """
        try:
            # Extract pet information
            pet_name = "the pet"
            pet_species = "animal"
            
            if pet_info:
                pet_name = pet_info.get('name', 'the pet')
                pet_species = pet_info.get('species', 'animal')
            
            # Generate the AI summary
            ai_summary = await self.generate_medical_summary(
                current_visit_transcript=current_visit_transcript,
                previous_visit_transcript=previous_visit_transcript,
                current_medical_record_description=current_medical_record_description,
                pet_name=pet_name,
                pet_species=pet_species
            )
            
            # Format the updated medical record description
            timestamp = datetime.utcnow().strftime('%Y-%m-%d')
            
            # If there's existing description, append the new summary
            if current_medical_record_description and current_medical_record_description.strip():
                updated_description = f"{current_medical_record_description.strip()}\n\n[AI Summary - {timestamp}]: {ai_summary}"
            else:
                updated_description = f"[AI Summary - {timestamp}]: {ai_summary}"
            
            return updated_description
            
        except Exception as e:
            logger.error(f"Failed to update medical record with summary: {e}")
            # Return original description if summary generation fails
            return current_medical_record_description or f"Medical record updated on {datetime.utcnow().strftime('%Y-%m-%d')}."


# Global medical summary service instance
medical_summary_service = MedicalSummaryService()
