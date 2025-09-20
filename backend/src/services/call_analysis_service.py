"""Service for retrieving and processing call analysis data."""

import os
from typing import List, Optional, Dict, Any
from retell import Retell
from uuid import UUID

from ..repositories_pg.voice_config_repository import VoiceConfigRepository


class CallAnalysisService:
    """Service for handling call analysis operations."""
    
    def __init__(self, voice_config_repo: VoiceConfigRepository):
        self.voice_config_repo = voice_config_repo
        self.retell_client = Retell(
            api_key=os.getenv("RETELL_API_KEY")
        )
    
    async def get_call_analysis_for_practice(
        self, 
        practice_id: UUID, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get call analysis data for a practice using their voice config.
        
        Args:
            practice_id: The practice ID to get calls for
            limit: Number of calls to retrieve (max 50)
            offset: Number of calls to skip for pagination
            
        Returns:
            List of call analysis data dictionaries
        """
        # Get the voice config for this practice
        voice_config = await self.voice_config_repo.get_by_practice_id(practice_id)
        if not voice_config:
            raise ValueError(f"No voice configuration found for practice {practice_id}")
        
        # Limit the number of calls to prevent abuse
        limit = min(limit, 50)
        
        try:
            # Get calls from Retell API
            calls = self.retell_client.call.list(
                filter_criteria={"agent_id": [voice_config.agent_id]},
                limit=limit,
                sort_order="descending"
            )
            
            results = []
            
            for call in calls:
                # Get detailed call info if needed
                call_id = getattr(call, 'call_id', None)
                if call_id:
                    try:
                        detailed_call = self.retell_client.call.retrieve(call_id)
                        call = detailed_call  # Use detailed version
                    except Exception:
                        pass  # Fall back to basic call info
                
                call_analysis = getattr(call, 'call_analysis', None)
                
                result = {
                    "call_id": getattr(call, 'call_id', None),
                    "recording_url": getattr(call, 'recording_url', None),
                    "start_timestamp": getattr(call, 'start_timestamp', None),
                    "end_timestamp": getattr(call, 'end_timestamp', None),
                    "call_analysis": {
                        "call_successful": getattr(call_analysis, 'call_successful', None) if call_analysis else None,
                        "call_summary": getattr(call_analysis, 'call_summary', None) if call_analysis else None,
                        "user_sentiment": getattr(call_analysis, 'user_sentiment', None) if call_analysis else None,
                        "in_voicemail": getattr(call_analysis, 'in_voicemail', None) if call_analysis else None,
                        "custom_analysis_data": getattr(call_analysis, 'custom_analysis_data', {}) if call_analysis else {}
                    } if call_analysis else None
                }
                
                results.append(result)
            
            return results
            
        except Exception as e:
            raise Exception(f"Error retrieving call analysis: {str(e)}")
    
    async def get_call_detail(self, practice_id: UUID, call_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific call.
        
        Args:
            practice_id: The practice ID (for authorization)
            call_id: The specific call ID to retrieve
            
        Returns:
            Detailed call information dictionary
        """
        # Verify practice has access to this call
        voice_config = await self.voice_config_repo.get_by_practice_id(practice_id)
        if not voice_config:
            raise ValueError(f"No voice configuration found for practice {practice_id}")
        
        try:
            call = self.retell_client.call.retrieve(call_id)
            
            # Verify this call belongs to the practice's agent
            if getattr(call, 'agent_id', None) != voice_config.agent_id:
                raise ValueError("Call does not belong to this practice")
            
            call_analysis = getattr(call, 'call_analysis', None)
            
            result = {
                "call_id": getattr(call, 'call_id', None),
                "recording_url": getattr(call, 'recording_url', None),
                "start_timestamp": getattr(call, 'start_timestamp', None),
                "end_timestamp": getattr(call, 'end_timestamp', None),
                "duration_ms": getattr(call, 'duration_ms', None),
                "agent_id": getattr(call, 'agent_id', None),
                "from_number": getattr(call, 'from_number', None),
                "to_number": getattr(call, 'to_number', None),
                "call_analysis": {
                    "call_successful": getattr(call_analysis, 'call_successful', None) if call_analysis else None,
                    "call_summary": getattr(call_analysis, 'call_summary', None) if call_analysis else None,
                    "user_sentiment": getattr(call_analysis, 'user_sentiment', None) if call_analysis else None,
                    "in_voicemail": getattr(call_analysis, 'in_voicemail', None) if call_analysis else None,
                    "custom_analysis_data": getattr(call_analysis, 'custom_analysis_data', {}) if call_analysis else {}
                } if call_analysis else None
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Error retrieving call detail: {str(e)}")
