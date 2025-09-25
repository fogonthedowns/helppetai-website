#!/bin/bash

# Voice Agent API Test Script
# Make sure to set your JWT token

BASE_URL="https://api.helppet.ai"
# BASE_URL="http://localhost:8000"  # For local testing

# Set your JWT token here
TOKEN="YOUR_JWT_TOKEN_HERE"

echo "🚀 Testing Voice Agent API endpoints..."
echo "=================================================="

# Test 1: Create Voice Agent
echo "🤖 Creating voice agent..."
CREATE_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/api/v1/voice-agent/register/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "practice_id": "934c57e7-4f9c-4d28-aa0f-3cb881e3c225",
    "timezone": "US/Pacific",
    "metadata": {
      "description": "Test voice agent from curl",
      "created_by": "curl_script"
    }
  }')

echo "Response: $CREATE_RESPONSE"

# Extract agent ID if creation was successful
AGENT_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id // empty')

echo ""

# Test 2: Get All Voice Agents
echo "📋 Getting all voice agents..."
curl -s -X GET \
  "${BASE_URL}/api/v1/voice-agent/register/" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.'

echo ""

if [ ! -z "$AGENT_ID" ]; then
  # Test 3: Get Specific Voice Agent
  echo "🔍 Getting voice agent $AGENT_ID..."
  curl -s -X GET \
    "${BASE_URL}/api/v1/voice-agent/register/${AGENT_ID}" \
    -H "Authorization: Bearer ${TOKEN}" | jq '.'

  echo ""

  # Test 4: Update Voice Agent
  echo "✏️ Updating voice agent $AGENT_ID..."
  curl -s -X PUT \
    "${BASE_URL}/api/v1/voice-agent/register/${AGENT_ID}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
      "timezone": "US/Eastern",
      "metadata": {
        "description": "Updated test voice agent from curl",
        "updated_by": "curl_script"
      }
    }' | jq '.'

  echo ""

  # Test 5: Soft Delete Voice Agent
  echo "🗑️ Soft deleting voice agent $AGENT_ID..."
  curl -s -X DELETE \
    "${BASE_URL}/api/v1/voice-agent/register/${AGENT_ID}" \
    -H "Authorization: Bearer ${TOKEN}" | jq '.'

  echo ""

else
  echo "❌ Could not extract agent ID from create response. Skipping individual tests."
fi

echo "✅ Test completed!"
