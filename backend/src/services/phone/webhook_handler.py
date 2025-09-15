"""
Phone Webhook Handler

Main webhook routing and handling for phone calls from Retell AI.
"""

import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .user_service import UserService
from .scheduling_service import SchedulingService
from .appointment_service import AppointmentService

logger = logging.getLogger(__name__)


# Pydantic models for request/response validation
class FunctionCall(BaseModel):
    name: str
    arguments: Dict[str, Any]


class CallInfo(BaseModel):
    call_id: str
    call_type: str
    agent_id: str
    agent_version: int
    agent_name: str
    call_status: str
    start_timestamp: int


class RetellWebhookRequest(BaseModel):
    event: Optional[str] = None  # For call events like "call_started"
    function_call: Optional[FunctionCall] = None  # For function calls (old format)
    call: Optional[CallInfo] = None  # Call information
    name: Optional[str] = None  # Function name (new format)
    args: Optional[Dict[str, Any]] = None  # Function arguments (new format)


class User(BaseModel):
    id: Optional[str] = None
    phone_number: str
    address: str = ""
    pet_name: str = ""
    pet_type: str = ""


class Appointment(BaseModel):
    id: Optional[str] = None
    user_id: str
    date_time: str
    service: str = "General Checkup"
    confirmed: bool = False


async def handle_phone_webhook(request: RetellWebhookRequest, db_session: AsyncSession) -> Dict[str, Any]:
    """Handle webhooks from Retell AI - both call events and function calls"""
    
    # Handle call events (like call_started, call_ended)
    if request.event:
        if request.event == "call_started":
            return {"message": "Call started successfully"}
        elif request.event == "call_ended":
            return {"message": "Call ended"}
        else:
            return {"message": f"Received event: {request.event}"}
    
    # Handle function calls (support both old and new formats)
    if request.function_call:
        # Old format: {"function_call": {"name": "...", "arguments": {...}}}
        function_name = request.function_call.name
        arguments = request.function_call.arguments
    elif request.name and request.args:
        # New format: {"name": "...", "args": {...}}
        function_name = request.name
        arguments = request.args
    else:
        return {
            "response": {
                "success": False,
                "message": "No function call or event found in request"
            }
        }
    
    # Initialize specialized services with database session
    user_service = UserService(db_session)
    scheduling_service = SchedulingService(db_session)
    appointment_service = AppointmentService(db_session)
    
    try:
        # Route to appropriate service based on function
        if function_name == "check_user":
            logger.info(f"🔍 USER SERVICE: check_user with phone_number: {arguments.get('phone_number')}")
            result = await user_service.check_user(arguments.get("phone_number"))
            logger.info(f"✅ check_user result: {result}")
            
        elif function_name == "check_user_by_email":
            logger.info(f"🔍 USER SERVICE: check_user_by_email")
            result = await user_service.check_user_by_email(arguments.get("email"))
            
        elif function_name == "create_user":
            logger.info(f"🔍 USER SERVICE: create_user")
            result = await user_service.create_user(
                arguments.get("phone_number"),
                arguments.get("email", ""),
                arguments.get("address", ""),
                arguments.get("owner_name", ""),
                arguments.get("practice_uuid", "")
            )
            
        elif function_name == "get_user_pets":
            logger.info(f"🔍 USER SERVICE: get_user_pets")
            result = await user_service.get_user_pets(arguments.get("pet_owner_id"))
            
        elif function_name == "check_calendar":
            logger.info(f"🔍 APPOINTMENT SERVICE: check_calendar")
            result = await appointment_service.check_calendar()
            
        elif function_name == "book_appointment":
            logger.info(f"🔍 APPOINTMENT SERVICE: book_appointment")
            
            # Handle both single pet_name and multiple pet_names
            pet_names = arguments.get("pet_names")
            if not pet_names and arguments.get("pet_name"):
                # Support backward compatibility with single pet_name
                pet_names = [arguments.get("pet_name")]
            
            result = await appointment_service.book_appointment(
                pet_owner_id=arguments.get("pet_owner_id") or arguments.get("user_id"),  # Support both field names
                practice_id=arguments.get("practice_id"),
                date=arguments.get("date"),
                start_time=arguments.get("start_time"),
                timezone=arguments.get("timezone", "America/Los_Angeles"),
                service=arguments.get("service", "General Checkup"),
                pet_names=pet_names,  # Changed from pet_name to pet_names
                notes=arguments.get("notes"),
                assigned_vet_user_id=arguments.get("assigned_vet_user_id")
            )
            
        elif function_name == "confirm_appointment":
            logger.info(f"🔍 APPOINTMENT SERVICE: confirm_appointment")
            result = await appointment_service.confirm_appointment(arguments.get("appointment_id"))
            
        elif function_name == "get_available_times":
            logger.info("🎯 SCHEDULING SERVICE: get_available_times CALLED")
            logger.info(f"📅 Arguments received: {arguments}")
            result = await scheduling_service.get_available_times(
                arguments.get("date"),
                arguments.get("time_preference"),
                arguments.get("practice_id"),
                arguments.get("timezone", "America/Los_Angeles")  # Default to PST if not provided
            )
            logger.info(f"✅ get_available_times result: {result}")
            
        else:
            result = {
                "success": False, 
                "message": f"I'm not sure how to handle that request. Let me get a human to help you."
            }
        
        return {"response": result}
        
    except Exception as e:
        logger.error(f"Error processing phone webhook: {str(e)}")
        return {
            "response": {
                "success": False,
                "message": "I'm experiencing a technical issue. Let me try that again."
            }
        }
