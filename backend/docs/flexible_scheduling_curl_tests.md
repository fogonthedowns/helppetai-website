# Flexible Scheduling API - cURL Test Commands

This document provides comprehensive cURL commands to test all the flexible scheduling functionality.

## Prerequisites

- Replace `YOUR_API_ENDPOINT` with your actual webhook endpoint
- Replace `PRACTICE_UUID` with a valid practice UUID from your database
- Ensure your backend server is running

## Basic Setup

```bash
# Set environment variables for easier testing
export API_ENDPOINT="http://localhost:8000/webhook/phone"  # Replace with your endpoint
export PRACTICE_ID="123e4567-e89b-12d3-a456-426614174000"  # Replace with valid practice UUID
```

## 1. Week-Based Scheduling Tests

### Test 1: "First available in 3 weeks"
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "morning",
      "practice_id": "'${PRACTICE_ID}'",
      "weeks_from_now": 3,
      "timezone": "America/Los_Angeles"
    }
  }'
```

### Test 2: "First available in 4 weeks on Wednesdays or Fridays"
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible", 
    "args": {
      "time_preference": "afternoon",
      "practice_id": "'${PRACTICE_ID}'",
      "weeks_from_now": 4,
      "preferred_days": ["wednesday", "friday"],
      "timezone": "America/Los_Angeles"
    }
  }'
```

### Test 3: "First available in 2 weeks, any time"
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "any time", 
      "practice_id": "'${PRACTICE_ID}'",
      "weeks_from_now": 2,
      "timezone": "America/New_York"
    }
  }'
```

## 2. Specific Week of Month Tests

### Test 4: "First available in week 3 of next month"
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "morning",
      "practice_id": "'${PRACTICE_ID}'",
      "specific_week_of_month": 3,
      "target_month_offset": 1,
      "timezone": "America/Los_Angeles"
    }
  }'
```

### Test 5: "First available in week 2 of this month on Tuesdays"
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "afternoon",
      "practice_id": "'${PRACTICE_ID}'",
      "specific_week_of_month": 2,
      "target_month_offset": 0,
      "preferred_days": ["tuesday"],
      "timezone": "America/Los_Angeles"
    }
  }'
```

### Test 6: "First available in week 4 of December"
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "evening",
      "practice_id": "'${PRACTICE_ID}'",
      "specific_week_of_month": 4,
      "target_month_offset": 3,
      "preferred_days": "monday,wednesday,friday",
      "timezone": "America/Los_Angeles"
    }
  }'
```

## 3. Month-Based Scheduling Tests

### Test 7: "First available next month"
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "morning",
      "practice_id": "'${PRACTICE_ID}'",
      "target_month_offset": 1,
      "timezone": "America/Los_Angeles"
    }
  }'
```

### Test 8: "First available in 2 months on preferred days"
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "afternoon",
      "practice_id": "'${PRACTICE_ID}'",
      "target_month_offset": 2,
      "preferred_days": ["tuesday", "wednesday", "thursday"],
      "timezone": "America/Los_Angeles"
    }
  }'
```

## 4. Custom Date Range Tests

### Test 9: "First available between specific dates"
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "any time",
      "practice_id": "'${PRACTICE_ID}'",
      "date_range_start": "2025-03-15",
      "date_range_end": "2025-03-30",
      "preferred_days": ["thursday", "friday"],
      "timezone": "America/Los_Angeles"
    }
  }'
```

### Test 10: "First available in natural date range"
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "morning",
      "practice_id": "'${PRACTICE_ID}'",
      "date_range_start": "next Monday",
      "date_range_end": "3 weeks from now",
      "preferred_days": "wednesday,friday",
      "timezone": "America/Los_Angeles"
    }
  }'
```

## 5. Complex Real-World Scenarios

### Test 11: "I need an appointment in 5 weeks, preferably Tuesday or Wednesday morning"
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "morning",
      "practice_id": "'${PRACTICE_ID}'",
      "weeks_from_now": 5,
      "preferred_days": ["tuesday", "wednesday"],
      "timezone": "America/New_York"
    }
  }'
```

### Test 12: "What's available in the second week of December, any day?"
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "any time",
      "practice_id": "'${PRACTICE_ID}'",
      "specific_week_of_month": 2,
      "target_month_offset": 3,
      "timezone": "America/Los_Angeles"
    }
  }'
```

### Test 13: "I can only do Fridays, what's the first Friday available in the next 6 weeks?"
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "afternoon",
      "practice_id": "'${PRACTICE_ID}'",
      "date_range_start": "tomorrow",
      "date_range_end": "6 weeks from now",
      "preferred_days": ["friday"],
      "timezone": "America/Los_Angeles"
    }
  }'
```

## 6. Edge Case Tests

### Test 14: No preferred days specified (should use defaults)
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "morning",
      "practice_id": "'${PRACTICE_ID}'",
      "weeks_from_now": 3,
      "timezone": "America/Los_Angeles"
    }
  }'
```

### Test 15: Invalid timezone (should return error)
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "morning",
      "practice_id": "'${PRACTICE_ID}'",
      "weeks_from_now": 2,
      "timezone": "Invalid/Timezone"
    }
  }'
```

### Test 16: Missing practice_id (should return error)
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "morning",
      "weeks_from_now": 2,
      "timezone": "America/Los_Angeles"
    }
  }'
```

## 7. Comparison Tests with Original Functions

### Test 17: Original get_available_times (for comparison)
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_available_times",
    "args": {
      "date": "tomorrow",
      "time_preference": "morning",
      "practice_id": "'${PRACTICE_ID}'",
      "timezone": "America/Los_Angeles"
    }
  }'
```

### Test 18: Original get_first_available_next_3_days (for comparison)
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_next_3_days",
    "args": {
      "time_preference": "morning",
      "practice_id": "'${PRACTICE_ID}'",
      "timezone": "America/Los_Angeles"
    }
  }'
```

## 8. Performance Tests

### Test 19: Large date range (should be limited automatically)
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "any time",
      "practice_id": "'${PRACTICE_ID}'",
      "target_month_offset": 1,
      "timezone": "America/Los_Angeles"
    }
  }'
```

### Test 20: Very specific constraints (might return no results)
```bash
curl -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "evening",
      "practice_id": "'${PRACTICE_ID}'",
      "weeks_from_now": 10,
      "preferred_days": ["sunday"],
      "timezone": "America/Los_Angeles"
    }
  }'
```

## Expected Response Format

All successful responses should follow this format:

```json
{
  "response": {
    "success": true,
    "appointments": [
      {
        "date": "2025-10-13",
        "day_name": "Monday", 
        "formatted_date": "Monday, October 13",
        "time": "9:00 AM",
        "slot_data": {...},
        "is_preferred_day": true
      }
    ],
    "message": "Great news! I found appointments on your preferred days in 3 weeks: 9:00 AM on Monday, October 13",
    "time_preference": "morning",
    "preferred_days_used": true,
    "date_range_start": "2025-10-13",
    "date_range_end": "2025-10-19",
    "range_description": "in 3 weeks",
    "timezone_used": "America/Los_Angeles",
    "version": "first_available_flexible_v1"
  }
}
```

## Error Response Format

Error responses should look like:

```json
{
  "response": {
    "success": false,
    "message": "I'm sorry, we don't have any morning appointments available in 3 weeks. Would you like me to check a different time period?"
  }
}
```

## Testing Script

Save this as `test_flexible_scheduling.sh`:

```bash
#!/bin/bash

# Configuration
API_ENDPOINT="http://localhost:8000/webhook/phone"
PRACTICE_ID="123e4567-e89b-12d3-a456-426614174000"

echo "Testing Flexible Scheduling API..."
echo "================================="

# Test 1: Week-based scheduling
echo "Test 1: First available in 3 weeks"
curl -s -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "morning",
      "practice_id": "'${PRACTICE_ID}'",
      "weeks_from_now": 3
    }
  }' | jq .

echo -e "\n---\n"

# Test 2: Specific week of month
echo "Test 2: First available in week 3 of next month"
curl -s -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "afternoon",
      "practice_id": "'${PRACTICE_ID}'",
      "specific_week_of_month": 3,
      "target_month_offset": 1,
      "preferred_days": ["tuesday", "wednesday"]
    }
  }' | jq .

echo -e "\n---\n"

# Test 3: Custom date range
echo "Test 3: Custom date range with preferred days"
curl -s -X POST "${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "get_first_available_flexible",
    "args": {
      "time_preference": "any time",
      "practice_id": "'${PRACTICE_ID}'",
      "date_range_start": "next Monday",
      "date_range_end": "3 weeks from now",
      "preferred_days": ["friday"]
    }
  }' | jq .

echo -e "\nTesting complete!"
```

Make it executable and run:
```bash
chmod +x test_flexible_scheduling.sh
./test_flexible_scheduling.sh
```

## Notes

1. **Replace placeholders**: Update `API_ENDPOINT` and `PRACTICE_ID` with your actual values
2. **Install jq**: For pretty JSON formatting: `brew install jq` (macOS) or `apt-get install jq` (Ubuntu)
3. **Check logs**: Monitor your backend logs for detailed debugging information
4. **Database setup**: Ensure you have test data (vets, availability slots) in your database
5. **Timezone testing**: Try different timezones to verify conversion logic
