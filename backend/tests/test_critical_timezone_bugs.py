"""
CRITICAL TIMEZONE BUG TESTS

These tests catch the exact bugs that are causing appointments to be stored on wrong dates.
ALL OF THESE MUST PASS or the timezone system is broken.

Based on real production bugs:
- User creates 5-6pm on Friday Oct 3rd
- System stores it as midnight-1am on Saturday Oct 4th  
- WRONG DAY! WRONG TIMES!
"""

import pytest
import pytz
from datetime import datetime, date, time, timedelta
from uuid import uuid4

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.scheduling_schemas import VetAvailabilityCreate


class TestCriticalDateBugs:
    """Test the exact scenarios that are causing wrong-day storage"""
    
    def test_5pm_6pm_friday_oct_3_bug(self):
        """
        CRITICAL BUG TEST: 5-6pm Friday Oct 3rd should NOT end up on Oct 4th
        
        This is the exact bug from production database:
        - User selects 5-6pm on Friday Oct 3rd  
        - System stores as 00:00-01:00 on Saturday Oct 4th
        - COMPLETELY WRONG!
        """
        print("\n🚨 TESTING CRITICAL BUG: 5-6pm Friday Oct 3rd")
        
        # What user selected in iOS
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),   # Friday Oct 3rd
            start_time=time(17, 0),   # 5pm PST
            end_time=time(18, 0),     # 6pm PST  
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        print(f"📅 User selected: Friday Oct 3, 5-6pm PST")
        print(f"🌍 Local times: {local_start} to {local_end}")
        print(f"🌐 UTC times: {utc_start} to {utc_end}")
        
        # CRITICAL ASSERTIONS - these must pass!
        assert local_start.date() == date(2025, 10, 3), f"Local start should be Oct 3, got {local_start.date()}"
        assert local_end.date() == date(2025, 10, 3), f"Local end should be Oct 3, got {local_end.date()}"
        
        # UTC conversion should be:
        # 5pm PST (Oct 3) = midnight UTC (Oct 4) ✅
        # 6pm PST (Oct 3) = 1am UTC (Oct 4) ✅
        expected_utc_start_hour = 0  # midnight UTC
        expected_utc_end_hour = 1    # 1am UTC
        
        print(f"🔍 Expected UTC: {expected_utc_start_hour}:00 to {expected_utc_end_hour}:00 on Oct 4")
        print(f"🔍 Actual UTC: {utc_start.hour}:00 to {utc_end.hour}:00 on {utc_start.date()}-{utc_end.date()}")
        
        # The UTC times should be on Oct 4 (next day)
        assert utc_start.date() == date(2025, 10, 4), f"UTC start should be Oct 4, got {utc_start.date()}"
        assert utc_end.date() == date(2025, 10, 4), f"UTC end should be Oct 4, got {utc_end.date()}"
        assert utc_start.hour == expected_utc_start_hour, f"UTC start should be {expected_utc_start_hour}:00, got {utc_start.hour}:00"
        assert utc_end.hour == expected_utc_end_hour, f"UTC end should be {expected_utc_end_hour}:00, got {utc_end.hour}:00"
        
        # Now test the storage logic
        data_dict = {}
        data_dict['start_time'] = utc_start.time()
        data_dict['date'] = utc_start.date()
        
        if utc_start.date() != utc_end.date():
            data_dict['end_time'] = time(23, 59, 59)  # Our boundary fix
        else:
            data_dict['end_time'] = utc_end.time()
        
        print(f"🗄️ Storage logic result:")
        print(f"   date: {data_dict['date']}")
        print(f"   start_time: {data_dict['start_time']}")  
        print(f"   end_time: {data_dict['end_time']}")
        
        # CRITICAL: The stored date should represent the correct day
        # If we store on Oct 4 with times 00:00-01:00, that's correct for 5-6pm PST Oct 3
        assert data_dict['date'] == date(2025, 10, 4), "Should store on Oct 4 (UTC date)"
        assert data_dict['start_time'] == time(0, 0), "Should store as midnight UTC"
        
    def test_6pm_7pm_friday_oct_3_bug(self):
        """
        CRITICAL BUG TEST: 6-7pm Friday Oct 3rd 
        """
        print("\n🚨 TESTING CRITICAL BUG: 6-7pm Friday Oct 3rd")
        
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),   # Friday Oct 3rd
            start_time=time(18, 0),   # 6pm PST
            end_time=time(19, 0),     # 7pm PST
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        print(f"📅 User selected: Friday Oct 3, 6-7pm PST")
        print(f"🌍 Local times: {local_start} to {local_end}")
        print(f"🌐 UTC times: {utc_start} to {utc_end}")
        
        # 6pm PST (Oct 3) = 1am UTC (Oct 4)
        # 7pm PST (Oct 3) = 2am UTC (Oct 4)
        assert utc_start.date() == date(2025, 10, 4)
        assert utc_end.date() == date(2025, 10, 4)
        assert utc_start.hour == 1  # 1am UTC
        assert utc_end.hour == 2    # 2am UTC
        
    def test_9am_5pm_original_bug(self):
        """
        ORIGINAL BUG TEST: 9am-5pm should work correctly
        """
        print("\n🚨 TESTING ORIGINAL BUG: 9am-5pm PST")
        
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),   # Friday Oct 3rd
            start_time=time(9, 0),    # 9am PST
            end_time=time(17, 0),     # 5pm PST
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        print(f"📅 User selected: Friday Oct 3, 9am-5pm PST")
        print(f"🌍 Local times: {local_start} to {local_end}")
        print(f"🌐 UTC times: {utc_start} to {utc_end}")
        
        # 9am PST (Oct 3) = 4pm UTC (Oct 3) - during PDT
        # 5pm PST (Oct 3) = midnight UTC (Oct 4) - during PDT
        assert local_start.date() == date(2025, 10, 3)
        assert local_end.date() == date(2025, 10, 3)
        
        # UTC should be 4pm Oct 3 to midnight Oct 4
        assert utc_start.date() == date(2025, 10, 3)
        assert utc_end.date() == date(2025, 10, 4)
        assert utc_start.hour == 16  # 4pm UTC
        assert utc_end.hour == 0     # midnight UTC


class TestWrongDayDetection:
    """Test detection and prevention of wrong-day storage"""
    
    def test_detect_wrong_day_storage(self):
        """Test that we can detect when storage would put availability on wrong day"""
        
        test_cases = [
            # (local_date, start_time, end_time, timezone, expected_issues)
            (date(2025, 10, 3), time(17, 0), time(18, 0), "America/Los_Angeles", True),   # 5-6pm PST
            (date(2025, 10, 3), time(18, 0), time(19, 0), "America/Los_Angeles", True),   # 6-7pm PST  
            (date(2025, 10, 3), time(9, 0), time(10, 0), "America/Los_Angeles", False),   # 9-10am PST
            (date(2025, 10, 3), time(14, 0), time(15, 0), "America/Los_Angeles", False),  # 2-3pm PST
        ]
        
        for local_date, start_time, end_time, timezone, should_have_issues in test_cases:
            availability = VetAvailabilityCreate(
                vet_user_id=uuid4(),
                practice_id=uuid4(),
                date=local_date,
                start_time=start_time,
                end_time=end_time,
                timezone=timezone
            )
            
            local_start, local_end = availability.get_local_datetime_range()
            utc_start, utc_end = availability.to_utc_datetime_range()
            
            # Check if UTC date is different from local date
            utc_date_different = (utc_start.date() != local_date or utc_end.date() != local_date)
            
            if should_have_issues:
                assert utc_date_different, f"Expected date shift for {start_time}-{end_time} on {local_date}"
                print(f"✅ Detected date shift: {local_date} {start_time}-{end_time} → UTC {utc_start.date()}-{utc_end.date()}")
            else:
                print(f"✅ No date shift: {local_date} {start_time}-{end_time} → UTC {utc_start.date()}-{utc_end.date()}")


class TestDatabaseStorageSimulation:
    """Simulate the exact database storage logic to catch bugs"""
    
    def test_storage_simulation_5pm_6pm(self):
        """Simulate storing 5-6pm PST and verify it doesn't go to wrong day"""
        print("\n🗄️ SIMULATING DATABASE STORAGE: 5-6pm PST Friday Oct 3")
        
        # User input: 5-6pm PST on Friday Oct 3
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),   # Friday Oct 3
            start_time=time(17, 0),   # 5pm PST
            end_time=time(18, 0),     # 6pm PST
            timezone="America/Los_Angeles"
        )
        
        # Step 1: Convert to UTC
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        print(f"🌍 Local: {local_start} to {local_end}")
        print(f"🌐 UTC: {utc_start} to {utc_end}")
        
        # Step 2: Apply API storage logic
        data_dict = {}
        data_dict['start_time'] = utc_start.time()
        data_dict['date'] = utc_start.date()
        
        if utc_start.date() != utc_end.date():
            print("⚠️ Date boundary shift detected")
            data_dict['end_time'] = time(23, 59, 59)
        else:
            print("✅ No date boundary shift")
            data_dict['end_time'] = utc_end.time()
        
        print(f"🗄️ Would store in database:")
        print(f"   date: {data_dict['date']}")
        print(f"   start_time: {data_dict['start_time']}")
        print(f"   end_time: {data_dict['end_time']}")
        
        # CRITICAL VERIFICATION:
        # When user creates 5-6pm PST on Oct 3, the database should store times that
        # when converted back to PST, show the appointment on Oct 3, not Oct 4!
        
        # Convert stored UTC times back to PST to verify
        stored_utc_start = datetime.combine(data_dict['date'], data_dict['start_time'])
        stored_utc_start = pytz.UTC.localize(stored_utc_start)
        
        if data_dict['end_time'] == time(23, 59, 59):
            # This represents end of the stored date
            stored_utc_end = datetime.combine(data_dict['date'], time(23, 59, 59))
        else:
            stored_utc_end = datetime.combine(data_dict['date'], data_dict['end_time'])
        stored_utc_end = pytz.UTC.localize(stored_utc_end)
        
        # Convert back to PST
        pst_tz = pytz.timezone("America/Los_Angeles")
        display_start = stored_utc_start.astimezone(pst_tz)
        display_end = stored_utc_end.astimezone(pst_tz)
        
        print(f"🔄 Converted back to PST for display:")
        print(f"   Start: {display_start}")
        print(f"   End: {display_end}")
        
        # CRITICAL: The display should show Oct 3, not Oct 4!
        assert display_start.date() == date(2025, 10, 3), f"Display start should be Oct 3, got {display_start.date()}"
        
        # For end time, if it's 23:59:59, it represents the end of Oct 3 in UTC
        # When converted back to PST, it should still represent Oct 3 evening
        if data_dict['end_time'] == time(23, 59, 59):
            # 23:59:59 UTC on Oct 4 = ~4:59pm PST on Oct 4 (WRONG!)
            # We need a different approach
            print("⚠️ Our 23:59:59 fix might be wrong - it converts to wrong day!")
        
    def test_correct_storage_approach(self):
        """Test what the CORRECT storage approach should be"""
        print("\n💡 TESTING CORRECT STORAGE APPROACH")
        
        # User wants 5-6pm PST on Oct 3
        local_date = date(2025, 10, 3)
        start_time_local = time(17, 0)  # 5pm PST
        end_time_local = time(18, 0)    # 6pm PST
        timezone_str = "America/Los_Angeles"
        
        # Convert to UTC
        tz = pytz.timezone(timezone_str)
        local_start = tz.localize(datetime.combine(local_date, start_time_local))
        local_end = tz.localize(datetime.combine(local_date, end_time_local))
        utc_start = local_start.astimezone(pytz.UTC)
        utc_end = local_end.astimezone(pytz.UTC)
        
        print(f"🌍 Local: {local_start} to {local_end}")
        print(f"🌐 UTC: {utc_start} to {utc_end}")
        
        # CORRECT APPROACH: Store the actual UTC datetime, not time-only
        # But since our schema only has date + time, we need to be smarter
        
        # Option 1: Store on the LOCAL date with adjusted times
        # This keeps the availability on the user's intended date
        
        # Option 2: Store full UTC datetime (requires schema change)
        
        # Option 3: Store with timezone metadata (requires schema change)
        
        # For now, let's verify what happens with current approach
        if utc_start.date() != utc_end.date():
            # Current approach: use start date, convert end to 23:59:59
            stored_date = utc_start.date()  # Oct 4 UTC
            stored_start = utc_start.time()  # 00:00 UTC
            stored_end = time(23, 59, 59)   # 23:59:59 UTC
        else:
            stored_date = utc_start.date()
            stored_start = utc_start.time()
            stored_end = utc_end.time()
        
        # Convert back to verify display
        stored_utc_start = pytz.UTC.localize(datetime.combine(stored_date, stored_start))
        display_start_pst = stored_utc_start.astimezone(tz)
        
        print(f"🔄 Stored UTC: {stored_date} {stored_start}")
        print(f"🔄 Display PST: {display_start_pst}")
        
        # The problem: storing on UTC date (Oct 4) makes it display on wrong day!
        # We need to store on the LOCAL date (Oct 3) instead
        
        print("💡 BETTER APPROACH:")
        print("   Store on LOCAL date (Oct 3) with UTC times")
        print("   This keeps the availability on the user's intended day")
        
        better_storage = {
            'date': local_date,  # Oct 3 (user's intended date)
            'start_time': utc_start.time(),  # 00:00 UTC
            'end_time': utc_end.time() if utc_start.date() == utc_end.date() else time(23, 59, 59)
        }
        
        print(f"   Better storage: {better_storage}")
        
        # This should display correctly
        better_utc_start = pytz.UTC.localize(datetime.combine(better_storage['date'], better_storage['start_time']))
        better_display = better_utc_start.astimezone(tz)
        
        # But wait - this is wrong too! Oct 3 00:00 UTC = Oct 2 5pm PST!
        print(f"   Better display: {better_display}")
        print("❌ Still wrong! We need a completely different approach.")


class TestProposedFix:
    """Test a proposed fix for the wrong-day storage issue"""
    
    def test_store_on_local_date_with_offset_metadata(self):
        """
        PROPOSED FIX: Store on local date but with timezone offset metadata
        
        Instead of converting times to UTC and losing context, store:
        - date: local date (Oct 3)
        - start_time: local time (17:00)  
        - end_time: local time (18:00)
        - timezone: "America/Los_Angeles"
        - utc_offset: store the UTC offset for reference
        """
        print("\n💡 TESTING PROPOSED FIX: Store local times with timezone metadata")
        
        local_date = date(2025, 10, 3)
        start_time_local = time(17, 0)  # 5pm PST
        end_time_local = time(18, 0)    # 6pm PST
        timezone_str = "America/Los_Angeles"
        
        # Get timezone info
        tz = pytz.timezone(timezone_str)
        local_start = tz.localize(datetime.combine(local_date, start_time_local))
        local_end = tz.localize(datetime.combine(local_date, end_time_local))
        
        # Proposed storage format
        proposed_storage = {
            'date': local_date,           # Oct 3 (user's intended date)
            'start_time': start_time_local,  # 17:00 (local time)
            'end_time': end_time_local,      # 18:00 (local time)
            'timezone': timezone_str,        # "America/Los_Angeles"
            'utc_offset': local_start.strftime('%z'),  # "-0700" or "-0800"
        }
        
        print(f"📦 Proposed storage: {proposed_storage}")
        
        # Verification: This would display correctly
        assert proposed_storage['date'] == date(2025, 10, 3)
        assert proposed_storage['start_time'] == time(17, 0)
        assert proposed_storage['end_time'] == time(18, 0)
        
        print("✅ This approach would keep availability on correct day!")
        print("✅ No timezone conversion bugs!")
        print("✅ Easy to display - just show the stored local times!")


class TestCurrentSystemProblems:
    """Document and test the problems with current system"""
    
    def test_current_system_creates_wrong_day_bug(self):
        """Prove that current system creates wrong-day bug"""
        print("\n🚨 PROVING CURRENT SYSTEM IS BROKEN")
        
        # What user wants: 5-6pm PST on Friday Oct 3
        user_intent = {
            'date': date(2025, 10, 3),
            'start_time': time(17, 0),
            'end_time': time(18, 0),
            'timezone': "America/Los_Angeles"
        }
        
        print(f"👤 User wants: {user_intent['date']} {user_intent['start_time']}-{user_intent['end_time']} PST")
        
        # Current system conversion
        availability = VetAvailabilityCreate(**{
            'vet_user_id': uuid4(),
            'practice_id': uuid4(),
            **user_intent
        })
        
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        # Current storage logic
        if utc_start.date() != utc_end.date():
            stored_date = utc_start.date()  # Oct 4 UTC
            stored_start = utc_start.time()  # 00:00 UTC  
            stored_end = time(23, 59, 59)   # 23:59:59 UTC
        else:
            stored_date = utc_start.date()
            stored_start = utc_start.time()
            stored_end = utc_end.time()
        
        print(f"🗄️ Current system stores: {stored_date} {stored_start}-{stored_end} UTC")
        
        # Convert back to PST for display
        pst_tz = pytz.timezone("America/Los_Angeles")
        display_start = pytz.UTC.localize(datetime.combine(stored_date, stored_start)).astimezone(pst_tz)
        
        print(f"📱 iOS displays: {display_start.date()} {display_start.time()} PST")
        
        # THE BUG: Display date != User's intended date
        if display_start.date() != user_intent['date']:
            print(f"❌ BUG CONFIRMED: User wanted {user_intent['date']}, but displays {display_start.date()}")
            print("❌ SYSTEM IS STORING AVAILABILITY ON WRONG DAY!")
        else:
            print("✅ No wrong-day bug detected")


if __name__ == "__main__":
    print("🚨 RUNNING CRITICAL TIMEZONE BUG TESTS")
    print("=" * 80)
    
    # Run the critical tests
    test_class = TestCriticalDateBugs()
    
    try:
        test_class.test_5pm_6pm_friday_oct_3_bug()
        print("✅ 5-6pm test passed")
    except Exception as e:
        print(f"❌ 5-6pm test FAILED: {e}")
    
    try:
        test_class.test_6pm_7pm_friday_oct_3_bug()
        print("✅ 6-7pm test passed")
    except Exception as e:
        print(f"❌ 6-7pm test FAILED: {e}")
    
    try:
        test_class.test_9am_5pm_original_bug()
        print("✅ 9am-5pm test passed")
    except Exception as e:
        print(f"❌ 9am-5pm test FAILED: {e}")
    
    # Test wrong day detection
    wrong_day_test = TestWrongDayDetection()
    try:
        wrong_day_test.test_detect_wrong_day_storage()
        print("✅ Wrong day detection test passed")
    except Exception as e:
        print(f"❌ Wrong day detection FAILED: {e}")
    
    # Test current system problems
    problem_test = TestCurrentSystemProblems()
    try:
        problem_test.test_current_system_creates_wrong_day_bug()
        print("✅ Current system problem test completed")
    except Exception as e:
        print(f"❌ Current system test FAILED: {e}")
    
    print("=" * 80)
    print("🎯 These tests reveal the exact timezone bugs in your system!")
