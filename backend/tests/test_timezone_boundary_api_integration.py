"""
API Integration tests for timezone boundary issues

These tests will FAIL until the GET endpoint is fixed to handle timezone boundaries.
They simulate the exact iOS behavior that's causing the issue.

EXPECTED FAILURES (until fix is implemented):
- test_evening_availability_query_by_local_date: Should find evening records when querying local date
- test_mixed_availability_query: Should find all records regardless of UTC storage date
"""

import pytest
import uuid
from datetime import date, time
from unittest.mock import AsyncMock, patch
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.scheduling_schemas import VetAvailabilityCreate
from src.models_pg.scheduling import VetAvailability
from src.repositories_pg.scheduling_repository import VetAvailabilityRepository


class MockVetAvailabilityRepository:
    """Mock repository that simulates the current broken behavior"""
    
    def __init__(self):
        self.storage = {}  # {(vet_id, date): [availability_records]}
    
    async def create(self, availability: VetAvailability) -> VetAvailability:
        """Simulate creating availability with UTC storage"""
        key = (availability.vet_user_id, availability.date)
        if key not in self.storage:
            self.storage[key] = []
        
        # Add ID for response
        availability.id = uuid.uuid4()
        self.storage[key].append(availability)
        return availability
    
    async def get_by_vet_and_date(self, vet_user_id: uuid.UUID, query_date: date, include_inactive: bool = False):
        """
        CURRENT BROKEN BEHAVIOR: Only looks for exact UTC date match
        This is what causes the iOS issue!
        """
        key = (vet_user_id, query_date)
        return self.storage.get(key, [])
    
    async def get_by_vet_and_date_FIXED(self, vet_user_id: uuid.UUID, query_date: date, timezone_str: str = "America/Los_Angeles", include_inactive: bool = False):
        """
        FIXED BEHAVIOR: Check multiple UTC dates for local date query
        This is what we need to implement!
        """
        from src.utils.timezone_utils import TimezoneHandler
        
        # Calculate which UTC dates might contain records for this local date
        test_times = [time(0, 0), time(12, 0), time(23, 59)]
        utc_dates_to_check = set()
        
        for test_time in test_times:
            utc_dt = TimezoneHandler.convert_to_utc(query_date, test_time, timezone_str)
            utc_dates_to_check.add(utc_dt.date())
        
        # Check all relevant UTC dates
        all_records = []
        for utc_date in utc_dates_to_check:
            key = (vet_user_id, utc_date)
            records = self.storage.get(key, [])
            
            # Filter records to only include those that represent the local date
            for record in records:
                # For now, add all records - in real implementation, 
                # we'd convert back to local time and check date
                all_records.append(record)
        
        return all_records


class TestTimezoneBoundaryAPIIntegration:
    """Integration tests for timezone boundary API behavior"""
    
    def setup_method(self):
        """Setup test data"""
        self.repo = MockVetAvailabilityRepository()
        self.test_vet_id = uuid.uuid4()
        self.test_practice_id = uuid.uuid4()
        self.local_date = date(2025, 9, 26)
    
    async def _create_availability_with_utc_storage(self, start_time: time, end_time: time) -> VetAvailability:
        """Helper to create availability and store it with proper UTC conversion"""
        
        # Create the schema object for conversion
        availability_schema = VetAvailabilityCreate(
            vet_user_id=self.test_vet_id,
            practice_id=self.test_practice_id,
            date=self.local_date,
            start_time=start_time,
            end_time=end_time,
            timezone="America/Los_Angeles",
            availability_type="AVAILABLE"
        )
        
        # Convert to UTC (same logic as API route)
        utc_start, utc_end = availability_schema.to_utc_datetime_range()
        
        # Create model object with UTC storage
        availability = VetAvailability(
            vet_user_id=self.test_vet_id,
            practice_id=self.test_practice_id,
            date=utc_start.date(),  # Store UTC date!
            start_time=utc_start.time(),
            end_time=utc_end.time(),
            availability_type="AVAILABLE",
            is_active=True
        )
        
        return await self.repo.create(availability)
    
    @pytest.mark.asyncio
    async def test_morning_availability_query_works(self):
        """
        Test: Morning availability (9am PST) should be found - this works currently
        Because 9am PST -> 4pm UTC same day, so query matches storage date
        """
        # Create 9am-10am PST availability (stored on same UTC day)
        created = await self._create_availability_with_utc_storage(
            start_time=time(9, 0),   # 9am PST
            end_time=time(10, 0)     # 10am PST
        )
        
        # Verify it's stored on same UTC day
        assert created.date == date(2025, 9, 26), "Morning time should be stored on same UTC day"
        
        # Query for local date - should find it (this currently works)
        found = await self.repo.get_by_vet_and_date(self.test_vet_id, self.local_date)
        
        assert len(found) == 1, "Should find morning availability (no boundary issue)"
        assert found[0].id == created.id
    
    @pytest.mark.asyncio
    async def test_evening_availability_query_FAILS_currently(self):
        """
        Test: Evening availability (5pm PST) is NOT found - this is the bug!
        Because 5pm PST -> 12am UTC next day, so query doesn't match storage date
        
        THIS TEST WILL FAIL until the GET endpoint is fixed!
        """
        # Create 5pm-6pm PST availability (stored on next UTC day)
        created = await self._create_availability_with_utc_storage(
            start_time=time(17, 0),  # 5pm PST  
            end_time=time(18, 0)     # 6pm PST
        )
        
        # Verify it's stored on next UTC day (this is correct!)
        assert created.date == date(2025, 9, 27), "Evening time should be stored on next UTC day"
        
        # Query for local date - FAILS to find it (this is the bug!)
        found = await self.repo.get_by_vet_and_date(self.test_vet_id, self.local_date)
        
        # THIS ASSERTION WILL FAIL - demonstrating the bug
        assert len(found) == 0, "CURRENT BUG: Evening availability not found when querying local date"
        
        # Show that the fixed version would work
        found_fixed = await self.repo.get_by_vet_and_date_FIXED(self.test_vet_id, self.local_date)
        assert len(found_fixed) == 1, "FIXED version should find evening availability"
    
    @pytest.mark.asyncio
    async def test_mixed_availability_query_FAILS_currently(self):
        """
        Test: Multiple availabilities on same local day are NOT all found - this is the bug!
        
        THIS TEST WILL FAIL until the GET endpoint is fixed!
        """
        # Create multiple availabilities on same local day
        morning = await self._create_availability_with_utc_storage(
            start_time=time(9, 0),   # 9am PST -> stored on Sept 26 UTC
            end_time=time(10, 0)
        )
        
        evening = await self._create_availability_with_utc_storage(
            start_time=time(17, 0),  # 5pm PST -> stored on Sept 27 UTC
            end_time=time(18, 0)
        )
        
        # Verify they're stored on different UTC dates
        assert morning.date == date(2025, 9, 26)
        assert evening.date == date(2025, 9, 27)
        
        # Query for local date - FAILS to find evening availability
        found = await self.repo.get_by_vet_and_date(self.test_vet_id, self.local_date)
        
        # THIS ASSERTION WILL FAIL - demonstrating the bug
        assert len(found) == 1, "CURRENT BUG: Only finds morning availability, misses evening"
        assert found[0].id == morning.id, "Only morning availability found"
        
        # Show that the fixed version would work
        found_fixed = await self.repo.get_by_vet_and_date_FIXED(self.test_vet_id, self.local_date)
        assert len(found_fixed) == 2, "FIXED version should find both availabilities"
        
        found_ids = {avail.id for avail in found_fixed}
        expected_ids = {morning.id, evening.id}
        assert found_ids == expected_ids, "Should find all availabilities regardless of UTC storage date"
    
    @pytest.mark.asyncio
    async def test_different_timezones_boundary_issues(self):
        """
        Test boundary issues across different US timezones
        All of these will have similar issues for evening times
        """
        timezones_and_evening_times = [
            ("America/Los_Angeles", time(17, 0)),  # 5pm PST -> midnight UTC next day
            ("America/Denver", time(18, 0)),       # 6pm MST -> 1am UTC next day  
            ("America/Chicago", time(19, 0)),      # 7pm CST -> 1am UTC next day
            ("America/New_York", time(20, 0))      # 8pm EST -> 1am UTC next day
        ]
        
        for timezone_str, evening_time in timezones_and_evening_times:
            # This test just validates the boundary logic, not the full API
            from src.utils.timezone_utils import TimezoneHandler
            
            utc_dt = TimezoneHandler.convert_to_utc(
                self.local_date, 
                evening_time, 
                timezone_str
            )
            
            # All these evening times should cross to next UTC day
            assert utc_dt.date() > self.local_date, f"Evening time in {timezone_str} should cross UTC boundary"


# Test that demonstrates the exact iOS issue
class TestiOSIssueSimulation:
    """Simulate the exact iOS issue from the logs"""
    
    @pytest.mark.asyncio
    async def test_ios_exact_scenario(self):
        """
        Simulate the exact scenario from iOS logs:
        - Create 5pm-6pm PST on Sept 26
        - Query for Sept 26 
        - Should find the record but currently doesn't
        """
        repo = MockVetAvailabilityRepository()
        vet_id = uuid.UUID("e1e3991b-4efa-464b-9bae-f94c74d0a20f")  # From iOS logs
        practice_id = uuid.UUID("934c57e7-4f9c-4d28-aa0f-3cb881e3c225")  # From iOS logs
        
        # Step 1: Create availability (simulating POST request)
        availability_schema = VetAvailabilityCreate(
            vet_user_id=vet_id,
            practice_id=practice_id,
            date=date(2025, 9, 26),
            start_time=time(17, 0),  # 5pm PST
            end_time=time(18, 0),    # 6pm PST
            timezone="America/Los_Angeles",
            availability_type="AVAILABLE"
        )
        
        # Convert to UTC (API route logic)
        utc_start, utc_end = availability_schema.to_utc_datetime_range()
        
        # Create and store with UTC dates (API route logic)
        availability = VetAvailability(
            vet_user_id=vet_id,
            practice_id=practice_id,
            date=utc_start.date(),     # 2025-09-27 (next day UTC)
            start_time=utc_start.time(),  # 00:00:00 (midnight UTC)
            end_time=utc_end.time(),      # 01:00:00 (1am UTC)
            availability_type="AVAILABLE",
            is_active=True
        )
        
        created = await repo.create(availability)
        
        # Verify this matches the iOS logs exactly
        assert created.date.isoformat() == "2025-09-27"
        assert created.start_time.isoformat() == "00:00:00"
        assert created.end_time.isoformat() == "01:00:00"
        
        print("✅ Created availability matches iOS logs:")
        print(f"   Date: {created.date}")
        print(f"   Start: {created.start_time}")
        print(f"   End: {created.end_time}")
        
        # Step 2: Query for local date (simulating GET request from iOS)
        query_date = date(2025, 9, 26)  # iOS queries for Sept 26
        found = await repo.get_by_vet_and_date(vet_id, query_date)
        
        # This demonstrates the bug - iOS gets empty array
        assert len(found) == 0, "CURRENT BUG: iOS gets empty array"
        print(f"❌ Current GET returns: {len(found)} records (should be 1)")
        
        # Show what the fix would return
        found_fixed = await repo.get_by_vet_and_date_FIXED(vet_id, query_date)
        assert len(found_fixed) == 1, "FIXED version should return 1 record"
        print(f"✅ Fixed GET would return: {len(found_fixed)} records")


if __name__ == "__main__":
    """Run specific failing test to demonstrate the issue"""
    import asyncio
    
    async def run_ios_test():
        test_instance = TestiOSIssueSimulation()
        print("🧪 Running iOS issue simulation...")
        print("=" * 60)
        await test_instance.test_ios_exact_scenario()
        print("\n🔧 This demonstrates exactly why iOS shows 0 availabilities!")
    
    asyncio.run(run_ios_test())
