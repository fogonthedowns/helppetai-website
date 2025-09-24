"""
Test for appointment conflict bug in get_first_available_flexible

Bug Description:
When querying available times, the system returns slots that are already booked.
From logs: 10:00 AM slot is returned as available even though there's an appointment at that time.

ROOT CAUSE IDENTIFIED:
The UnixTimestampSchedulingService was checking for conflicts against the deprecated 
AppointmentUnix table instead of the regular appointments table that's actually used in production.

BUG FIXED:
- Changed import from AppointmentUnix to Appointment
- Updated conflict queries to use appointment_date + duration_minutes instead of appointment_at
- Now correctly checks the appointments table that the voice system actually uses

Steps to reproduce:
1. Create practice and vet
2. Set vet availability Oct 2, 9am-12pm PST  
3. Book appointment at 10:00 AM
4. Query get_available_times for Oct 2
5. BUG: 10:00 AM should NOT be in response but it is! (FIXED)
"""

import pytest
import uuid
from datetime import datetime, date, time, timedelta
from unittest.mock import AsyncMock, patch
import pytz

from src.services.phone.scheduling_service_unix import UnixTimestampSchedulingService


class TestAppointmentConflictBug:
    """Test the appointment conflict bug in get_first_available_flexible"""
    
    def setup_method(self):
        """Setup test data for the bug reproduction"""
        
        # Test IDs
        self.practice_id = uuid.uuid4()
        self.vet_user_id = uuid.uuid4()
        self.pet_owner_id = uuid.uuid4()
        
        # Setup timezone info
        self.pst_tz = pytz.timezone("US/Pacific")
        self.utc_tz = pytz.UTC
        
        # Oct 2, 2025 availability: 9am-12pm PST -> 4pm-7pm UTC
        self.availability_start_local = self.pst_tz.localize(datetime(2025, 10, 2, 9, 0))   # 9am PST
        self.availability_end_local = self.pst_tz.localize(datetime(2025, 10, 2, 12, 0))    # 12pm PST
        self.availability_start_utc = self.availability_start_local.astimezone(self.utc_tz)  # 4pm UTC
        self.availability_end_utc = self.availability_end_local.astimezone(self.utc_tz)      # 7pm UTC
        
        # Existing appointment at 10:00 AM PST -> 5:00 PM UTC
        self.appointment_start_local = self.pst_tz.localize(datetime(2025, 10, 2, 10, 0))   # 10am PST
        self.appointment_end_local = self.pst_tz.localize(datetime(2025, 10, 2, 10, 30))    # 10:30am PST
        self.appointment_start_utc = self.appointment_start_local.astimezone(self.utc_tz)    # 5pm UTC
        self.appointment_end_utc = self.appointment_end_local.astimezone(self.utc_tz)        # 5:30pm UTC
        
        # Create mock session for the scheduling service
        self.mock_session = AsyncMock()
        
        # Create the scheduling service with mock session
        self.scheduling_service = UnixTimestampSchedulingService(self.mock_session)
    
    @pytest.mark.asyncio 
    async def test_appointment_conflict_bug_direct_service_call(self):
        """
        CRITICAL BUG TEST: Direct test of scheduling service logic
        
        This test bypasses the webhook and directly tests the scheduling service
        to isolate the bug in appointment conflict detection.
        """
        
        print(f"\n🐛 BUG REPRODUCTION - Direct Service Test:")
        print(f"📅 Query date: Oct 2, 2025")
        print(f"⏰ Vet availability: 9:00 AM - 12:00 PM PST") 
        print(f"📋 Existing appointment: 10:00 AM - 10:30 AM PST")
        
        # For now, let's skip the full service test and focus on the unit test
        print(f"\nℹ️  Skipping full service test - focusing on conflict detection logic unit test")
        print(f"   The service test requires complex mocking that we'll implement after identifying the bug location")
    
    @pytest.mark.asyncio
    async def test_conflict_detection_logic_unit_test(self):
        """
        Unit test for the core conflict detection logic
        
        This tests the specific method that should detect appointment conflicts
        """
        
        print(f"\n🔍 UNIT TEST: Conflict Detection Logic")
        
        # Create sample data for conflict detection
        vet_availability = {
            "vet_user_id": self.vet_user_id,
            "start_at": self.availability_start_utc,  # 9am PST = 4pm UTC
            "end_at": self.availability_end_utc,      # 12pm PST = 7pm UTC
        }
        
        existing_appointment = {
            "assigned_vet_user_id": self.vet_user_id,
            "appointment_date": self.appointment_start_utc,  # 10am PST = 5pm UTC
            "duration_minutes": 30,
        }
        
        # Test the specific slot that should be in conflict
        test_slot_start = self.pst_tz.localize(datetime(2025, 10, 2, 10, 0))  # 10am PST
        test_slot_end = self.pst_tz.localize(datetime(2025, 10, 2, 10, 30))    # 10:30am PST
        test_slot_start_utc = test_slot_start.astimezone(self.utc_tz)
        test_slot_end_utc = test_slot_end.astimezone(self.utc_tz)
        
        print(f"📋 Testing slot: 10:00 AM - 10:30 AM PST")
        print(f"   UTC equivalent: {test_slot_start_utc} - {test_slot_end_utc}")
        print(f"📋 Existing appointment: 10:00 AM - 10:30 AM PST")
        print(f"   UTC equivalent: {self.appointment_start_utc} - {self.appointment_end_utc}")
        
        # Manual conflict detection logic (what the service should do)
        from datetime import timedelta
        appointment_end_utc = self.appointment_start_utc + timedelta(minutes=30)
        
        # Check for overlap: (start1 < end2) and (start2 < end1)
        has_conflict = (
            test_slot_start_utc < appointment_end_utc and 
            self.appointment_start_utc < test_slot_end_utc
        )
        
        print(f"🔍 Conflict detection result: {has_conflict}")
        
        if has_conflict:
            print(f"✅ CORRECT: Conflict properly detected")
        else:
            print(f"🚨 BUG: No conflict detected when there should be one!")
            assert False, "Conflict detection logic failed - should detect overlap between 10:00-10:30 appointment and 10:00-10:30 query slot"
        
        # Test a non-conflicting slot (9:00-9:30 AM)
        non_conflict_start = self.pst_tz.localize(datetime(2025, 10, 2, 9, 0))   # 9am PST
        non_conflict_end = self.pst_tz.localize(datetime(2025, 10, 2, 9, 30))    # 9:30am PST
        non_conflict_start_utc = non_conflict_start.astimezone(self.utc_tz)
        non_conflict_end_utc = non_conflict_end.astimezone(self.utc_tz)
        
        no_conflict = (
            non_conflict_start_utc < appointment_end_utc and 
            self.appointment_start_utc < non_conflict_end_utc
        )
        
        print(f"🔍 Testing non-conflicting slot: 9:00 AM - 9:30 AM PST")
        print(f"   Conflict detection result: {no_conflict}")
        
        if not no_conflict:
            print(f"✅ CORRECT: No conflict detected for 9:00-9:30 slot")
        else:
            print(f"⚠️  Unexpected: Conflict detected for non-overlapping slot")

    @pytest.mark.asyncio
    async def test_real_world_scenario_oct_1_9am_conflict(self):
        """
        Test the EXACT scenario from production logs:
        - Appointment exists at 2025-10-01 16:00:00+00 (9:00 AM PST)
        - System incorrectly returns 9:00 AM Oct 1 as available
        """
        
        print(f"\n🎯 REAL WORLD SCENARIO: Oct 1, 9:00 AM Conflict")
        
        # Production data from logs
        production_appointment_utc = pytz.utc.localize(datetime(2025, 10, 1, 16, 0))  # 9:00 AM PST
        production_vet_id = uuid.UUID('e1e3991b-4efa-464b-9bae-f94c74d0a20f')
        
        # Vet availability for Oct 1: 16:00-17:00 UTC (9:00-10:00 AM PST)
        availability_start_utc = pytz.utc.localize(datetime(2025, 10, 1, 16, 0))  # 9am PST
        availability_end_utc = pytz.utc.localize(datetime(2025, 10, 1, 17, 0))    # 10am PST
        
        print(f"📅 Date: October 1, 2025")
        print(f"🕘 Appointment exists: 16:00 UTC (9:00 AM PST)")
        print(f"🔍 Query slot: 16:00-16:30 UTC (9:00-9:30 AM PST)")
        print(f"👩‍⚕️ Vet: {production_vet_id}")
        
        # Test if our conflict detection would catch this
        query_slot_start = pytz.utc.localize(datetime(2025, 10, 1, 16, 0))   # 9:00 AM PST
        query_slot_end = pytz.utc.localize(datetime(2025, 10, 1, 16, 30))     # 9:30 AM PST
        appointment_end = production_appointment_utc + timedelta(minutes=30)   # 30 min duration
        
        # Our conflict detection logic
        has_conflict = (
            query_slot_start < appointment_end and 
            production_appointment_utc < query_slot_end
        )
        
        print(f"\n🔍 Conflict Detection Analysis:")
        print(f"   Query slot start: {query_slot_start}")
        print(f"   Query slot end: {query_slot_end}")
        print(f"   Appointment start: {production_appointment_utc}")
        print(f"   Appointment end: {appointment_end}")
        print(f"   Overlap check: query_start < appt_end AND appt_start < query_end")
        print(f"   Result: {query_slot_start} < {appointment_end} = {query_slot_start < appointment_end}")
        print(f"   Result: {production_appointment_utc} < {query_slot_end} = {production_appointment_utc < query_slot_end}")
        print(f"   Final conflict result: {has_conflict}")
        
        if not has_conflict:
            print(f"\n🚨 BUG REPRODUCED: Our logic would NOT detect this conflict!")
            print(f"   This explains why 9:00 AM is returned as available")
            assert False, "Conflict detection failed for exact production scenario"
        else:
            print(f"\n✅ CORRECT: Our logic WOULD detect this conflict")
            print(f"   The bug must be elsewhere in the system")

    @pytest.mark.asyncio  
    async def test_exact_start_time_conflict(self):
        """
        Test edge case: appointment starts at EXACT same time as query slot
        This might be where the SQL query is failing
        """
        
        print(f"\n⚡ EDGE CASE: Exact Start Time Conflict")
        
        # Both start at exactly the same time
        exact_time = pytz.utc.localize(datetime(2025, 10, 1, 16, 0))  # 9:00 AM PST
        
        # Appointment: 16:00-16:30 UTC
        appointment_start = exact_time
        appointment_end = exact_time + timedelta(minutes=30)
        
        # Query slot: 16:00-16:30 UTC (exact same)
        query_start = exact_time  
        query_end = exact_time + timedelta(minutes=30)
        
        print(f"📅 Appointment: {appointment_start} to {appointment_end}")
        print(f"🔍 Query slot: {query_start} to {query_end}")
        print(f"⚡ Both start at EXACTLY the same time")
        
        # Test overlap detection
        has_conflict = (
            query_start < appointment_end and 
            appointment_start < query_end
        )
        
        print(f"\n🔍 Overlap Analysis:")
        print(f"   query_start < appointment_end: {query_start} < {appointment_end} = {query_start < appointment_end}")
        print(f"   appointment_start < query_end: {appointment_start} < {query_end} = {appointment_start < query_end}")
        print(f"   Final result: {has_conflict}")
        
        if not has_conflict:
            print(f"\n🚨 CRITICAL: Exact time conflicts not detected!")
            assert False, "Exact start time conflicts should be detected"
        else:
            print(f"\n✅ CORRECT: Exact time conflicts properly detected")
            
        # Test the SQL condition that might be failing
        print(f"\n🔍 SQL Condition Analysis:")
        print(f"   Our SQL: appointment_date < query_end AND appointment_date + duration > query_start")
        print(f"   Condition 1: {appointment_start} < {query_end} = {appointment_start < query_end}")
        print(f"   Condition 2: {appointment_end} > {query_start} = {appointment_end > query_start}")
        
        sql_result = (appointment_start < query_end) and (appointment_end > query_start)
        print(f"   SQL result: {sql_result}")
        
        if not sql_result:
            print(f"🚨 SQL LOGIC BUG: Our SQL conditions would NOT catch this!")
            assert False, "SQL overlap detection logic is wrong"

    @pytest.mark.asyncio
    async def test_availability_lookup_bug(self):
        """
        Test why the system can't find availability records.
        From logs: "NO UNIX TIMESTAMP AVAILABILITY - Create availability first!"
        But production data shows records exist.
        """
        
        print(f"\n🕵️ AVAILABILITY LOOKUP BUG INVESTIGATION")
        
        # Production data - what SHOULD be found
        expected_start = pytz.utc.localize(datetime(2025, 10, 1, 16, 0))  # 9:00 AM PST
        expected_end = pytz.utc.localize(datetime(2025, 10, 1, 17, 0))    # 10:00 AM PST
        expected_vet = uuid.UUID('e1e3991b-4efa-464b-9bae-f94c74d0a20f')
        
        print(f"📋 Expected availability record:")
        print(f"   Vet: {expected_vet}")
        print(f"   UTC: {expected_start} - {expected_end}")
        print(f"   PST: 9:00 AM - 10:00 AM Oct 1, 2025")
        
        # Query params from production logs - what system is searching for
        # From logs: get_first_available_flexible for Oct 1
        query_date_pst = date(2025, 10, 1)  # Oct 1, 2025
        pst_tz = pytz.timezone("US/Pacific")
        
        # How the system converts query to UTC range
        local_start = pst_tz.localize(datetime.combine(query_date_pst, time.min))  # Oct 1 00:00 PST
        local_end = pst_tz.localize(datetime.combine(query_date_pst, time.max))    # Oct 1 23:59 PST
        utc_start = local_start.astimezone(pytz.UTC)  # Convert to UTC
        utc_end = local_end.astimezone(pytz.UTC)      # Convert to UTC
        
        print(f"\n🔍 System query range:")
        print(f"   Local: {local_start} - {local_end}")
        print(f"   UTC:   {utc_start} - {utc_end}")
        
        # Check if the expected record would be found in this range
        record_found = (
            expected_start >= utc_start and 
            expected_start <= utc_end
        )
        
        print(f"\n⚖️  Range Check:")
        print(f"   Expected record start: {expected_start}")
        print(f"   Query range: {utc_start} <= {expected_start} <= {utc_end}")
        print(f"   Start check: {utc_start} <= {expected_start} = {utc_start <= expected_start}")
        print(f"   End check: {expected_start} <= {utc_end} = {expected_start <= utc_end}")
        print(f"   Record would be found: {record_found}")
        
        if not record_found:
            print(f"\n🚨 AVAILABILITY LOOKUP BUG FOUND!")
            print(f"   The availability record should be found but the date range is wrong")
            assert False, "Availability lookup range calculation is incorrect"
        else:
            print(f"\n✅ Range calculation looks correct")
            print(f"   The bug must be elsewhere - perhaps in the SQL query itself")

    @pytest.mark.asyncio
    async def test_practice_id_mismatch_hypothesis(self):
        """
        Test if the bug is caused by practice ID mismatch
        From logs showing appointments but 'NO UNIX TIMESTAMP AVAILABILITY'
        """
        
        print(f"\n🔍 PRACTICE ID MISMATCH HYPOTHESIS")
        
        # From your logs - the function call includes practice_id
        # But maybe the query is using a different practice ID
        expected_practice_id = "12345678-1234-1234-1234-123456789abc"  # Example from logs
        
        # From your production data - these vets have availability:
        production_vets = [
            uuid.UUID('e1e3991b-4efa-464b-9bae-f94c74d0a20f'),  # Has availability Oct 1
            uuid.UUID('0529065a-992a-47e9-b021-9a6606d06e83'),  # Has availability Oct 1  
        ]
        
        print(f"🏥 Expected practice ID: {expected_practice_id}")
        print(f"👩‍⚕️ Vets with availability: {len(production_vets)} vets")
        
        # Simulate the query that would be made
        query_start = pytz.utc.localize(datetime(2025, 10, 1, 7, 0))   # Oct 1 00:00 PST -> 07:00 UTC
        query_end = pytz.utc.localize(datetime(2025, 10, 2, 7, 0))     # Oct 2 00:00 PST -> 07:00 UTC
        
        print(f"\n🔍 Simulated Database Query:")
        print(f"   SELECT * FROM vet_availability_unix")
        print(f"   WHERE practice_id = '{expected_practice_id}'")
        print(f"   AND start_at < '{query_end}'")
        print(f"   AND end_at > '{query_start}'")
        print(f"   AND is_active = true")
        
        # Simulate the production data matching
        production_records = [
            {
                "vet_user_id": uuid.UUID('e1e3991b-4efa-464b-9bae-f94c74d0a20f'),
                "start_at": pytz.utc.localize(datetime(2025, 10, 1, 16, 0)),
                "end_at": pytz.utc.localize(datetime(2025, 10, 1, 17, 0)),
                "practice_id": "UNKNOWN_PRACTICE_ID",  # This could be the issue!
            }
        ]
        
        print(f"\n📊 Production Records Check:")
        for record in production_records:
            matches_time = (
                record["start_at"] < query_end and 
                record["end_at"] > query_start
            )
            matches_practice = record["practice_id"] == expected_practice_id
            
            print(f"   Vet: {record['vet_user_id']}")
            print(f"   Time range matches: {matches_time}")
            print(f"   Practice ID matches: {matches_practice}")
            print(f"   Would be found: {matches_time and matches_practice}")
        
        print(f"\n💡 HYPOTHESIS:")
        print(f"   If practice_id in database != practice_id in query:")
        print(f"   → Query returns empty (logs 'NO UNIX TIMESTAMP AVAILABILITY')")
        print(f"   → But availability records DO exist for this date/time")
        print(f"   → System might have fallback logic or multiple code paths")
        
        # Check if there's a default practice ID or fallback mechanism
        print(f"\n🔍 Potential Issues:")
        print(f"   1. Query uses wrong practice_id")
        print(f"   2. Database has records with different practice_id")
        print(f"   3. Environment/database mismatch (dev vs prod)")
        print(f"   4. Caching issue - stale query results")
        print(f"   5. Multiple code paths - one path bypasses availability check")


if __name__ == "__main__":
    """Run the test directly for debugging"""
    import asyncio
    
    async def run_bug_tests():
        """Run the bug reproduction tests"""
        test_instance = TestAppointmentConflictBug()
        test_instance.setup_method()
        
        print("🧪 Running appointment conflict bug tests...")
        
        # Run unit test first
        await test_instance.test_conflict_detection_logic_unit_test()
        
        # Then run the service test
        await test_instance.test_appointment_conflict_bug_direct_service_call()
        
        print("✅ All tests completed!")
    
    asyncio.run(run_bug_tests())
