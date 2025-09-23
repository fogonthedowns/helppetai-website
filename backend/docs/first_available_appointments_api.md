# First Available Appointments API

This document describes the three new scheduling functions that find first available appointments across different time ranges.

## Overview

The scheduling service now supports three new functions for finding first available appointments:

1. **`get_first_available_next_3_days`** - Returns first available appointment for each of the next 3 days
2. **`get_first_available_next_week`** - Returns first available appointments for next week, prioritizing preferred days
3. **`get_first_available_next_month`** - Returns first available appointments for next month, prioritizing preferred days

## Function Details

### 1. get_first_available_next_3_days

**Purpose**: Returns the first available appointment for each of the next 3 days. If there are multiple slots available on a day, returns only the first one.

**Phone Webhook Function Name**: `get_first_available_next_3_days`

**Parameters**:
- `time_preference` (string): Time preference ('morning', 'afternoon', 'evening', 'any time')
- `practice_id` (string): UUID of the practice
- `timezone` (string, optional): Practice timezone (default: "America/Los_Angeles")

**Example Request**:
```json
{
  "name": "get_first_available_next_3_days",
  "args": {
    "time_preference": "morning",
    "practice_id": "123e4567-e89b-12d3-a456-426614174000",
    "timezone": "America/Los_Angeles"
  }
}
```

**Example Response**:
```json
{
  "success": true,
  "appointments": [
    {
      "date": "2025-09-23",
      "day_name": "Tuesday",
      "formatted_date": "Tuesday, September 23",
      "time": "9:00 AM",
      "slot_data": { ... }
    },
    {
      "date": "2025-09-24",
      "day_name": "Wednesday", 
      "formatted_date": "Wednesday, September 24",
      "time": "10:30 AM",
      "slot_data": { ... }
    }
  ],
  "message": "I found the first available appointments in the next 3 days: 9:00 AM on Tuesday, September 23, 10:30 AM on Wednesday, September 24",
  "time_preference": "morning",
  "timezone_used": "America/Los_Angeles",
  "version": "first_available_next_3_days_v1"
}
```

### 2. get_first_available_next_week

**Purpose**: Returns first available appointments for next week, prioritizing preferred days (defaults to Tuesdays and Wednesdays).

**Phone Webhook Function Name**: `get_first_available_next_week`

**Parameters**:
- `time_preference` (string): Time preference ('morning', 'afternoon', 'evening', 'any time')
- `practice_id` (string): UUID of the practice
- `timezone` (string, optional): Practice timezone (default: "America/Los_Angeles")
- `preferred_days` (array or string, optional): Preferred days (['tuesday', 'wednesday'] or "tuesday,wednesday")

**Example Request**:
```json
{
  "name": "get_first_available_next_week",
  "args": {
    "time_preference": "afternoon",
    "practice_id": "123e4567-e89b-12d3-a456-426614174000",
    "timezone": "America/Los_Angeles",
    "preferred_days": ["tuesday", "wednesday"]
  }
}
```

**Example Response (with preferred days available)**:
```json
{
  "success": true,
  "appointments": [
    {
      "date": "2025-09-30",
      "day_name": "Tuesday",
      "formatted_date": "Tuesday, September 30",
      "time": "2:00 PM",
      "slot_data": { ... },
      "is_preferred_day": true
    },
    {
      "date": "2025-10-01",
      "day_name": "Wednesday",
      "formatted_date": "Wednesday, October 1",
      "time": "3:30 PM", 
      "slot_data": { ... },
      "is_preferred_day": true
    }
  ],
  "message": "Great news! I found appointments on your preferred days next week: 2:00 PM on Tuesday, September 30, 3:30 PM on Wednesday, October 1",
  "time_preference": "afternoon",
  "preferred_days_used": true,
  "timezone_used": "America/Los_Angeles",
  "version": "first_available_next_week_v1"
}
```

### 3. get_first_available_next_month

**Purpose**: Returns first available appointments for next month, prioritizing preferred days (defaults to Tuesdays and Wednesdays).

**Phone Webhook Function Name**: `get_first_available_next_month`

**Parameters**:
- `time_preference` (string): Time preference ('morning', 'afternoon', 'evening', 'any time')
- `practice_id` (string): UUID of the practice
- `timezone` (string, optional): Practice timezone (default: "America/Los_Angeles")
- `preferred_days` (array or string, optional): Preferred days (['tuesday', 'wednesday'] or "tuesday,wednesday")

**Example Request**:
```json
{
  "name": "get_first_available_next_month",
  "args": {
    "time_preference": "any time",
    "practice_id": "123e4567-e89b-12d3-a456-426614174000",
    "timezone": "America/New_York",
    "preferred_days": "tuesday,wednesday,thursday"
  }
}
```

**Example Response**:
```json
{
  "success": true,
  "appointments": [
    {
      "date": "2025-10-07",
      "day_name": "Tuesday",
      "formatted_date": "Tuesday, October 7",
      "time": "11:00 AM",
      "slot_data": { ... },
      "is_preferred_day": true
    },
    {
      "date": "2025-10-08",
      "day_name": "Wednesday",
      "formatted_date": "Wednesday, October 8", 
      "time": "2:15 PM",
      "slot_data": { ... },
      "is_preferred_day": true
    }
  ],
  "message": "Great news! I found appointments on your preferred days in October: 11:00 AM on Tuesday, October 7, 2:15 PM on Wednesday, October 8",
  "time_preference": "any time",
  "preferred_days_used": true,
  "timezone_used": "America/New_York",
  "version": "first_available_next_month_v1"
}
```

## Key Features

### Smart Day Preference Logic

- **Preferred Days**: Both next week and next month functions prioritize specified preferred days
- **Fallback**: If no preferred days have availability, the functions check all days
- **Default Preferred Days**: If no preferred days are specified, defaults to ['tuesday', 'wednesday']
- **Flexible Input**: Preferred days can be passed as an array `["tuesday", "wednesday"]` or comma-separated string `"tuesday,wednesday"`

### Time Preference Support

All functions support the same time preference filtering as the original `get_available_times`:
- `"morning"` - 6 AM to 12 PM
- `"afternoon"` - 12 PM to 5 PM  
- `"evening"` - 5 PM to 9 PM
- `"any time"` - All available slots

### Timezone Handling

- Full timezone support with proper conversion from UTC to local time
- Defaults to "America/Los_Angeles" if not specified
- Supports all standard timezone names (e.g., "America/New_York", "Europe/London")

### Response Limits

- **Next 3 Days**: Returns up to 3 appointments (1 per day)
- **Next Week**: Returns all preferred day appointments, or up to 3 if using fallback
- **Next Month**: Returns up to 3 preferred day appointments, or up to 3 from first 2 weeks if using fallback

## Error Handling

All functions return consistent error responses:

```json
{
  "success": false,
  "message": "User-friendly error message for phone caller"
}
```

Common error scenarios:
- Invalid practice_id
- No available vets
- Invalid timezone
- No appointments available in the requested time range

## Integration Notes

### Webhook Handler

The functions are integrated into the phone webhook handler (`webhook_handler.py`) and support both old and new Retell AI webhook formats.

### Database Integration

- Uses the existing `VetAvailabilityRepository` for slot lookups
- Leverages the same timezone conversion logic as `get_available_times`
- Filters out unavailable slots and handles appointment conflicts

### Logging

Comprehensive logging is included for debugging:
- Function entry/exit with parameters
- Date range calculations
- Slot filtering results
- Error conditions with full stack traces
