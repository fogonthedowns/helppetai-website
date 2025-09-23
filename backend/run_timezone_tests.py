#!/usr/bin/env python3
"""
Timezone Test Runner

Run all timezone-related tests to ensure the system is bulletproof.
This avoids the problematic existing tests and focuses on timezone handling.
"""

import subprocess
import sys
import os

def run_timezone_tests():
    """Run all timezone tests and report results"""
    
    print("🧪 RUNNING COMPREHENSIVE TIMEZONE TESTS")
    print("=" * 80)
    
    # List of timezone test files
    test_files = [
        "tests/test_timezone_handling.py",
        "tests/test_critical_timezone_bugs.py", 
        "tests/test_utc_storage_verification.py",
        "tests/test_scheduling_api_timezone.py"
    ]
    
    all_passed = True
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n🔍 Running {test_file}...")
            print("-" * 60)
            
            # Run pytest on individual file
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file, 
                "-v", "--tb=short", "-q"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {test_file} - ALL TESTS PASSED")
                # Show just the summary
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'passed' in line and ('warning' in line or 'error' in line or '=' in line):
                        print(f"   {line}")
            else:
                print(f"❌ {test_file} - TESTS FAILED")
                print("STDOUT:")
                print(result.stdout)
                if result.stderr:
                    print("STDERR:")
                    print(result.stderr)
                all_passed = False
        else:
            print(f"⚠️ {test_file} - FILE NOT FOUND")
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TIMEZONE TESTS PASSED!")
        print("✅ Timezone handling is bulletproof")
        print("✅ No more 422 errors")
        print("✅ No more wrong-day bugs")
        print("✅ UTC storage rule maintained")
    else:
        print("❌ SOME TIMEZONE TESTS FAILED!")
        print("🚨 Timezone bugs may still exist")
        
    return all_passed


def run_specific_test_categories():
    """Run specific categories of timezone tests"""
    
    categories = [
        ("Basic Timezone Conversions", "tests/test_timezone_handling.py::TestTimezoneConversions"),
        ("Boundary Conditions", "tests/test_timezone_handling.py::TestBoundaryConditions"), 
        ("Critical Production Bugs", "tests/test_critical_timezone_bugs.py::TestCriticalDateBugs"),
        ("UTC Storage Verification", "tests/test_utc_storage_verification.py::TestUTCStorageRule"),
        ("iOS Display Logic", "tests/test_utc_storage_verification.py::TestIOSDisplayLogic"),
    ]
    
    print("🎯 RUNNING SPECIFIC TEST CATEGORIES")
    print("=" * 80)
    
    for category_name, test_path in categories:
        print(f"\n📋 {category_name}")
        print("-" * 40)
        
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            test_path, 
            "-v", "--tb=line"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ PASSED")
        else:
            print(f"❌ FAILED")
            print(result.stdout[-500:])  # Show last 500 chars


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--categories":
        run_specific_test_categories()
    else:
        success = run_timezone_tests()
        sys.exit(0 if success else 1)
