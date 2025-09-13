"""
Simplified MVP Scheduling Service - Schedule-focused with human decision making
KEY ISSUE: The current system returns broad availability windows (9 AM - 5 PM)
SOLUTION: This shows how to calculate actual available 30-minute slots
"""

from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Tuple
from enum import Enum

class SimplifiedSchedulingService:
    """MVP scheduling service focused on vet availability and human decision-making"""
    
    def get_actual_available_slots(
        self, 
        practice_id: str, 
        vet_user_id: str,
        date: datetime.date, 
        slot_duration_minutes: int = 30
    ) -> List[Dict]:
        """
        THIS IS THE MISSING LOGIC!
        
        Instead of returning broad windows like:
        {"start_time": "09:00:00", "end_time": "17:00:00"}
        
        This returns actual bookable slots like:
        [
            {"start_time": "09:00:00", "end_time": "09:30:00", "available": true},
            {"start_time": "09:30:00", "end_time": "10:00:00", "available": true},
            {"start_time": "10:00:00", "end_time": "10:30:00", "available": false}, // booked
            {"start_time": "10:30:00", "end_time": "11:00:00", "available": true},
            ...
        ]
        """
        query = """
        WITH practice_open_hours AS (
            -- Check if practice is open on this day
            SELECT ph.open_time, ph.close_time
            FROM practice_hours ph
            WHERE ph.practice_id = %s
                AND ph.day_of_week = EXTRACT(DOW FROM %s::date)
                AND ph.is_active = true
                AND ph.effective_from <= %s
                AND (ph.effective_until IS NULL OR ph.effective_until >= %s)
                AND ph.open_time IS NOT NULL 
                AND ph.close_time IS NOT NULL
        ),
        vet_daily_availability AS (
            -- Get vet's availability for this date
            SELECT va.start_time, va.end_time, va.availability_type
            FROM vet_availability va
            WHERE va.vet_user_id = %s
                AND va.practice_id = %s
                AND va.date = %s
                AND va.is_active = true
                AND va.availability_type IN ('AVAILABLE', 'EMERGENCY_ONLY')
        ),
        effective_availability AS (
            -- Intersect practice hours with vet availability
            SELECT 
                GREATEST(vda.start_time, poh.open_time) as start_time,
                LEAST(vda.end_time, poh.close_time) as end_time,
                vda.availability_type
            FROM vet_daily_availability vda
            CROSS JOIN practice_open_hours poh
            WHERE vda.start_time < poh.close_time 
                AND vda.end_time > poh.open_time
        ),
        time_slots AS (
            -- Generate 30-minute slots within availability
            SELECT 
                slot_start::time as start_time,
                (slot_start + INTERVAL '%s minutes')::time as end_time,
                ea.availability_type
            FROM effective_availability ea,
            LATERAL generate_series(
                ea.start_time,
                ea.end_time - INTERVAL '%s minutes',
                INTERVAL '%s minutes'
            ) AS slot_start
        ),
        existing_appointments AS (
            -- Get existing appointments that overlap with our slots
            SELECT 
                a.appointment_date::time as appt_start,
                (a.appointment_date + INTERVAL (a.duration_minutes || ' minutes'))::time as appt_end,
                a.title,
                a.appointment_type,
                a.status
            FROM appointment a
            WHERE a.assigned_vet_user_id = %s
                AND a.practice_id = %s
                AND a.appointment_date::date = %s
                AND a.status NOT IN ('CANCELLED', 'NO_SHOW', 'COMPLETED')
        )
        SELECT 
            ts.start_time,
            ts.end_time,
            ts.availability_type,
            CASE 
                WHEN ea.appt_start IS NOT NULL THEN false
                ELSE true
            END as available,
            ea.title as conflicting_appointment,
            ea.appointment_type as conflicting_type,
            CASE 
                WHEN ea.appt_start IS NOT NULL THEN 'Slot already booked'
                WHEN ts.availability_type = 'EMERGENCY_ONLY' THEN 'Emergency slot - can be used if needed'
                ELSE 'Available'
            END as notes
        FROM time_slots ts
        LEFT JOIN existing_appointments ea ON (
            -- Check if appointment overlaps with this time slot
            ea.appt_start < ts.end_time AND ea.appt_end > ts.start_time
        )
        ORDER BY ts.start_time
        """
        
        params = [
            practice_id, date, date, date,  # practice hours
            vet_user_id, practice_id, date,  # vet availability
            slot_duration_minutes, slot_duration_minutes, slot_duration_minutes,  # slot generation
            vet_user_id, practice_id, date  # existing appointments
        ]
        
        # This would return actual bookable slots, not broad windows
        return self._execute_query(query, params)
    
    def get_available_appointment_times(
        self, 
        practice_id: str, 
        date: datetime.date, 
        time_preference: str = None,  # "morning", "afternoon", "evening"
        duration_minutes: int = 30,
        preferred_vet_id: str = None
    ) -> List[Dict]:
        """
        Query: "What are some appointment times on September 17th, in the afternoon?"
        
        FIXED VERSION: Returns actual available slots, not broad windows
        """
        
        # If specific vet requested, get their actual slots
        if preferred_vet_id:
            slots = self.get_actual_available_slots(
                practice_id, preferred_vet_id, date, duration_minutes
            )
            # Filter by time preference
            if time_preference:
                slots = self._filter_by_time_preference(slots, time_preference)
            return slots
        
        # Otherwise, get slots for all available vets
        query = """
        SELECT DISTINCT
            va.vet_user_id,
            u.full_name as vet_name
        FROM vet_availability va
        JOIN users u ON u.id = va.vet_user_id
        WHERE va.practice_id = %s
            AND va.date = %s
            AND va.is_active = true
            AND va.availability_type IN ('AVAILABLE', 'EMERGENCY_ONLY')
        """
        
        available_vets = self._execute_query(query, [practice_id, date])
        
        all_slots = []
        for vet in available_vets.get('vets', []):
            vet_slots = self.get_actual_available_slots(
                practice_id, vet['vet_user_id'], date, duration_minutes
            )
            # Add vet info to each slot
            for slot in vet_slots:
                slot['vet_user_id'] = vet['vet_user_id']
                slot['vet_name'] = vet['vet_name']
                all_slots.append(slot)
        
        # Filter by time preference
        if time_preference:
            all_slots = self._filter_by_time_preference(all_slots, time_preference)
            
        return all_slots
    
    def _filter_by_time_preference(self, slots: List[Dict], preference: str) -> List[Dict]:
        """Filter slots by morning/afternoon/evening preference"""
        filtered = []
        for slot in slots:
            start_hour = int(slot['start_time'].split(':')[0])
            
            if preference == "morning" and start_hour < 12:
                filtered.append(slot)
            elif preference == "afternoon" and 12 <= start_hour < 17:
                filtered.append(slot)
            elif preference == "evening" and start_hour >= 17:
                filtered.append(slot)
            elif preference is None:
                filtered.append(slot)
                
        return filtered
    
    def schedule_appointment_with_conflict_check(
        self,
        practice_id: str,
        pet_owner_id: str,
        pet_ids: List[str],
        appointment_date: datetime,
        duration_minutes: int = 30,
        appointment_type: str = "CHECKUP",
        preferred_vet_id: str = None,
        title: str = "Appointment",
        description: str = None,
        force_emergency: bool = False
    ) -> Dict:
        """
        Schedule an appointment with proper conflict checking
        HARD CONSTRAINT: Practice must be open (unless emergency override)
        """
        
        # 1. Check if practice is open
        practice_status = self._check_practice_hours(practice_id, appointment_date)
        
        if not force_emergency and not practice_status['is_open']:
            return {
                "can_schedule": False,
                "blocking_reason": "PRACTICE_CLOSED",
                "message": f"Practice is closed at {appointment_date.strftime('%I:%M %p on %A')}.",
                "recommendation": "CHOOSE_DIFFERENT_TIME_OR_EMERGENCY_OVERRIDE"
            }
        
        # 2. Check if specific slot is available
        if preferred_vet_id:
            available_slots = self.get_actual_available_slots(
                practice_id, preferred_vet_id, appointment_date.date(), duration_minutes
            )
            
            appointment_time = appointment_date.time()
            slot_available = any(
                slot['start_time'] <= appointment_time.strftime('%H:%M:%S') < slot['end_time']
                and slot['available']
                for slot in available_slots
            )
            
            if not slot_available and not force_emergency:
                return {
                    "can_schedule": False,
                    "blocking_reason": "TIME_SLOT_UNAVAILABLE", 
                    "message": f"The requested time slot is not available.",
                    "available_alternatives": [
                        slot for slot in available_slots if slot['available']
                    ][:5]  # Show first 5 alternatives
                }
        
        # 3. If we get here, we can schedule (practice open + slot available)
        return {
            "can_schedule": True,
            "message": "Appointment can be scheduled" + (" (Emergency override)" if force_emergency else ""),
            "appointment_details": {
                "practice_id": practice_id,
                "pet_owner_id": pet_owner_id,
                "pet_ids": pet_ids,
                "appointment_date": appointment_date,
                "duration_minutes": duration_minutes,
                "appointment_type": appointment_type,
                "preferred_vet_id": preferred_vet_id,
                "title": title,
                "description": description,
                "is_emergency": force_emergency
            }
        }
    
    def _check_practice_hours(self, practice_id: str, check_time: datetime) -> Dict:
        """Check if practice is open at given time"""
        query = """
        SELECT 
            ph.open_time,
            ph.close_time,
            CASE 
                WHEN ph.open_time IS NULL OR ph.close_time IS NULL THEN false
                WHEN %s::time >= ph.open_time AND %s::time <= ph.close_time THEN true
                ELSE false
            END as is_open
        FROM practice_hours ph
        WHERE ph.practice_id = %s
            AND ph.day_of_week = EXTRACT(DOW FROM %s::date)
            AND ph.is_active = true
            AND ph.effective_from <= %s::date
            AND (ph.effective_until IS NULL OR ph.effective_until >= %s::date)
        """
        
        return self._execute_query(query, [
            check_time, check_time, practice_id, 
            check_time, check_time, check_time
        ])

    def _execute_query(self, query: str, params: List) -> Dict:
        """Mock query execution - replace with actual database call"""
        return {
            "query": query.strip(),
            "params": params,
            "result": "This is the ACTUAL logic your system needs to implement",
            "note": "Replace this mock with real database execution"
        }

# ============================================================================
# ACTUAL IMPLEMENTATION EXAMPLE (what your system should do)
# ============================================================================

def fix_your_current_endpoint():
    """
    Your current system returns:
    [{"start_time":"09:00:00","end_time":"17:00:00","availability_type":"AVAILABLE"}]
    
    It SHOULD return something like:
    """
    return [
        {"start_time": "09:00:00", "end_time": "09:30:00", "available": True},
        {"start_time": "09:30:00", "end_time": "10:00:00", "available": True}, 
        {"start_time": "10:00:00", "end_time": "10:30:00", "available": False, "reason": "Already booked"},
        {"start_time": "10:30:00", "end_time": "11:00:00", "available": True},
        {"start_time": "11:00:00", "end_time": "11:30:00", "available": True},
        # ... and so on for each 30-minute slot
    ]

# Usage example:
scheduler = SimplifiedSchedulingService()

# This will return ACTUAL bookable slots, not broad windows
actual_slots = scheduler.get_actual_available_slots(
    practice_id="practice-123",
    vet_user_id="vet-456", 
    date=datetime(2025, 9, 13).date()
)

print("SOLUTION: Replace broad availability windows with granular slot checking!")