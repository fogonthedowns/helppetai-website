"""
REFACTORED Scheduling Service using Unix timestamps

This implements the voice input → Unix timestamp flow from suggestion.txt:
1. Parse voice input with timezone context
2. Convert to UTC Unix timestamp 
3. Store in DB
4. Convert back to local timezone for voice output

🔑 KEY PRINCIPLE: Store in UTC, display in local timezones
"""

import logging
import pytz
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date, time
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from ...models_pg.user import User
from ...models_pg.practice import VeterinaryPractice
from ...models_pg.scheduling_unix import VetAvailability
# AppointmentUnix is deprecated - voice system uses regular AppointmentRepository
from ...repositories_pg.scheduling_repository_unix import VetAvailabilityUnixRepository
# AppointmentUnixRepository is deprecated - voice system uses regular AppointmentRepository

logger = logging.getLogger(__name__)


class UnixTimestampSchedulingService:
    """
    REFACTORED: Scheduling service using Unix timestamps
    
    This follows the exact recommendations from suggestion.txt
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_available_times(
        self, 
        date_str: str, 
        time_preference: str, 
        practice_id: str, 
        timezone: str = "America/Los_Angeles"
    ) -> Dict[str, Any]:
        """
        🎯 GET AVAILABLE TIMES - UNIX TIMESTAMP VERSION
        
        Voice input flow:
        1. "9pm Oct 3 PST" → Parse with timezone
        2. Convert to UTC Unix timestamp  
        3. Query DB (simple UTC range queries)
        4. Convert results back to local timezone
        5. Speak local times to user
        
        Args:
            date_str: "Oct 3", "tomorrow", "9-14"
            time_preference: "morning", "afternoon", "evening"
            practice_id: UUID string
            timezone: Practice timezone ("America/Los_Angeles")
        """
        logger.info("=" * 80)
        logger.info("🔍 UNIX TIMESTAMP SCHEDULING: get_available_times() CALLED")
        logger.info(f"📅 Voice date input: '{date_str}'")
        logger.info(f"⏰ Voice time preference: '{time_preference}'")
        logger.info(f"🌍 Practice timezone: '{timezone}'")
        logger.info("=" * 80)
        
        try:
            # Step 1: Parse voice input with timezone context
            local_date = self._parse_voice_date(date_str, timezone)
            time_range = self._parse_time_preference(time_preference)
            
            logger.info(f"✅ Parsed local date: {local_date}")
            logger.info(f"✅ Time preference range: {time_range}")
            
            # Step 2: Convert local date + time range to UTC timestamps
            tz = pytz.timezone(timezone)
            
            # Create UTC timestamp range for the entire local day
            local_start_of_day = tz.localize(
                datetime.combine(local_date, time.min)
            )
            local_end_of_day = tz.localize(
                datetime.combine(local_date, time.max)
            )
            
            utc_day_start = local_start_of_day.astimezone(pytz.UTC)
            utc_day_end = local_end_of_day.astimezone(pytz.UTC)
            
            logger.info(f"🌐 UTC day range: {utc_day_start} to {utc_day_end}")
            
            # Step 3: Query available slots using simple UTC range
            practice_uuid = UUID(practice_id)
            available_slots = await self._get_utc_availability_slots(
                practice_uuid, utc_day_start, utc_day_end, time_range, timezone
            )
            
            # Step 4: Convert UTC results back to local timezone for voice output
            local_slots = []
            for slot in available_slots:
                local_start = slot['utc_start'].astimezone(tz)
                local_end = slot['utc_end'].astimezone(tz)
                
                local_slots.append({
                    'start_time': local_start.strftime('%-I:%M %p'),
                    'end_time': local_end.strftime('%-I:%M %p'),
                    'vet_name': slot['vet_name'],
                    'available': slot['available'],
                    'local_datetime': local_start.isoformat(),
                    'utc_datetime': slot['utc_start'].isoformat()
                })
            
            logger.info(f"✅ Found {len(local_slots)} available slots")
            
            # Step 5: Generate voice-friendly response
            if local_slots:
                response_message = self._generate_availability_message(local_slots, local_date)
                return {
                    "success": True,
                    "message": response_message,
                    "available_times": local_slots,
                    "date": local_date.isoformat(),
                    "timezone": timezone
                }
            else:
                return {
                    "success": False,
                    "message": f"I don't see any available appointments on {local_date.strftime('%A, %B %d')}. Would you like me to check other dates?",
                    "available_times": [],
                    "date": local_date.isoformat(),
                    "timezone": timezone
                }
                
        except Exception as e:
            logger.error(f"❌ Error in get_available_times: {e}")
            return {
                "success": False,
                "message": "I'm having trouble checking availability. Let me get a human to help you.",
                "error": str(e)
            }
    
    async def book_appointment(
        self,
        pet_owner_id: str,
        practice_id: str,
        date_str: str,
        time_str: str,
        timezone: str,
        service: str = "General Checkup",
        pet_names: List[str] = None,
        notes: Optional[str] = None,
        assigned_vet_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        🎯 BOOK APPOINTMENT - UNIX TIMESTAMP VERSION
        
        Voice booking flow:
        1. "9pm Oct 3 PST" → Parse with timezone
        2. Convert to UTC Unix timestamp
        3. Store UTC timestamp in DB
        4. Confirm with local time to user
        
        Args:
            date_str: "Oct 3", "tomorrow"
            time_str: "9pm", "21:00"
            timezone: Practice timezone
        """
        logger.info("=" * 80)
        logger.info("🔍 UNIX TIMESTAMP BOOKING: book_appointment() CALLED")
        logger.info(f"📅 Voice date: '{date_str}'")
        logger.info(f"⏰ Voice time: '{time_str}'")
        logger.info(f"🌍 Timezone: '{timezone}'")
        logger.info("=" * 80)
        
        try:
            # Step 1: Parse voice input with timezone context
            local_date = self._parse_voice_date(date_str, timezone)
            local_time = self._parse_voice_time(time_str)
            
            tz = pytz.timezone(timezone)
            local_datetime = tz.localize(
                datetime.combine(local_date, local_time)
            )
            
            # Step 2: Convert to UTC Unix timestamp for storage
            utc_datetime = local_datetime.astimezone(pytz.UTC)
            
            logger.info(f"✅ Local appointment time: {local_datetime}")
            logger.info(f"🌐 UTC storage time: {utc_datetime}")
            
            # Step 3: Select an available vet for this time (capacity-aware across vets)
            practice_uuid = UUID(practice_id)
            selected_vet_uuid: Optional[UUID] = None

            if assigned_vet_user_id:
                candidate_vet_uuid = UUID(assigned_vet_user_id)
                appointment_end = utc_datetime + timedelta(minutes=30)

                # Ensure specified vet has an availability window and no conflict
                vet_avail_query = select(VetAvailability).where(
                    VetAvailability.practice_id == practice_uuid,
                    VetAvailability.vet_user_id == candidate_vet_uuid,
                    VetAvailability.start_at <= utc_datetime,
                    VetAvailability.end_at >= appointment_end,
                    VetAvailability.is_active == True,
                )
                vet_avail_result = await self.db.execute(vet_avail_query)
                if vet_avail_result.scalars().first() is not None:
                    vet_conflict_query = select(AppointmentUnix).where(
                        AppointmentUnix.practice_id == practice_uuid,
                        AppointmentUnix.assigned_vet_user_id == candidate_vet_uuid,
                        AppointmentUnix.appointment_at < appointment_end,
                        AppointmentUnix.appointment_at + timedelta(minutes=30) > utc_datetime,
                        AppointmentUnix.status.notin_(['CANCELLED', 'NO_SHOW', 'COMPLETED'])
                    )
                    vet_conflict_result = await self.db.execute(vet_conflict_query)
                    if vet_conflict_result.scalars().first() is None:
                        selected_vet_uuid = candidate_vet_uuid

                if selected_vet_uuid is None:
                    local_time_str = local_datetime.strftime('%-I:%M %p on %A, %B %d')
                    return {
                        "success": False,
                        "message": f"The selected veterinarian is not available at {local_time_str}. Would you like me to find another available vet at that time?",
                        "local_datetime": local_datetime.isoformat(),
                        "utc_datetime": utc_datetime.isoformat(),
                    }
            else:
                selected_vet_uuid = await self._find_available_vet_for_time(
                    practice_uuid, utc_datetime, duration_minutes=30
                )
                if selected_vet_uuid is None:
                    local_time_str = local_datetime.strftime('%-I:%M %p on %A, %B %d')
                    return {
                        "success": False,
                        "message": f"That time slot at {local_time_str} is not available. Would you like me to suggest other times?",
                        "local_datetime": local_datetime.isoformat(),
                        "utc_datetime": utc_datetime.isoformat(),
                    }

            # Step 4: Create appointment using CLEAN repository with selected vet
            assigned_vet_user_id = str(selected_vet_uuid)
            
            # Use clean repository for appointment creation
            appointment_repo = AppointmentUnixRepository(self.db)
            appointment = await appointment_repo.create_from_voice_booking(
                practice_id=UUID(practice_id),
                pet_owner_id=UUID(pet_owner_id),
                assigned_vet_user_id=UUID(assigned_vet_user_id),
                created_by_user_id=UUID(assigned_vet_user_id),  # For now
                local_date_str=date_str,
                local_time_str=time_str,
                timezone_str=timezone,
                duration_minutes=30,
                title=f"{service} - {', '.join(pet_names) if pet_names else 'Pet'}",
                appointment_type=service.upper().replace(' ', '_'),
                notes=notes
            )
            
            # Step 6: Confirm with local time for user
            local_confirmation_time = local_datetime.strftime('%-I:%M %p on %A, %B %d')
            
            logger.info(f"✅ Appointment booked: {appointment.id}")
            
            return {
                "success": True,
                "message": f"Perfect! I've scheduled your {service} appointment for {local_confirmation_time}.",
                "appointment_id": str(appointment.id),
                "local_datetime": local_datetime.isoformat(),
                "utc_datetime": utc_datetime.isoformat(),
                "confirmation_time": local_confirmation_time,
                "pet_names": pet_names or []
            }
            
        except Exception as e:
            logger.error(f"❌ Error booking appointment: {e}")
            return {
                "success": False,
                "message": "I'm having trouble booking that appointment. Let me get a human to help you.",
                "error": str(e)
            }
    
    async def _get_utc_availability_slots(
        self,
        practice_id: UUID,
        utc_start: datetime,
        utc_end: datetime,
        time_preference_range: tuple,
        timezone_str: str,
        slot_duration_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get available slots using CLEAN Unix timestamp repositories
        """
        availability_repo = VetAvailabilityUnixRepository(self.db)
        
        # Get all availability for the practice in the UTC range
        availability_records = await availability_repo.get_by_practice_and_date_range(
            practice_id, utc_start, utc_end
        )
        
        if not availability_records:
            logger.info(f"🔧 NO UNIX TIMESTAMP AVAILABILITY - Create availability first!")
            return []
        
        # Use repository to get slots for each vet
        all_slots = []
        processed_vets = set()
        
        for availability in availability_records:
            if availability.vet_user_id not in processed_vets:
                vet_slots = await availability_repo.get_available_slots(
                    availability.vet_user_id,
                    practice_id,
                    utc_start,
                    utc_end,
                    slot_duration_minutes,
                    timezone_str
                )
                
                # Filter by time preference
                for slot in vet_slots:
                    local_time = slot['start_time']
                    if (time_preference_range[0] <= local_time <= time_preference_range[1]):
                        # Get vet name
                        vet_name = await self._get_vet_name(slot['vet_user_id'])
                        
                        all_slots.append({
                            'utc_start': slot['utc_start'],
                            'utc_end': slot['utc_end'],
                            'vet_user_id': slot['vet_user_id'],
                            'vet_name': vet_name,
                            'available': slot['available'],
                            'availability_type': slot['availability_type']
                        })
                
                processed_vets.add(availability.vet_user_id)
        
        # Sort by UTC start time
        all_slots.sort(key=lambda x: x['utc_start'])
        
        return all_slots
    
    async def _check_utc_slot_availability(
        self,
        practice_id: UUID,
        utc_appointment_time: datetime,
        duration_minutes: int = 30
    ) -> bool:
        """Capacity-aware check: True if at least one vet is free at this time."""
        appointment_end = utc_appointment_time + timedelta(minutes=duration_minutes)

        # Find vets whose availability windows cover the requested slot
        available_vets_query = (
            select(VetAvailability.vet_user_id)
            .where(
                VetAvailability.practice_id == practice_id,
                VetAvailability.start_at <= utc_appointment_time,
                VetAvailability.end_at >= appointment_end,
                VetAvailability.is_active == True,
            )
            .distinct()
        )

        result = await self.db.execute(available_vets_query)
        vet_ids = [row[0] for row in result.all()]
        if not vet_ids:
            return False

        # Return True if any available vet has no conflicting appointment at that time
        for vet_id in vet_ids:
            vet_conflict_query = select(AppointmentUnix).where(
                AppointmentUnix.practice_id == practice_id,
                AppointmentUnix.assigned_vet_user_id == vet_id,
                AppointmentUnix.appointment_at < appointment_end,
                AppointmentUnix.appointment_at + timedelta(minutes=duration_minutes) > utc_appointment_time,
                AppointmentUnix.status.notin_(['CANCELLED', 'NO_SHOW', 'COMPLETED'])
            )
            vet_conflict_result = await self.db.execute(vet_conflict_query)
            if vet_conflict_result.scalars().first() is None:
                return True

        return False

    async def _find_available_vet_for_time(
        self,
        practice_id: UUID,
        utc_appointment_time: datetime,
        duration_minutes: int = 30,
    ) -> Optional[UUID]:
        """Return an available vet ID for the requested time, or None if none available."""
        appointment_end = utc_appointment_time + timedelta(minutes=duration_minutes)

        available_vets_query = (
            select(VetAvailability.vet_user_id)
            .where(
                VetAvailability.practice_id == practice_id,
                VetAvailability.start_at <= utc_appointment_time,
                VetAvailability.end_at >= appointment_end,
                VetAvailability.is_active == True,
            )
            .distinct()
        )

        result = await self.db.execute(available_vets_query)
        vet_ids = [row[0] for row in result.all()]
        if not vet_ids:
            return None

        for vet_id in vet_ids:
            vet_conflict_query = select(AppointmentUnix).where(
                AppointmentUnix.practice_id == practice_id,
                AppointmentUnix.assigned_vet_user_id == vet_id,
                AppointmentUnix.appointment_at < appointment_end,
                AppointmentUnix.appointment_at + timedelta(minutes=duration_minutes) > utc_appointment_time,
                AppointmentUnix.status.notin_(['CANCELLED', 'NO_SHOW', 'COMPLETED'])
            )
            vet_conflict_result = await self.db.execute(vet_conflict_query)
            if vet_conflict_result.scalars().first() is None:
                return vet_id

        return None
    
    def _parse_voice_date(self, date_str: str, timezone_str: str) -> date:
        """
        Parse voice date input with timezone context
        
        Examples: 'today', 'tomorrow', 'Oct 3', '9-14'
        """
        from dateutil import parser
        
        # Get current date in practice timezone
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        
        date_str = date_str.lower().strip()
        
        if 'today' in date_str:
            return now.date()
        elif 'tomorrow' in date_str:
            return (now + timedelta(days=1)).date()
        elif 'next week' in date_str:
            return (now + timedelta(days=7)).date()
        
        # Handle ISO format dates
        iso_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_str)
        if iso_match:
            year, month, day = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
            return date(year, month, day)
        
        # Handle numeric formats like '9-14', '9/14'
        numeric_match = re.search(r'(\d{1,2})[-/](\d{1,2})', date_str)
        if numeric_match:
            month, day = int(numeric_match.group(1)), int(numeric_match.group(2))
            year = now.year
            try:
                parsed_date = date(year, month, day)
                if parsed_date < now.date():
                    parsed_date = date(year + 1, month, day)
                return parsed_date
            except ValueError:
                pass
        
        # Try dateutil parser as fallback
        try:
            parsed = parser.parse(date_str)
            return parsed.date()
        except:
            # Default to tomorrow if parsing fails
            return (now + timedelta(days=1)).date()
    
    def _parse_voice_time(self, time_str: str) -> time:
        """Parse voice time input"""
        from dateutil import parser
        
        try:
            parsed = parser.parse(time_str)
            return parsed.time()
        except:
            # Default to 9 AM if parsing fails
            return time(9, 0)
    
    def _parse_time_preference(self, time_preference: str) -> tuple[time, time]:
        """Parse time preference into time range"""
        pref = time_preference.lower().strip()
        
        if 'morning' in pref:
            return (time(6, 0), time(12, 0))
        elif 'afternoon' in pref:
            return (time(12, 0), time(17, 0))
        elif 'evening' in pref:
            return (time(17, 0), time(21, 0))
        else:
            # Default to all day
            return (time(6, 0), time(21, 0))
    
    async def _get_available_vet(self, practice_id: UUID) -> UUID:
        """Get first available vet for the practice"""
        query = select(User.id).where(
            User.practice_id == practice_id,
            User.role == "VET",
            User.is_active == True
        ).limit(1)
        
        result = await self.db.execute(query)
        vet_id = result.scalar()
        
        if not vet_id:
            raise ValueError("No available vets found")
        
        return vet_id
    
    async def _get_vet_name(self, vet_user_id: UUID) -> str:
        """Get vet display name"""
        query = select(User.full_name).where(User.id == vet_user_id)
        result = await self.db.execute(query)
        name = result.scalar()
        return name or "Dr. Vet"
    
    def _generate_availability_message(self, slots: List[Dict], local_date: date) -> str:
        """Generate voice-friendly availability message"""
        date_str = local_date.strftime('%A, %B %d')
        
        if not slots:
            return f"I don't see any available appointments on {date_str}."
        
        available_slots = [s for s in slots if s['available']]
        
        if not available_slots:
            return f"All slots are booked on {date_str}. Would you like me to check other dates?"
        
        if len(available_slots) == 1:
            slot = available_slots[0]
            return f"I have one appointment available on {date_str} at {slot['start_time']} with {slot['vet_name']}. Would you like to book it?"
        
        # Multiple slots
        times = [s['start_time'] for s in available_slots[:3]]  # Show first 3
        times_str = ', '.join(times[:-1]) + f" and {times[-1]}" if len(times) > 1 else times[0]
        
        return f"I have several appointments available on {date_str}. The earliest times are {times_str}. Which time works best for you?"

    # ---------------------------------------------------------------------
    # Unix-native implementations for voice endpoints (migration-safe)
    # ---------------------------------------------------------------------

    async def get_first_available_next_3_days(
        self,
        time_preference: str,
        practice_id: str,
        timezone: str = "America/Los_Angeles",
    ) -> Dict[str, Any]:
        tz = pytz.timezone(timezone)
        today = datetime.now(tz).date()
        next_3_days = [today + timedelta(days=i + 1) for i in range(3)]
        practice_uuid = UUID(practice_id)
        time_range = self._parse_time_preference(time_preference)

        results: List[Dict[str, Any]] = []
        for check_date in next_3_days:
            slot = await self._first_available_for_day(practice_uuid, check_date, time_range, timezone)
            if slot:
                results.append(slot)

        if results:
            message = "I found the first available appointments in the next 3 days: " + \
                ", ".join([f"{r['time']} on {r['formatted_date']}" for r in results])
            return {
                "success": True,
                "appointments": results,
                "message": message,
                "time_preference": time_preference,
                "timezone_used": timezone,
                "version": "unix_next_3_days_v1",
            }
        return {
            "success": False,
            "message": "I'm sorry, we don't have any appointments available in the next 3 days. Would you like me to check next week?",
        }

    async def get_first_available_next_week(
        self,
        time_preference: str,
        practice_id: str,
        timezone: str = "America/Los_Angeles",
        preferred_days: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if preferred_days is None:
            preferred_days = ["tuesday", "wednesday"]

        tz = pytz.timezone(timezone)
        today = datetime.now(tz).date()
        # Next Monday (weekday: Monday=0)
        days_until_next_monday = (7 - today.weekday()) % 7 or 7
        next_monday = today + timedelta(days=days_until_next_monday)
        week_dates = [next_monday + timedelta(days=i) for i in range(7)]

        practice_uuid = UUID(practice_id)
        time_range = self._parse_time_preference(time_preference)

        results: List[Dict[str, Any]] = []
        # Try preferred days first
        for d in week_dates:
            if d.strftime('%A').lower() in [p.lower() for p in preferred_days]:
                slot = await self._first_available_for_day(practice_uuid, d, time_range, timezone)
                if slot:
                    slot["is_preferred_day"] = True
                    results.append(slot)

        if results:
            message = "Great news! I found appointments on your preferred days next week: " + \
                ", ".join([f"{r['time']} on {r['formatted_date']}" for r in results])
            return {
                "success": True,
                "appointments": results,
                "message": message,
                "time_preference": time_preference,
                "preferred_days_used": True,
                "timezone_used": timezone,
                "version": "unix_next_week_v1",
            }

        # Fallback to any day (limit 3)
        all_results: List[Dict[str, Any]] = []
        for d in week_dates:
            slot = await self._first_available_for_day(practice_uuid, d, time_range, timezone)
            if slot:
                slot["is_preferred_day"] = False
                all_results.append(slot)
                if len(all_results) >= 3:
                    break

        if all_results:
            message = "I found these available appointments next week: " + \
                ", ".join([f"{r['time']} on {r['formatted_date']}" for r in all_results])
            return {
                "success": True,
                "appointments": all_results,
                "message": message,
                "time_preference": time_preference,
                "preferred_days_used": False,
                "timezone_used": timezone,
                "version": "unix_next_week_v1",
            }
        return {
            "success": False,
            "message": "I'm sorry, we don't have any appointments available next week. Would you like me to check the following week?",
        }

    async def get_first_available_next_month(
        self,
        time_preference: str,
        practice_id: str,
        timezone: str = "America/Los_Angeles",
        preferred_days: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if preferred_days is None:
            preferred_days = ["tuesday", "wednesday"]

        tz = pytz.timezone(timezone)
        today = datetime.now(tz).date()
        # First day of next month
        if today.month == 12:
            next_month_start = date(today.year + 1, 1, 1)
        else:
            next_month_start = date(today.year, today.month + 1, 1)
        # Last day of next month
        if next_month_start.month == 12:
            next_month_end = date(next_month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            next_month_end = date(next_month_start.year, next_month_start.month + 1, 1) - timedelta(days=1)

        practice_uuid = UUID(practice_id)
        time_range = self._parse_time_preference(time_preference)

        preferred: List[Dict[str, Any]] = []
        d = next_month_start
        while d <= next_month_end and len(preferred) < 3:
            if d.strftime('%A').lower() in [p.lower() for p in preferred_days]:
                slot = await self._first_available_for_day(practice_uuid, d, time_range, timezone)
                if slot:
                    slot["is_preferred_day"] = True
                    preferred.append(slot)
            d += timedelta(days=1)

        if preferred:
            month_name = next_month_start.strftime('%B')
            message = f"Great news! I found appointments on your preferred days in {month_name}: " + \
                ", ".join([f"{r['time']} on {r['formatted_date']}" for r in preferred])
            return {
                "success": True,
                "appointments": preferred,
                "message": message,
                "time_preference": time_preference,
                "preferred_days_used": True,
                "timezone_used": timezone,
                "version": "unix_next_month_v1",
            }

        # Otherwise scan first 14 days, limit 3
        others: List[Dict[str, Any]] = []
        d = next_month_start
        scanned = 0
        while d <= next_month_end and scanned < 14 and len(others) < 3:
            slot = await self._first_available_for_day(practice_uuid, d, time_range, timezone)
            if slot:
                slot["is_preferred_day"] = False
                others.append(slot)
            d += timedelta(days=1)
            scanned += 1

        if others:
            month_name = next_month_start.strftime('%B')
            message = f"I found these available appointments in {month_name}: " + \
                ", ".join([f"{r['time']} on {r['formatted_date']}" for r in others])
            return {
                "success": True,
                "appointments": others,
                "message": message,
                "time_preference": time_preference,
                "preferred_days_used": False,
                "timezone_used": timezone,
                "version": "unix_next_month_v1",
            }

        month_name = next_month_start.strftime('%B')
        return {
            "success": False,
            "message": f"I'm sorry, we don't have any {time_preference} appointments available in {month_name}. Would you like me to check a different month?",
        }

    async def get_first_available_flexible(
        self,
        time_preference: str,
        practice_id: str,
        timezone: str = "America/Los_Angeles",
        weeks_from_now: Optional[int] = None,
        specific_week_of_month: Optional[int] = None,
        target_month_offset: Optional[int] = None,
        preferred_days: Optional[List[str]] = None,
        date_range_start: Optional[str] = None,
        date_range_end: Optional[str] = None,
    ) -> Dict[str, Any]:
        tz = pytz.timezone(timezone)
        today = datetime.now(tz).date()
        start_date, end_date, range_desc = self._calculate_flexible_date_range_unix(
            today,
            weeks_from_now,
            specific_week_of_month,
            target_month_offset,
            date_range_start,
            date_range_end,
            timezone,
        )

        if preferred_days is None:
            preferred_days = ["tuesday", "wednesday"]

        practice_uuid = UUID(practice_id)
        time_range = self._parse_time_preference(time_preference)

        preferred: List[Dict[str, Any]] = []
        current = start_date
        while current <= end_date and len(preferred) < 3:
            if current.strftime('%A').lower() in [p.lower() for p in preferred_days]:
                slot = await self._first_available_for_day(practice_uuid, current, time_range, timezone)
                if slot:
                    preferred.append(slot)
            current += timedelta(days=1)

        if preferred:
            message = f"Great news! I found appointments on your preferred days {range_desc}: " + \
                ", ".join([f"{r['time']} on {r['formatted_date']}" for r in preferred])
            return {
                "success": True,
                "appointments": preferred,
                "message": message,
                "time_preference": time_preference,
                "preferred_days_used": True,
                "date_range_start": start_date.strftime('%Y-%m-%d'),
                "date_range_end": end_date.strftime('%Y-%m-%d'),
                "range_description": range_desc,
                "timezone_used": timezone,
                "version": "unix_flexible_v1",
            }

        # Fallback: scan up to 21 days, limit 3
        results: List[Dict[str, Any]] = []
        current = start_date
        scanned = 0
        while current <= end_date and scanned < 21 and len(results) < 3:
            slot = await self._first_available_for_day(practice_uuid, current, time_range, timezone)
            if slot:
                results.append(slot)
            current += timedelta(days=1)
            scanned += 1

        if results:
            message = f"I found these available appointments {range_desc}: " + \
                ", ".join([f"{r['time']} on {r['formatted_date']}" for r in results])
            return {
                "success": True,
                "appointments": results,
                "message": message,
                "time_preference": time_preference,
                "preferred_days_used": False,
                "date_range_start": start_date.strftime('%Y-%m-%d'),
                "date_range_end": end_date.strftime('%Y-%m-%d'),
                "range_description": range_desc,
                "timezone_used": timezone,
                "version": "unix_flexible_v1",
            }
        return {
            "success": False,
            "message": f"I'm sorry, we don't have any {time_preference} appointments available {range_desc}. Would you like me to check a different time period?",
        }

    async def _first_available_for_day(
        self,
        practice_id: UUID,
        local_date: date,
        time_range: tuple,
        timezone: str,
    ) -> Optional[Dict[str, Any]]:
        tz = pytz.timezone(timezone)
        local_start = tz.localize(datetime.combine(local_date, time.min))
        local_end = tz.localize(datetime.combine(local_date, time.max))
        utc_start = local_start.astimezone(pytz.UTC)
        utc_end = local_end.astimezone(pytz.UTC)
        
        slots = await self._get_utc_availability_slots(practice_id, utc_start, utc_end, time_range, timezone)
        available = [s for s in slots if s.get('available')]
        if not available:
            return None
        first = sorted(available, key=lambda s: s['utc_start'])[0]
        local_time = first['utc_start'].astimezone(tz)
        return {
            "date": local_date.strftime('%Y-%m-%d'),
            "day_name": local_date.strftime('%A'),
            "formatted_date": local_date.strftime('%A, %B %d'),
            "time": local_time.strftime('%-I:%M %p'),
            "slot_data": first,
        }

    def _parse_simple_date(self, date_str: str, timezone_str: str = "America/Los_Angeles") -> date:
        # Try ISO
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            pass
        # Fallback to dateutil
        try:
            from dateutil import parser
            return parser.parse(date_str).date()
        except Exception:
            tz = pytz.timezone(timezone_str)
            return (datetime.now(tz) + timedelta(days=1)).date()

    def _calculate_flexible_date_range_unix(
        self,
        today: date,
        weeks_from_now: Optional[int],
        specific_week_of_month: Optional[int],
        target_month_offset: Optional[int],
        date_range_start: Optional[str],
        date_range_end: Optional[str],
        timezone_str: str,
    ) -> tuple[date, date, str]:
        # Custom range
        if date_range_start and date_range_end:
            start_date = self._parse_simple_date(date_range_start, timezone_str)
            end_date = self._parse_simple_date(date_range_end, timezone_str)
            return start_date, end_date, f"between {start_date.strftime('%B %d')} and {end_date.strftime('%B %d')}"
        # Weeks from now
        if weeks_from_now is not None:
            start_date = today + timedelta(weeks=weeks_from_now)
            end_date = start_date + timedelta(days=6)
            if weeks_from_now == 1:
                return start_date, end_date, "next week"
            elif weeks_from_now == 2:
                return start_date, end_date, "in 2 weeks"
            else:
                return start_date, end_date, f"in {weeks_from_now} weeks"
        # Specific week of target month
        if specific_week_of_month is not None and target_month_offset is not None:
            target_year = today.year
            target_month = today.month + target_month_offset
            while target_month > 12:
                target_month -= 12
                target_year += 1
            while target_month < 1:
                target_month += 12
                target_year -= 1
            first_day = date(target_year, target_month, 1)
            days_to_monday = (7 - first_day.weekday()) % 7
            first_monday = first_day + timedelta(days=days_to_monday)
            start_date = first_monday + timedelta(weeks=specific_week_of_month - 1)
            end_date = start_date + timedelta(days=6)
            month_name = first_day.strftime('%B')
            if target_month_offset == 0:
                month_desc = f"this {month_name}"
            elif target_month_offset == 1:
                month_desc = f"next {month_name}"
            else:
                month_desc = f"{month_name} {target_year}"
            return start_date, end_date, f"in week {specific_week_of_month} of {month_desc}"
        # Entire target month
        if target_month_offset is not None:
            target_year = today.year
            target_month = today.month + target_month_offset
            while target_month > 12:
                target_month -= 12
                target_year += 1
            while target_month < 1:
                target_month += 12
                target_year -= 1
            start_date = date(target_year, target_month, 1)
            if target_month == 12:
                end_date = date(target_year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(target_year, target_month + 1, 1) - timedelta(days=1)
            month_name = start_date.strftime('%B')
            if target_month_offset == 0:
                month_desc = f"this {month_name}"
            elif target_month_offset == 1:
                month_desc = f"next {month_name}"
            else:
                month_desc = f"{month_name} {target_year}"
            return start_date, end_date, f"in {month_desc}"
        # Default
        start_date = today + timedelta(days=1)
        end_date = today + timedelta(days=7)
        return start_date, end_date, "in the next week"
