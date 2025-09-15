"""
Scheduling Service for Phone Operations

Handles availability checking, slot filtering, and timezone conversions for phone calls.
"""

import logging
import pytz
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date, time
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...models_pg.user import User
from ...repositories_pg.scheduling_repository import VetAvailabilityRepository

logger = logging.getLogger(__name__)


class SchedulingService:
    """Service class for scheduling and availability operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_available_times(self, date_str: str, time_preference: str, practice_id: str, timezone: str = "America/Los_Angeles") -> Dict[str, Any]:
        """
        🎯 GET AVAILABLE APPOINTMENT TIMES - PHONE WEBHOOK FUNCTION
        
        This function integrates with our slot-based scheduling system to return
        actual available appointment slots for phone callers.
        
        Args:
            date_str: Raw date input from caller (e.g., '9-14', 'September 14', 'tomorrow')
            time_preference: Time preference (e.g., 'morning', 'afternoon', 'evening')
            practice_id: UUID of the practice to check availability for
            timezone: Practice timezone (e.g., 'America/Los_Angeles', 'America/New_York')
        
        Returns:
            Dict with success status and available appointment times
        """
        logger.info("=" * 80)
        logger.info("🔍 SCHEDULING SERVICE: get_available_times() CALLED")
        logger.info(f"📅 Raw date input: '{date_str}'")
        logger.info(f"⏰ Raw time preference: '{time_preference}'")
        logger.info(f"🌍 Timezone parameter: '{timezone}'")
        logger.info("=" * 80)
        
        try:
            # Step 1: Parse and clean the date
            parsed_date = self._parse_date_string(date_str)
            logger.info(f"✅ Parsed date: {parsed_date}")
            
            # Step 2: Clean time preference
            cleaned_time_pref = self._clean_time_preference(time_preference)
            logger.info(f"✅ Cleaned time preference: {cleaned_time_pref}")
            
            # Step 3: Validate practice_id and timezone
            if not practice_id:
                logger.error("❌ No practice ID provided")
                return {
                    "success": False,
                    "message": "I'm having trouble accessing our scheduling system. Let me get a human to help you."
                }
            
            # Validate timezone parameter
            logger.info(f"🌍 Using timezone: {timezone}")
            try:
                tz = pytz.timezone(timezone)
            except pytz.UnknownTimeZoneError:
                logger.error(f"❌ Invalid timezone: {timezone}")
                return {
                    "success": False,
                    "message": "I'm having trouble with the timezone configuration. Let me get a human to help you."
                }
            
            # Get first available vet for this specific practice
            practice_uuid = UUID(practice_id)
            vet_user_id = await self._get_available_vet(practice_uuid)
            if not vet_user_id:
                logger.error("❌ No available vets found")
                return {
                    "success": False,
                    "message": "I don't see any vets available. Let me check with our staff."
                }
            
            logger.info(f"🏥 Using practice: {practice_uuid}")
            logger.info(f"👩‍⚕️ Using vet: {vet_user_id}")
            
            # Step 4: Get actual available slots using our slot system
            repo = VetAvailabilityRepository(self.db)
            
            # Step 4: Convert local date to UTC date range for database lookup
            # The parsed_date is in local timezone, but availability might be stored in UTC
            local_start = tz.localize(datetime.combine(parsed_date, time.min))
            local_end = tz.localize(datetime.combine(parsed_date, time.max))
            
            # Convert to UTC for database lookup
            utc_start = local_start.astimezone(pytz.UTC)
            utc_end = local_end.astimezone(pytz.UTC)
            
            # We need to check availability for potentially multiple UTC dates
            utc_dates_to_check = set()
            utc_dates_to_check.add(utc_start.date())
            utc_dates_to_check.add(utc_end.date())
            
            logger.info(f"🔍 Local date range: {local_start} to {local_end}")
            logger.info(f"🔍 UTC date range: {utc_start} to {utc_end}")
            logger.info(f"🔍 Checking UTC dates: {utc_dates_to_check}")
            
            # Get slots for all relevant UTC dates
            all_slot_data = []
            for utc_date in utc_dates_to_check:
                logger.info(f"🔍 Calling get_available_slots for UTC date: {utc_date}")
                daily_slots = await repo.get_available_slots(
                    vet_user_id=vet_user_id,
                    practice_id=practice_uuid,
                    date=utc_date,
                    slot_duration_minutes=45
                )
                all_slot_data.extend(daily_slots)
            
            logger.info(f"📊 Raw slots returned: {len(all_slot_data)} slots")
            
            # Step 5: Filter slots to only include those within the requested local date
            valid_slots = []
            for slot in all_slot_data:
                if not slot['available']:
                    continue
                    
                # Convert UTC slot time to local timezone
                start_time = slot['start_time']
                if hasattr(start_time, 'hour'):
                    utc_hour, utc_minute = start_time.hour, start_time.minute
                else:
                    utc_hour, utc_minute = map(int, str(start_time).split(':')[:2])
                
                # Create UTC datetime for this slot (we need to figure out which UTC date this belongs to)
                # Try both UTC dates to see which one makes sense
                for check_utc_date in utc_dates_to_check:
                    utc_slot_datetime = pytz.UTC.localize(
                        datetime.combine(check_utc_date, time(hour=utc_hour, minute=utc_minute))
                    )
                    local_slot_datetime = utc_slot_datetime.astimezone(tz)
                    
                    # Check if this slot falls within our target local date
                    if local_slot_datetime.date() == parsed_date:
                        slot['local_datetime'] = local_slot_datetime
                        valid_slots.append(slot)
                        logger.info(f"  ✅ Valid slot: UTC {utc_hour:02d}:{utc_minute:02d} → Local {local_slot_datetime.strftime('%H:%M on %Y-%m-%d')}")
                        break
                else:
                    logger.info(f"  ❌ Slot outside target date: UTC {utc_hour:02d}:{utc_minute:02d}")
            
            logger.info(f"📊 Valid slots for {parsed_date}: {len(valid_slots)} slots")
            
            # Step 6: Filter by time preference
            filtered_slots = self._filter_slots_by_time_preference(valid_slots, cleaned_time_pref)
            
            logger.info(f"✅ Available slots after filtering: {len(filtered_slots)}")
            
            # Step 7: Format response for phone caller (return max 3 options)
            if filtered_slots:
                formatted_times = []
                for slot in filtered_slots[:3]:  # Return top 3 options
                    formatted_time = self._format_slot_for_caller(slot, parsed_date, timezone)
                    formatted_times.append(formatted_time)
                    logger.info(f"📞 Formatted for caller: {formatted_time}")
                
                message = f"I found {len(formatted_times)} available times on {parsed_date.strftime('%A, %B %d')}: " + ", ".join(formatted_times)
                
                logger.info(f"✅ SUCCESS: Returning {len(formatted_times)} options")
                return {
                    "success": True,
                    "available_times": formatted_times,
                    "message": message,
                    "date": parsed_date.strftime('%Y-%m-%d'),
                    "time_preference": cleaned_time_pref,
                    "timezone_used": timezone,
                    "version": "scheduling_service_v1"
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
    
    # Scheduling helper methods
    def _parse_date_string(self, date_str: str) -> date:
        """
        Parse various date formats from phone callers
        
        Examples: '9-14', 'September 14', 'tomorrow', 'next Friday'
        """
        logger.info(f"🔍 Parsing date string: '{date_str}'")
        
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
                parsed_date = dt_date(year, month, day)
                logger.info(f"✅ Parsed ISO date: {parsed_date}")
                return parsed_date
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
                logger.info(f"✅ Parsed numeric date: {parsed_date}")
                return parsed_date
            except ValueError:
                pass
        
        # Handle weekday names like 'monday', 'tuesday', 'wednesday', etc.
        weekday_names = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1, 'tues': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }
        
        for weekday_name, weekday_num in weekday_names.items():
            if weekday_name in date_str:
                # Find the next occurrence of this weekday
                today = now.date()
                days_ahead = weekday_num - today.weekday()
                
                # Handle "next" prefix (e.g., "next wednesday")
                if 'next' in date_str:
                    # For "next", always go to next week (add 7 days to get to next week)
                    if days_ahead <= 0:
                        days_ahead += 7  # If it's today or past, go to next week
                    else:
                        days_ahead += 7  # If it's later this week, still go to next week
                else:
                    # Normal weekday parsing - if it's today or in the past this week, get next week's occurrence
                    if days_ahead <= 0:
                        days_ahead += 7
                
                target_date = today + timedelta(days=days_ahead)
                logger.info(f"✅ Parsed weekday '{weekday_name}': {target_date}")
                return target_date
        
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
            # Use local_datetime if available (from timezone conversion), otherwise fall back to UTC time
            if 'local_datetime' in slot:
                # Use the converted local time
                hour = slot['local_datetime'].hour
                logger.info(f"  Slot at LOCAL hour {hour} ({'morning' if 6 <= hour < 12 else 'afternoon' if 12 <= hour < 17 else 'evening' if 17 <= hour < 21 else 'other'})")
            else:
                # Fallback to UTC time (for backward compatibility)
                start_time = slot['start_time']
                if hasattr(start_time, 'hour'):
                    hour = start_time.hour
                else:
                    hour = int(str(start_time).split(':')[0])
                logger.info(f"  Slot at UTC hour {hour} ({'morning' if 6 <= hour < 12 else 'afternoon' if 12 <= hour < 17 else 'evening' if 17 <= hour < 21 else 'other'})")
            
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
