#!/usr/bin/env python3
"""
Test script for phone call integration
Run this to verify the phone webhook endpoints are working
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust if your server runs on different port
WEBHOOK_URL = f"{BASE_URL}/api/v1/webhook/phone"
SETUP_URL = f"{BASE_URL}/api/v1/webhook/setup-retell"

def test_phone_webhook():
    """Test the phone webhook endpoint"""
    
    # Test payload simulating Retell AI webhook for phone lookup
    test_payload_phone = {
        "function_call": {
            "name": "check_user",
            "arguments": {
                "phone_number": "+1234567890"
            }
        }
    }
    
    print("Testing phone webhook endpoint (phone lookup)...")
    print(f"URL: {WEBHOOK_URL}")
    print(f"Payload: {json.dumps(test_payload_phone, indent=2)}")
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=test_payload_phone,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Phone lookup webhook is working!")
        else:
            print("❌ Phone lookup webhook returned an error")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure your FastAPI server is running.")
    except Exception as e:
        print(f"❌ Error testing phone lookup: {e}")

def test_email_webhook():
    """Test the email webhook endpoint"""
    
    # Test payload simulating Retell AI webhook for email lookup
    test_payload_email = {
        "function_call": {
            "name": "check_user_by_email",
            "arguments": {
                "email": "test@example.com"
            }
        }
    }
    
    print("\nTesting email webhook endpoint...")
    print(f"URL: {WEBHOOK_URL}")
    print(f"Payload: {json.dumps(test_payload_email, indent=2)}")
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=test_payload_email,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Email lookup webhook is working!")
        else:
            print("❌ Email lookup webhook returned an error")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure your FastAPI server is running.")
    except Exception as e:
        print(f"❌ Error testing email lookup: {e}")

def test_setup_endpoint():
    """Test the Retell AI setup endpoint"""
    
    print("\nTesting Retell AI setup endpoint...")
    print(f"URL: {SETUP_URL}")
    
    try:
        response = requests.post(
            SETUP_URL,
            params={"phone_number": "+1234567890"},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Setup endpoint is accessible!")
        else:
            print("❌ Setup endpoint returned an error")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure your FastAPI server is running.")
    except Exception as e:
        print(f"❌ Error testing setup: {e}")

def test_health_check():
    """Test the general health endpoint"""
    
    health_url = f"{BASE_URL}/health"
    
    print(f"\nTesting health endpoint...")
    print(f"URL: {health_url}")
    
    try:
        response = requests.get(health_url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Server is running!")
        else:
            print("❌ Health check failed")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure your FastAPI server is running.")
    except Exception as e:
        print(f"❌ Error testing health: {e}")

if __name__ == "__main__":
    print("🔧 Testing HelpPet Phone Integration")
    print("=" * 50)
    
    # Test health first
    test_health_check()
    
    # Test phone webhook
    test_phone_webhook()
    
    # Test email webhook
    test_email_webhook()
    
    # Test setup endpoint (this will fail without RETELL_API_KEY, but should be accessible)
    test_setup_endpoint()
    
    print("\n" + "=" * 50)
    print("📋 Next Steps:")
    print("1. Set RETELL_API_KEY environment variable")
    print("2. Run: curl -X POST 'http://localhost:8000/api/v1/webhook/setup-retell?phone_number=%2B1234567890'")
    print("3. Your phone webhook will be available at: http://localhost:8000/api/v1/webhook/phone")
    print("4. Update webhook_url in phone_call_service.py to match your production domain")
    print("\n🔍 User Verification Features:")
    print("- Primary lookup by phone number")
    print("- Fallback lookup by email address")
    print("- Duplicate prevention during account creation")
    print("- Reliable identification using phone/email instead of name matching")
