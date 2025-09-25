#!/usr/bin/env python3
"""
Test script for Voice Agent API endpoints
"""

import requests
import json

# Configuration
BASE_URL = "https://api.helppet.ai"
# BASE_URL = "http://localhost:8000"  # For local testing

# You'll need a valid token for testing
TOKEN = "YOUR_JWT_TOKEN_HERE"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def test_create_voice_agent():
    """Test creating a voice agent"""
    print("🤖 Testing CREATE voice agent...")
    
    data = {
        "practice_id": "934c57e7-4f9c-4d28-aa0f-3cb881e3c225",
        "timezone": "US/Pacific",
        "metadata": {
            "description": "Test voice agent",
            "created_by": "test_script"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/voice-agent/register/",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 201:
        return response.json()["id"]
    return None


def test_get_voice_agents():
    """Test getting all voice agents"""
    print("\n📋 Testing GET all voice agents...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/voice-agent/register/",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")


def test_get_voice_agent(agent_id):
    """Test getting a specific voice agent"""
    print(f"\n🔍 Testing GET voice agent {agent_id}...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/voice-agent/register/{agent_id}",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")


def test_update_voice_agent(agent_id):
    """Test updating a voice agent"""
    print(f"\n✏️ Testing UPDATE voice agent {agent_id}...")
    
    data = {
        "timezone": "US/Eastern",
        "metadata": {
            "description": "Updated test voice agent",
            "updated_by": "test_script"
        }
    }
    
    response = requests.put(
        f"{BASE_URL}/api/v1/voice-agent/register/{agent_id}",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")


def test_delete_voice_agent(agent_id):
    """Test soft deleting a voice agent"""
    print(f"\n🗑️ Testing DELETE voice agent {agent_id}...")
    
    response = requests.delete(
        f"{BASE_URL}/api/v1/voice-agent/register/{agent_id}",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")


if __name__ == "__main__":
    print("🚀 Testing Voice Agent API endpoints...")
    print("="*50)
    
    # Test creating a voice agent
    agent_id = test_create_voice_agent()
    
    # Test getting all voice agents
    test_get_voice_agents()
    
    if agent_id:
        # Test getting specific voice agent
        test_get_voice_agent(agent_id)
        
        # Test updating voice agent
        test_update_voice_agent(agent_id)
        
        # Test deleting voice agent
        test_delete_voice_agent(agent_id)
    
    print("\n✅ Test completed!")
