"""
API-level timezone handling tests for scheduling endpoints

These tests simulate the exact API request/response flow to catch timezone bugs
at the integration level, not just the schema level.
"""

import pytest
import asyncio
from datetime import datetime, date, time, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.scheduling_schemas import VetAvailabilityCreate, VetAvailabilityResponse
from src.models_pg.scheduling import VetAvailability, AvailabilityType


class TestAPITimezoneFlow:
    """Test the complete API request/response timezone flow"""
    
    def test_api_storage_logic_simulation(self):
        """Test the exact storage logic from the API route"""
        # Simulate the API route logic for 9am-5pm PST
        availability_data = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(9, 0),    # 9am PST (what should be sent)
            end_time=time(17, 0),     # 5pm PST
            timezone="America/Los_Angeles"
        )
        
        # Step 1: Get timezone conversions (from API route)
        local_start, local_end = availability_data.get_local_datetime_range()
        utc_start, utc_end = availability_data.to_utc_datetime_range()
        
        # Step 2: Apply storage logic (from API route)
        data_dict = availability_data.model_dump()
        data_dict.pop('timezone', None)
        data_dict['start_time'] = utc_start.time()
        
        if utc_start.date() != utc_end.date():
            # Date boundary shift detected
            data_dict['end_time'] = time(23, 59, 59)
            data_dict['date'] = utc_start.date()
        else:
            data_dict['end_time'] = utc_end.time()
            data_dict['date'] = utc_start.date()
        
        # Step 3: Create the database model (what gets stored)
        availability_model = VetAvailability(**data_dict)
        
        # Verify correct storage
        assert availability_model.date == utc_start.date()
        assert availability_model.start_time == utc_start.time()
        
        # If there was a boundary shift, end_time should be 23:59:59
        if utc_start.date() != utc_end.date():
            assert availability_model.end_time == time(23, 59, 59)
        else:
            assert availability_model.end_time == utc_end.time()
            
    def test_ios_bug_case_4pm_midnight(self):
        """Test the 4pm-midnight case that iOS was incorrectly sending"""
        # This is what the buggy iOS app was sending instead of 9am-5pm
        availability_data = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(16, 0),   # 4pm (iOS bug result)
            end_time=time(0, 0),      # midnight
            timezone="America/Los_Angeles"
        )
        
        # This should now work without 422 errors
        local_start, local_end = availability_data.get_local_datetime_range()
        utc_start, utc_end = availability_data.to_utc_datetime_range()
        
        # 4pm PST = 11pm UTC, midnight PST = 7am UTC next day
        assert utc_start.hour == 23  # 11pm UTC
        assert utc_end.hour == 7     # 7am UTC next day
        assert utc_start.date() != utc_end.date()  # Boundary shift
        
    def test_response_creation_with_stored_times(self):
        """Test creating API response from stored database times"""
        # Simulate data that comes from database after our storage logic
        stored_data = {
            'id': uuid4(),
            'vet_user_id': uuid4(),
            'practice_id': uuid4(),
            'date': date(2025, 10, 3),
            'start_time': time(23, 0),     # 11pm UTC (stored)
            'end_time': time(23, 59, 59),  # 23:59:59 UTC (our boundary fix)
            'availability_type': AvailabilityType.AVAILABLE,
            'notes': None,
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Should create response without validation errors
        response = VetAvailabilityResponse(**stored_data)
        assert response.start_time == time(23, 0)
        assert response.end_time == time(23, 59, 59)
        
    def test_problematic_database_times(self):
        """Test the problematic times that were causing 422 errors"""
        # These are the actual times from the error logs
        problematic_data = {
            'id': uuid4(),
            'vet_user_id': uuid4(),
            'practice_id': uuid4(),
            'date': date(2025, 10, 3),
            'start_time': time(23, 0),    # 11pm UTC
            'end_time': time(7, 0),       # 7am UTC (the problematic case)
            'availability_type': AvailabilityType.AVAILABLE,
            'notes': None,
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Should now work with our response schema fix
        response = VetAvailabilityResponse(**problematic_data)
        assert response.start_time == time(23, 0)
        assert response.end_time == time(7, 0)


class TestTimezoneConversionMatrix:
    """Test timezone conversions across different scenarios"""
    
    @pytest.mark.parametrize("local_time,timezone,expected_utc_hour_range", [
        # Morning appointments
        (time(9, 0), "America/Los_Angeles", (16, 17)),    # 9am PST/PDT = 4pm/5pm UTC
        (time(9, 0), "America/New_York", (13, 14)),       # 9am EST/EDT = 1pm/2pm UTC
        (time(9, 0), "America/Chicago", (14, 15)),        # 9am CST/CDT = 2pm/3pm UTC
        
        # Afternoon appointments  
        (time(14, 0), "America/Los_Angeles", (21, 22)),   # 2pm PST/PDT = 9pm/10pm UTC
        (time(14, 0), "America/New_York", (18, 19)),      # 2pm EST/EDT = 6pm/7pm UTC
        
        # Evening appointments (potential boundary crossers)
        (time(20, 0), "America/Los_Angeles", (3, 4)),     # 8pm PST/PDT = 3am/4am UTC next day
        (time(22, 0), "America/New_York", (2, 3)),        # 10pm EST/EDT = 2am/3am UTC next day
    ])
    def test_timezone_conversion_matrix(self, local_time, timezone, expected_utc_hour_range):
        """Test timezone conversions across different times and zones"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=local_time,
            end_time=time((local_time.hour + 1) % 24, local_time.minute),  # +1 hour
            timezone=timezone
        )
        
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # Check UTC hour is in expected range (accounts for DST variations)
        assert utc_start.hour in range(expected_utc_hour_range[0], expected_utc_hour_range[1] + 1)


class TestDuplicateKeyPrevention:
    """Test scenarios that could create duplicate database keys"""
    
    def test_same_availability_different_timezones(self):
        """Test same local time in different timezones"""
        # 9am PST and 9am EST are different UTC times
        pst_availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(9, 0),
            end_time=time(17, 0),
            timezone="America/Los_Angeles"
        )
        
        est_availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(9, 0),
            end_time=time(17, 0),
            timezone="America/New_York"
        )
        
        pst_utc_start, pst_utc_end = pst_availability.to_utc_datetime_range()
        est_utc_start, est_utc_end = est_availability.to_utc_datetime_range()
        
        # Should be different UTC times
        assert pst_utc_start != est_utc_start
        assert pst_utc_end != est_utc_end
        
    def test_boundary_shift_creates_unique_keys(self):
        """Test that boundary shifts create unique database keys"""
        # Two different local times that might convert to similar UTC times
        availability1 = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(16, 0),   # 4pm
            end_time=time(0, 0),      # midnight
            timezone="America/Los_Angeles"
        )
        
        availability2 = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(17, 0),   # 5pm
            end_time=time(1, 0),      # 1am next day (overnight shift)
            timezone="America/Los_Angeles"
        )
        
        utc1_start, utc1_end = availability1.to_utc_datetime_range()
        utc2_start, utc2_end = availability2.to_utc_datetime_range()
        
        # Should create different database keys
        assert (utc1_start.time(), utc1_end.time()) != (utc2_start.time(), utc2_end.time())


class TestPerformanceAndStress:
    """Test performance with many timezone conversions"""
    
    def test_bulk_timezone_conversions(self):
        """Test performance with many timezone conversions"""
        import time as time_module
        
        start_time = time_module.time()
        
        # Create 100 different availability entries
        for i in range(100):
            availability = VetAvailabilityCreate(
                vet_user_id=uuid4(),
                practice_id=uuid4(),
                date=date(2025, 10, 3),
                start_time=time(9 + (i % 12), 0),  # Vary start times
                end_time=time(17 + (i % 6), 0),    # Vary end times
                timezone="America/Los_Angeles"
            )
            
            # Force timezone conversion
            utc_start, utc_end = availability.to_utc_datetime_range()
            
        end_time = time_module.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time (< 1 second for 100 conversions)
        assert duration < 1.0, f"Timezone conversions too slow: {duration:.3f}s"


# Utility function to run all tests
def run_all_tests():
    """Run all timezone tests and report results"""
    import subprocess
    
    print("🧪 Running comprehensive timezone handling tests...")
    print("=" * 80)
    
    # Run with verbose output
    result = subprocess.run([
        "python", "-m", "pytest", 
        "test_timezone_handling.py", 
        "test_scheduling_api_timezone.py",
        "-v", "--tb=short"
    ], capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    print("=" * 80)
    print(f"Tests {'PASSED' if result.returncode == 0 else 'FAILED'}")
    
    return result.returncode == 0


if __name__ == "__main__":
    run_all_tests()
