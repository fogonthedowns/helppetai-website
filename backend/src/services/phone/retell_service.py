"""
Retell AI Service for Phone Operations

Handles Retell AI integration for voice calls and agent management.
"""

import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RetellAIService:
    """Service class to handle Retell AI operations"""
    
    def __init__(self):
        self.api_key = os.getenv("RETELL_API_KEY")
        self.base_url = "https://api.retellai.com"
        
        if not self.api_key:
            raise ValueError("RETELL_API_KEY environment variable is required")
    
    def create_agent(self, webhook_url: str, llm_id: str = None) -> str:
        """Create a Retell AI agent for appointment scheduling"""
        
        # Use provided LLM ID or raise error if not provided
        if not llm_id:
            raise ValueError("llm_id is required - create LLM manually and pass the ID")
        
        agent_config = {
            "agent_name": "Pet Appointment Scheduler",
            "voice_id": "openai-Alloy",
            "language": "en-US",
            "response_engine": {
                "type": "retell-llm",
                "llm_id": llm_id  # Use the LLM we just created
            },
            "webhook_url": webhook_url
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}/create-agent",
            headers=headers,
            json=agent_config
        )
        
        # Check for successful status codes (200, 201)
        if response.status_code in [200, 201]:
            agent_data = response.json()
            agent_id = agent_data.get("agent_id")
            if agent_id:
                return agent_id
            else:
                raise Exception(f"Agent created but no agent_id in response: {response.text}")
        else:
            raise Exception(f"Failed to create agent: Status {response.status_code}, Response: {response.text}")


# Initialize Retell service lazily (will be created when first needed)
retell_service = None

def get_retell_service() -> RetellAIService:
    """Get or create the Retell AI service instance"""
    global retell_service
    if retell_service is None:
        retell_service = RetellAIService()
    return retell_service
