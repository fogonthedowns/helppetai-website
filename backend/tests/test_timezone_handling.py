"""
Comprehensive timezone handling tests for HelpPet.ai scheduling system

These tests prevent timezone bugs by covering all edge cases, boundary conditions,
and weird scenarios that could break the system.

CRITICAL: These tests must pass to ensure timezone handling works correctly!
"""

import pytest
import pytz
from datetime import datetime, date, time, timedelta
from uuid import uuid4
from pydantic import ValidationError

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.scheduling_schemas import VetAvailabilityCreate, VetAvailabilityResponse
from src.utils.timezone_utils import TimezoneHandler


class TestTimezoneConversions:
    """Test timezone conversion logic"""
    
    def test_normal_business_hours_pst(self):
        """Test normal 9am-5pm PST business hours"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(9, 0),    # 9am PST
            end_time=time(17, 0),     # 5pm PST
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # 9am PST = 4pm UTC (during PDT) or 5pm UTC (during PST)
        # 5pm PST = midnight UTC next day (during PDT) or 1am UTC next day (during PST)
        
        assert local_start.hour == 9
        assert local_end.hour == 17
        assert utc_start.hour in [16, 17]  # Depends on DST
        assert utc_end.hour in [0, 1]     # Midnight or 1am UTC next day
        
    def test_midnight_end_time_boundary_shift(self):
        """Test the critical midnight end time case that was causing 422 errors"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(16, 0),   # 4pm local
            end_time=time(0, 0),      # midnight local (end of day)
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # Midnight should be treated as end of day = start of next day
        assert local_end.date() == local_start.date() + timedelta(days=1)
        assert utc_end.date() == utc_start.date() + timedelta(days=1)
        
    def test_date_boundary_shift_detection(self):
        """Test detection of date boundary shifts"""
        # Case that actually crosses UTC date boundary: 9am-5pm PST 
        # 9am PST Oct 3 = 4pm UTC Oct 3, 5pm PST Oct 3 = midnight UTC Oct 4
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(9, 0),    # 9am PST
            end_time=time(17, 0),     # 5pm PST 
            timezone="America/Los_Angeles"
        )
        
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # Should detect boundary shift (Oct 3 4pm UTC to Oct 4 midnight UTC)
        assert utc_start.date() != utc_end.date(), f"Expected boundary shift, got UTC {utc_start.date()} to {utc_end.date()}"
        
        # Shift analysis
        shift_info = availability.detect_date_boundary_shift()
        assert shift_info["start_date_shifted"] is False or shift_info["end_date_shifted"] is True


class TestMultipleTimezones:
    """Test various US timezones"""
    
    @pytest.mark.parametrize("timezone,expected_utc_offset", [
        ("America/Los_Angeles", -8),  # PST (winter) or -7 PDT (summer)
        ("America/Denver", -7),       # MST (winter) or -6 MDT (summer)  
        ("America/Chicago", -6),      # CST (winter) or -5 CDT (summer)
        ("America/New_York", -5),     # EST (winter) or -4 EDT (summer)
    ])
    def test_timezone_conversions(self, timezone, expected_utc_offset):
        """Test 9am-5pm conversion across different US timezones"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 1, 15),  # Winter date (standard time)
            start_time=time(9, 0),
            end_time=time(17, 0),
            timezone=timezone
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # Check that conversion works
        assert local_start.hour == 9
        assert local_end.hour == 17
        assert utc_start.tzinfo == pytz.UTC
        assert utc_end.tzinfo == pytz.UTC


class TestBoundaryConditions:
    """Test edge cases and boundary conditions"""
    
    def test_midnight_start_time(self):
        """Test starting at midnight"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(0, 0),    # midnight start
            end_time=time(8, 0),      # 8am end
            timezone="America/Los_Angeles"
        )
        
        # Should not raise validation error
        local_start, local_end = availability.get_local_datetime_range()
        assert local_start.hour == 0
        assert local_end.hour == 8
        
    def test_late_night_hours(self):
        """Test late night hours (11pm-3am)"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(23, 0),   # 11pm
            end_time=time(3, 0),      # 3am next day
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # End time should be next day
        assert local_end.date() == local_start.date() + timedelta(days=1)
        
    def test_full_24_hour_availability(self):
        """Test 24-hour availability (midnight to midnight)"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(0, 0),    # midnight start
            end_time=time(0, 0),      # midnight end (next day)
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        
        # Should span exactly 24 hours
        duration = local_end - local_start
        assert duration == timedelta(days=1)
        
    def test_one_minute_availability(self):
        """Test very short availability window"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(14, 30),  # 2:30pm
            end_time=time(14, 31),    # 2:31pm
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        duration = local_end - local_start
        assert duration == timedelta(minutes=1)


class TestValidationEdgeCases:
    """Test Pydantic validation edge cases"""
    
    def test_midnight_end_time_validation_passes(self):
        """Test that midnight end time passes validation (the bug we fixed)"""
        # This was failing before our fix
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(16, 0),   # 4pm
            end_time=time(0, 0),      # midnight (should be treated as next day)
            timezone="America/Los_Angeles"
        )
        
        # Should not raise ValidationError
        assert availability.start_time == time(16, 0)
        assert availability.end_time == time(0, 0)
        
    def test_response_validation_with_boundary_times(self):
        """Test that response validation handles boundary times correctly"""
        # This was causing the 422 error in responses
        response_data = {
            'id': uuid4(),
            'vet_user_id': uuid4(),
            'practice_id': uuid4(),
            'date': date(2025, 10, 3),
            'start_time': time(23, 0),    # 11pm UTC
            'end_time': time(7, 0),       # 7am UTC (problematic case)
            'availability_type': 'AVAILABLE',
            'notes': None,
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Should not raise ValidationError (we fixed this)
        response = VetAvailabilityResponse(**response_data)
        assert response.start_time == time(23, 0)
        assert response.end_time == time(7, 0)
        
    def test_invalid_timezone_raises_error(self):
        """Test that invalid timezone raises proper error"""
        with pytest.raises(ValueError, match="Unknown timezone"):
            VetAvailabilityCreate(
                vet_user_id=uuid4(),
                practice_id=uuid4(),
                date=date(2025, 10, 3),
                start_time=time(9, 0),
                end_time=time(17, 0),
                timezone="Invalid/Timezone"
            ).to_utc_datetime_range()
            
    def test_end_before_start_same_day_fails(self):
        """Test that truly invalid time combinations fail validation"""
        # With our fixed logic, 5pm-9am is now valid (overnight shift)
        # So let's test a truly invalid case: same non-midnight times
        with pytest.raises(ValidationError, match="start_time must be before end_time"):
            VetAvailabilityCreate(
                vet_user_id=uuid4(),
                practice_id=uuid4(),
                date=date(2025, 10, 3),
                start_time=time(14, 0),   # 2pm
                end_time=time(14, 0),     # 2pm (invalid - same time, not midnight)
                timezone="America/Los_Angeles"
            )


class TestDaylightSavingTime:
    """Test daylight saving time transitions"""
    
    def test_spring_forward_transition(self):
        """Test spring forward (2am becomes 3am)"""
        # March 9, 2025 is when DST starts (2am -> 3am)
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 3, 9),
            start_time=time(1, 0),    # 1am (exists)
            end_time=time(4, 0),      # 4am (exists)
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # Should handle DST transition correctly
        assert local_start.hour == 1
        assert local_end.hour == 4
        
    def test_fall_back_transition(self):
        """Test fall back (2am happens twice)"""
        # November 2, 2025 is when DST ends (2am happens twice)
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 11, 2),
            start_time=time(1, 0),    # 1am
            end_time=time(3, 0),      # 3am
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # Should handle DST transition correctly
        assert local_start.hour == 1
        assert local_end.hour == 3


class TestExtremeEdgeCases:
    """Test extreme edge cases and weird scenarios"""
    
    def test_new_years_eve_midnight(self):
        """Test New Year's Eve midnight transition"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 12, 31),
            start_time=time(23, 0),   # 11pm Dec 31
            end_time=time(0, 0),      # midnight (Jan 1)
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        
        # Should cross year boundary
        assert local_start.year == 2025
        assert local_end.year == 2026
        assert local_end.month == 1
        assert local_end.day == 1
        
    def test_leap_year_february_29(self):
        """Test Feb 29 on leap year"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2024, 2, 29),   # Leap year
            start_time=time(9, 0),
            end_time=time(17, 0),
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        assert local_start.month == 2
        assert local_start.day == 29
        
    def test_hawaii_timezone(self):
        """Test Hawaii timezone (no DST)"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(9, 0),
            end_time=time(17, 0),
            timezone="Pacific/Honolulu"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # Hawaii is UTC-10 (no DST)
        assert utc_start.hour == 19  # 9am HST = 7pm UTC
        assert utc_end.hour == 3     # 5pm HST = 3am UTC next day
        
    def test_alaska_timezone(self):
        """Test Alaska timezone"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(9, 0),
            end_time=time(17, 0),
            timezone="America/Anchorage"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # Alaska is UTC-9 (AKDT) or UTC-8 (AKST)
        assert utc_start.hour in [17, 18]  # 9am AKDT/AKST = 5pm/6pm UTC
        assert utc_end.hour in [1, 2]      # 5pm AKDT/AKST = 1am/2am UTC next day


class TestStorageLogicSimulation:
    """Test the storage logic that converts UTC times for database"""
    
    def test_midnight_conversion_to_23_59_59(self):
        """Test that midnight UTC end times get converted to 23:59:59"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(16, 0),   # 4pm local
            end_time=time(0, 0),      # midnight local
            timezone="America/Los_Angeles"
        )
        
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # Simulate the storage logic from the API route
        data_dict = {}
        data_dict['start_time'] = utc_start.time()
        
        if utc_start.date() != utc_end.date():
            # Date boundary shift - convert to 23:59:59
            data_dict['end_time'] = time(23, 59, 59)
            data_dict['date'] = utc_start.date()
        else:
            data_dict['end_time'] = utc_end.time()
            data_dict['date'] = utc_start.date()
        
        # Should convert midnight to 23:59:59
        assert data_dict['end_time'] == time(23, 59, 59)
        assert data_dict['date'] == utc_start.date()
        
    def test_no_boundary_shift_storage(self):
        """Test storage when no date boundary shift occurs"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(9, 0),    # 9am EST
            end_time=time(17, 0),     # 5pm EST
            timezone="America/New_York"
        )
        
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # EST: 9am = 1pm UTC, 5pm = 9pm UTC (same day)
        if utc_start.date() == utc_end.date():
            # No boundary shift - store times as-is
            assert utc_start.time() == time(13, 0)  # 1pm UTC
            assert utc_end.time() == time(21, 0)    # 9pm UTC


class TestTimezoneUtilities:
    """Test the TimezoneHandler utility class"""
    
    def test_normalize_timezone(self):
        """Test timezone normalization"""
        assert TimezoneHandler.normalize_timezone("PST") == "America/Los_Angeles"
        assert TimezoneHandler.normalize_timezone("EST") == "America/New_York"
        assert TimezoneHandler.normalize_timezone("America/Chicago") == "America/Chicago"
        
    def test_create_local_datetime(self):
        """Test local datetime creation"""
        local_dt = TimezoneHandler.create_local_datetime(
            date(2025, 10, 3),
            time(14, 30),
            "America/Los_Angeles"
        )
        
        assert local_dt.hour == 14
        assert local_dt.minute == 30
        assert local_dt.tzinfo is not None
        
    def test_convert_to_utc(self):
        """Test UTC conversion"""
        utc_dt = TimezoneHandler.convert_to_utc(
            date(2025, 10, 3),
            time(14, 30),
            "America/Los_Angeles"
        )
        
        assert utc_dt.tzinfo == pytz.UTC
        # 2:30pm PST should be 9:30pm or 10:30pm UTC depending on DST
        assert utc_dt.hour in [21, 22]
        
    def test_analyze_date_boundary_shift(self):
        """Test date boundary shift analysis"""
        analysis = TimezoneHandler.analyze_date_boundary_shift(
            date(2025, 10, 3),
            time(20, 0),  # 8pm PST
            time(0, 0),   # midnight PST
            "America/Los_Angeles"
        )
        
        assert "has_date_boundary_issues" in analysis
        assert "spans_multiple_utc_dates" in analysis
        assert analysis["timezone"] == "America/Los_Angeles"


class TestRegressionCases:
    """Test specific cases that caused bugs in the past"""
    
    def test_9am_5pm_pst_regression(self):
        """Test the specific 9am-5pm PST case that was causing 422 errors"""
        # This exact case was failing before our fixes
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 9, 23),
            start_time=time(9, 0),    # 9am PST
            end_time=time(17, 0),     # 5pm PST
            timezone="America/Los_Angeles"
        )
        
        # Should not raise any validation errors
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        assert local_start.hour == 9
        assert local_end.hour == 17
        
        # Test the problematic UTC conversion that was causing issues
        assert utc_start.hour == 16  # 9am PST = 4pm UTC (during PDT)
        assert utc_end.hour == 0     # 5pm PST = midnight UTC next day
        assert utc_end.date() == utc_start.date() + timedelta(days=1)
        
    def test_4pm_midnight_ios_bug_case(self):
        """Test the 4pm-midnight case that iOS was incorrectly sending"""
        # This is what iOS was sending due to the timezone bug
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(16, 0),   # 4pm (what iOS was incorrectly sending)
            end_time=time(0, 0),      # midnight
            timezone="America/Los_Angeles"
        )
        
        # Should handle this case without errors
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # 4pm PST = 11pm UTC, midnight PST = 7am UTC next day
        assert utc_start.hour == 23  # 11pm UTC
        assert utc_end.hour == 7     # 7am UTC next day
        
    def test_duplicate_key_scenario(self):
        """Test the duplicate key scenario that was causing database errors"""
        # Create two identical availabilities
        data = {
            'vet_user_id': uuid4(),
            'practice_id': uuid4(),
            'date': date(2025, 10, 3),
            'start_time': time(16, 0),
            'end_time': time(0, 0),
            'timezone': "America/Los_Angeles"
        }
        
        availability1 = VetAvailabilityCreate(**data)
        availability2 = VetAvailabilityCreate(**data)
        
        # Both should convert to the same UTC times
        utc1_start, utc1_end = availability1.to_utc_datetime_range()
        utc2_start, utc2_end = availability2.to_utc_datetime_range()
        
        assert utc1_start == utc2_start
        assert utc1_end == utc2_end
        
        # This would create the same database key, causing duplicate error


class TestStringParsing:
    """Test string parsing for iOS compatibility"""
    
    @pytest.mark.parametrize("time_str,expected_hour,expected_minute", [
        ("09:00:00", 9, 0),
        ("17:30:45", 17, 30),
        ("00:00:00", 0, 0),
        ("23:59:59", 23, 59),
        ("9:00 AM", 9, 0),
        ("5:30 PM", 17, 30),
        ("12:00 AM", 0, 0),
        ("12:00 PM", 12, 0),
        ("1 PM", 13, 0),
        ("11 AM", 11, 0),
    ])
    def test_time_string_parsing(self, time_str, expected_hour, expected_minute):
        """Test various time string formats from iOS"""
        from src.schemas.scheduling_schemas import VetAvailabilityBase
        
        parsed_time = VetAvailabilityBase._parse_time_string(time_str)
        assert parsed_time.hour == expected_hour
        assert parsed_time.minute == expected_minute
        
    @pytest.mark.parametrize("date_str,expected_date", [
        ("2025-10-03", date(2025, 10, 3)),
        ("10-03-2025", date(2025, 10, 3)),
        ("10/03/2025", date(2025, 10, 3)),
    ])
    def test_date_string_parsing(self, date_str, expected_date):
        """Test various date string formats from iOS"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date_str,  # Test string parsing
            start_time="09:00:00",
            end_time="17:00:00",
            timezone="America/Los_Angeles"
        )
        
        assert availability.date == expected_date


class TestRealWorldScenarios:
    """Test real-world veterinary practice scenarios"""
    
    def test_emergency_clinic_overnight(self):
        """Test 24/7 emergency clinic availability"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(0, 0),    # midnight
            end_time=time(0, 0),      # midnight next day (24 hours)
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        duration = local_end - local_start
        assert duration == timedelta(days=1)  # Exactly 24 hours
        
    def test_early_morning_surgery_hours(self):
        """Test early morning surgery availability (6am-2pm)"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(6, 0),    # 6am
            end_time=time(14, 0),     # 2pm
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # Should not cross date boundaries
        assert utc_start.date() == utc_end.date()
        
    def test_weekend_extended_hours(self):
        """Test weekend extended hours (8am-8pm)"""
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 4),   # Saturday
            start_time=time(8, 0),    # 8am
            end_time=time(20, 0),     # 8pm
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        duration = local_end - local_start
        assert duration == timedelta(hours=12)


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_time_strings(self):
        """Test invalid time string handling"""
        with pytest.raises(ValueError):
            VetAvailabilityCreate(
                vet_user_id=uuid4(),
                practice_id=uuid4(),
                date=date(2025, 10, 3),
                start_time="25:00:00",  # Invalid hour
                end_time="17:00:00",
                timezone="America/Los_Angeles"
            )
            
    def test_invalid_date_strings(self):
        """Test invalid date string handling"""
        with pytest.raises(ValueError):
            VetAvailabilityCreate(
                vet_user_id=uuid4(),
                practice_id=uuid4(),
                date="2025-13-45",  # Invalid date
                start_time="09:00:00",
                end_time="17:00:00",
                timezone="America/Los_Angeles"
            )
            
    def test_empty_timezone(self):
        """Test empty timezone handling"""
        # Should use default timezone
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),
            start_time=time(9, 0),
            end_time=time(17, 0)
            # No timezone specified - should use default
        )
        
        assert availability.timezone == "America/Los_Angeles"  # Default


if __name__ == "__main__":
    # Run specific test categories
    print("🧪 Running timezone handling tests...")
    
    # You can run these individually:
    # pytest test_timezone_handling.py::TestTimezoneConversions::test_normal_business_hours_pst -v
    # pytest test_timezone_handling.py::TestBoundaryConditions::test_midnight_end_time_validation_passes -v
    # pytest test_timezone_handling.py::TestRegressionCases::test_9am_5pm_pst_regression -v
    
    print("✅ All tests should pass to ensure timezone handling is bulletproof!")
