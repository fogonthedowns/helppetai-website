"""Service for retrieving and processing call analysis data with caching."""

import os
import asyncio
from typing import List, Optional, Dict, Any
from retell import Retell
from uuid import UUID
from datetime import datetime

from ..repositories_pg.voice_config_repository import VoiceConfigRepository
from ..repositories_pg.call_record_repository import CallRecordRepository
from ..models_pg.call_record import CallRecord
from ..models_pg.pet_owner import PetOwner
from ..utils.phone_utils import normalize_phone
from sqlalchemy import select


class CallAnalysisService:
    """Service for handling call analysis operations with caching."""
    
    def __init__(self, voice_config_repo: VoiceConfigRepository, call_record_repo: CallRecordRepository):
        self.voice_config_repo = voice_config_repo
        self.call_record_repo = call_record_repo
        self.retell_client = None
        
        # Initialize Retell client if API key is available
        api_key = os.getenv("RETELL_API_KEY")
        if api_key:
            self.retell_client = Retell(api_key=api_key)
    
    async def get_call_analysis_for_practice(
        self, 
        practice_id: UUID, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get call analysis data for a practice.
        Simple: 1. Call API 2. Save to DB 3. Return results
        """
        limit = min(limit, 50)  # Prevent abuse
        
        # Check if practice has voice config
        voice_config = await self.voice_config_repo.get_by_practice_id(practice_id)
        if not voice_config:
            print(f"No voice config found for practice {practice_id}")
            return []
        
        if not self.retell_client:
            print("No Retell API client configured")
            return []
        
        try:
            print(f"Fetching calls for agent {voice_config.agent_id}")
            
            # 1. Call API
            calls = self.retell_client.call.list(
                filter_criteria={"agent_id": [voice_config.agent_id]},
                limit=limit,
                sort_order="descending"
            )
            
            if not calls:
                print(f"No calls found for agent {voice_config.agent_id}")
                return []
            
            results = []
            for call in calls:
                call_id = getattr(call, 'call_id', None)
                if not call_id:
                    continue
                
                try:
                    # Get detailed call info
                    detailed_call = self.retell_client.call.retrieve(call_id)
                    
                    # 2. Save to DB
                    call_record = await self._update_call_record_from_api(practice_id, detailed_call)
                    
                    # 3. Add to results
                    if call_record:
                        results.append(call_record.to_api_dict())
                        
                except Exception as e:
                    print(f"Error processing call {call_id}: {e}")
                    continue
            
            print(f"Successfully processed {len(results)} calls")
            return results
            
        except Exception as e:
            print(f"Error fetching calls: {e}")
            return []
    
    async def get_call_detail(self, practice_id: UUID, call_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific call from cache.
        
        Args:
            practice_id: The practice ID (for authorization)
            call_id: The specific call ID to retrieve
            
        Returns:
            Detailed call information dictionary
        """
        # Get from cache first
        cached_call = await self.call_record_repo.get_by_call_id(call_id)
        
        if cached_call and cached_call.practice_id == practice_id:
            # Trigger background refresh for this specific call
            asyncio.create_task(self._background_sync_single_call(practice_id, call_id))
            return cached_call.to_api_dict(include_details=True)
        
        # If not in cache, verify practice access and try to sync
        voice_config = await self.voice_config_repo.get_by_practice_id(practice_id)
        if not voice_config:
            raise ValueError(f"No voice configuration found for practice {practice_id}")
        
        # Try to sync this specific call
        synced_call = await self._sync_single_call_from_api(practice_id, call_id, voice_config.agent_id)
        if synced_call:
            return synced_call.to_api_dict(include_details=True)
        
        raise ValueError(f"Call {call_id} not found or does not belong to practice {practice_id}")
    
    async def _background_sync_calls(self, practice_id: UUID) -> None:
        """Background task to sync recent calls from Retell API."""
        if not self.retell_client:
            return  # No API key configured
        
        # Create new database session for background task
        from ..database_pg import get_db_session
        from ..repositories_pg.voice_config_repository import VoiceConfigRepository
        from ..repositories_pg.call_record_repository import CallRecordRepository
        
        try:
            async for session in get_db_session():
                voice_config_repo = VoiceConfigRepository(session)
                call_record_repo = CallRecordRepository(session)
                
                voice_config = await voice_config_repo.get_by_practice_id(practice_id)
                if not voice_config:
                    return
            
                # Get recent calls from API
                print(f"🔄 Background sync: fetching calls for agent {voice_config.agent_id}")
                calls = self.retell_client.call.list(
                    filter_criteria={"agent_id": [voice_config.agent_id]},
                    limit=20,  # Sync recent calls
                    sort_order="descending"
                )
                
                print(f"🔄 Background sync: got {len(calls) if calls else 0} calls from API")
                
                for call in calls:
                    call_id = getattr(call, 'call_id', None)
                    if not call_id:
                        continue
                    
                    try:
                        # Get detailed call info
                        detailed_call = self.retell_client.call.retrieve(call_id)
                        await self._update_call_record_from_api_with_session(
                            practice_id, detailed_call, call_record_repo
                        )
                    except Exception as e:
                        # Log error but continue with other calls
                        print(f"Error syncing call {call_id}: {e}")
                        continue
                
                # Commit the session
                await session.commit()
                break  # Successfully completed, exit session loop
        
        except Exception as e:
            print(f"Background sync error for practice {practice_id}: {e}")
    
    async def _initial_sync_calls(self, practice_id: UUID, limit: int = 10) -> List[CallRecord]:
        """
        Initial sync for when cache is empty - synchronous with timeout.
        Returns call records directly for immediate response.
        """
        if not self.retell_client:
            return []
        
        try:
            # Get voice config to verify practice has API access
            voice_config = await self.voice_config_repo.get_by_practice_id(practice_id)
            if not voice_config:
                print(f"No voice config found for practice {practice_id}")
                return []
            
            print(f"🔍 Fetching calls from Retell API for agent {voice_config.agent_id}...")
            
            # Get recent calls from API (limit to requested amount)
            calls = self.retell_client.call.list(
                filter_criteria={"agent_id": [voice_config.agent_id]},
                limit=min(limit, 20),  # Don't fetch too many on initial sync
                sort_order="descending"
            )
            
            print(f"📞 Retell API returned {len(calls) if calls else 0} calls")
            
            if not calls:
                print(f"⚠️ No calls found for agent {voice_config.agent_id} - this could mean:")
                print(f"   - Agent has no calls yet")
                print(f"   - Agent ID is incorrect") 
                print(f"   - API key doesn't have access to this agent")
                return []
            
            synced_calls = []
            for i, call in enumerate(calls):
                call_id = getattr(call, 'call_id', None)
                if not call_id:
                    print(f"⚠️ Call #{i+1} missing call_id, skipping")
                    continue
                
                print(f"🔄 Processing call {i+1}/{len(calls)}: {call_id}")
                
                try:
                    # Get detailed call info
                    detailed_call = self.retell_client.call.retrieve(call_id)
                    print(f"✅ Retrieved detailed info for call {call_id}")
                    
                    call_record = await self._update_call_record_from_api(practice_id, detailed_call)
                    if call_record:
                        synced_calls.append(call_record)
                        print(f"✅ Synced call {call_id} to database")
                    else:
                        print(f"⚠️ Failed to create call record for {call_id}")
                except Exception as e:
                    print(f"❌ Error syncing call {call_id} in initial sync: {e}")
                    continue
            
            print(f"🎉 Initial sync completed: {len(synced_calls)} calls synced successfully")
            return synced_calls
            
        except Exception as e:
            print(f"Initial sync error for practice {practice_id}: {e}")
            return []
    
    async def _background_sync_single_call(self, practice_id: UUID, call_id: str) -> None:
        """Background task to sync a specific call."""
        if not self.retell_client:
            return
        
        # Create new database session for background task
        from ..database_pg import get_db_session
        from ..repositories_pg.voice_config_repository import VoiceConfigRepository
        from ..repositories_pg.call_record_repository import CallRecordRepository
        
        try:
            async for session in get_db_session():
                voice_config_repo = VoiceConfigRepository(session)
                call_record_repo = CallRecordRepository(session)
                
                voice_config = await voice_config_repo.get_by_practice_id(practice_id)
                if not voice_config:
                    return
                
                detailed_call = self.retell_client.call.retrieve(call_id)
                await self._update_call_record_from_api_with_session(
                    practice_id, detailed_call, call_record_repo
                )
                
                # Commit the session
                await session.commit()
                break  # Successfully completed, exit session loop
        
        except Exception as e:
            print(f"Background sync error for call {call_id}: {e}")
    
    async def _sync_single_call_from_api(
        self, 
        practice_id: UUID, 
        call_id: str, 
        agent_id: str
    ) -> Optional[CallRecord]:
        """Sync a single call from API (blocking)."""
        if not self.retell_client:
            return None
        
        try:
            detailed_call = self.retell_client.call.retrieve(call_id)
            
            # Verify call belongs to practice
            if getattr(detailed_call, 'agent_id', None) != agent_id:
                raise ValueError("Call does not belong to this practice")
            
            return await self._update_call_record_from_api(practice_id, detailed_call)
        
        except Exception as e:
            print(f"Error syncing call {call_id}: {e}")
            return None
    
    async def _update_call_record_from_api(self, practice_id: UUID, api_call) -> CallRecord:
        """Update or create call record from API data."""
        call_id = getattr(api_call, 'call_id', None)
        if not call_id:
            raise ValueError("Call missing call_id")
        
        # Get or create call record
        existing_record = await self.call_record_repo.get_by_call_id(call_id)
        
        if existing_record:
            call_record = existing_record
        else:
            call_record = CallRecord(practice_id=practice_id, call_id=call_id)
        
        # Convert API data to dict format
        api_data = {
            "call_id": call_id,
            "agent_id": getattr(api_call, 'agent_id', None),
            "recording_url": getattr(api_call, 'recording_url', None),
            "start_timestamp": getattr(api_call, 'start_timestamp', None),
            "end_timestamp": getattr(api_call, 'end_timestamp', None),
            "from_number": getattr(api_call, 'from_number', None),
            "to_number": getattr(api_call, 'to_number', None),
            "duration_ms": getattr(api_call, 'duration_ms', None),
            "call_status": getattr(api_call, 'call_status', None),
            "disconnect_reason": getattr(api_call, 'disconnect_reason', None),
            "call_analysis": None
        }
        
        # Extract call analysis if available
        call_analysis = getattr(api_call, 'call_analysis', None)
        if call_analysis:
            api_data["call_analysis"] = {
                "call_successful": getattr(call_analysis, 'call_successful', None),
                "call_summary": getattr(call_analysis, 'call_summary', None),
                "user_sentiment": getattr(call_analysis, 'user_sentiment', None),
                "in_voicemail": getattr(call_analysis, 'in_voicemail', None),
                "custom_analysis_data": getattr(call_analysis, 'custom_analysis_data', {})
            }
        
        # Update the record
        call_record.update_from_api_data(api_data)
        
        # Save to database first
        saved_record = await self.call_record_repo.create_or_update(call_record)
        
        # Try to match caller by phone number in background (temporarily disabled)
        # asyncio.create_task(self._match_caller_by_phone_background(saved_record.id))
        
        return saved_record
    
    async def _update_call_record_from_api_with_session(
        self, 
        practice_id: UUID, 
        api_call, 
        call_record_repo: CallRecordRepository
    ) -> CallRecord:
        """Update or create call record from API data using provided repository."""
        call_id = getattr(api_call, 'call_id', None)
        if not call_id:
            raise ValueError("Call missing call_id")
        
        # Get or create call record
        existing_record = await call_record_repo.get_by_call_id(call_id)
        
        if existing_record:
            call_record = existing_record
        else:
            call_record = CallRecord(practice_id=practice_id, call_id=call_id)
        
        # Convert API data to dict format
        api_data = {
            "call_id": call_id,
            "agent_id": getattr(api_call, 'agent_id', None),
            "recording_url": getattr(api_call, 'recording_url', None),
            "start_timestamp": getattr(api_call, 'start_timestamp', None),
            "end_timestamp": getattr(api_call, 'end_timestamp', None),
            "from_number": getattr(api_call, 'from_number', None),
            "to_number": getattr(api_call, 'to_number', None),
            "duration_ms": getattr(api_call, 'duration_ms', None),
            "call_status": getattr(api_call, 'call_status', None),
            "disconnect_reason": getattr(api_call, 'disconnect_reason', None),
            "call_analysis": None
        }
        
        # Extract call analysis if available
        call_analysis = getattr(api_call, 'call_analysis', None)
        if call_analysis:
            api_data["call_analysis"] = {
                "call_successful": getattr(call_analysis, 'call_successful', None),
                "call_summary": getattr(call_analysis, 'call_summary', None),
                "user_sentiment": getattr(call_analysis, 'user_sentiment', None),
                "in_voicemail": getattr(call_analysis, 'in_voicemail', None),
                "custom_analysis_data": getattr(call_analysis, 'custom_analysis_data', {})
            }
        
        # Update the record
        call_record.update_from_api_data(api_data)
        
        # Save to database
        saved_record = await call_record_repo.create_or_update(call_record)
        
        return saved_record
    
    async def _match_caller_by_phone_background(self, call_record_id: str) -> None:
        """Background task to match caller by phone number."""
        try:
            from ..database_pg import get_session
            
            async with get_session() as session:
                # Get the call record
                call_record = await self.call_record_repo.get_by_id(call_record_id)
                if not call_record or not call_record.from_number:
                    return
                
                normalized_phone = normalize_phone(call_record.from_number)
                if not normalized_phone:
                    return
                
                # Simple query for pet owners with matching phone numbers
                query = select(PetOwner).where(
                    PetOwner.phone.ilike(f'%{normalized_phone[-10:]}%')
                )
                
                result = await session.execute(query)
                pet_owners = result.scalars().all()
                
                # Check for exact phone matches
                for pet_owner in pet_owners:
                    if (normalize_phone(pet_owner.phone) == normalized_phone or 
                        (pet_owner.secondary_phone and normalize_phone(pet_owner.secondary_phone) == normalized_phone)):
                        # Update the call record with matched pet owner
                        call_record.caller_pet_owner_id = pet_owner.id
                        await self.call_record_repo.create_or_update(call_record)
                        return
        
        except Exception as e:
            # Don't fail - this is background processing
            print(f"Background phone matching error: {e}")
            pass
