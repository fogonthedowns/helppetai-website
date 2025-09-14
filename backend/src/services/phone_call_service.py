import os
import requests
import json
import logging
import pytz
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, date
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

# Import your existing models and repositories
try:
    from ..models_pg.pet_owner import PetOwner
    from ..models_pg.pet import Pet
    from ..models_pg.appointment import Appointment, AppointmentStatus, AppointmentType
    from ..models_pg.practice import VeterinaryPractice
    from ..repositories_pg.pet_owner_repository import PetOwnerRepository
    from ..repositories_pg.pet_repository import PetRepository
except ImportError:
    from models_pg.pet_owner import PetOwner
    from models_pg.pet import Pet
    from models_pg.appointment import Appointment, AppointmentStatus, AppointmentType
    from models_pg.practice import VeterinaryPractice
    from repositories_pg.pet_owner_repository import PetOwnerRepository
    from repositories_pg.pet_repository import PetRepository

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

class RetellAIService:
    """Service class to handle Retell AI operations"""
    
    def __init__(self):
        self.api_key = os.getenv("RETELL_API_KEY")
        self.base_url = "https://api.retellai.com"
        
        if not self.api_key:
            raise ValueError("RETELL_API_KEY environment variable is required")
    
    def create_llm(self) -> str:
        """Create a Retell LLM first"""
        
        llm_config = {
            "general_prompt": """You are a friendly pet appointment scheduling assistant for HelpPet. Your job is to:

1. Greet the caller warmly: "Hello! Thank you for calling HelpPet. I'm here to help you schedule an appointment for your pet."
2. Get the caller's phone number (or confirm it matches the calling number)
3. Use check_user function to see if they're an existing customer by phone number
4. If not found by phone, ask for their email address and try check_user_by_email
5. If new customer, use create_user function after collecting:
   - Owner's full name
   - Pet's name and type (dog, cat, bird, etc.)
   - Owner's address for our records
   - Email address (optional but recommended)
6. When they want to schedule, ask for their preferred date and time of day
7. Use get_available_times function with their date and time preference (morning/afternoon/evening/any time)
8. Present the available options and let them choose
9. Use book_appointment function to schedule the appointment
10. Use confirm_appointment function to finalize everything

Be conversational, warm, and helpful. Ask one question at a time. Always confirm information before proceeding. Show excitement about helping their pet!""",

            "begin_message": "Hello! Thank you for calling HelpPet. I'm here to help you schedule an appointment for your furry friend. May I start by getting your phone number?",
            
            "functions": [
                {
                    "name": "check_user",
                    "description": "Check if customer exists by phone number",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "phone_number": {
                                "type": "string",
                                "description": "The customer's phone number"
                            }
                        },
                        "required": ["phone_number"]
                    }
                },
                {
                    "name": "check_user_by_email",
                    "description": "Check if customer exists by email address",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "The customer's email address"
                            }
                        },
                        "required": ["email"]
                    }
                },
                {
                    "name": "create_user",
                    "description": "Create new customer profile",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "phone_number": {
                                "type": "string",
                                "description": "The customer's phone number"
                            },
                            "email": {
                                "type": "string",
                                "description": "The customer's email address (optional)"
                            },
                            "address": {
                                "type": "string",
                                "description": "The customer's address"
                            },
                            "pet_name": {
                                "type": "string",
                                "description": "The pet's name"
                            },
                            "pet_type": {
                                "type": "string",
                                "description": "The type of pet (dog, cat, bird, etc.)"
                            },
                            "owner_name": {
                                "type": "string",
                                "description": "The owner's full name"
                            }
                        },
                        "required": ["phone_number", "owner_name"]
                    }
                },
                {
                    "name": "check_calendar",
                    "description": "Get available appointment times",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "book_appointment",
                    "description": "Book the appointment slot",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The customer's user ID"
                            },
                            "date_time": {
                                "type": "string",
                                "description": "The appointment date and time"
                            },
                            "service": {
                                "type": "string",
                                "description": "The type of service (default: General Checkup)"
                            }
                        },
                        "required": ["user_id", "date_time"]
                    }
                },
                {
                    "name": "confirm_appointment",
                    "description": "Confirm and finalize the appointment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "appointment_id": {
                                "type": "string",
                                "description": "The appointment ID to confirm"
                            }
                        },
                        "required": ["appointment_id"]
                    }
                },
                {
                    "name": "get_available_times",
                    "description": "Get available appointment times for a specific date and time preference",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "The date for the appointment (e.g., '9-14', 'September 14', 'tomorrow')"
                            },
                            "time_preference": {
                                "type": "string",
                                "description": "Time of day preference (e.g., 'morning', 'afternoon', 'evening', 'any time')"
                            }
                        },
                        "required": ["date", "time_preference"]
                    }
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}/create-retell-llm",
            headers=headers,
            json=llm_config
        )
        
        # Check for successful status codes (200, 201)
        if response.status_code in [200, 201]:
            llm_data = response.json()
            # The response contains the llm_id directly in the response
            llm_id = llm_data.get("llm_id")
            if llm_id:
                return llm_id
            else:
                raise Exception(f"LLM created but no llm_id in response: {response.text}")
        else:
            raise Exception(f"Failed to create LLM: Status {response.status_code}, Response: {response.text}")

    def create_agent(self, webhook_url: str) -> str:
        """Create a Retell AI agent for appointment scheduling"""
        
        # First, create the LLM
        llm_id = self.create_llm()
        
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
    
    def configure_phone_number(self, agent_id: str, phone_number: str):
        """Configure a phone number to use the agent"""
        
        phone_config = {
            "phone_number": phone_number,
            "agent_id": agent_id
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}/create-phone-number",
            headers=headers,
            json=phone_config
        )
        
        # Check for any success status code (200-299)
        if not (200 <= response.status_code < 300):
            raise Exception(f"Failed to configure phone number: {response.text}")


    def update_agent(self, agent_id: str, webhook_url: str, llm_id: str = None):
        """Update an existing Retell AI agent configuration"""
        
        # If no LLM ID provided, create a new one
        if not llm_id:
            llm_id = self.create_llm()
        
        agent_config = {
            "agent_name": "Pet Appointment Scheduler",
            "voice_id": "openai-Alloy",
            "language": "en-US",
            "response_engine": {
                "type": "retell-llm",
                "llm_id": llm_id
            },
            "webhook_url": webhook_url
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.patch(
            f"{self.base_url}/update-agent/{agent_id}",
            headers=headers,
            json=agent_config
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to update agent: {response.text}")

class AppointmentService:
    """Service class for appointment booking business logic"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.pet_owner_repo = PetOwnerRepository(db_session)
        self.pet_repo = PetRepository(db_session)
    
    async def check_user(self, phone_number: str) -> Dict[str, Any]:
        """Check if user exists by phone number"""
        try:
            # Clean phone number (remove formatting)
            clean_phone = self._clean_phone_number(phone_number)
            
            # Look up pet owner by phone
            pet_owner = await self.pet_owner_repo.get_by_phone(clean_phone)
            logger.info(f"Pet owner: {clean_phone}")
          
            if pet_owner:
                logger.info(f"Pet owner found!!!!!!!!!!!!!!!!!!!!!!!: {pet_owner}")
                return await self._format_user_response(pet_owner, "phone")
            else:
                logger.info(f"Pet owner not found!!!!!!!!!!!!!!!!!!!!!!!")
                return {
                    "success": True,
                    "user_exists": False,
                    "message": "I don't see that phone number in our system. Could you provide your email address so I can check that way?"
                }
        except Exception as e:
            return {
                "success": False,
                "message": "I'm having trouble looking up your information. Let me try again."
            }
    
    async def check_user_by_email(self, email: str) -> Dict[str, Any]:
        """Check if user exists by email address"""
        try:
            # Clean email (convert to lowercase)
            clean_email = email.lower().strip()
            
            # Look up pet owner by email
            pet_owner = await self.pet_owner_repo.get_by_email(clean_email)
            
            if pet_owner:
                return await self._format_user_response(pet_owner, "email")
            else:
                return {
                    "success": True,
                    "user_exists": False,
                    "message": "I don't see that email in our system either. Let me get you set up as a new customer!"
                }
        except Exception as e:
            return {
                "success": False,
                "message": "I'm having trouble looking up your information. Let me try again."
            }
    
    async def _format_user_response(self, pet_owner: PetOwner, found_by: str) -> Dict[str, Any]:
        """Format user response with pet information"""
        try:
            # Get their pets
            pets = await self.pet_repo.get_by_owner_id(pet_owner.id)
            
            if pets:
                pet = pets[0]  # Use first pet for greeting
                return {
                    "success": True,
                    "user_exists": True,
                    "user": {
                        "id": str(pet_owner.id),
                        "phone_number": pet_owner.phone or "",
                        "email": pet_owner.email or "",
                        "address": pet_owner.address or "",
                        "pet_name": pet.name,
                        "pet_type": pet.species,
                        "owner_name": pet_owner.full_name
                    },
                    "message": f"Welcome back {pet_owner.full_name}! I found you by your {found_by}. I see you have {pet.name} the {pet.species} in our system."
                }
            else:
                return {
                    "success": True,
                    "user_exists": True,
                    "user": {
                        "id": str(pet_owner.id),
                        "phone_number": pet_owner.phone or "",
                        "email": pet_owner.email or "",
                        "address": pet_owner.address or "",
                        "pet_name": "",
                        "pet_type": "",
                        "owner_name": pet_owner.full_name
                    },
                    "message": f"Welcome back {pet_owner.full_name}! I found you by your {found_by}. Let me help you schedule an appointment."
                }
        except Exception as e:
            return {
                "success": False,
                "message": "I found your information but I'm having trouble loading your details. Let me try again."
            }
    
    async def create_user(self, phone_number: str, email: str, address: str, pet_name: str, pet_type: str, owner_name: str) -> Dict[str, Any]:
        """Create a new user in your database"""
        try:
            # Clean phone number and email
            clean_phone = self._clean_phone_number(phone_number)
            clean_email = email.lower().strip() if email else None
            
            # Validate required fields
            if not owner_name or not owner_name.strip():
                return {
                    "success": False,
                    "message": "I need your full name to create your profile. Could you please provide that?"
                }
            
            # Check if phone or email already exists
            if clean_phone:
                existing_by_phone = await self.pet_owner_repo.get_by_phone(clean_phone)
                if existing_by_phone:
                    return {
                        "success": False,
                        "message": "I found an existing account with that phone number. Let me look that up for you instead."
                    }
            
            if clean_email:
                existing_by_email = await self.pet_owner_repo.get_by_email(clean_email)
                if existing_by_email:
                    return {
                        "success": False,
                        "message": "I found an existing account with that email address. Let me look that up for you instead."
                    }
            
            # Create pet owner
            pet_owner = PetOwner(
                full_name=owner_name.strip(),
                phone=clean_phone,
                email=clean_email,
                address=address.strip() if address else None,
                preferred_communication="phone"
            )
            
            self.db.add(pet_owner)
            await self.db.flush()  # Get the ID
            
            # Create pet if provided
            if pet_name and pet_type:
                pet = Pet(
                    name=pet_name.strip(),
                    species=pet_type.title(),
                    owner_id=pet_owner.id
                )
                self.db.add(pet)
            
            await self.db.commit()
            
            return {
                "success": True,
                "user_id": str(pet_owner.id),
                "message": f"Perfect! I've created a profile for {owner_name}{' and ' + pet_name if pet_name else ''}. Now let's find an appointment time."
            }
        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "message": "I'm having trouble creating your profile. Let me try again."
            }
    
    async def check_calendar(self) -> Dict[str, Any]:
        """Check available appointment slots"""
        try:
            # Get available slots (simplified - you can integrate with actual calendar system)
            available_times = await self._get_available_slots()
            
            if available_times:
                return {
                    "success": True,
                    "available_times": available_times,
                    "message": "Here are our available appointment times:"
                }
            else:
                return {
                    "success": False,
                    "message": "I'm sorry, we don't have any available slots right now. Would you like me to put you on our waitlist?"
                }
        except Exception as e:
            return {
                "success": False,
                "message": "I'm having trouble checking our calendar. Let me try again."
            }
    
    async def book_appointment(self, user_id: str, date_time: str, service: str = "General Checkup") -> Dict[str, Any]:
        """Book an appointment"""
        try:
            # Parse the date_time (you might need to adjust this based on format)
            appointment_datetime = self._parse_appointment_time(date_time)
            
            # Get default practice (you might want to make this configurable)
            practice = await self._get_default_practice()
            if not practice:
                return {
                    "success": False,
                    "message": "I'm having trouble accessing our scheduling system. Let me get a human to help you."
                }
            
            # Create appointment
            appointment = Appointment(
                practice_id=practice.id,
                pet_owner_id=UUID(user_id),
                created_by_user_id=practice.owner_user_id,  # Use practice owner as creator
                appointment_date=appointment_datetime,
                title=f"{service} Appointment",
                description=f"Phone scheduled {service}",
                appointment_type=AppointmentType.CHECKUP.value,
                status=AppointmentStatus.SCHEDULED.value,
                duration_minutes=30
            )
            
            self.db.add(appointment)
            await self.db.commit()
            
            return {
                "success": True,
                "appointment_id": str(appointment.id),
                "message": f"Great! I've reserved {date_time} for {service}. Let me confirm all the details.",
                "details": {
                    "date_time": date_time,
                    "service": service
                }
            }
        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "message": "I'm sorry, that time slot just became unavailable. Let me check other options."
            }
    
    async def confirm_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Confirm an appointment"""
        try:
            # Get the appointment
            result = await self.db.execute(
                select(Appointment).where(Appointment.id == UUID(appointment_id))
            )
            appointment = result.scalar_one_or_none()
            
            if not appointment:
                return {
                    "success": False,
                    "message": "I'm having trouble finding that appointment. Let me try again."
                }
            
            # Update status to confirmed
            appointment.status = AppointmentStatus.CONFIRMED.value
            await self.db.commit()
            
            # Format the date for the message
            formatted_date = appointment.appointment_date.strftime("%A, %B %d at %I:%M %p")
            
            return {
                "success": True,
                "message": f"Perfect! Your appointment is confirmed for {formatted_date}. We'll send you a reminder before your visit. Thank you for choosing HelpPet!"
            }
        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "message": "I'm having trouble confirming that appointment. Let me try again."
            }
    
    async def get_available_times(self, date_str: str, time_preference: str) -> Dict[str, Any]:
        """
        🎯 GET AVAILABLE APPOINTMENT TIMES - PHONE WEBHOOK FUNCTION
        
        This function integrates with our slot-based scheduling system to return
        actual available appointment slots for phone callers.
        
        Args:
            date_str: Raw date input from caller (e.g., '9-14', 'September 14', 'tomorrow')
            time_preference: Time preference (e.g., 'morning', 'afternoon', 'evening')
        
        Returns:
            Dict with success status and available appointment times
        """
        logger.info("=" * 80)
        logger.info("🔍 PHONE WEBHOOK: get_available_times() CALLED")
        logger.info(f"📅 Raw date input: '{date_str}'")
        logger.info(f"⏰ Raw time preference: '{time_preference}'")
        logger.info("=" * 80)
        
        try:
            # Step 1: Parse and clean the date
            parsed_date = self._parse_date_string(date_str)
            logger.info(f"✅ Parsed date: {parsed_date}")
            
            # Step 2: Clean time preference
            cleaned_time_pref = self._clean_time_preference(time_preference)
            logger.info(f"✅ Cleaned time preference: {cleaned_time_pref}")
            
            # Step 3: Get default practice and vet
            practice = await self._get_default_practice()
            if not practice:
                logger.error("❌ No default practice found")
                return {
                    "success": False,
                    "message": "I'm having trouble accessing our scheduling system. Let me get a human to help you."
                }
            
            # Get first available vet (you might want to make this smarter)
            vet_user_id = await self._get_available_vet(practice.id)
            if not vet_user_id:
                logger.error("❌ No available vets found")
                return {
                    "success": False,
                    "message": "I don't see any vets available. Let me check with our staff."
                }
            
            logger.info(f"🏥 Using practice: {practice.id}")
            logger.info(f"👩‍⚕️ Using vet: {vet_user_id}")
            
            # Step 4: Get actual available slots using our slot system
            from ..repositories_pg.scheduling_repository import VetAvailabilityRepository
            
            # Create repository
            repo = VetAvailabilityRepository(self.db)
            
            logger.info(f"🔍 Calling get_available_slots for date: {parsed_date}")
            slot_data = await repo.get_available_slots(
                vet_user_id=vet_user_id,
                practice_id=practice.id,
                date=parsed_date,
                slot_duration_minutes=45  # 45-minute appointments as requested
            )
            
            logger.info(f"📊 Raw slots returned: {len(slot_data)} slots")
            for i, slot in enumerate(slot_data):
                logger.info(f"  Slot {i+1}: {slot['start_time']}-{slot['end_time']} available={slot['available']}")
            
            # Step 5: Filter by time preference and availability
            available_slots = [slot for slot in slot_data if slot['available']]
            filtered_slots = self._filter_slots_by_time_preference(available_slots, cleaned_time_pref)
            
            logger.info(f"✅ Available slots after filtering: {len(filtered_slots)}")
            
            # Step 6: Format response for phone caller (return max 3 options)
            if filtered_slots:
                formatted_times = []
                for slot in filtered_slots[:3]:  # Return top 3 options
                    formatted_time = self._format_slot_for_caller(slot, parsed_date, practice.timezone)
                    formatted_times.append(formatted_time)
                    logger.info(f"📞 Formatted for caller: {formatted_time}")
                
                message = f"I found {len(formatted_times)} available times on {parsed_date.strftime('%A, %B %d')}: " + ", ".join(formatted_times)
                
                logger.info(f"✅ SUCCESS: Returning {len(formatted_times)} options")
                return {
                    "success": True,
                    "available_times": formatted_times,
                    "message": message,
                    "date": parsed_date.strftime('%Y-%m-%d'),
                    "time_preference": cleaned_time_pref
                }
            else:
                logger.warning(f"⚠️ No available slots found for {parsed_date} {cleaned_time_pref}")
                return {
                    "success": False,
                    "message": f"I'm sorry, we don't have any {cleaned_time_pref} appointments available on {parsed_date.strftime('%A, %B %d')}. Would you like to try a different day or time?"
                }
                
        except Exception as e:
            logger.error(f"❌ ERROR in get_available_times: {str(e)}")
            logger.exception("Full traceback:")
            return {
                "success": False,
                "message": "I'm having trouble checking our calendar. Let me try again or get a human to help you."
            }
    
    # Helper methods
    def _clean_phone_number(self, phone_number: str) -> str:
        """Clean and format phone number"""
        # Remove all non-digit characters
        clean = ''.join(filter(str.isdigit, phone_number))
        
        # Add +1 if it's a 10-digit US number
        if len(clean) == 10:
            clean = '1' + clean
        
        # Format as +1XXXXXXXXXX
        if len(clean) == 11 and clean.startswith('1'):
            return '+' + clean
        
        return phone_number  # Return original if we can't parse it
    
    async def _get_available_slots(self) -> List[str]:
        """Get available appointment slots"""
        # This is a simplified version - you can integrate with actual calendar system
        # For now, generate some sample slots
        now = datetime.now()
        slots = []
        
        # Generate slots for next 7 days, 9 AM to 5 PM
        for day_offset in range(7):
            date = now + timedelta(days=day_offset)
            if date.weekday() < 5:  # Monday to Friday
                for hour in [9, 11, 14, 16]:  # 9 AM, 11 AM, 2 PM, 4 PM
                    slot_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    if slot_time > now:  # Only future slots
                        formatted = slot_time.strftime("%A, %B %d at %I:%M %p")
                        slots.append(formatted)
        
        return slots[:6]  # Return first 6 available slots
    
    def _parse_appointment_time(self, date_time_str: str) -> datetime:
        """Parse appointment time string to datetime"""
        # This is a simplified parser - you might need more sophisticated parsing
        # For now, assume format like "Tomorrow at 3:00 PM"
        now = datetime.now()
        
        if "today" in date_time_str.lower():
            base_date = now.date()
        elif "tomorrow" in date_time_str.lower():
            base_date = (now + timedelta(days=1)).date()
        else:
            # For more complex parsing, you might want to use dateutil.parser
            base_date = (now + timedelta(days=1)).date()  # Default to tomorrow
        
        # Extract time (simplified)
        if "2:00 PM" in date_time_str or "2 PM" in date_time_str:
            time = datetime.strptime("14:00", "%H:%M").time()
        elif "4:00 PM" in date_time_str or "4 PM" in date_time_str:
            time = datetime.strptime("16:00", "%H:%M").time()
        elif "10:00 AM" in date_time_str or "10 AM" in date_time_str:
            time = datetime.strptime("10:00", "%H:%M").time()
        elif "3:00 PM" in date_time_str or "3 PM" in date_time_str:
            time = datetime.strptime("15:00", "%H:%M").time()
        elif "9:00 AM" in date_time_str or "9 AM" in date_time_str:
            time = datetime.strptime("09:00", "%H:%M").time()
        else:
            time = datetime.strptime("14:00", "%H:%M").time()  # Default to 2 PM
        
        return datetime.combine(base_date, time)
    
    def _parse_date_string(self, date_str: str) -> date:
        """
        Parse various date formats from phone callers
        
        Examples: '9-14', 'September 14', 'tomorrow', 'next Friday'
        """
        logger.info(f"🔍 Parsing date string: '{date_str}'")
        
        from datetime import date as dt_date
        import re
        
        # Clean the input
        date_str = date_str.lower().strip()
        
        # Handle relative dates
        now = datetime.now()
        
        if 'today' in date_str:
            return now.date()
        elif 'tomorrow' in date_str:
            return (now + timedelta(days=1)).date()
        elif 'next week' in date_str:
            return (now + timedelta(days=7)).date()
        
        # Handle numeric formats like '9-14', '9/14', '09-14'
        numeric_match = re.search(r'(\d{1,2})[-/](\d{1,2})', date_str)
        if numeric_match:
            month, day = int(numeric_match.group(1)), int(numeric_match.group(2))
            year = now.year
            # If the date has passed this year, assume next year
            try:
                parsed_date = dt_date(year, month, day)
                if parsed_date < now.date():
                    parsed_date = dt_date(year + 1, month, day)
                logger.info(f"✅ Parsed numeric date: {parsed_date}")
                return parsed_date
            except ValueError:
                pass
        
        # Handle month names like 'September 14', 'Sep 14'
        month_names = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
            'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
            'aug': 8, 'august': 8, 'sep': 9, 'september': 9, 'oct': 10, 'october': 10,
            'nov': 11, 'november': 11, 'dec': 12, 'december': 12
        }
        
        for month_name, month_num in month_names.items():
            if month_name in date_str:
                # Look for day number
                day_match = re.search(r'\b(\d{1,2})\b', date_str)
                if day_match:
                    day = int(day_match.group(1))
                    year = now.year
                    try:
                        parsed_date = dt_date(year, month_num, day)
                        if parsed_date < now.date():
                            parsed_date = dt_date(year + 1, month_num, day)
                        logger.info(f"✅ Parsed month name date: {parsed_date}")
                        return parsed_date
                    except ValueError:
                        pass
        
        # Default fallback - tomorrow
        fallback_date = (now + timedelta(days=1)).date()
        logger.warning(f"⚠️ Could not parse '{date_str}', defaulting to tomorrow: {fallback_date}")
        return fallback_date
    
    def _clean_time_preference(self, time_pref: str) -> str:
        """
        Clean and standardize time preference
        
        Examples: 'Morning', 'afternoon', 'evening', 'any time', 'AM', 'PM'
        """
        logger.info(f"🔍 Cleaning time preference: '{time_pref}'")
        
        time_pref = time_pref.lower().strip()
        
        if any(word in time_pref for word in ['any', 'anytime', 'any time', 'flexible', 'whenever', 'doesn\'t matter', 'no preference']):
            return 'any time'
        elif any(word in time_pref for word in ['morning', 'am', 'early', 'before noon']):
            return 'morning'
        elif any(word in time_pref for word in ['afternoon', 'pm', 'after noon', 'midday']):
            return 'afternoon'
        elif any(word in time_pref for word in ['evening', 'night', 'late', 'after 5']):
            return 'evening'
        else:
            # Default to any time if unclear
            logger.warning(f"⚠️ Unclear time preference '{time_pref}', defaulting to any time")
            return 'any time'
    
    def _filter_slots_by_time_preference(self, slots: List[Dict], time_pref: str) -> List[Dict]:
        """
        Filter slots based on time preference
        
        Morning: 6 AM - 12 PM
        Afternoon: 12 PM - 5 PM  
        Evening: 5 PM - 9 PM
        Any time: All available slots
        """
        logger.info(f"🔍 Filtering {len(slots)} slots by time preference: {time_pref}")
        
        # If "any time", return all available slots
        if time_pref == 'any time':
            logger.info(f"✅ Any time preference - returning all {len(slots)} slots")
            return slots
        
        filtered = []
        for slot in slots:
            start_time = slot['start_time']
            
            # Handle both datetime.time objects and string formats
            if hasattr(start_time, 'hour'):
                # It's a datetime.time object
                hour = start_time.hour
            else:
                # It's a string like "14:30:00"
                hour = int(str(start_time).split(':')[0])
            
            logger.info(f"  Slot at hour {hour} ({'morning' if 6 <= hour < 12 else 'afternoon' if 12 <= hour < 17 else 'evening' if 17 <= hour < 21 else 'other'})")
            
            if time_pref == 'morning' and 6 <= hour < 12:
                filtered.append(slot)
            elif time_pref == 'afternoon' and 12 <= hour < 17:
                filtered.append(slot)
            elif time_pref == 'evening' and 17 <= hour < 21:
                filtered.append(slot)
        
        logger.info(f"✅ Filtered to {len(filtered)} slots for {time_pref}")
        return filtered
    
    def _format_slot_for_caller(self, slot: Dict, date: date, practice_timezone: str = "UTC") -> str:
        """
        Format a slot for phone caller in natural language, converting from UTC to practice timezone
        
        Example: "2:30 PM" or "10:00 AM" (in practice local time)
        """
        from datetime import datetime as dt
        
        start_time = slot['start_time']
        
        # Handle both datetime.time objects and string formats
        if hasattr(start_time, 'hour'):
            # It's a datetime.time object
            utc_hour = start_time.hour
            utc_minute = start_time.minute
        else:
            # It's a string like "14:30:00"
            utc_hour, utc_minute = map(int, str(start_time).split(':')[:2])
        
        # Create UTC datetime for the slot
        utc_datetime = dt.combine(date, dt.min.time().replace(hour=utc_hour, minute=utc_minute))
        utc_datetime = pytz.UTC.localize(utc_datetime)
        
        # Convert to practice timezone
        try:
            practice_tz = pytz.timezone(practice_timezone)
            local_datetime = utc_datetime.astimezone(practice_tz)
            hour = local_datetime.hour
            minute = local_datetime.minute
            
            logger.info(f"🌍 Timezone conversion: UTC {utc_hour:02d}:{utc_minute:02d} → {practice_timezone} {hour:02d}:{minute:02d}")
        except Exception as e:
            logger.warning(f"⚠️ Timezone conversion failed for {practice_timezone}: {e}, using UTC")
            hour = utc_hour
            minute = utc_minute
        
        # Convert to 12-hour format
        if hour == 0:
            formatted = f"12:{minute:02d} AM"
        elif hour < 12:
            formatted = f"{hour}:{minute:02d} AM"
        elif hour == 12:
            formatted = f"12:{minute:02d} PM"
        else:
            formatted = f"{hour-12}:{minute:02d} PM"
        
        return formatted
    
    async def _get_available_vet(self, practice_id: UUID) -> Optional[UUID]:
        """
        Get an available vet for the practice
        
        This is a simplified version - you might want to make this smarter
        by checking vet schedules, specialties, etc.
        """
        logger.info(f"🔍 Looking for available vet in practice: {practice_id}")
        
        from ..models_pg.user import User
        
        # Get vets associated with this practice
        result = await self.db.execute(
            select(User).where(
                User.practice_id == practice_id,
                User.role == 'VET_STAFF',
                User.is_active == True
            ).limit(1)
        )
        
        vet = result.scalar_one_or_none()
        if vet:
            logger.info(f"✅ Found vet: {vet.id} ({vet.full_name})")
            return vet.id
        else:
            logger.warning("⚠️ No vets found for this practice")
            return None
    
    async def _get_default_practice(self) -> Optional[VeterinaryPractice]:
        """Get the default practice for appointments"""
        # Get the first available practice - you might want to make this configurable
        result = await self.db.execute(
            select(VeterinaryPractice).limit(1)
        )
        return result.scalar_one_or_none()

# Initialize Retell service lazily (will be created when first needed)
retell_service = None

def get_retell_service() -> RetellAIService:
    """Get or create the Retell AI service instance"""
    global retell_service
    if retell_service is None:
        retell_service = RetellAIService()
    return retell_service

# Function to handle phone webhook requests (will be called from webhook route)
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
    
    # Initialize appointment service with database session
    appointment_service = AppointmentService(db_session)
    
    try:
        # Route to appropriate function
        if function_name == "check_user":
            logger.info(f"🔍 CALLING check_user with phone_number: {arguments.get('phone_number')}")
            result = await appointment_service.check_user(arguments.get("phone_number"))
            logger.info(f"✅ check_user result: {result}")
            
        elif function_name == "check_user_by_email":
            result = await appointment_service.check_user_by_email(arguments.get("email"))
            
        elif function_name == "create_user":
            result = await appointment_service.create_user(
                arguments.get("phone_number"),
                arguments.get("email", ""),
                arguments.get("address", ""),
                arguments.get("pet_name", ""),
                arguments.get("pet_type", ""),
                arguments.get("owner_name", "")
            )
            
        elif function_name == "check_calendar":
            result = await appointment_service.check_calendar()
            
        elif function_name == "book_appointment":
            result = await appointment_service.book_appointment(
                arguments.get("user_id"),
                arguments.get("date_time"),
                arguments.get("service", "General Checkup")
            )
            
        elif function_name == "confirm_appointment":
            result = await appointment_service.confirm_appointment(arguments.get("appointment_id"))
            
        elif function_name == "get_available_times":
            logger.info("🎯 PHONE WEBHOOK: get_available_times CALLED")
            logger.info(f"📅 Arguments received: {arguments}")
            result = await appointment_service.get_available_times(
                arguments.get("date"),
                arguments.get("time_preference")
            )
            logger.info(f"✅ get_available_times result: {result}")
            
        else:
            result = {
                "success": False, 
                "message": f"I'm not sure how to handle that request. Let me get a human to help you."
            }
        
        return {"response": result}
        
    except Exception as e:
        return {
            "response": {
                "success": False,
                "message": "I'm experiencing a technical issue. Let me try that again."
            }
        }

# Function to setup Retell agent (will be called from setup endpoint)
async def setup_retell_agent(phone_number: str) -> Dict[str, Any]:
    """Setup endpoint to create and configure Retell AI agent"""
    try:
        webhook_url = "https://api.helppet.ai/api/v1/webhook/phone"
        service = get_retell_service()
        
        # Create agent
        agent_id = service.create_agent(webhook_url)
        
        # Configure phone number
        service.configure_phone_number(agent_id, phone_number)
        
        return {
            "success": True,
            "agent_id": agent_id,
            "message": "Retell AI setup completed successfully!"
        }
        
    except Exception as e:
        raise Exception(f"Failed to setup Retell AI: {str(e)}")

# Function to update existing Retell agent (will be called from update endpoint)
async def update_retell_agent(agent_id: str, phone_number: str = None) -> Dict[str, Any]:
    """Update existing Retell AI agent configuration"""
    try:
        webhook_url = "https://api.helppet.ai/api/v1/webhook/phone"
        service = get_retell_service()
        
        # Update agent configuration
        service.update_agent(agent_id, webhook_url)
        
        # Configure new phone number if provided
        if phone_number:
            service.configure_phone_number(agent_id, phone_number)
        
        return {
            "success": True,
            "agent_id": agent_id,
            "message": f"Retell AI agent {agent_id} updated successfully!"
        }
        
    except Exception as e:
        raise Exception(f"Failed to update Retell AI agent: {str(e)}")
