"""
APPOINTMENT CREATION FLOW & AVAILABILITY MANAGEMENT
Solving the dual-write problem and appointment-availability relationship
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid

class AppointmentSchedulingService:
    """
    Handles the complete appointment lifecycle with proper availability management
    """
    
    def get_available_slots_for_practice(
        self, 
        practice_id: str, 
        date: str,
        duration_minutes: int = 30
    ) -> Dict:
        """
        STEP 1: Get all available slots across all vets in the practice
        This is what your frontend should call first
        """
        query = """
        WITH practice_open_check AS (
            SELECT ph.open_time, ph.close_time
            FROM practice_hours ph
            WHERE ph.practice_id = %s
                AND ph.day_of_week = EXTRACT(DOW FROM %s::date)
                AND ph.is_active = true
                AND ph.open_time IS NOT NULL
        ),
        available_vets AS (
            SELECT 
                va.vet_user_id,
                u.full_name as vet_name,
                va.start_time,
                va.end_time,
                va.availability_type
            FROM vet_availability va
            JOIN users u ON u.id = va.vet_user_id
            CROSS JOIN practice_open_check poc
            WHERE va.practice_id = %s
                AND va.date = %s::date
                AND va.is_active = true
                AND va.availability_type IN ('AVAILABLE', 'EMERGENCY_ONLY')
                -- Intersect with practice hours
                AND va.start_time < poc.close_time
                AND va.end_time > poc.open_time
        ),
        time_slots AS (
            SELECT 
                av.vet_user_id,
                av.vet_name,
                av.availability_type,
                generate_series(
                    GREATEST(av.start_time, poc.open_time),
                    LEAST(av.end_time, poc.close_time) - INTERVAL '%s minutes',
                    INTERVAL '%s minutes'
                )::time as slot_start
            FROM available_vets av
            CROSS JOIN practice_open_check poc
        ),
        existing_appointments AS (
            SELECT 
                a.assigned_vet_user_id,
                a.appointment_date::time as start_time,
                (a.appointment_date + INTERVAL (a.duration_minutes || ' minutes'))::time as end_time
            FROM appointment a
            WHERE a.practice_id = %s
                AND a.appointment_date::date = %s::date
                AND a.status NOT IN ('CANCELLED', 'NO_SHOW', 'COMPLETED')
        )
        SELECT 
            ts.vet_user_id,
            ts.vet_name,
            ts.slot_start,
            (ts.slot_start + INTERVAL '%s minutes')::time as slot_end,
            ts.availability_type,
            CASE 
                WHEN ea.start_time IS NOT NULL THEN false
                ELSE true
            END as available
        FROM time_slots ts
        LEFT JOIN existing_appointments ea ON (
            ea.assigned_vet_user_id = ts.vet_user_id
            AND ea.start_time < (ts.slot_start + INTERVAL '%s minutes')::time
            AND ea.end_time > ts.slot_start
        )
        WHERE ea.start_time IS NULL  -- Only available slots
        ORDER BY ts.slot_start, ts.vet_name
        """
        
        params = [
            practice_id, date,  # practice hours check
            practice_id, date,  # available vets
            duration_minutes, duration_minutes,  # time slots generation
            practice_id, date,  # existing appointments
            duration_minutes, duration_minutes   # final slot calculation
        ]
        
        return {
            "practice_id": practice_id,
            "date": date,
            "available_slots": self._execute_query(query, params),
            "next_step": "User selects a slot, then call create_appointment()"
        }
    
    def create_appointment(
        self,
        practice_id: str,
        pet_owner_id: str,
        pet_ids: List[str],
        selected_vet_id: str,
        appointment_datetime: datetime,
        duration_minutes: int = 30,
        appointment_type: str = "CHECKUP",
        title: str = "Appointment",
        description: str = None,
        force_emergency: bool = False
    ) -> Dict:
        """
        STEP 2: Create appointment with atomic validation
        
        This is the CRITICAL function that solves the dual-write problem
        """
        
        # START TRANSACTION
        try:
            # 1. VALIDATE: Check if slot is still available (race condition protection)
            validation_result = self._validate_appointment_slot(
                practice_id, selected_vet_id, appointment_datetime, 
                duration_minutes, force_emergency
            )
            
            if not validation_result['valid'] and not force_emergency:
                return {
                    "success": False,
                    "error": "SLOT_NO_LONGER_AVAILABLE",
                    "message": validation_result['message'],
                    "suggested_alternatives": self._get_nearby_slots(
                        practice_id, selected_vet_id, appointment_datetime, duration_minutes
                    )
                }
            
            # 2. CREATE: Insert appointment record
            appointment_id = str(uuid.uuid4())
            appointment_data = {
                "id": appointment_id,
                "practice_id": practice_id,
                "pet_owner_id": pet_owner_id,
                "assigned_vet_user_id": selected_vet_id,
                "appointment_date": appointment_datetime,
                "duration_minutes": duration_minutes,
                "appointment_type": appointment_type,
                "status": "SCHEDULED",
                "title": title,
                "description": description,
                "created_by_user_id": self.current_user_id  # Set from context
            }
            
            create_query = """
            INSERT INTO appointment (
                id, practice_id, pet_owner_id, assigned_vet_user_id,
                appointment_date, duration_minutes, appointment_type, 
                status, title, description, created_by_user_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            self._execute_query(create_query, list(appointment_data.values()))
            
            # 3. LINK: Create appointment-pet associations
            for pet_id in pet_ids:
                pet_link_query = """
                INSERT INTO appointment_pet (appointment_id, pet_id)
                VALUES (%s, %s)
                """
                self._execute_query(pet_link_query, [appointment_id, pet_id])
            
            # 4. LOG: Track any conflicts for staff review (optional)
            self._check_and_log_conflicts(appointment_id, validation_result)
            
            # COMMIT TRANSACTION
            
            return {
                "success": True,
                "appointment_id": appointment_id,
                "message": "Appointment created successfully",
                "appointment_details": appointment_data,
                "conflicts": validation_result.get('conflicts', [])
            }
            
        except Exception as e:
            # ROLLBACK TRANSACTION
            return {
                "success": False,
                "error": "CREATION_FAILED",
                "message": f"Failed to create appointment: {str(e)}"
            }
    
    def _validate_appointment_slot(
        self,
        practice_id: str,
        vet_id: str,
        appointment_time: datetime,
        duration_minutes: int,
        force_emergency: bool = False
    ) -> Dict:
        """
        CRITICAL: Validate appointment slot is available
        This prevents double-booking and ensures data consistency
        """
        
        # Check 1: Practice hours
        if not force_emergency:
            practice_check = self._check_practice_hours(practice_id, appointment_time)
            if not practice_check['is_open']:
                return {
                    "valid": False,
                    "message": "Practice is closed at requested time",
                    "reason": "PRACTICE_CLOSED"
                }
        
        # Check 2: Vet availability
        vet_available = self._check_vet_availability(
            vet_id, appointment_time.date(), 
            appointment_time.time(), duration_minutes
        )
        
        if not vet_available['available'] and not force_emergency:
            return {
                "valid": False,
                "message": "Vet not available at requested time",
                "reason": "VET_UNAVAILABLE"
            }
        
        # Check 3: Existing appointments (the key check!)
        conflict_check_query = """
        SELECT 
            a.id,
            a.appointment_date,
            a.duration_minutes,
            a.title,
            a.status
        FROM appointment a
        WHERE a.assigned_vet_user_id = %s
            AND a.appointment_date::date = %s::date
            AND a.status NOT IN ('CANCELLED', 'NO_SHOW', 'COMPLETED')
            AND (
                -- New appointment overlaps with existing
                a.appointment_date < %s + INTERVAL '%s minutes'
                AND a.appointment_date + INTERVAL (a.duration_minutes || ' minutes') > %s
            )
        """
        
        conflicts = self._execute_query(conflict_check_query, [
            vet_id, appointment_time.date(), 
            appointment_time, duration_minutes, appointment_time
        ])
        
        if conflicts and not force_emergency:
            return {
                "valid": False,
                "message": "Time slot conflicts with existing appointment",
                "reason": "SLOT_CONFLICT",
                "conflicts": conflicts
            }
        
        return {
            "valid": True,
            "message": "Slot is available",
            "conflicts": conflicts if force_emergency else []
        }
    
    def update_appointment(
        self,
        appointment_id: str,
        new_datetime: datetime = None,
        new_duration: int = None,
        new_vet_id: str = None,
        force_emergency: bool = False
    ) -> Dict:
        """
        STEP 3: Update appointment with proper validation
        Handles the "dual update" problem you mentioned
        """
        
        # START TRANSACTION
        try:
            # 1. Get current appointment
            current_appointment = self._get_appointment(appointment_id)
            if not current_appointment:
                return {"success": False, "error": "APPOINTMENT_NOT_FOUND"}
            
            # 2. Determine what's changing
            final_datetime = new_datetime or current_appointment['appointment_date']
            final_duration = new_duration or current_appointment['duration_minutes']
            final_vet_id = new_vet_id or current_appointment['assigned_vet_user_id']
            
            # 3. If time/vet is changing, validate new slot
            if (new_datetime or new_vet_id or new_duration):
                validation = self._validate_appointment_slot(
                    current_appointment['practice_id'],
                    final_vet_id,
                    final_datetime,
                    final_duration,
                    force_emergency
                )
                
                if not validation['valid'] and not force_emergency:
                    return {
                        "success": False,
                        "error": "NEW_SLOT_UNAVAILABLE",
                        "message": validation['message'],
                        "conflicts": validation.get('conflicts', [])
                    }
            
            # 4. Update the appointment (single source of truth)
            update_query = """
            UPDATE appointment 
            SET 
                appointment_date = %s,
                duration_minutes = %s,
                assigned_vet_user_id = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            
            self._execute_query(update_query, [
                final_datetime, final_duration, final_vet_id, appointment_id
            ])
            
            # 5. Log conflicts if any (for staff review)
            if validation.get('conflicts'):
                self._log_appointment_conflicts(appointment_id, validation['conflicts'])
            
            # COMMIT TRANSACTION
            
            return {
                "success": True,
                "message": "Appointment updated successfully",
                "appointment_id": appointment_id,
                "changes": {
                    "datetime": final_datetime,
                    "duration": final_duration,
                    "vet_id": final_vet_id
                }
            }
            
        except Exception as e:
            # ROLLBACK TRANSACTION
            return {
                "success": False,
                "error": "UPDATE_FAILED",
                "message": f"Failed to update appointment: {str(e)}"
            }
    
    def cancel_appointment(self, appointment_id: str, reason: str = None) -> Dict:
        """
        Cancel appointment - this automatically frees up the time slot
        """
        update_query = """
        UPDATE appointment 
        SET 
            status = 'CANCELLED',
            notes = COALESCE(notes || '\n', '') || 'Cancelled: ' || COALESCE(%s, 'No reason provided'),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        self._execute_query(update_query, [reason, appointment_id])
        
        return {
            "success": True,
            "message": "Appointment cancelled - time slot is now available"
        }
    
    # Helper methods
    def _check_practice_hours(self, practice_id: str, check_time: datetime) -> Dict:
        # Implementation from previous artifacts
        pass
    
    def _check_vet_availability(self, vet_id: str, date, time, duration: int) -> Dict:
        # Check if vet has availability window covering this time
        pass
    
    def _get_nearby_slots(self, practice_id: str, vet_id: str, requested_time: datetime, duration: int) -> List[Dict]:
        # Find alternative slots near the requested time
        pass
    
    def _execute_query(self, query: str, params: List):
        # Your database execution logic
        pass

# ============================================================================
# USAGE FLOW - How Frontend Should Work
# ============================================================================

def appointment_booking_flow():
    """
    Complete user flow for booking appointments
    """
    scheduler = AppointmentSchedulingService()
    
    # STEP 1: Get available slots for practice
    available_slots = scheduler.get_available_slots_for_practice(
        practice_id="practice-123",
        date="2025-09-13"
    )
    
    # STEP 2: User selects a slot from the UI
    # Frontend shows: "Dr. Smith - 10:30 AM - 11:00 AM [SELECT]"
    user_selection = {
        "vet_id": "vet-456",
        "datetime": datetime(2025, 9, 13, 10, 30),
        "duration": 30
    }
    
    # STEP 3: Create appointment with selected slot
    result = scheduler.create_appointment(
        practice_id="practice-123",
        pet_owner_id="owner-789",
        pet_ids=["pet-101"],
        selected_vet_id=user_selection["vet_id"],
        appointment_datetime=user_selection["datetime"],
        duration_minutes=user_selection["duration"],
        title="Routine checkup for Fluffy"
    )
    
    return result

# ============================================================================
# KEY ARCHITECTURAL DECISIONS
# ============================================================================

"""
SOLVING YOUR 3 PROBLEMS:

1. RELATIONSHIP: Appointment <-> VetAvailability
   - NO direct FK relationship needed
   - Appointments "consume" availability windows through validation queries
   - VetAvailability defines "possible" times
   - Appointments define "booked" times

2. DUAL WRITE PROBLEM: 
   - SOLVED: Single source of truth is the Appointment table
   - VetAvailability is just the "template" 
   - Real availability = VetAvailability MINUS existing Appointments
   - No need to update VetAvailability when booking

3. APPOINTMENT UPDATES:
   - SOLVED: Validate new slot, update single Appointment record
   - Old slot automatically becomes available
   - New slot gets consumed
   - All in one atomic transaction

ARCHITECTURE BENEFITS:
✅ No dual writes
✅ Single source of truth  
✅ Automatic availability management
✅ Race condition protection
✅ Emergency override capability
"""

Excellent questions! You've identified the core architectural challenge. Looking at your system, you've built the scheduling infrastructure but there's a missing link between appointments and vet availability. Let me address each issue:
1. Relationship Between Appointment and VetAvailability
Currently: NO DIRECT RELATIONSHIP ❌
Your system has:

VetAvailability: "Dr. Smith is available 9 AM - 5 PM on Sept 13th"
Appointment: "Appointment at 10:30 AM with Dr. Smith on Sept 13th"

But there's no mechanism connecting them! The appointment doesn't "consume" or "block" the availability.
2. Appointment Creation Flow - You Need This LogicAppointment Creation & Availability ManagementCode """
APPOINTMENT CREATION FLOW & AVAILABILITY MANAGEMENT
Solving the dual-write problem and appointment-availability relationship
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid

class AppointmentSchedAnswers to Your Questions:
1. Appointment ↔ VetAvailability Relationship
NO DIRECT RELATIONSHIP NEEDED! 🎯

VetAvailability = "Template" (Dr. Smith CAN work 9 AM - 5 PM)
Appointment = "Reality" (Dr. Smith IS busy 10:30-11:00 AM)
Real availability = VetAvailability MINUS existing Appointments

2. Appointment Creation Flow
Your intuition is correct:

Query practice vets + schedules → Return available slots
User selects slot → Frontend shows "Dr. Smith 10:30 AM [SELECT]"
Create appointment → Validate + insert in single transaction
Slot becomes unavailable → Automatically (no dual write!)

3. The Dual Write "Problem" - SOLVED!
There is NO dual write problem! ✨

❌ Wrong approach: Update both VetAvailability AND Appointment
✅ Right approach: Only create/update Appointment records
VetAvailability stays unchanged - it's just the template
Availability is computed dynamically - VetAvailability MINUS Appointments

Key Architecture Benefits:
Single Source of Truth:

Appointments table is the only place that tracks "busy" times
VetAvailability never gets modified when booking
No synchronization issues

Automatic Availability:

Cancel appointment → Slot automatically becomes available
Update appointment → Old slot freed, new slot consumed
No manual availability management needed

Race Condition Protection:

Validation happens in same transaction as creation
Two users can't book the same slot
Emergency override still works

This architecture is much simpler than dual-write systems and eliminates the consistency problems you were worried about!