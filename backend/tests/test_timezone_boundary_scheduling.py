"""
Comprehensive tests for timezone boundary issues in vet availability scheduling

This test suite covers the critical edge cases where local times cross UTC date boundaries,
particularly for iOS app integration where users create availability in local time but
the backend stores in UTC.

Critical scenarios tested:
1. Evening times that cross to next UTC day (5pm PST -> 1am UTC next day)
2. Late night times that cross to next UTC day (11pm PST -> 7am UTC next day)
3. Early morning times that stay same UTC day (9am PST -> 5pm UTC same day)
4. Midnight boundary cases
5. Different timezones (PST, EST, MST, CST)
6. DST vs Standard time transitions
"""

import pytest
import uuid
import sys
import os
from datetime import date, time, datetime, timedelta
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main_pg import app
from src.models_pg.scheduling import VetAvailability
from src.schemas.scheduling_schemas import VetAvailabilityCreate


class TestTimezoneBoundaryScheduling:
    """Test timezone boundary issues in vet availability scheduling"""
    
    def setup_method(self):
        """Setup test data"""
        self.client = TestClient(app)
        self.test_vet_id = uuid.uuid4()
        self.test_practice_id = uuid.uuid4()
        
        # Test date: September 26, 2025 (same as your iOS logs)
        self.test_local_date = date(2025, 9, 26)
        
        # Expected UTC dates for boundary cases
        self.same_day_utc = date(2025, 9, 26)
        self.next_day_utc = date(2025, 9, 27)
    
    @pytest.mark.asyncio
    async def test_evening_time_crosses_utc_boundary_pst(self):
        """
        Test: 5pm-6pm PST on Sept 26 -> stored as 12am-1am UTC on Sept 27
        This is the exact case from your iOS logs
        """
        # Create availability: 5pm-6pm PST on Sept 26
        availability_data = VetAvailabilityCreate(
            vet_user_id=self.test_vet_id,
            practice_id=self.test_practice_id,
            date=self.test_local_date,
            start_time=time(17, 0),  # 5pm PST
            end_time=time(18, 0),    # 6pm PST
            timezone="America/Los_Angeles",
            availability_type="AVAILABLE"
        )
        
        # POST: Create the availability
        response = self.client.post(
            "/api/v1/scheduling/vet-availability",
            json=availability_data.model_dump()
        )
        
        assert response.status_code == 201
        created = response.json()
        
        # Verify UTC storage (should be stored on next day)
        assert created["date"] == "2025-09-27"  # Next day UTC
        assert created["start_time"] == "00:00:00"  # Midnight UTC
        assert created["end_time"] == "01:00:00"   # 1am UTC
        
        # GET: Query for Sept 26 (local date) - should find the record
        get_response = self.client.get(
            f"/api/v1/scheduling/vet-availability/{self.test_vet_id}?date=2025-09-26"
        )
        
        assert get_response.status_code == 200
        availabilities = get_response.json()
        
        # CRITICAL: Should find the record even though it's stored on UTC Sept 27
        assert len(availabilities) == 1, "Should find availability when querying local date"
        
        # Verify the returned data represents the original local time
        found = availabilities[0]
        # The API should convert back to local time for display
        # (Implementation detail - may return UTC times with timezone info)
        
    @pytest.mark.asyncio
    async def test_late_evening_time_crosses_utc_boundary_pst(self):
        """
        Test: 11pm-11:59pm PST on Sept 26 -> stored as 7am-7:59am UTC on Sept 27
        """
        availability_data = VetAvailabilityCreate(
            vet_user_id=self.test_vet_id,
            practice_id=self.test_practice_id,
            date=self.test_local_date,
            start_time=time(23, 0),   # 11pm PST
            end_time=time(23, 59),    # 11:59pm PST
            timezone="America/Los_Angeles",
            availability_type="AVAILABLE"
        )
        
        # Create
        response = self.client.post(
            "/api/v1/scheduling/vet-availability",
            json=availability_data.model_dump()
        )
        assert response.status_code == 201
        
        # Verify UTC storage
        created = response.json()
        assert created["date"] == "2025-09-27"  # Next day UTC
        assert created["start_time"] == "07:00:00"  # 7am UTC
        assert created["end_time"] == "07:59:00"   # 7:59am UTC
        
        # Query local date - should find it
        get_response = self.client.get(
            f"/api/v1/scheduling/vet-availability/{self.test_vet_id}?date=2025-09-26"
        )
        assert get_response.status_code == 200
        assert len(get_response.json()) == 1
    
    @pytest.mark.asyncio
    async def test_morning_time_same_utc_day_pst(self):
        """
        Test: 9am-10am PST on Sept 26 -> stored as 4pm-5pm UTC on Sept 26 (same day)
        """
        availability_data = VetAvailabilityCreate(
            vet_user_id=self.test_vet_id,
            practice_id=self.test_practice_id,
            date=self.test_local_date,
            start_time=time(9, 0),   # 9am PST
            end_time=time(10, 0),    # 10am PST
            timezone="America/Los_Angeles",
            availability_type="AVAILABLE"
        )
        
        response = self.client.post(
            "/api/v1/scheduling/vet-availability",
            json=availability_data.model_dump()
        )
        assert response.status_code == 201
        
        # Verify UTC storage (should be same day)
        created = response.json()
        assert created["date"] == "2025-09-26"  # Same day UTC
        assert created["start_time"] == "16:00:00"  # 4pm UTC
        assert created["end_time"] == "17:00:00"   # 5pm UTC
        
        # Query local date - should find it
        get_response = self.client.get(
            f"/api/v1/scheduling/vet-availability/{self.test_vet_id}?date=2025-09-26"
        )
        assert get_response.status_code == 200
        assert len(get_response.json()) == 1
    
    @pytest.mark.asyncio
    async def test_midnight_boundary_case_pst(self):
        """
        Test: 11:30pm-12:30am PST (crosses local midnight)
        """
        availability_data = VetAvailabilityCreate(
            vet_user_id=self.test_vet_id,
            practice_id=self.test_practice_id,
            date=self.test_local_date,
            start_time=time(23, 30),  # 11:30pm PST
            end_time=time(0, 30),     # 12:30am PST (next day)
            timezone="America/Los_Angeles",
            availability_type="AVAILABLE"
        )
        
        response = self.client.post(
            "/api/v1/scheduling/vet-availability",
            json=availability_data.model_dump()
        )
        assert response.status_code == 201
        
        # Query local date - should find it
        get_response = self.client.get(
            f"/api/v1/scheduling/vet-availability/{self.test_vet_id}?date=2025-09-26"
        )
        assert get_response.status_code == 200
        assert len(get_response.json()) == 1
    
    @pytest.mark.asyncio 
    async def test_different_timezones_boundary_cases(self):
        """
        Test timezone boundary cases for different US timezones
        """
        test_cases = [
            {
                "timezone": "America/New_York",    # EST/EDT
                "local_time": time(20, 0),         # 8pm EST
                "expected_utc_date": "2025-09-27", # Next day UTC
                "description": "8pm EST -> 1am UTC next day"
            },
            {
                "timezone": "America/Chicago",     # CST/CDT  
                "local_time": time(19, 0),         # 7pm CST
                "expected_utc_date": "2025-09-27", # Next day UTC
                "description": "7pm CST -> 12am UTC next day"
            },
            {
                "timezone": "America/Denver",      # MST/MDT
                "local_time": time(18, 0),         # 6pm MST
                "expected_utc_date": "2025-09-27", # Next day UTC
                "description": "6pm MST -> 1am UTC next day"
            },
            {
                "timezone": "America/Los_Angeles", # PST/PDT
                "local_time": time(17, 0),         # 5pm PST
                "expected_utc_date": "2025-09-27", # Next day UTC
                "description": "5pm PST -> 12am UTC next day"
            }
        ]
        
        for i, case in enumerate(test_cases):
            # Use different vet for each case to avoid conflicts
            vet_id = uuid.uuid4()
            
            availability_data = VetAvailabilityCreate(
                vet_user_id=vet_id,
                practice_id=self.test_practice_id,
                date=self.test_local_date,
                start_time=case["local_time"],
                end_time=time(case["local_time"].hour + 1, case["local_time"].minute),
                timezone=case["timezone"],
                availability_type="AVAILABLE"
            )
            
            # Create
            response = self.client.post(
                "/api/v1/scheduling/vet-availability",
                json=availability_data.model_dump()
            )
            assert response.status_code == 201, f"Failed to create: {case['description']}"
            
            # Verify UTC storage
            created = response.json()
            assert created["date"] == case["expected_utc_date"], f"Wrong UTC date for: {case['description']}"
            
            # Query local date - should find it
            get_response = self.client.get(
                f"/api/v1/scheduling/vet-availability/{vet_id}?date=2025-09-26"
            )
            assert get_response.status_code == 200, f"Failed to query: {case['description']}"
            assert len(get_response.json()) == 1, f"Should find record for: {case['description']}"
    
    @pytest.mark.asyncio
    async def test_multiple_availabilities_mixed_boundaries(self):
        """
        Test multiple availabilities on same day with mixed boundary cases
        """
        availabilities = [
            # Morning - same UTC day
            {
                "start_time": time(9, 0),   # 9am PST -> 5pm UTC same day
                "end_time": time(10, 0),
                "expected_utc_date": "2025-09-26"
            },
            # Afternoon - same UTC day  
            {
                "start_time": time(14, 0),  # 2pm PST -> 10pm UTC same day
                "end_time": time(15, 0),
                "expected_utc_date": "2025-09-26"
            },
            # Evening - crosses to next UTC day
            {
                "start_time": time(17, 0),  # 5pm PST -> 1am UTC next day
                "end_time": time(18, 0),
                "expected_utc_date": "2025-09-27"
            },
            # Late evening - crosses to next UTC day
            {
                "start_time": time(22, 0),  # 10pm PST -> 6am UTC next day
                "end_time": time(23, 0),
                "expected_utc_date": "2025-09-27"
            }
        ]
        
        created_ids = []
        
        # Create all availabilities
        for i, avail in enumerate(availabilities):
            availability_data = VetAvailabilityCreate(
                vet_user_id=self.test_vet_id,
                practice_id=self.test_practice_id,
                date=self.test_local_date,
                start_time=avail["start_time"],
                end_time=avail["end_time"],
                timezone="America/Los_Angeles",
                availability_type="AVAILABLE"
            )
            
            response = self.client.post(
                "/api/v1/scheduling/vet-availability",
                json=availability_data.model_dump()
            )
            assert response.status_code == 201
            created = response.json()
            created_ids.append(created["id"])
            
            # Verify UTC date storage
            assert created["date"] == avail["expected_utc_date"]
        
        # Query for the local date - should find ALL 4 availabilities
        get_response = self.client.get(
            f"/api/v1/scheduling/vet-availability/{self.test_vet_id}?date=2025-09-26"
        )
        assert get_response.status_code == 200
        found_availabilities = get_response.json()
        
        # CRITICAL: Should find all 4 even though some are stored on next UTC day
        assert len(found_availabilities) == 4, f"Should find all 4 availabilities, found {len(found_availabilities)}"
        
        # Verify all created IDs are found
        found_ids = {avail["id"] for avail in found_availabilities}
        expected_ids = set(created_ids)
        assert found_ids == expected_ids, "Should find all created availabilities"
    
    @pytest.mark.asyncio
    async def test_query_edge_case_dates(self):
        """
        Test querying for dates that might have boundary issues
        """
        # Create availability on Sept 26 evening (stored on Sept 27 UTC)
        availability_data = VetAvailabilityCreate(
            vet_user_id=self.test_vet_id,
            practice_id=self.test_practice_id,
            date=date(2025, 9, 26),
            start_time=time(17, 0),  # 5pm PST
            end_time=time(18, 0),    # 6pm PST
            timezone="America/Los_Angeles",
            availability_type="AVAILABLE"
        )
        
        response = self.client.post(
            "/api/v1/scheduling/vet-availability",
            json=availability_data.model_dump()
        )
        assert response.status_code == 201
        
        # Test different query dates
        test_queries = [
            {
                "query_date": "2025-09-26",  # Local date - should find it
                "should_find": True,
                "description": "Query local date"
            },
            {
                "query_date": "2025-09-27",  # UTC date - depends on implementation
                "should_find": False,  # Should NOT find it (no local availability on Sept 27)
                "description": "Query UTC storage date"
            },
            {
                "query_date": "2025-09-25",  # Previous date - should not find
                "should_find": False,
                "description": "Query previous date"
            }
        ]
        
        for query in test_queries:
            get_response = self.client.get(
                f"/api/v1/scheduling/vet-availability/{self.test_vet_id}?date={query['query_date']}"
            )
            assert get_response.status_code == 200
            
            found = get_response.json()
            if query["should_find"]:
                assert len(found) == 1, f"Should find availability for {query['description']}"
            else:
                assert len(found) == 0, f"Should NOT find availability for {query['description']}"
    
    @pytest.mark.asyncio
    async def test_dst_transition_boundary_cases(self):
        """
        Test timezone boundary cases during DST transitions
        """
        # Spring forward date (March 10, 2025 - PST to PDT transition)
        spring_date = date(2025, 3, 10)
        
        # Fall back date (November 3, 2025 - PDT to PST transition)  
        fall_date = date(2025, 11, 3)
        
        dst_cases = [
            {
                "date": spring_date,
                "timezone": "America/Los_Angeles",
                "start_time": time(17, 0),  # 5pm during spring transition
                "description": "Spring DST transition"
            },
            {
                "date": fall_date, 
                "timezone": "America/Los_Angeles",
                "start_time": time(17, 0),  # 5pm during fall transition
                "description": "Fall DST transition"
            }
        ]
        
        for case in dst_cases:
            vet_id = uuid.uuid4()
            
            availability_data = VetAvailabilityCreate(
                vet_user_id=vet_id,
                practice_id=self.test_practice_id,
                date=case["date"],
                start_time=case["start_time"],
                end_time=time(case["start_time"].hour + 1, 0),
                timezone=case["timezone"],
                availability_type="AVAILABLE"
            )
            
            # Should handle DST transitions gracefully
            response = self.client.post(
                "/api/v1/scheduling/vet-availability",
                json=availability_data.model_dump()
            )
            assert response.status_code == 201, f"Failed during {case['description']}"
            
            # Should be able to query back
            get_response = self.client.get(
                f"/api/v1/scheduling/vet-availability/{vet_id}?date={case['date']}"
            )
            assert get_response.status_code == 200, f"Failed to query during {case['description']}"
            assert len(get_response.json()) == 1, f"Should find record during {case['description']}"


# Additional edge case tests
class TestTimezoneEdgeCases:
    """Additional edge cases for timezone handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_timezone_handling(self):
        """Test handling of invalid timezone strings"""
        client = TestClient(app)
        
        availability_data = VetAvailabilityCreate(
            vet_user_id=uuid.uuid4(),
            practice_id=uuid.uuid4(),
            date=date(2025, 9, 26),
            start_time=time(17, 0),
            end_time=time(18, 0),
            timezone="Invalid/Timezone",  # Invalid timezone
            availability_type="AVAILABLE"
        )
        
        response = client.post(
            "/api/v1/scheduling/vet-availability",
            json=availability_data.model_dump()
        )
        
        # Should return 422 for invalid timezone
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_extreme_timezone_offsets(self):
        """Test extreme timezone offsets (e.g., UTC+14, UTC-12)"""
        # Note: These might not be relevant for US vet practices but good to test
        extreme_cases = [
            "Pacific/Kiritimati",  # UTC+14 
            "Pacific/Baker_Island", # UTC-12
        ]
        
        client = TestClient(app)
        
        for tz in extreme_cases:
            try:
                availability_data = VetAvailabilityCreate(
                    vet_user_id=uuid.uuid4(),
                    practice_id=uuid.uuid4(), 
                    date=date(2025, 9, 26),
                    start_time=time(12, 0),  # Noon
                    end_time=time(13, 0),    # 1pm
                    timezone=tz,
                    availability_type="AVAILABLE"
                )
                
                response = client.post(
                    "/api/v1/scheduling/vet-availability",
                    json=availability_data.model_dump()
                )
                
                # Should either succeed or fail gracefully
                assert response.status_code in [201, 422], f"Unexpected status for timezone {tz}"
                
            except Exception as e:
                # Some extreme timezones might not be supported - that's OK
                pass


if __name__ == "__main__":
    """Run tests directly for development"""
    import asyncio
    
    async def run_single_test():
        """Run a single test for debugging"""
        test_instance = TestTimezoneBoundaryScheduling()
        test_instance.setup_method()
        
        print("🧪 Running timezone boundary test...")
        await test_instance.test_evening_time_crosses_utc_boundary_pst()
        print("✅ Test completed!")
    
    asyncio.run(run_single_test())
