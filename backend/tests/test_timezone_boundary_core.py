"""
Core timezone boundary tests for vet availability scheduling

These tests focus on the fundamental timezone conversion and query logic
that causes the iOS scheduling issue.

THE PROBLEM:
- iOS creates 5pm-6pm PST on Sept 26 
- Backend stores it as midnight-1am UTC on Sept 27
- When iOS queries for Sept 26, it doesn't find the record (stored on Sept 27)

SOLUTION NEEDED:
- GET endpoint must handle timezone boundaries
- When querying local date, check both same-day and next-day UTC records
"""

import pytest
import uuid
from datetime import date, time, datetime, timedelta
from typing import List, Set
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.scheduling_schemas import VetAvailabilityCreate
from src.utils.timezone_utils import TimezoneHandler


class TestTimezoneBoundaryCore:
    """Core tests for timezone boundary logic"""
    
    def test_evening_time_boundary_conversion(self):
        """
        Test: 5pm PST on Sept 26 -> midnight UTC on Sept 27
        This is the exact case from iOS logs
        """
        availability = VetAvailabilityCreate(
            vet_user_id=uuid.uuid4(),
            practice_id=uuid.uuid4(),
            date=date(2025, 9, 26),        # Local date: Sept 26
            start_time=time(17, 0),        # 5pm PST
            end_time=time(18, 0),          # 6pm PST
            timezone="America/Los_Angeles",
            availability_type="AVAILABLE"
        )
        
        # Get UTC conversion
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # Verify boundary crossing
        assert utc_start.date() == date(2025, 9, 27), "Should store on next UTC day"
        assert utc_start.time() == time(0, 0), "Should be midnight UTC"
        assert utc_end.time() == time(1, 0), "Should be 1am UTC"
        
        print(f"✅ Evening boundary test passed:")
        print(f"   Local: Sept 26 5pm-6pm PST")
        print(f"   UTC: Sept 27 {utc_start.time()}-{utc_end.time()}")
    
    def test_morning_time_same_day_conversion(self):
        """
        Test: 9am PST on Sept 26 -> 4pm UTC on Sept 26 (same day)
        """
        availability = VetAvailabilityCreate(
            vet_user_id=uuid.uuid4(),
            practice_id=uuid.uuid4(),
            date=date(2025, 9, 26),        # Local date: Sept 26
            start_time=time(9, 0),         # 9am PST
            end_time=time(10, 0),          # 10am PST
            timezone="America/Los_Angeles",
            availability_type="AVAILABLE"
        )
        
        # Get UTC conversion
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # Verify NO boundary crossing
        assert utc_start.date() == date(2025, 9, 26), "Should store on same UTC day"
        assert utc_start.time() == time(16, 0), "Should be 4pm UTC"
        assert utc_end.time() == time(17, 0), "Should be 5pm UTC"
        
        print(f"✅ Morning same-day test passed:")
        print(f"   Local: Sept 26 9am-10am PST")
        print(f"   UTC: Sept 26 {utc_start.time()}-{utc_end.time()}")
    
    def test_boundary_detection_utility(self):
        """
        Test the timezone boundary detection utility
        """
        # Test evening time (crosses boundary)
        evening_analysis = TimezoneHandler.analyze_date_boundary_shift(
            local_date=date(2025, 9, 26),
            start_time=time(17, 0),  # 5pm PST
            end_time=time(18, 0),    # 6pm PST
            timezone_str="America/Los_Angeles"
        )
        
        assert evening_analysis["has_date_boundary_issues"] == True
        assert evening_analysis["utc_start_date"] == "2025-09-27"
        assert evening_analysis["local_start_date"] == "2025-09-26"
        
        # Test morning time (no boundary crossing)
        morning_analysis = TimezoneHandler.analyze_date_boundary_shift(
            local_date=date(2025, 9, 26),
            start_time=time(9, 0),   # 9am PST
            end_time=time(10, 0),    # 10am PST
            timezone_str="America/Los_Angeles"
        )
        
        assert morning_analysis["has_date_boundary_issues"] == False
        assert morning_analysis["utc_start_date"] == "2025-09-26"
        assert morning_analysis["local_start_date"] == "2025-09-26"
        
        print("✅ Boundary detection utility tests passed")
    
    def test_query_date_range_calculation(self):
        """
        Test: Calculate which UTC dates to check when querying a local date
        
        This is the core logic needed to fix the GET endpoint.
        When iOS queries for Sept 26, we need to check both Sept 26 and Sept 27 UTC.
        """
        query_local_date = date(2025, 9, 26)
        timezone_str = "America/Los_Angeles"
        
        # Calculate UTC date range to check
        utc_dates_to_check = self._get_utc_dates_for_local_query(
            query_local_date, 
            timezone_str
        )
        
        # Should check both Sept 26 and Sept 27 UTC
        expected_dates = {date(2025, 9, 26), date(2025, 9, 27)}
        assert utc_dates_to_check == expected_dates
        
        print(f"✅ Query range calculation test passed:")
        print(f"   Local query date: Sept 26")
        print(f"   UTC dates to check: {sorted(utc_dates_to_check)}")
    
    def _get_utc_dates_for_local_query(self, local_date: date, timezone_str: str) -> Set[date]:
        """
        Calculate which UTC dates might contain records for a given local date.
        This is the logic that the GET endpoint needs.
        """
        # Test boundary times to see which UTC dates they fall on
        test_times = [
            time(0, 0),   # Midnight local
            time(12, 0),  # Noon local  
            time(23, 59)  # End of day local
        ]
        
        utc_dates = set()
        
        for test_time in test_times:
            utc_dt = TimezoneHandler.convert_to_utc(local_date, test_time, timezone_str)
            utc_dates.add(utc_dt.date())
        
        return utc_dates
    
    def test_multiple_timezone_boundaries(self):
        """
        Test boundary calculations for different US timezones
        """
        test_cases = [
            {
                "timezone": "America/Los_Angeles",  # PST: UTC-8
                "evening_time": time(17, 0),        # 5pm PST -> 1am UTC next day
                "expected_boundary": True
            },
            {
                "timezone": "America/Denver",       # MST: UTC-7  
                "evening_time": time(18, 0),        # 6pm MST -> 1am UTC next day
                "expected_boundary": True
            },
            {
                "timezone": "America/Chicago",      # CST: UTC-6
                "evening_time": time(19, 0),        # 7pm CST -> 1am UTC next day
                "expected_boundary": True
            },
            {
                "timezone": "America/New_York",     # EST: UTC-5
                "evening_time": time(20, 0),        # 8pm EST -> 1am UTC next day
                "expected_boundary": True
            }
        ]
        
        for case in test_cases:
            analysis = TimezoneHandler.analyze_date_boundary_shift(
                local_date=date(2025, 9, 26),
                start_time=case["evening_time"],
                end_time=time(case["evening_time"].hour + 1, 0),
                timezone_str=case["timezone"]
            )
            
            assert analysis["has_date_boundary_issues"] == case["expected_boundary"], \
                f"Failed for {case['timezone']}"
            
            print(f"✅ {case['timezone']}: {case['evening_time']} -> boundary crossing: {analysis['has_date_boundary_issues']}")
    
    def test_fix_strategy_requirements(self):
        """
        Test what the fix needs to handle
        """
        # Scenario: iOS creates multiple availabilities on Sept 26
        availabilities = [
            # Morning - stored on same UTC day
            {
                "local_time": time(9, 0),
                "description": "Morning (same UTC day)"
            },
            # Evening - stored on next UTC day
            {
                "local_time": time(17, 0), 
                "description": "Evening (next UTC day)"
            }
        ]
        
        storage_dates = set()
        
        for avail in availabilities:
            availability = VetAvailabilityCreate(
                vet_user_id=uuid.uuid4(),
                practice_id=uuid.uuid4(),
                date=date(2025, 9, 26),
                start_time=avail["local_time"],
                end_time=time(avail["local_time"].hour + 1, 0),
                timezone="America/Los_Angeles",
                availability_type="AVAILABLE"
            )
            
            utc_start, _ = availability.to_utc_datetime_range()
            storage_dates.add(utc_start.date())
            
            print(f"   {avail['description']}: stored on UTC {utc_start.date()}")
        
        # The GET endpoint must check both storage dates
        expected_storage_dates = {date(2025, 9, 26), date(2025, 9, 27)}
        assert storage_dates == expected_storage_dates
        
        print(f"✅ Fix strategy test passed:")
        print(f"   Local query: Sept 26")
        print(f"   Must check UTC dates: {sorted(storage_dates)}")


if __name__ == "__main__":
    """Run tests directly"""
    test_instance = TestTimezoneBoundaryCore()
    
    print("🧪 Running timezone boundary core tests...")
    print("=" * 60)
    
    test_instance.test_evening_time_boundary_conversion()
    print()
    
    test_instance.test_morning_time_same_day_conversion()
    print()
    
    test_instance.test_boundary_detection_utility()
    print()
    
    test_instance.test_query_date_range_calculation()
    print()
    
    test_instance.test_multiple_timezone_boundaries()
    print()
    
    test_instance.test_fix_strategy_requirements()
    print()
    
    print("✅ All core tests passed!")
    print("\n🔧 Next step: Fix the GET endpoint to check multiple UTC dates")
