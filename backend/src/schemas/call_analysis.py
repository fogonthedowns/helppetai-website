"""
Comprehensive schemas for call analysis API responses.

This module provides detailed Pydantic models for all call analysis API endpoints
with comprehensive field descriptions and example values for iOS development.
"""

from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class CallAnalysisData(BaseModel):
    """
    Detailed call analysis information from the voice service.
    
    This contains the AI-generated analysis of the call content and outcome.
    """
    call_successful: Optional[bool] = Field(
        None, 
        description="Whether the call achieved its intended purpose",
        example=True
    )
    call_summary: Optional[str] = Field(
        None, 
        description="AI-generated summary of the call content and key points",
        example="Customer called to schedule a checkup for their Golden Retriever, Max. Appointment scheduled for next Tuesday at 2 PM. Customer mentioned Max has been limping slightly."
    )
    user_sentiment: Optional[str] = Field(
        None, 
        description="Detected emotional sentiment of the caller (positive, negative, neutral, concerned, urgent)",
        example="concerned"
    )
    in_voicemail: Optional[bool] = Field(
        None, 
        description="Whether the call went to voicemail instead of being answered",
        example=False
    )
    custom_analysis_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured analysis data (appointment type, urgency level, follow-up needed, etc.)",
        example={
            "appointment_type": "checkup",
            "urgency_level": "medium",
            "follow_up_needed": True,
            "pet_mentioned": "Golden Retriever named Max",
            "symptoms_mentioned": ["limping"],
            "appointment_scheduled": True,
            "appointment_date": "2025-09-27T14:00:00Z"
        }
    )


class CallSummary(BaseModel):
    """
    Basic call information for list views.
    
    Contains essential call data for displaying in call history lists.
    """
    call_id: Optional[str] = Field(
        None, 
        description="Unique identifier for the call",
        example="call_1a2b3c4d5e6f7g8h9i0j"
    )
    recording_url: Optional[str] = Field(
        None, 
        description="URL to access the call recording audio file",
        example="https://recordings.retellai.com/call_1a2b3c4d5e6f7g8h9i0j.mp3"
    )
    start_timestamp: Optional[datetime] = Field(
        None, 
        description="When the call started (ISO 8601 format with timezone)",
        example="2025-09-20T14:30:15.123Z"
    )
    end_timestamp: Optional[datetime] = Field(
        None, 
        description="When the call ended (ISO 8601 format with timezone)",
        example="2025-09-20T14:35:42.456Z"
    )
    call_analysis: Optional[CallAnalysisData] = Field(
        None,
        description="AI analysis of the call content and outcome"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "call_id": "call_1a2b3c4d5e6f7g8h9i0j",
                "recording_url": "https://recordings.retellai.com/call_1a2b3c4d5e6f7g8h9i0j.mp3",
                "start_timestamp": "2025-09-20T14:30:15.123Z",
                "end_timestamp": "2025-09-20T14:35:42.456Z",
                "call_analysis": {
                    "call_successful": True,
                    "call_summary": "Customer called to schedule a checkup for their Golden Retriever, Max. Appointment scheduled for next Tuesday at 2 PM. Customer mentioned Max has been limping slightly.",
                    "user_sentiment": "concerned",
                    "in_voicemail": False,
                    "custom_analysis_data": {
                        "appointment_type": "checkup",
                        "urgency_level": "medium",
                        "follow_up_needed": True,
                        "pet_mentioned": "Golden Retriever named Max",
                        "symptoms_mentioned": ["limping"],
                        "appointment_scheduled": True,
                        "appointment_date": "2025-09-27T14:00:00Z"
                    }
                }
            }
        }


class CallDetail(CallSummary):
    """
    Comprehensive call information for detailed views.
    
    Extends CallSummary with additional technical metadata and call details.
    """
    duration_ms: Optional[int] = Field(
        None, 
        description="Total call duration in milliseconds",
        example=327000
    )
    agent_id: Optional[str] = Field(
        None, 
        description="ID of the voice agent that handled the call",
        example="agent_11583fd62e3ba8128cb73fcb0e"
    )
    from_number: Optional[str] = Field(
        None, 
        description="Phone number that initiated the call (caller's number)",
        example="+15551234567"
    )
    to_number: Optional[str] = Field(
        None, 
        description="Phone number that received the call (practice's number)",
        example="+15559876543"
    )
    call_status: Optional[str] = Field(
        None,
        description="Final status of the call (completed, busy, no-answer, failed)",
        example="completed"
    )
    disconnect_reason: Optional[str] = Field(
        None,
        description="Reason the call ended (user_hangup, agent_hangup, error, timeout)",
        example="user_hangup"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "call_id": "call_1a2b3c4d5e6f7g8h9i0j",
                "recording_url": "https://recordings.retellai.com/call_1a2b3c4d5e6f7g8h9i0j.mp3",
                "start_timestamp": "2025-09-20T14:30:15.123Z",
                "end_timestamp": "2025-09-20T14:35:42.456Z",
                "duration_ms": 327000,
                "agent_id": "agent_11583fd62e3ba8128cb73fcb0e",
                "from_number": "+15551234567",
                "to_number": "+15559876543",
                "call_status": "completed",
                "disconnect_reason": "user_hangup",
                "call_analysis": {
                    "call_successful": True,
                    "call_summary": "Customer called to schedule a checkup for their Golden Retriever, Max. Appointment scheduled for next Tuesday at 2 PM. Customer mentioned Max has been limping slightly.",
                    "user_sentiment": "concerned",
                    "in_voicemail": False,
                    "custom_analysis_data": {
                        "appointment_type": "checkup",
                        "urgency_level": "medium",
                        "follow_up_needed": True,
                        "pet_mentioned": "Golden Retriever named Max",
                        "symptoms_mentioned": ["limping"],
                        "appointment_scheduled": True,
                        "appointment_date": "2025-09-27T14:00:00Z",
                        "customer_phone": "+15551234567",
                        "callback_requested": False
                    }
                }
            }
        }


class PaginationInfo(BaseModel):
    """
    Pagination metadata for call lists.
    
    Helps iOS app implement infinite scroll or page-based navigation.
    """
    limit: int = Field(
        description="Number of items requested per page",
        example=20
    )
    offset: int = Field(
        description="Number of items skipped (for pagination)",
        example=0
    )
    count: int = Field(
        description="Number of items returned in this response",
        example=20
    )
    has_more: Optional[bool] = Field(
        None,
        description="Whether there are more items available beyond this page",
        example=True
    )
    total_count: Optional[int] = Field(
        None,
        description="Total number of calls available (if known)",
        example=847
    )

    class Config:
        json_schema_extra = {
            "example": {
                "limit": 20,
                "offset": 0,
                "count": 20,
                "has_more": True,
                "total_count": 847
            }
        }


class CallListResponse(BaseModel):
    """
    Response for GET /api/v1/call-analysis/practice/{practice_id}/calls
    
    Returns a paginated list of calls for a veterinary practice.
    """
    practice_id: str = Field(
        description="UUID of the veterinary practice",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    calls: List[CallSummary] = Field(
        description="Array of call summaries for this page"
    )
    pagination: PaginationInfo = Field(
        description="Pagination information for implementing scroll/navigation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "practice_id": "550e8400-e29b-41d4-a716-446655440000",
                "calls": [
                    {
                        "call_id": "call_1a2b3c4d5e6f7g8h9i0j",
                        "recording_url": "https://recordings.retellai.com/call_1a2b3c4d5e6f7g8h9i0j.mp3",
                        "start_timestamp": "2025-09-20T14:30:15.123Z",
                        "end_timestamp": "2025-09-20T14:35:42.456Z",
                        "call_analysis": {
                            "call_successful": True,
                            "call_summary": "Customer called to schedule a checkup for their Golden Retriever, Max.",
                            "user_sentiment": "concerned",
                            "in_voicemail": False,
                            "custom_analysis_data": {
                                "appointment_type": "checkup",
                                "urgency_level": "medium"
                            }
                        }
                    },
                    {
                        "call_id": "call_2b3c4d5e6f7g8h9i0j1k",
                        "recording_url": "https://recordings.retellai.com/call_2b3c4d5e6f7g8h9i0j1k.mp3",
                        "start_timestamp": "2025-09-20T13:15:30.789Z",
                        "end_timestamp": "2025-09-20T13:18:45.012Z",
                        "call_analysis": {
                            "call_successful": False,
                            "call_summary": "Customer called about emergency - cat ingested something toxic. Directed to emergency clinic.",
                            "user_sentiment": "urgent",
                            "in_voicemail": False,
                            "custom_analysis_data": {
                                "appointment_type": "emergency",
                                "urgency_level": "high",
                                "emergency_referral": True
                            }
                        }
                    }
                ],
                "pagination": {
                    "limit": 20,
                    "offset": 0,
                    "count": 2,
                    "has_more": True,
                    "total_count": 847
                }
            }
        }


class CallDetailResponse(BaseModel):
    """
    Response for GET /api/v1/call-analysis/practice/{practice_id}/calls/{call_id}
    
    Returns detailed information for a specific call.
    """
    practice_id: str = Field(
        description="UUID of the veterinary practice",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    call: CallDetail = Field(
        description="Detailed call information including full metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "practice_id": "550e8400-e29b-41d4-a716-446655440000",
                "call": {
                    "call_id": "call_1a2b3c4d5e6f7g8h9i0j",
                    "recording_url": "https://recordings.retellai.com/call_1a2b3c4d5e6f7g8h9i0j.mp3",
                    "start_timestamp": "2025-09-20T14:30:15.123Z",
                    "end_timestamp": "2025-09-20T14:35:42.456Z",
                    "duration_ms": 327000,
                    "agent_id": "agent_11583fd62e3ba8128cb73fcb0e",
                    "from_number": "+15551234567",
                    "to_number": "+15559876543",
                    "call_status": "completed",
                    "disconnect_reason": "user_hangup",
                    "call_analysis": {
                        "call_successful": True,
                        "call_summary": "Customer called to schedule a checkup for their Golden Retriever, Max. Appointment scheduled for next Tuesday at 2 PM. Customer mentioned Max has been limping slightly.",
                        "user_sentiment": "concerned",
                        "in_voicemail": False,
                        "custom_analysis_data": {
                            "appointment_type": "checkup",
                            "urgency_level": "medium",
                            "follow_up_needed": True,
                            "pet_mentioned": "Golden Retriever named Max",
                            "symptoms_mentioned": ["limping"],
                            "appointment_scheduled": True,
                            "appointment_date": "2025-09-27T14:00:00Z",
                            "customer_phone": "+15551234567",
                            "callback_requested": False
                        }
                    }
                }
            }
        }


class VoiceConfigResponse(BaseModel):
    """
    Response for GET /api/v1/call-analysis/practice/{practice_id}/voice-config
    
    Returns voice configuration settings for a practice.
    """
    practice_id: str = Field(
        description="UUID of the veterinary practice",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    agent_id: str = Field(
        description="Voice agent ID used for this practice's calls",
        example="agent_11583fd62e3ba8128cb73fcb0e"
    )
    timezone: Optional[str] = Field(
        None,
        description="Practice timezone for call scheduling and display",
        example="America/Los_Angeles"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional voice configuration settings",
        example={
            "business_hours": {
                "monday": {"open": "08:00", "close": "18:00"},
                "tuesday": {"open": "08:00", "close": "18:00"},
                "wednesday": {"open": "08:00", "close": "18:00"},
                "thursday": {"open": "08:00", "close": "18:00"},
                "friday": {"open": "08:00", "close": "18:00"},
                "saturday": {"open": "09:00", "close": "16:00"},
                "sunday": {"closed": True}
            },
            "emergency_number": "+15551234567",
            "after_hours_message": "For emergencies, please call our emergency line.",
            "appointment_booking_enabled": True,
            "max_call_duration_minutes": 15
        }
    )
    is_active: bool = Field(
        description="Whether voice services are active for this practice",
        example=True
    )
    created_at: datetime = Field(
        description="When the voice configuration was created",
        example="2025-09-15T10:30:00.000Z"
    )
    updated_at: datetime = Field(
        description="When the voice configuration was last updated",
        example="2025-09-20T08:15:30.000Z"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "practice_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent_id": "agent_11583fd62e3ba8128cb73fcb0e",
                "timezone": "America/Los_Angeles",
                "metadata": {
                    "business_hours": {
                        "monday": {"open": "08:00", "close": "18:00"},
                        "tuesday": {"open": "08:00", "close": "18:00"},
                        "wednesday": {"open": "08:00", "close": "18:00"},
                        "thursday": {"open": "08:00", "close": "18:00"},
                        "friday": {"open": "08:00", "close": "18:00"},
                        "saturday": {"open": "09:00", "close": "16:00"},
                        "sunday": {"closed": True}
                    },
                    "emergency_number": "+15551234567",
                    "after_hours_message": "For emergencies, please call our emergency line.",
                    "appointment_booking_enabled": True,
                    "max_call_duration_minutes": 15
                },
                "is_active": True,
                "created_at": "2025-09-15T10:30:00.000Z",
                "updated_at": "2025-09-20T08:15:30.000Z"
            }
        }


# Error response schemas for comprehensive API documentation
class ErrorDetail(BaseModel):
    """Standard error detail structure."""
    detail: str = Field(
        description="Human-readable error message",
        example="Voice configuration not found for practice"
    )
    error_code: Optional[str] = Field(
        None,
        description="Machine-readable error code for client handling",
        example="VOICE_CONFIG_NOT_FOUND"
    )


class ValidationErrorDetail(BaseModel):
    """Detailed validation error for 422 responses."""
    detail: str = Field(
        description="General error message",
        example="Validation error"
    )
    errors: List[Dict[str, Any]] = Field(
        description="Specific validation errors",
        example=[
            {
                "field": "limit",
                "message": "ensure this value is less than or equal to 50",
                "type": "value_error.number.not_le",
                "input": 100
            }
        ]
    )
