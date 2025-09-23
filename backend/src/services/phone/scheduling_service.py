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
                    slot_duration_minutes=45,
                    timezone_str=timezone
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
            # Use word boundary regex to ensure the weekday is isolated (not part of another word)
            weekday_pattern = r'\b' + re.escape(weekday_name) + r'\b'
            if re.search(weekday_pattern, date_str):
                # Additional validation: check if this looks like garbled input
                # Split the string and see if we have reasonable context around the weekday
                words = date_str.split()
                weekday_word_found = False
                has_reasonable_context = False
                
                for word in words:
                    # Clean the word of punctuation
                    clean_word = re.sub(r'[^\w]', '', word.lower())
                    if clean_word == weekday_name:
                        weekday_word_found = True
                        # Check if other words in the sentence are reasonable English words or common date-related terms
                        other_words = [re.sub(r'[^\w]', '', w.lower()) for w in words if re.sub(r'[^\w]', '', w.lower()) != weekday_name]
                        
                        # Check if any words look like obvious garbage (contains non-alphabetic characters, gibberish)
                        has_garbage = False
                        for word in other_words:
                            # Skip empty words and very short words
                            if not word or len(word) <= 2:
                                continue
                            # Check for obvious garbage: contains numbers, special chars, or looks like gibberish
                            if any(char.isdigit() for char in word) or any(not char.isalpha() for char in word):
                                continue  # Skip words with numbers/special chars, they might be valid
                            # Check for gibberish: consecutive consonants or very unusual patterns
                            if len(word) >= 3 and self._looks_like_gibberish(word):
                                has_garbage = True
                                break
                        
                        # Accept if no obvious garbage is found
                        if not has_garbage:
                            has_reasonable_context = True
                        break
                
                if weekday_word_found and has_reasonable_context:
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
                # Look for day number (including ordinals like 20th, 1st, 2nd, 3rd)
                day_match = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\b', date_str)
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
    
    def _looks_like_gibberish(self, word: str) -> bool:
        """
        Check if a word looks like gibberish/random characters
        
        This is a simple heuristic that looks for patterns that are uncommon in English:
        - Too many consecutive consonants
        - Unusual character patterns
        """
        word = word.lower()
        
        # Very short words are probably not gibberish
        if len(word) < 3:
            return False
        
        # Check for too many consecutive consonants (more than 3 is unusual in English)
        consonants = 'bcdfghjklmnpqrstvwxyz'
        consecutive_consonants = 0
        max_consecutive_consonants = 0
        
        for char in word:
            if char in consonants:
                consecutive_consonants += 1
                max_consecutive_consonants = max(max_consecutive_consonants, consecutive_consonants)
            else:
                consecutive_consonants = 0
        
        # If more than 3 consecutive consonants, likely gibberish
        if max_consecutive_consonants > 3:
            return True
        
        # Check for unusual patterns like "xyz", "qzx", etc.
        unusual_sequences = ['xyz', 'qzx', 'zxc', 'qwerty', 'asdf', 'zzzz']
        for seq in unusual_sequences:
            if seq in word:
                return True
        
        return False
    
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
        
        IMPORTANT: Database stores times in UTC, we convert to practice local time for display
        
        Example: "2:30 PM" or "10:00 AM" (converted to practice local time)
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
            
            logger.info(f"🌍 UTC→Local conversion: {utc_hour:02d}:{utc_minute:02d} UTC → {hour:02d}:{minute:02d} {practice_timezone}")
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
    
    async def get_first_available_next_3_days(self, time_preference: str, practice_id: str, timezone: str = "America/Los_Angeles") -> Dict[str, Any]:
        """
        🎯 GET FIRST AVAILABLE APPOINTMENTS - NEXT 3 DAYS
        
        Returns the first available appointment for each of the next 3 days.
        If multiple slots are available on a day, returns only the first one.
        
        Args:
            time_preference: Time preference (e.g., 'morning', 'afternoon', 'evening', 'any time')
            practice_id: UUID of the practice to check availability for
            timezone: Practice timezone (e.g., 'America/Los_Angeles', 'America/New_York')
        
        Returns:
            Dict with success status and first available appointments for next 3 days
        """
        logger.info("=" * 80)
        logger.info("🔍 SCHEDULING SERVICE: get_first_available_next_3_days() CALLED")
        logger.info(f"⏰ Time preference: '{time_preference}'")
        logger.info(f"🌍 Timezone parameter: '{timezone}'")
        logger.info("=" * 80)
        
        try:
            # Clean time preference
            cleaned_time_pref = self._clean_time_preference(time_preference)
            logger.info(f"✅ Cleaned time preference: {cleaned_time_pref}")
            
            # Validate inputs
            if not practice_id:
                return {"success": False, "message": "I'm having trouble accessing our scheduling system. Let me get a human to help you."}
            
            try:
                tz = pytz.timezone(timezone)
            except pytz.UnknownTimeZoneError:
                return {"success": False, "message": "I'm having trouble with the timezone configuration. Let me get a human to help you."}
            
            practice_uuid = UUID(practice_id)
            vet_user_id = await self._get_available_vet(practice_uuid)
            if not vet_user_id:
                return {"success": False, "message": "I don't see any vets available. Let me check with our staff."}
            
            # Get next 3 days
            today = datetime.now(tz).date()
            next_3_days = [today + timedelta(days=i+1) for i in range(3)]
            
            repo = VetAvailabilityRepository(self.db)
            first_available_appointments = []
            
            for check_date in next_3_days:
                # Get slots for this date
                daily_slots = await self._get_slots_for_date(repo, vet_user_id, practice_uuid, check_date, tz, timezone)
                
                # Filter by time preference
                filtered_slots = self._filter_slots_by_time_preference(daily_slots, cleaned_time_pref)
                
                if filtered_slots:
                    # Take only the first available slot for this day
                    first_slot = filtered_slots[0]
                    formatted_time = self._format_slot_for_caller(first_slot, check_date, timezone)
                    
                    first_available_appointments.append({
                        "date": check_date.strftime('%Y-%m-%d'),
                        "day_name": check_date.strftime('%A'),
                        "formatted_date": check_date.strftime('%A, %B %d'),
                        "time": formatted_time,
                        "slot_data": first_slot
                    })
                    
                    logger.info(f"✅ Found first available on {check_date}: {formatted_time}")
            
            if first_available_appointments:
                message_parts = []
                for appt in first_available_appointments:
                    message_parts.append(f"{appt['time']} on {appt['formatted_date']}")
                
                message = f"I found the first available appointments in the next 3 days: " + ", ".join(message_parts)
                
                return {
                    "success": True,
                    "appointments": first_available_appointments,
                    "message": message,
                    "time_preference": cleaned_time_pref,
                    "timezone_used": timezone,
                    "version": "first_available_next_3_days_v1"
                }
            else:
                return {
                    "success": False,
                    "message": f"I'm sorry, we don't have any {cleaned_time_pref} appointments available in the next 3 days. Would you like me to check next week?"
                }
                
        except Exception as e:
            logger.error(f"❌ ERROR in get_first_available_next_3_days: {str(e)}")
            logger.exception("Full traceback:")
            return {"success": False, "message": "I'm having trouble checking our calendar. Let me try again or get a human to help you."}
    
    async def get_first_available_next_week(self, time_preference: str, practice_id: str, timezone: str = "America/Los_Angeles", preferred_days: List[str] = None) -> Dict[str, Any]:
        """
        🎯 GET FIRST AVAILABLE APPOINTMENTS - NEXT WEEK
        
        Returns first available appointments for next week, prioritizing preferred days (Tuesdays and Wednesdays).
        
        Args:
            time_preference: Time preference (e.g., 'morning', 'afternoon', 'evening', 'any time')
            practice_id: UUID of the practice to check availability for
            timezone: Practice timezone
            preferred_days: List of preferred day names (defaults to ['tuesday', 'wednesday'])
        
        Returns:
            Dict with success status and first available appointments for next week
        """
        logger.info("=" * 80)
        logger.info("🔍 SCHEDULING SERVICE: get_first_available_next_week() CALLED")
        logger.info(f"⏰ Time preference: '{time_preference}'")
        logger.info(f"📅 Preferred days: {preferred_days}")
        logger.info("=" * 80)
        
        if preferred_days is None:
            preferred_days = ['tuesday', 'wednesday']
        
        try:
            cleaned_time_pref = self._clean_time_preference(time_preference)
            
            if not practice_id:
                return {"success": False, "message": "I'm having trouble accessing our scheduling system. Let me get a human to help you."}
            
            try:
                tz = pytz.timezone(timezone)
            except pytz.UnknownTimeZoneError:
                return {"success": False, "message": "I'm having trouble with the timezone configuration. Let me get a human to help you."}
            
            practice_uuid = UUID(practice_id)
            vet_user_id = await self._get_available_vet(practice_uuid)
            if not vet_user_id:
                return {"success": False, "message": "I don't see any vets available. Let me check with our staff."}
            
            # Get next week's date range (next Monday to next Sunday)
            today = datetime.now(tz).date()
            days_until_next_monday = 7 - today.weekday()  # Monday is 0, so this gets us to next Monday
            next_monday = today + timedelta(days=days_until_next_monday)
            next_week_dates = [next_monday + timedelta(days=i) for i in range(7)]
            
            repo = VetAvailabilityRepository(self.db)
            
            # First, try preferred days
            preferred_appointments = []
            for check_date in next_week_dates:
                day_name = check_date.strftime('%A').lower()
                if day_name in [day.lower() for day in preferred_days]:
                    daily_slots = await self._get_slots_for_date(repo, vet_user_id, practice_uuid, check_date, tz, timezone)
                    filtered_slots = self._filter_slots_by_time_preference(daily_slots, cleaned_time_pref)
                    
                    if filtered_slots:
                        first_slot = filtered_slots[0]
                        formatted_time = self._format_slot_for_caller(first_slot, check_date, timezone)
                        
                        preferred_appointments.append({
                            "date": check_date.strftime('%Y-%m-%d'),
                            "day_name": check_date.strftime('%A'),
                            "formatted_date": check_date.strftime('%A, %B %d'),
                            "time": formatted_time,
                            "slot_data": first_slot,
                            "is_preferred_day": True
                        })
            
            # If we have preferred day appointments, return those
            if preferred_appointments:
                message_parts = []
                for appt in preferred_appointments:
                    message_parts.append(f"{appt['time']} on {appt['formatted_date']}")
                
                message = f"Great news! I found appointments on your preferred days next week: " + ", ".join(message_parts)
                
                return {
                    "success": True,
                    "appointments": preferred_appointments,
                    "message": message,
                    "time_preference": cleaned_time_pref,
                    "preferred_days_used": True,
                    "timezone_used": timezone,
                    "version": "first_available_next_week_v1"
                }
            
            # If no preferred days available, check all days of next week
            all_appointments = []
            for check_date in next_week_dates:
                daily_slots = await self._get_slots_for_date(repo, vet_user_id, practice_uuid, check_date, tz, timezone)
                filtered_slots = self._filter_slots_by_time_preference(daily_slots, cleaned_time_pref)
                
                if filtered_slots:
                    first_slot = filtered_slots[0]
                    formatted_time = self._format_slot_for_caller(first_slot, check_date, timezone)
                    
                    all_appointments.append({
                        "date": check_date.strftime('%Y-%m-%d'),
                        "day_name": check_date.strftime('%A'),
                        "formatted_date": check_date.strftime('%A, %B %d'),
                        "time": formatted_time,
                        "slot_data": first_slot,
                        "is_preferred_day": False
                    })
            
            if all_appointments:
                # Limit to first 3 appointments
                limited_appointments = all_appointments[:3]
                message_parts = []
                for appt in limited_appointments:
                    message_parts.append(f"{appt['time']} on {appt['formatted_date']}")
                
                message = f"I found these available appointments next week: " + ", ".join(message_parts)
                
                return {
                    "success": True,
                    "appointments": limited_appointments,
                    "message": message,
                    "time_preference": cleaned_time_pref,
                    "preferred_days_used": False,
                    "timezone_used": timezone,
                    "version": "first_available_next_week_v1"
                }
            else:
                return {
                    "success": False,
                    "message": f"I'm sorry, we don't have any {cleaned_time_pref} appointments available next week. Would you like me to check the following week?"
                }
                
        except Exception as e:
            logger.error(f"❌ ERROR in get_first_available_next_week: {str(e)}")
            logger.exception("Full traceback:")
            return {"success": False, "message": "I'm having trouble checking our calendar. Let me try again or get a human to help you."}
    
    async def get_first_available_next_month(self, time_preference: str, practice_id: str, timezone: str = "America/Los_Angeles", preferred_days: List[str] = None) -> Dict[str, Any]:
        """
        🎯 GET FIRST AVAILABLE APPOINTMENTS - NEXT MONTH
        
        Returns first available appointments for next month, prioritizing preferred days (Tuesdays and Wednesdays).
        
        Args:
            time_preference: Time preference (e.g., 'morning', 'afternoon', 'evening', 'any time')
            practice_id: UUID of the practice to check availability for
            timezone: Practice timezone
            preferred_days: List of preferred day names (defaults to ['tuesday', 'wednesday'])
        
        Returns:
            Dict with success status and first available appointments for next month
        """
        logger.info("=" * 80)
        logger.info("🔍 SCHEDULING SERVICE: get_first_available_next_month() CALLED")
        logger.info(f"⏰ Time preference: '{time_preference}'")
        logger.info(f"📅 Preferred days: {preferred_days}")
        logger.info("=" * 80)
        
        if preferred_days is None:
            preferred_days = ['tuesday', 'wednesday']
        
        try:
            cleaned_time_pref = self._clean_time_preference(time_preference)
            
            if not practice_id:
                return {"success": False, "message": "I'm having trouble accessing our scheduling system. Let me get a human to help you."}
            
            try:
                tz = pytz.timezone(timezone)
            except pytz.UnknownTimeZoneError:
                return {"success": False, "message": "I'm having trouble with the timezone configuration. Let me get a human to help you."}
            
            practice_uuid = UUID(practice_id)
            vet_user_id = await self._get_available_vet(practice_uuid)
            if not vet_user_id:
                return {"success": False, "message": "I don't see any vets available. Let me check with our staff."}
            
            # Get next month's date range
            today = datetime.now(tz).date()
            # Start from next month's first day
            if today.month == 12:
                next_month_start = date(today.year + 1, 1, 1)
            else:
                next_month_start = date(today.year, today.month + 1, 1)
            
            # Get last day of next month
            if next_month_start.month == 12:
                next_month_end = date(next_month_start.year + 1, 1, 1) - timedelta(days=1)
            else:
                next_month_end = date(next_month_start.year, next_month_start.month + 1, 1) - timedelta(days=1)
            
            # Generate all dates for next month
            next_month_dates = []
            current_date = next_month_start
            while current_date <= next_month_end:
                next_month_dates.append(current_date)
                current_date += timedelta(days=1)
            
            repo = VetAvailabilityRepository(self.db)
            
            # First, try preferred days
            preferred_appointments = []
            for check_date in next_month_dates:
                day_name = check_date.strftime('%A').lower()
                if day_name in [day.lower() for day in preferred_days]:
                    daily_slots = await self._get_slots_for_date(repo, vet_user_id, practice_uuid, check_date, tz, timezone)
                    filtered_slots = self._filter_slots_by_time_preference(daily_slots, cleaned_time_pref)
                    
                    if filtered_slots:
                        first_slot = filtered_slots[0]
                        formatted_time = self._format_slot_for_caller(first_slot, check_date, timezone)
                        
                        preferred_appointments.append({
                            "date": check_date.strftime('%Y-%m-%d'),
                            "day_name": check_date.strftime('%A'),
                            "formatted_date": check_date.strftime('%A, %B %d'),
                            "time": formatted_time,
                            "slot_data": first_slot,
                            "is_preferred_day": True
                        })
                        
                        # Limit to first 3 preferred appointments
                        if len(preferred_appointments) >= 3:
                            break
            
            # If we have preferred day appointments, return those
            if preferred_appointments:
                message_parts = []
                for appt in preferred_appointments:
                    message_parts.append(f"{appt['time']} on {appt['formatted_date']}")
                
                month_name = next_month_start.strftime('%B')
                message = f"Great news! I found appointments on your preferred days in {month_name}: " + ", ".join(message_parts)
                
                return {
                    "success": True,
                    "appointments": preferred_appointments,
                    "message": message,
                    "time_preference": cleaned_time_pref,
                    "preferred_days_used": True,
                    "timezone_used": timezone,
                    "version": "first_available_next_month_v1"
                }
            
            # If no preferred days available, check all days of next month (limit search to avoid performance issues)
            all_appointments = []
            for check_date in next_month_dates[:14]:  # Check first 2 weeks of next month
                daily_slots = await self._get_slots_for_date(repo, vet_user_id, practice_uuid, check_date, tz, timezone)
                filtered_slots = self._filter_slots_by_time_preference(daily_slots, cleaned_time_pref)
                
                if filtered_slots:
                    first_slot = filtered_slots[0]
                    formatted_time = self._format_slot_for_caller(first_slot, check_date, timezone)
                    
                    all_appointments.append({
                        "date": check_date.strftime('%Y-%m-%d'),
                        "day_name": check_date.strftime('%A'),
                        "formatted_date": check_date.strftime('%A, %B %d'),
                        "time": formatted_time,
                        "slot_data": first_slot,
                        "is_preferred_day": False
                    })
                    
                    # Limit to first 3 appointments
                    if len(all_appointments) >= 3:
                        break
            
            if all_appointments:
                message_parts = []
                for appt in all_appointments:
                    message_parts.append(f"{appt['time']} on {appt['formatted_date']}")
                
                month_name = next_month_start.strftime('%B')
                message = f"I found these available appointments in {month_name}: " + ", ".join(message_parts)
                
                return {
                    "success": True,
                    "appointments": all_appointments,
                    "message": message,
                    "time_preference": cleaned_time_pref,
                    "preferred_days_used": False,
                    "timezone_used": timezone,
                    "version": "first_available_next_month_v1"
                }
            else:
                month_name = next_month_start.strftime('%B')
                return {
                    "success": False,
                    "message": f"I'm sorry, we don't have any {cleaned_time_pref} appointments available in {month_name}. Would you like me to check a different month?"
                }
                
        except Exception as e:
            logger.error(f"❌ ERROR in get_first_available_next_month: {str(e)}")
            logger.exception("Full traceback:")
            return {"success": False, "message": "I'm having trouble checking our calendar. Let me try again or get a human to help you."}
    
    async def _get_slots_for_date(self, repo: VetAvailabilityRepository, vet_user_id: UUID, practice_uuid: UUID, check_date: date, tz: pytz.BaseTzInfo, timezone_str: str = "America/Los_Angeles") -> List[Dict]:
        """
        Helper method to get available slots for a specific date with timezone conversion
        """
        # Convert local date to UTC date range for database lookup
        local_start = tz.localize(datetime.combine(check_date, time.min))
        local_end = tz.localize(datetime.combine(check_date, time.max))
        
        # Convert to UTC for database lookup
        utc_start = local_start.astimezone(pytz.UTC)
        utc_end = local_end.astimezone(pytz.UTC)
        
        # We need to check availability for potentially multiple UTC dates
        utc_dates_to_check = set()
        utc_dates_to_check.add(utc_start.date())
        utc_dates_to_check.add(utc_end.date())
        
        # Get slots for all relevant UTC dates
        all_slot_data = []
        for utc_date in utc_dates_to_check:
            daily_slots = await repo.get_available_slots(
                vet_user_id=vet_user_id,
                practice_id=practice_uuid,
                date=utc_date,
                slot_duration_minutes=45,
                timezone_str=timezone_str
            )
            all_slot_data.extend(daily_slots)
        
        # Filter slots to only include those within the requested local date
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
            
            # Create UTC datetime for this slot
            for check_utc_date in utc_dates_to_check:
                utc_slot_datetime = pytz.UTC.localize(
                    datetime.combine(check_utc_date, time(hour=utc_hour, minute=utc_minute))
                )
                local_slot_datetime = utc_slot_datetime.astimezone(tz)
                
                # Check if this slot falls within our target local date
                if local_slot_datetime.date() == check_date:
                    slot['local_datetime'] = local_slot_datetime
                    valid_slots.append(slot)
                    break
        
        return valid_slots

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
        date_range_end: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        🎯 GET FIRST AVAILABLE APPOINTMENTS - FLEXIBLE SCHEDULING
        
        This is the most flexible scheduling function that can handle complex queries like:
        - "First available in 3 weeks"
        - "First available in week 3 of next month" 
        - "First available in 4 weeks on Wednesdays or Fridays"
        - "First available between March 15 and March 30"
        
        Args:
            time_preference: Time preference ('morning', 'afternoon', 'evening', 'any time')
            practice_id: UUID of the practice to check availability for
            timezone: Practice timezone
            weeks_from_now: Number of weeks from now (e.g., 3 for "in 3 weeks")
            specific_week_of_month: Specific week of target month (1-4, e.g., 3 for "week 3")
            target_month_offset: Month offset (0=this month, 1=next month, 2=month after next)
            preferred_days: List of preferred day names (e.g., ['wednesday', 'friday'])
            date_range_start: Start date for custom range (ISO format or natural language)
            date_range_end: End date for custom range (ISO format or natural language)
        
        Returns:
            Dict with success status and first available appointments in the specified range
        """
        logger.info("=" * 80)
        logger.info("🔍 SCHEDULING SERVICE: get_first_available_flexible() CALLED")
        logger.info(f"⏰ Time preference: '{time_preference}'")
        logger.info(f"📅 Weeks from now: {weeks_from_now}")
        logger.info(f"📅 Specific week of month: {specific_week_of_month}")
        logger.info(f"📅 Target month offset: {target_month_offset}")
        logger.info(f"📅 Preferred days: {preferred_days}")
        logger.info(f"📅 Date range: {date_range_start} to {date_range_end}")
        logger.info("=" * 80)
        
        try:
            cleaned_time_pref = self._clean_time_preference(time_preference)
            
            if not practice_id:
                return {"success": False, "message": "I'm having trouble accessing our scheduling system. Let me get a human to help you."}
            
            try:
                tz = pytz.timezone(timezone)
            except pytz.UnknownTimeZoneError:
                return {"success": False, "message": "I'm having trouble with the timezone configuration. Let me get a human to help you."}
            
            practice_uuid = UUID(practice_id)
            vet_user_id = await self._get_available_vet(practice_uuid)
            if not vet_user_id:
                return {"success": False, "message": "I don't see any vets available. Let me check with our staff."}
            
            # Calculate the date range based on the parameters
            today = datetime.now(tz).date()
            start_date, end_date, range_description = self._calculate_flexible_date_range(
                today, weeks_from_now, specific_week_of_month, target_month_offset, 
                date_range_start, date_range_end, tz
            )
            
            logger.info(f"🔍 Calculated date range: {start_date} to {end_date}")
            logger.info(f"📝 Range description: {range_description}")
            
            # Set default preferred days if none specified
            if preferred_days is None:
                preferred_days = ['tuesday', 'wednesday']
            
            repo = VetAvailabilityRepository(self.db)
            
            # First, try preferred days within the date range
            preferred_appointments = []
            current_date = start_date
            while current_date <= end_date:
                day_name = current_date.strftime('%A').lower()
                if day_name in [day.lower() for day in preferred_days]:
                    daily_slots = await self._get_slots_for_date(repo, vet_user_id, practice_uuid, current_date, tz, timezone)
                    filtered_slots = self._filter_slots_by_time_preference(daily_slots, cleaned_time_pref)
                    
                    if filtered_slots:
                        first_slot = filtered_slots[0]
                        formatted_time = self._format_slot_for_caller(first_slot, current_date, timezone)
                        
                        preferred_appointments.append({
                            "date": current_date.strftime('%Y-%m-%d'),
                            "day_name": current_date.strftime('%A'),
                            "formatted_date": current_date.strftime('%A, %B %d'),
                            "time": formatted_time,
                            "slot_data": first_slot,
                            "is_preferred_day": True
                        })
                        
                        # Limit to first 3 preferred appointments
                        if len(preferred_appointments) >= 3:
                            break
                
                current_date += timedelta(days=1)
            
            # If we have preferred day appointments, return those
            if preferred_appointments:
                message_parts = []
                for appt in preferred_appointments:
                    message_parts.append(f"{appt['time']} on {appt['formatted_date']}")
                
                message = f"Great news! I found appointments on your preferred days {range_description}: " + ", ".join(message_parts)
                
                return {
                    "success": True,
                    "appointments": preferred_appointments,
                    "message": message,
                    "time_preference": cleaned_time_pref,
                    "preferred_days_used": True,
                    "date_range_start": start_date.strftime('%Y-%m-%d'),
                    "date_range_end": end_date.strftime('%Y-%m-%d'),
                    "range_description": range_description,
                    "timezone_used": timezone,
                    "version": "first_available_flexible_v1"
                }
            
            # If no preferred days available, check all days in the range
            all_appointments = []
            current_date = start_date
            checked_days = 0
            max_days_to_check = 21  # Limit to avoid performance issues
            
            while current_date <= end_date and checked_days < max_days_to_check:
                daily_slots = await self._get_slots_for_date(repo, vet_user_id, practice_uuid, current_date, tz, timezone)
                filtered_slots = self._filter_slots_by_time_preference(daily_slots, cleaned_time_pref)
                
                if filtered_slots:
                    first_slot = filtered_slots[0]
                    formatted_time = self._format_slot_for_caller(first_slot, current_date, timezone)
                    
                    all_appointments.append({
                        "date": current_date.strftime('%Y-%m-%d'),
                        "day_name": current_date.strftime('%A'),
                        "formatted_date": current_date.strftime('%A, %B %d'),
                        "time": formatted_time,
                        "slot_data": first_slot,
                        "is_preferred_day": False
                    })
                    
                    # Limit to first 3 appointments
                    if len(all_appointments) >= 3:
                        break
                
                current_date += timedelta(days=1)
                checked_days += 1
            
            if all_appointments:
                message_parts = []
                for appt in all_appointments:
                    message_parts.append(f"{appt['time']} on {appt['formatted_date']}")
                
                message = f"I found these available appointments {range_description}: " + ", ".join(message_parts)
                
                return {
                    "success": True,
                    "appointments": all_appointments,
                    "message": message,
                    "time_preference": cleaned_time_pref,
                    "preferred_days_used": False,
                    "date_range_start": start_date.strftime('%Y-%m-%d'),
                    "date_range_end": end_date.strftime('%Y-%m-%d'),
                    "range_description": range_description,
                    "timezone_used": timezone,
                    "version": "first_available_flexible_v1"
                }
            else:
                return {
                    "success": False,
                    "message": f"I'm sorry, we don't have any {cleaned_time_pref} appointments available {range_description}. Would you like me to check a different time period?"
                }
                
        except Exception as e:
            logger.error(f"❌ ERROR in get_first_available_flexible: {str(e)}")
            logger.exception("Full traceback:")
            return {"success": False, "message": "I'm having trouble checking our calendar. Let me try again or get a human to help you."}
    
    def _calculate_flexible_date_range(
        self, 
        today: date, 
        weeks_from_now: Optional[int],
        specific_week_of_month: Optional[int],
        target_month_offset: Optional[int],
        date_range_start: Optional[str],
        date_range_end: Optional[str],
        tz: pytz.BaseTzInfo
    ) -> tuple[date, date, str]:
        """
        Calculate the date range based on flexible parameters
        
        Returns: (start_date, end_date, description)
        """
        
        # Custom date range takes priority
        if date_range_start and date_range_end:
            start_date = self._parse_date_string(date_range_start)
            end_date = self._parse_date_string(date_range_end)
            return start_date, end_date, f"between {start_date.strftime('%B %d')} and {end_date.strftime('%B %d')}"
        
        # Weeks from now (e.g., "in 3 weeks")
        if weeks_from_now is not None:
            start_date = today + timedelta(weeks=weeks_from_now)
            end_date = start_date + timedelta(days=6)  # 1 week window
            
            if weeks_from_now == 1:
                return start_date, end_date, "next week"
            elif weeks_from_now == 2:
                return start_date, end_date, "in 2 weeks"
            else:
                return start_date, end_date, f"in {weeks_from_now} weeks"
        
        # Specific week of a target month (e.g., "week 3 of next month")
        if specific_week_of_month is not None and target_month_offset is not None:
            # Calculate target month
            target_year = today.year
            target_month = today.month + target_month_offset
            
            # Handle year rollover
            while target_month > 12:
                target_month -= 12
                target_year += 1
            while target_month < 1:
                target_month += 12
                target_year -= 1
            
            # Find the first day of the target month
            first_day_of_month = date(target_year, target_month, 1)
            
            # Find the first Monday of the month (week 1 starts on Monday)
            days_to_monday = (7 - first_day_of_month.weekday()) % 7
            if first_day_of_month.weekday() == 0:  # If it's already Monday
                days_to_monday = 0
            else:
                days_to_monday = 7 - first_day_of_month.weekday()
            
            first_monday = first_day_of_month + timedelta(days=days_to_monday)
            
            # Calculate the start of the specific week
            start_date = first_monday + timedelta(weeks=specific_week_of_month - 1)
            end_date = start_date + timedelta(days=6)
            
            month_name = first_day_of_month.strftime('%B')
            if target_month_offset == 0:
                month_desc = f"this {month_name}"
            elif target_month_offset == 1:
                month_desc = f"next {month_name}"
            else:
                month_desc = f"{month_name} {target_year}"
            
            return start_date, end_date, f"in week {specific_week_of_month} of {month_desc}"
        
        # Just target month offset (entire month)
        if target_month_offset is not None:
            target_year = today.year
            target_month = today.month + target_month_offset
            
            # Handle year rollover
            while target_month > 12:
                target_month -= 12
                target_year += 1
            while target_month < 1:
                target_month += 12
                target_year -= 1
            
            # First day of target month
            start_date = date(target_year, target_month, 1)
            
            # Last day of target month
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
        
        # Default: next 7 days
        start_date = today + timedelta(days=1)
        end_date = today + timedelta(days=7)
        return start_date, end_date, "in the next week"

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
