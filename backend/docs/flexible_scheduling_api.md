# Flexible Scheduling API

This document describes the powerful `get_first_available_flexible` function that can handle complex scheduling requests with precise date ranges and day preferences.

## Overview

The `get_first_available_flexible` function is the most versatile scheduling function that supports:

- **Week-based scheduling**: "First available in 3 weeks", "First available in 4 weeks"
- **Specific week of month**: "First available in week 3 of next month"
- **Custom date ranges**: "First available between March 15 and March 30"
- **Complex day preferences**: "First available in 4 weeks on Wednesdays or Fridays"
- **Month targeting**: "First available in next month", "First available in 2 months"

## Function Details

### get_first_available_flexible

**Phone Webhook Function Name**: `get_first_available_flexible`

**Parameters**:
- `time_preference` (string): Time preference ('morning', 'afternoon', 'evening', 'any time')
- `practice_id` (string): UUID of the practice
- `timezone` (string, optional): Practice timezone (default: "America/Los_Angeles")
- `weeks_from_now` (integer, optional): Number of weeks from now (e.g., 3 for "in 3 weeks")
- `specific_week_of_month` (integer, optional): Specific week of target month (1-4)
- `target_month_offset` (integer, optional): Month offset (0=this month, 1=next month, 2=month after next)
- `preferred_days` (array or string, optional): Preferred day names
- `date_range_start` (string, optional): Start date for custom range
- `date_range_end` (string, optional): End date for custom range

## Usage Examples

### 1. Week-Based Scheduling

#### "First available in 3 weeks"
```json
{
  "name": "get_first_available_flexible",
  "args": {
    "time_preference": "morning",
    "practice_id": "123e4567-e89b-12d3-a456-426614174000",
    "weeks_from_now": 3
  }
}
```

**Response**:
```json
{
  "success": true,
  "appointments": [
    {
      "date": "2025-10-13",
      "day_name": "Monday",
      "formatted_date": "Monday, October 13",
      "time": "9:00 AM",
      "is_preferred_day": true
    }
  ],
  "message": "Great news! I found appointments on your preferred days in 3 weeks: 9:00 AM on Monday, October 13",
  "range_description": "in 3 weeks",
  "preferred_days_used": true
}
```

#### "First available in 4 weeks on Wednesdays or Fridays"
```json
{
  "name": "get_first_available_flexible",
  "args": {
    "time_preference": "afternoon",
    "practice_id": "123e4567-e89b-12d3-a456-426614174000",
    "weeks_from_now": 4,
    "preferred_days": ["wednesday", "friday"]
  }
}
```

### 2. Specific Week of Month

#### "First available in week 3 of next month"
```json
{
  "name": "get_first_available_flexible",
  "args": {
    "time_preference": "any time",
    "practice_id": "123e4567-e89b-12d3-a456-426614174000",
    "specific_week_of_month": 3,
    "target_month_offset": 1
  }
}
```

**Response**:
```json
{
  "success": true,
  "appointments": [
    {
      "date": "2025-10-14",
      "day_name": "Tuesday",
      "formatted_date": "Tuesday, October 14",
      "time": "2:30 PM",
      "is_preferred_day": true
    },
    {
      "date": "2025-10-15",
      "day_name": "Wednesday", 
      "formatted_date": "Wednesday, October 15",
      "time": "10:00 AM",
      "is_preferred_day": true
    }
  ],
  "message": "Great news! I found appointments on your preferred days in week 3 of next October: 2:30 PM on Tuesday, October 14, 10:00 AM on Wednesday, October 15",
  "range_description": "in week 3 of next October",
  "preferred_days_used": true
}
```

#### "First available in week 2 of this month"
```json
{
  "name": "get_first_available_flexible",
  "args": {
    "time_preference": "morning",
    "practice_id": "123e4567-e89b-12d3-a456-426614174000",
    "specific_week_of_month": 2,
    "target_month_offset": 0
  }
}
```

### 3. Month-Based Scheduling

#### "First available next month"
```json
{
  "name": "get_first_available_flexible",
  "args": {
    "time_preference": "afternoon",
    "practice_id": "123e4567-e89b-12d3-a456-426614174000",
    "target_month_offset": 1
  }
}
```

#### "First available in 2 months"
```json
{
  "name": "get_first_available_flexible",
  "args": {
    "time_preference": "evening",
    "practice_id": "123e4567-e89b-12d3-a456-426614174000",
    "target_month_offset": 2,
    "preferred_days": "monday,tuesday,wednesday"
  }
}
```

### 4. Custom Date Ranges

#### "First available between March 15 and March 30"
```json
{
  "name": "get_first_available_flexible",
  "args": {
    "time_preference": "any time",
    "practice_id": "123e4567-e89b-12d3-a456-426614174000",
    "date_range_start": "March 15",
    "date_range_end": "March 30",
    "preferred_days": ["thursday", "friday"]
  }
}
```

**Response**:
```json
{
  "success": true,
  "appointments": [
    {
      "date": "2025-03-20",
      "day_name": "Thursday",
      "formatted_date": "Thursday, March 20",
      "time": "11:30 AM",
      "is_preferred_day": true
    },
    {
      "date": "2025-03-21",
      "day_name": "Friday",
      "formatted_date": "Friday, March 21", 
      "time": "3:15 PM",
      "is_preferred_day": true
    }
  ],
  "message": "Great news! I found appointments on your preferred days between March 15 and March 30: 11:30 AM on Thursday, March 20, 3:15 PM on Friday, March 21",
  "range_description": "between March 15 and March 30",
  "preferred_days_used": true
}
```

## Complex Real-World Examples

### Example 1: "I need an appointment in 5 weeks, preferably on a Tuesday or Wednesday morning"

```json
{
  "name": "get_first_available_flexible",
  "args": {
    "time_preference": "morning",
    "practice_id": "123e4567-e89b-12d3-a456-426614174000",
    "weeks_from_now": 5,
    "preferred_days": ["tuesday", "wednesday"],
    "timezone": "America/New_York"
  }
}
```

### Example 2: "What's available in the second week of December?"

```json
{
  "name": "get_first_available_flexible",
  "args": {
    "time_preference": "any time",
    "practice_id": "123e4567-e89b-12d3-a456-426614174000",
    "specific_week_of_month": 2,
    "target_month_offset": 3,
    "timezone": "America/Los_Angeles"
  }
}
```

### Example 3: "I can only do Fridays, what's the first Friday available in the next 6 weeks?"

```json
{
  "name": "get_first_available_flexible",
  "args": {
    "time_preference": "afternoon",
    "practice_id": "123e4567-e89b-12d3-a456-426614174000",
    "date_range_start": "tomorrow",
    "date_range_end": "6 weeks from now",
    "preferred_days": ["friday"]
  }
}
```

## Parameter Priority Logic

The function processes parameters in this priority order:

1. **Custom Date Range** (`date_range_start` + `date_range_end`) - Takes highest priority
2. **Week Offset** (`weeks_from_now`) - Looks at a specific week N weeks from now
3. **Specific Week of Month** (`specific_week_of_month` + `target_month_offset`) - Targets a specific week within a month
4. **Month Offset** (`target_month_offset` only) - Searches entire target month
5. **Default** - Next 7 days if no other parameters specified

## Advanced Features

### Smart Day Preference Logic

- **Preferred Days First**: Always checks preferred days first within the calculated date range
- **Fallback to Any Day**: If no preferred days have availability, checks all days in range
- **Multiple Formats**: Supports both array format `["tuesday", "wednesday"]` and string format `"tuesday,wednesday"`
- **Case Insensitive**: Day names are case insensitive

### Intelligent Date Parsing

The `date_range_start` and `date_range_end` parameters support:
- **Natural Language**: "tomorrow", "next Friday", "March 15"
- **ISO Formats**: "2025-03-15", "2025/03/15"
- **Numeric Formats**: "3-15", "3/15"
- **Relative Dates**: "2 weeks from now", "next month"

### Performance Optimizations

- **Smart Date Limiting**: Automatically limits search ranges to prevent performance issues
- **Max Days Check**: Limits to checking 21 days maximum for very wide ranges
- **Early Exit**: Stops searching once 3 appointments are found
- **Efficient Querying**: Uses optimized database queries with proper indexing

### Timezone Handling

- **Full Timezone Support**: Converts between UTC and local practice timezone
- **DST Awareness**: Handles daylight saving time transitions correctly
- **Global Support**: Works with any standard timezone identifier

## Response Format

All responses include:

```json
{
  "success": true/false,
  "appointments": [...],
  "message": "Human-readable message",
  "time_preference": "cleaned preference",
  "preferred_days_used": true/false,
  "date_range_start": "2025-10-13",
  "date_range_end": "2025-10-19", 
  "range_description": "in 3 weeks",
  "timezone_used": "America/Los_Angeles",
  "version": "first_available_flexible_v1"
}
```

## Error Handling

Common error scenarios and responses:

### No Appointments Available
```json
{
  "success": false,
  "message": "I'm sorry, we don't have any morning appointments available in 3 weeks. Would you like me to check a different time period?"
}
```

### Invalid Parameters
```json
{
  "success": false,
  "message": "I'm having trouble with the timezone configuration. Let me get a human to help you."
}
```

### System Errors
```json
{
  "success": false,
  "message": "I'm having trouble checking our calendar. Let me try again or get a human to help you."
}
```

## Integration Notes

### Voice Assistant Integration

This function is designed to work seamlessly with voice assistants and phone systems. The natural language responses are optimized for spoken delivery.

### Backward Compatibility

The function works alongside the existing simpler functions (`get_first_available_next_3_days`, etc.) without conflicts.

### Database Performance

- Uses the same efficient slot-based system as other scheduling functions
- Leverages existing indexes and caching
- Includes comprehensive logging for debugging and monitoring

This flexible scheduling system gives users unprecedented control over when they want to schedule appointments while maintaining excellent performance and user experience.
