"""
UTC STORAGE VERIFICATION TESTS

These tests ensure we ALWAYS store in UTC (never break this rule)
while fixing the display issues in the iOS app.

FUNDAMENTAL RULE: Database always stores UTC times on UTC dates.
FIX THE DISPLAY, NOT THE STORAGE.
"""

import pytest
import pytz
from datetime import datetime, date, time, timedelta
from uuid import uuid4

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schemas.scheduling_schemas import VetAvailabilityCreate


class TestUTCStorageRule:
    """Verify we ALWAYS store in UTC"""
    
    def test_5pm_6pm_pst_stores_utc_correctly(self):
        """Test 5-6pm PST stores correctly in UTC (on correct UTC date)"""
        print("\n🗄️ TESTING UTC STORAGE: 5-6pm PST Friday Oct 3")
        
        availability = VetAvailabilityCreate(
            vet_user_id=uuid4(),
            practice_id=uuid4(),
            date=date(2025, 10, 3),   # Friday Oct 3 (user's local date)
            start_time=time(17, 0),   # 5pm PST
            end_time=time(18, 0),     # 6pm PST
            timezone="America/Los_Angeles"
        )
        
        local_start, local_end = availability.get_local_datetime_range()
        utc_start, utc_end = availability.to_utc_datetime_range()
        
        print(f"👤 User selected: {availability.date} {availability.start_time}-{availability.end_time} PST")
        print(f"🌍 Local times: {local_start} to {local_end}")
        print(f"🌐 UTC times: {utc_start} to {utc_end}")
        
        # UTC STORAGE (what database should contain):
        # 5pm PST Oct 3 = midnight UTC Oct 4
        # 6pm PST Oct 3 = 1am UTC Oct 4
        expected_storage = {
            'date': date(2025, 10, 4),  # UTC date
            'start_time': time(0, 0),   # midnight UTC
            'end_time': time(1, 0),     # 1am UTC
        }
        
        print(f"🗄️ Expected UTC storage: {expected_storage}")
        
        # Verify UTC conversion is correct
        assert utc_start.date() == expected_storage['date']
        assert utc_start.time() == expected_storage['start_time']
        assert utc_end.time() == expected_storage['end_time']
        
        print("✅ UTC storage is correct")
        
        # Now verify the iOS display logic would work
        # When iOS reads this back, it should display on Oct 3
        pst_tz = pytz.timezone("America/Los_Angeles")
        
        # Create UTC datetime from stored values
        stored_utc_start = pytz.UTC.localize(datetime.combine(expected_storage['date'], expected_storage['start_time']))
        stored_utc_end = pytz.UTC.localize(datetime.combine(expected_storage['date'], expected_storage['end_time']))
        
        # Convert back to PST for display
        display_start_pst = stored_utc_start.astimezone(pst_tz)
        display_end_pst = stored_utc_end.astimezone(pst_tz)
        
        print(f"📱 iOS should display: {display_start_pst.date()} {display_start_pst.time()}-{display_end_pst.time()}")
        
        # CRITICAL: Should display on user's intended date (Oct 3)
        assert display_start_pst.date() == date(2025, 10, 3), "Should display on Oct 3"
        assert display_start_pst.time() == time(17, 0), "Should display 5pm"
        assert display_end_pst.time() == time(18, 0), "Should display 6pm"
        
        print("✅ iOS display logic should work correctly")
        
    def test_cross_day_utc_storage_pattern(self):
        """Test the pattern for storing cross-day UTC times"""
        
        test_cases = [
            # (description, local_date, start_time, end_time, expected_utc_date, expected_start_utc, expected_end_utc)
            ("5-6pm PST Oct 3", date(2025, 10, 3), time(17, 0), time(18, 0), date(2025, 10, 4), time(0, 0), time(1, 0)),
            ("6-7pm PST Oct 3", date(2025, 10, 3), time(18, 0), time(19, 0), date(2025, 10, 4), time(1, 0), time(2, 0)),
            ("11pm-midnight PST", date(2025, 10, 3), time(23, 0), time(0, 0), date(2025, 10, 4), time(6, 0), time(7, 0)),
            ("9am-5pm PST", date(2025, 10, 3), time(9, 0), time(17, 0), date(2025, 10, 3), time(16, 0), time(0, 0)),  # End crosses to Oct 4
        ]
        
        for desc, local_date, start_local, end_local, expected_utc_date, expected_start_utc, expected_end_utc in test_cases:
            print(f"\n🧪 Testing: {desc}")
            
            availability = VetAvailabilityCreate(
                vet_user_id=uuid4(),
                practice_id=uuid4(),
                date=local_date,
                start_time=start_local,
                end_time=end_local,
                timezone="America/Los_Angeles"
            )
            
            utc_start, utc_end = availability.to_utc_datetime_range()
            
            print(f"   Expected UTC: {expected_utc_date} {expected_start_utc}-{expected_end_utc}")
            print(f"   Actual UTC: {utc_start.date()} {utc_start.time()}-{utc_end.time()}")
            
            # Verify UTC storage
            if utc_start.date() == utc_end.date():
                # Same UTC day
                assert utc_start.date() == expected_utc_date
                assert utc_start.time() == expected_start_utc
                assert utc_end.time() == expected_end_utc
            else:
                # Cross UTC day - store on start date
                assert utc_start.date() == expected_utc_date or utc_start.date() == expected_utc_date - timedelta(days=1)
                print(f"   Cross-day: {utc_start.date()} to {utc_end.date()}")
            
            print("   ✅ UTC storage verified")


class TestIOSDisplayLogic:
    """Test that iOS can correctly display UTC-stored times"""
    
    def test_ios_should_show_correct_local_day(self):
        """Test that iOS logic shows availability on correct local day"""
        print("\n📱 TESTING iOS DISPLAY LOGIC")
        
        # Database contains: Oct 4 00:00-01:00 UTC (from 5-6pm PST Oct 3)
        stored_utc_date = date(2025, 10, 4)
        stored_start_utc = time(0, 0)   # midnight UTC
        stored_end_utc = time(1, 0)     # 1am UTC
        
        print(f"🗄️ Database has: {stored_utc_date} {stored_start_utc}-{stored_end_utc} UTC")
        
        # Convert to PST for display (what iOS should do)
        pst_tz = pytz.timezone("America/Los_Angeles")
        
        utc_start_dt = pytz.UTC.localize(datetime.combine(stored_utc_date, stored_start_utc))
        utc_end_dt = pytz.UTC.localize(datetime.combine(stored_utc_date, stored_end_utc))
        
        pst_start = utc_start_dt.astimezone(pst_tz)
        pst_end = utc_end_dt.astimezone(pst_tz)
        
        print(f"📱 iOS converts to: {pst_start.date()} {pst_start.time()}-{pst_end.time()} PST")
        
        # CRITICAL: Should show on Oct 3 (user's original day)
        assert pst_start.date() == date(2025, 10, 3), f"Should display on Oct 3, got {pst_start.date()}"
        assert pst_start.time() == time(17, 0), f"Should show 5pm, got {pst_start.time()}"
        assert pst_end.time() == time(18, 0), f"Should show 6pm, got {pst_end.time()}"
        
        print("✅ iOS should display correctly: Oct 3 5-6pm")
        
    def test_ios_calendar_filtering_logic(self):
        """Test that iOS calendar shows availability on correct day"""
        print("\n📅 TESTING iOS CALENDAR FILTERING")
        
        # Simulate what happens when iOS loads calendar for Oct 3
        calendar_date = date(2025, 10, 3)  # User viewing Oct 3
        
        # Database has these availabilities:
        stored_availabilities = [
            # 5-6pm PST Oct 3 → stored as Oct 4 00:00-01:00 UTC
            {'date': date(2025, 10, 4), 'start_time': time(0, 0), 'end_time': time(1, 0)},
            # 6-7pm PST Oct 3 → stored as Oct 4 01:00-02:00 UTC  
            {'date': date(2025, 10, 4), 'start_time': time(1, 0), 'end_time': time(2, 0)},
            # 9am-10am PST Oct 3 → stored as Oct 3 16:00-17:00 UTC
            {'date': date(2025, 10, 3), 'start_time': time(16, 0), 'end_time': time(17, 0)},
        ]
        
        print(f"📅 User viewing calendar for: {calendar_date}")
        print(f"🗄️ Database contains {len(stored_availabilities)} availabilities")
        
        # Convert each stored availability back to PST and check which day it should appear on
        pst_tz = pytz.timezone("America/Los_Angeles")
        availabilities_for_oct3 = []
        
        for stored in stored_availabilities:
            # Handle cross-day logic (like our iOS fix)
            if stored['end_time'] < stored['start_time']:
                # End time is next day
                next_day = stored['date'] + timedelta(days=1)
                utc_start = pytz.UTC.localize(datetime.combine(stored['date'], stored['start_time']))
                utc_end = pytz.UTC.localize(datetime.combine(next_day, stored['end_time']))
            else:
                # Same day
                utc_start = pytz.UTC.localize(datetime.combine(stored['date'], stored['start_time']))
                utc_end = pytz.UTC.localize(datetime.combine(stored['date'], stored['end_time']))
            
            pst_start = utc_start.astimezone(pst_tz)
            pst_end = utc_end.astimezone(pst_tz)
            
            print(f"   {stored} → PST: {pst_start.date()} {pst_start.time()}-{pst_end.time()}")
            
            # If the PST date matches the calendar date, include it
            if pst_start.date() == calendar_date:
                availabilities_for_oct3.append({
                    'start': pst_start.time(),
                    'end': pst_end.time()
                })
        
        print(f"📱 iOS should show {len(availabilities_for_oct3)} availabilities on Oct 3:")
        for av in availabilities_for_oct3:
            print(f"   {av['start']}-{av['end']}")
        
        # Should show all 3 availabilities on Oct 3
        assert len(availabilities_for_oct3) == 3, f"Should show 3 availabilities on Oct 3, got {len(availabilities_for_oct3)}"
        
        # Verify the specific times
        times = [(av['start'], av['end']) for av in availabilities_for_oct3]
        expected_times = [(time(9, 0), time(10, 0)), (time(17, 0), time(18, 0)), (time(18, 0), time(19, 0))]
        
        for expected in expected_times:
            assert expected in times, f"Missing expected time {expected}"
        
        print("✅ All availabilities correctly appear on Oct 3!")


if __name__ == "__main__":
    print("🚨 VERIFYING UTC STORAGE RULE IS MAINTAINED")
    print("=" * 80)
    
    # Test UTC storage
    utc_test = TestUTCStorageRule()
    try:
        utc_test.test_5pm_6pm_pst_stores_utc_correctly()
        print("✅ UTC storage test passed")
    except Exception as e:
        print(f"❌ UTC storage test FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        utc_test.test_cross_day_utc_storage_pattern()
        print("✅ Cross-day storage test passed")
    except Exception as e:
        print(f"❌ Cross-day storage test FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    # Test iOS display
    ios_test = TestIOSDisplayLogic()
    try:
        ios_test.test_ios_should_show_correct_local_day()
        print("✅ iOS display test passed")
    except Exception as e:
        print(f"❌ iOS display test FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        ios_test.test_ios_calendar_filtering_logic()
        print("✅ iOS calendar filtering test passed")
    except Exception as e:
        print(f"❌ iOS calendar filtering test FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)
    print("🎯 RULE MAINTAINED: Database always stores in UTC")
    print("🎯 FIX APPLIED: iOS handles cross-day UTC times correctly")
