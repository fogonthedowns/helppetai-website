"""
Appointment Service for Phone Operations

Handles appointment booking, confirmation, and calendar operations for phone calls.
"""

import logging
import pytz
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, time, date
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ...models_pg.appointment import AppointmentStatus, AppointmentType
from ...repositories_pg.appointment_repository import AppointmentRepository
from ...repositories_pg.pet_owner_repository import PetOwnerRepository
from ...repositories_pg.practice_repository import PracticeRepository
from ...schemas.appointment_schemas import BookAppointmentRequest, BookAppointmentResponse

logger = logging.getLogger(__name__)


class AppointmentService:
    """Service class for core appointment booking operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.appointment_repo = AppointmentRepository(db_session)
        self.pet_owner_repo = PetOwnerRepository(db_session)
        self.practice_repo = PracticeRepository(db_session)
    
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
    
    async def book_appointment(
        self,
        pet_owner_id: str,
        practice_id: str,
        date: str,
        start_time: str,
        timezone: str = "America/Los_Angeles",
        service: str = "General Checkup",
        pet_names: List[str] = None,  # Changed from pet_name to pet_names (list)
        notes: str = None,
        assigned_vet_user_id: str = None
    ) -> Dict[str, Any]:
        """
        Book an appointment with proper timezone handling
        
        Args:
            pet_owner_id: Pet owner UUID
            practice_id: Practice UUID 
            date: Local date (e.g., '2025-09-15', 'September 15')
            start_time: Local start time (e.g., '2:30 PM', '14:30')
            timezone: Practice timezone (e.g., 'America/Los_Angeles')
            service: Service type
            pet_names: List of pet names (e.g., ['Amira'], ['Winston'], ['Amira', 'Winston']) - optional
            notes: Additional notes
            assigned_vet_user_id: Specific vet UUID (optional)
        """
        try:
            logger.info(f"🎯 BOOKING APPOINTMENT: {pet_owner_id} at {practice_id} on {date} {start_time} ({timezone})")
            
            # Validate UUIDs
            try:
                practice_uuid = UUID(practice_id)
                pet_owner_uuid = UUID(pet_owner_id)
                assigned_vet_uuid = UUID(assigned_vet_user_id) if assigned_vet_user_id else None
            except ValueError as e:
                logger.error(f"❌ Invalid UUID format: {e}")
                return {
                    "success": False,
                    "message": "I'm having trouble with the booking information. Let me try again."
                }
            
            # Find a user associated with this practice to use as creator
            from ...models_pg.user import User, UserRole
            from sqlalchemy import select as sql_select
            
            # Look for an admin or vet staff user for this practice
            creator_user_result = await self.db.execute(
                sql_select(User).where(
                    User.practice_id == practice_uuid,
                    User.role.in_([UserRole.ADMIN, UserRole.VET_STAFF]),
                    User.is_active == True
                ).limit(1)
            )
            creator_user = creator_user_result.scalar_one_or_none()
            
            if not creator_user:
                logger.error(f"❌ No active admin/vet staff found for practice {practice_id}")
                return {
                    "success": False,
                    "message": "I'm having trouble accessing our scheduling system. Let me get a human to help you."
                }
            
            creator_user_id = creator_user.id
            logger.info(f"👤 Using creator: {creator_user.full_name} ({creator_user_id})")
            
            # TODO: HUGE FIXME - PROPER VET ASSIGNMENT LOGIC NEEDED!
            # Currently defaulting to first available vet in practice for UI display
            # This is a temporary hack to make appointments show up in the dashboard
            # We need to implement proper vet assignment logic based on:
            # - Availability/scheduling
            # - Specialization
            # - Patient history
            # - Load balancing
            # - User preference
            if not assigned_vet_uuid:
                # Find the first available vet for this practice
                default_vet_result = await self.db.execute(
                    sql_select(User).where(
                        User.practice_id == practice_uuid,
                        User.role.in_([UserRole.VET_STAFF, UserRole.ADMIN]),
                        User.is_active == True
                    ).limit(1)
                )
                default_vet = default_vet_result.scalar_one_or_none()
                
                if default_vet:
                    assigned_vet_uuid = default_vet.id
                    logger.warning(f"⚠️ TODO: DEFAULTING to first vet: {default_vet.full_name} ({assigned_vet_uuid}) - NEEDS PROPER ASSIGNMENT LOGIC!")
                else:
                    logger.warning(f"⚠️ No vet found for practice {practice_id} - appointment will not show in vet dashboard")
            
            # Get pet owner details
            pet_owner = await self.pet_owner_repo.get_by_id(pet_owner_uuid)
            if not pet_owner:
                logger.error(f"❌ Pet owner not found: {pet_owner_id}")
                return {
                    "success": False,
                    "message": "I'm having trouble finding your profile. Let me verify your information."
                }
            
            # Parse the local date and time into a timezone-aware datetime
            appointment_datetime = self._parse_local_datetime(date, start_time, timezone)
            if not appointment_datetime:
                logger.error(f"❌ Could not parse date/time: {date} {start_time}")
                return {
                    "success": False,
                    "message": "I'm having trouble understanding that date and time. Could you try again?"
                }
            
            logger.info(f"📅 Parsed appointment datetime: {appointment_datetime} (UTC: {appointment_datetime.astimezone(pytz.UTC)})")
            
            # Check for conflicts if vet is assigned
            if assigned_vet_uuid:
                conflicts = await self.appointment_repo.check_time_conflict(
                    vet_user_id=assigned_vet_uuid,
                    appointment_date=appointment_datetime.astimezone(pytz.UTC),  # Store in UTC
                    duration_minutes=30  # Default 30 minutes
                )
                
                if conflicts:
                    logger.warning(f"⚠️ Time conflict found for vet {assigned_vet_user_id}")
                    return {
                        "success": False,
                        "message": "I'm sorry, that time slot is no longer available. Let me check other options.",
                        "conflicts": [{"appointment_id": str(c.id), "time": str(c.appointment_date)} for c in conflicts]
                    }
            
            # Handle pet selection by name
            from ...repositories_pg.pet_repository import PetRepository
            pet_repo = PetRepository(self.db)
            pets = await pet_repo.get_by_owner_id(pet_owner_uuid)
            
            if not pets:
                return {
                    "success": False,
                    "message": "I don't see any pets in your profile. Let me help you add a pet first before booking an appointment."
                }
            
            # Determine which pets to use (support multiple pets in one appointment)
            pet_uuids = []
            if pet_names:
                # Look for pets by names (case-insensitive)
                matched_pets = []
                not_found_names = []
                
                for requested_name in pet_names:
                    requested_name_lower = requested_name.lower().strip()
                    matching_pet = None
                    for pet in pets:
                        if pet.name.lower().strip() == requested_name_lower:
                            matching_pet = pet
                            break
                    
                    if matching_pet:
                        matched_pets.append(matching_pet)
                        pet_uuids.append(matching_pet.id)
                    else:
                        not_found_names.append(requested_name)
                
                if not_found_names:
                    # Some pet names not found
                    available_names = [pet.name for pet in pets]
                    available_names_str = ", ".join(available_names[:-1]) + f" and {available_names[-1]}" if len(available_names) > 1 else available_names[0]
                    not_found_str = ", ".join(not_found_names)
                    return {
                        "success": False,
                        "message": f"I couldn't find pet(s) named '{not_found_str}'. You have: {available_names_str}. Please specify the correct pet names."
                    }
                
                # Log matched pets
                pet_names_matched = [pet.name for pet in matched_pets]
                pet_names_str = ", ".join(pet_names_matched[:-1]) + f" and {pet_names_matched[-1]}" if len(pet_names_matched) > 1 else pet_names_matched[0]
                logger.info(f"🐕 Using pets by name: {pet_names_str} ({[str(uuid) for uuid in pet_uuids]})")
                
            else:
                # No pet names provided - use all pets by default
                pet_uuids = [pet.id for pet in pets]
                pet_names_all = [pet.name for pet in pets]
                pet_names_str = ", ".join(pet_names_all[:-1]) + f" and {pet_names_all[-1]}" if len(pet_names_all) > 1 else pet_names_all[0]
                logger.info(f"🐕 No pets specified, using all pets: {pet_names_str} ({[str(uuid) for uuid in pet_uuids]})")
            
            # Create the appointment using repository
            appointment = await self.appointment_repo.create_appointment(
                practice_id=practice_uuid,
                pet_owner_id=pet_owner_uuid,
                created_by_user_id=creator_user_id,  # Use found user as creator
                appointment_date=appointment_datetime.astimezone(pytz.UTC),  # Store in UTC
                title=f"{service} Appointment",
                description=f"Phone scheduled {service}" + (f" - {notes}" if notes else ""),
                appointment_type=AppointmentType.CHECKUP,
                duration_minutes=30,  # Default 30 minutes
                assigned_vet_user_id=assigned_vet_uuid,
                pet_ids=pet_uuids
            )
            
            # Format response with local time
            local_time_str = appointment_datetime.strftime("%A, %B %d at %I:%M %p")
            
            logger.info(f"✅ Appointment created: {appointment.id}")
            
            return {
                "success": True,
                "appointment_id": str(appointment.id),
                "message": f"Perfect! I've booked your {service} appointment for {local_time_str}. Let me confirm all the details.",
                "details": {
                    "appointment_id": str(appointment.id),
                    "date_time": local_time_str,
                    "service": service,
                    "practice_id": practice_id,
                    "timezone": timezone
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error booking appointment: {str(e)}")
            logger.exception("Full traceback:")
            return {
                "success": False,
                "message": "I'm sorry, I'm having trouble booking that appointment. Let me try again or get a human to help you."
            }
    
    async def confirm_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Confirm an appointment"""
        try:
            logger.info(f"🎯 CONFIRMING APPOINTMENT: {appointment_id}")
            
            # Validate UUID
            try:
                appointment_uuid = UUID(appointment_id)
            except ValueError:
                logger.error(f"❌ Invalid appointment UUID: {appointment_id}")
                return {
                    "success": False,
                    "message": "I'm having trouble finding that appointment. Let me try again."
                }
            
            # Get the appointment using repository
            appointment = await self.appointment_repo.get_by_id(appointment_uuid)
            
            if not appointment:
                logger.error(f"❌ Appointment not found: {appointment_id}")
                return {
                    "success": False,
                    "message": "I'm having trouble finding that appointment. Let me try again."
                }
            
            # Update status to confirmed using repository
            updated_appointment = await self.appointment_repo.update_status(
                appointment_uuid, 
                AppointmentStatus.CONFIRMED
            )
            
            if not updated_appointment:
                logger.error(f"❌ Failed to update appointment status: {appointment_id}")
                return {
                    "success": False,
                    "message": "I'm having trouble confirming that appointment. Let me try again."
                }
            
            # Format the date for the message (convert from UTC to local time)
            # Note: For proper timezone display, we'd need the practice timezone
            formatted_date = updated_appointment.appointment_date.strftime("%A, %B %d at %I:%M %p")
            
            logger.info(f"✅ Appointment confirmed: {appointment_id}")
            
            return {
                "success": True,
                "message": f"Perfect! Your appointment is confirmed for {formatted_date}. We'll send you a reminder before your visit. Thank you for choosing HelpPet!",
                "appointment_details": {
                    "appointment_id": str(updated_appointment.id),
                    "date_time": formatted_date,
                    "status": updated_appointment.status,
                    "title": updated_appointment.title
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error confirming appointment: {str(e)}")
            logger.exception("Full traceback:")
            return {
                "success": False,
                "message": "I'm having trouble confirming that appointment. Let me try again."
            }
    
    # Helper methods
    def _parse_local_datetime(self, date_str: str, time_str: str, timezone_str: str) -> Optional[datetime]:
        """
        Parse local date and time strings into a timezone-aware datetime
        
        Args:
            date_str: Date string (e.g., '2025-09-15', 'September 15', 'tomorrow')
            time_str: Time string (e.g., '2:30 PM', '14:30', '7:30 PM')
            timezone_str: Timezone (e.g., 'America/Los_Angeles')
        
        Returns:
            Timezone-aware datetime in the specified timezone
        """
        try:
            # Parse date using the same logic as SchedulingService
            parsed_date = self._parse_date_string(date_str)
            
            # Parse time
            parsed_time = self._parse_time_string(time_str)
            if not parsed_time:
                return None
            
            # Combine date and time
            naive_datetime = datetime.combine(parsed_date, parsed_time)
            
            # Make it timezone-aware
            tz = pytz.timezone(timezone_str)
            local_datetime = tz.localize(naive_datetime)
            
            logger.info(f"🕐 Parsed {date_str} {time_str} ({timezone_str}) → {local_datetime}")
            
            return local_datetime
            
        except Exception as e:
            logger.error(f"❌ Error parsing datetime: {e}")
            return None
    
    def _parse_date_string(self, date_str: str) -> date:
        """Parse date string - reuse logic from SchedulingService"""
        import re
        from datetime import date as dt_date
        
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
        
        # Handle ISO format dates like '2025-09-16', '2025/09/16'
        iso_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_str)
        if iso_match:
            year, month, day = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
            try:
                return dt_date(year, month, day)
            except ValueError:
                pass
        
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
                        return parsed_date
                    except ValueError:
                        pass
        
        # Default fallback - tomorrow
        return (now + timedelta(days=1)).date()
    
    def _parse_time_string(self, time_str: str) -> Optional[time]:
        """
        Parse time string into time object
        
        Args:
            time_str: Time string (e.g., '2:30 PM', '14:30', '7:30 PM')
        
        Returns:
            time object or None if parsing fails
        """
        import re
        
        try:
            time_str = time_str.strip().upper()
            
            # Handle 12-hour format with AM/PM
            twelve_hour_match = re.match(r'(\d{1,2}):?(\d{0,2})\s*(AM|PM)', time_str)
            if twelve_hour_match:
                hour = int(twelve_hour_match.group(1))
                minute = int(twelve_hour_match.group(2)) if twelve_hour_match.group(2) else 0
                period = twelve_hour_match.group(3)
                
                # Convert to 24-hour format
                if period == 'AM':
                    if hour == 12:
                        hour = 0
                else:  # PM
                    if hour != 12:
                        hour += 12
                
                return time(hour=hour, minute=minute)
            
            # Handle 24-hour format
            twenty_four_hour_match = re.match(r'(\d{1,2}):(\d{2})', time_str)
            if twenty_four_hour_match:
                hour = int(twenty_four_hour_match.group(1))
                minute = int(twenty_four_hour_match.group(2))
                
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return time(hour=hour, minute=minute)
            
            # Handle simple hour format
            hour_only_match = re.match(r'(\d{1,2})\s*(AM|PM)', time_str)
            if hour_only_match:
                hour = int(hour_only_match.group(1))
                period = hour_only_match.group(2)
                
                # Convert to 24-hour format
                if period == 'AM':
                    if hour == 12:
                        hour = 0
                else:  # PM
                    if hour != 12:
                        hour += 12
                
                return time(hour=hour, minute=0)
            
            logger.warning(f"⚠️ Could not parse time string: {time_str}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error parsing time string '{time_str}': {e}")
            return None
