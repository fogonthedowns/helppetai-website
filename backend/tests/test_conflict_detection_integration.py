"""
Integration test for appointment conflict detection in get_first_available_flexible

This test verifies the fix for the bug where booked appointments were still
appearing as available in the scheduling system.
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import pytz
from unittest.mock import AsyncMock, patch

from src.models_pg.user import User, UserRole
from src.models_pg.practice import VeterinaryPractice
from src.models_pg.pet_owner import PetOwner
from src.models_pg.pet import Pet
from src.models_pg.appointment import Appointment
from src.models_pg.scheduling_unix import VetAvailability
from src.auth.jwt_auth_pg import get_password_hash


class TestConflictDetectionIntegration:
    """Integration test for appointment conflict detection"""
    
    def setup_method(self):
        """Setup test data using mocks to avoid async database issues"""
        
        # Create test data objects
        self.practice_id = uuid4()
        self.vet_user_id = uuid4()
        self.pet_owner_id = uuid4()
        self.pet_id = uuid4()
        
        self.practice = VeterinaryPractice(
            id=self.practice_id,
            name="Test Practice",
            phone="555-0123",
            email="test@practice.com",
            address_line1="123 Test St",
            license_number="TEST-001",
            timezone="US/Pacific"
        )
        
        self.vet_user = User(
            id=self.vet_user_id,
            username="vet1",
            password_hash=get_password_hash("password"),
            email="vet1@test.com",
            full_name="Test Vet",
            role=UserRole.VET_STAFF,
            practice_id=self.practice_id,
            is_active=True
        )
        
        self.pet_owner = PetOwner(
            id=self.pet_owner_id,
            full_name="Pet Owner",
            email="owner@test.com",
            phone="555-1234",
            address="456 Oak St"
        )
        
        self.pet = Pet(
            id=self.pet_id,
            owner_id=self.pet_owner_id,
            name="Test Pet",
            species="dog",
            breed="mutt",
            gender="male"
        )
    
    @pytest.mark.asyncio
    async def test_appointment_conflict_detection(self, test_db_session, test_data):
        """
        Test that booked appointments don't appear as available in get_first_available_flexible
        
        This is the core test for the bug we just fixed.
        """
        session = test_db_session
        practice = test_data["practice"]
        vet_user = test_data["vet_user"]
        pet = test_data["pet"]
        
        # Set up availability for tomorrow 9 AM - 5 PM PST (16:00 - 00:00 UTC)
        pst_tz = pytz.timezone("US/Pacific")
        tomorrow = datetime.now(pst_tz).date() + timedelta(days=1)
        
        # 9 AM PST = 16:00 UTC (during PST) or 17:00 UTC (during PDT)
        availability_start_local = pst_tz.localize(datetime.combine(tomorrow, datetime.min.time().replace(hour=9)))
        availability_end_local = pst_tz.localize(datetime.combine(tomorrow, datetime.min.time().replace(hour=17)))
        
        availability_start_utc = availability_start_local.astimezone(pytz.UTC)
        availability_end_utc = availability_end_local.astimezone(pytz.UTC)
        
        # Create vet availability
        availability = VetAvailability(
            id=uuid4(),
            vet_user_id=vet_user.id,
            practice_id=practice.id,
            start_at=availability_start_utc,
            end_at=availability_end_utc,
            is_active=True
        )
        session.add(availability)
        
        # Create a conflicting appointment at 9:00 AM PST (16:00 UTC)
        appointment_time_utc = availability_start_utc  # Exactly 9:00 AM PST
        
        conflicting_appointment = Appointment(
            id=uuid4(),
            pet_id=pet.id,
            practice_id=practice.id,
            assigned_vet_user_id=vet_user.id,
            appointment_date=appointment_time_utc,
            duration_minutes=30,
            title="Conflicting Appointment",
            appointment_type="checkup",
            status="scheduled"
        )
        session.add(conflicting_appointment)
        
        await session.commit()
        
        print(f"\n🔍 TEST SETUP:")
        print(f"   Practice: {practice.name} (ID: {practice.id})")
        print(f"   Vet: {vet_user.full_name} (ID: {vet_user.id})")
        print(f"   Date: {tomorrow}")
        print(f"   Availability: {availability_start_local} - {availability_end_local} PST")
        print(f"   Availability UTC: {availability_start_utc} - {availability_end_utc}")
        print(f"   Conflicting appointment: {appointment_time_utc} UTC (9:00 AM PST)")
        
        # Now test the get_first_available_flexible function directly
        from src.services.phone.scheduling_service_unix import UnixTimestampSchedulingService
        
        scheduling_service = UnixTimestampSchedulingService(session)
        
        # Call get_first_available_flexible for the day with the conflict
        result = await scheduling_service.get_first_available_flexible(
            time_preference="any time",
            practice_id=str(practice.id),
            timezone="US/Pacific",
            date_range_start=tomorrow.strftime("%Y-%m-%d"),
            date_range_end=tomorrow.strftime("%Y-%m-%d")
        )
        
        print(f"\n📅 RESULT:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Appointments found: {len(result.get('appointments', []))}")
        
        appointments = result.get('appointments', [])
        if appointments:
            first_appointment = appointments[0]
            print(f"   First available time: {first_appointment.get('time', 'N/A')}")
            print(f"   Date: {first_appointment.get('date', 'N/A')}")
            
            # CRITICAL TEST: The first available time should NOT be 9:00 AM
            # because there's a conflicting appointment at that time
            assert first_appointment['time'] != "9:00 AM", \
                "❌ BUG: 9:00 AM appears as available despite conflicting appointment!"
            
            # The first available time should be 9:30 AM (after the 30-min appointment)
            assert first_appointment['time'] == "9:30 AM", \
                f"❌ Expected first available time to be 9:30 AM, got {first_appointment['time']}"
            
            print(f"✅ PASS: Conflict detection working - 9:00 AM correctly excluded")
            print(f"✅ PASS: First available time is {first_appointment['time']} (expected 9:30 AM)")
        else:
            pytest.fail("❌ No appointments returned - expected at least 9:30 AM to be available")
    
    @pytest.mark.asyncio
    async def test_no_conflict_when_no_appointment(self, test_db_session, test_data):
        """
        Test that 9:00 AM appears as available when there's no conflicting appointment
        """
        session = test_db_session
        practice = test_data["practice"]
        vet_user = test_data["vet_user"]
        
        # Set up availability for day after tomorrow (no conflicts)
        pst_tz = pytz.timezone("US/Pacific")
        day_after_tomorrow = datetime.now(pst_tz).date() + timedelta(days=2)
        
        availability_start_local = pst_tz.localize(datetime.combine(day_after_tomorrow, datetime.min.time().replace(hour=9)))
        availability_end_local = pst_tz.localize(datetime.combine(day_after_tomorrow, datetime.min.time().replace(hour=17)))
        
        availability_start_utc = availability_start_local.astimezone(pytz.UTC)
        availability_end_utc = availability_end_local.astimezone(pytz.UTC)
        
        # Create vet availability (no conflicting appointments)
        availability = VetAvailability(
            id=uuid4(),
            vet_user_id=vet_user.id,
            practice_id=practice.id,
            start_at=availability_start_utc,
            end_at=availability_end_utc,
            is_active=True
        )
        session.add(availability)
        await session.commit()
        
        # Test the scheduling service
        from src.services.phone.scheduling_service_unix import UnixTimestampSchedulingService
        
        scheduling_service = UnixTimestampSchedulingService(session)
        
        result = await scheduling_service.get_first_available_flexible(
            time_preference="any time",
            practice_id=str(practice.id),
            timezone="US/Pacific",
            date_range_start=day_after_tomorrow.strftime("%Y-%m-%d"),
            date_range_end=day_after_tomorrow.strftime("%Y-%m-%d")
        )
        
        print(f"\n📅 NO CONFLICT TEST:")
        appointments = result.get('appointments', [])
        if appointments:
            first_appointment = appointments[0]
            print(f"   First available time: {first_appointment.get('time', 'N/A')}")
            
            # When there's no conflict, 9:00 AM should be the first available time
            assert first_appointment['time'] == "9:00 AM", \
                f"❌ Expected 9:00 AM to be available when no conflict, got {first_appointment['time']}"
            
            print(f"✅ PASS: No conflict - 9:00 AM correctly appears as available")
        else:
            pytest.fail("❌ No appointments returned - expected 9:00 AM to be available")


if __name__ == "__main__":
    # Allow running this test directly
    pytest.main([__file__, "-v"])
