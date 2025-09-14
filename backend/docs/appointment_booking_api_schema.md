# Appointment Booking API Schema

## Overview

The HelpPet appointment booking system now uses a proper repository pattern with timezone-aware scheduling. This document provides the exact schemas needed for external integrations (like Retell AI).

## 🎯 **book_appointment** Function Schema

### Request Schema

```json
{
  "type": "object",
  "properties": {
    "practice_id": {
      "type": "string",
      "description": "Practice UUID - use the practice_id variable exactly as provided"
    },
    "pet_owner_id": {
      "type": "string", 
      "description": "Pet owner UUID from user lookup (can also use 'user_id' for backward compatibility)"
    },
    "date": {
      "type": "string",
      "description": "Local date for the appointment (e.g., '2025-09-15', '9-15', 'September 15', 'tomorrow')"
    },
    "start_time": {
      "type": "string",
      "description": "Local start time selected by user (e.g., '2:30 PM', '14:30', '7:30 PM')"
    },
    "timezone": {
      "type": "string",
      "description": "Practice timezone (e.g., 'America/New_York', 'US/Pacific', 'US/Mountain')",
      "default": "America/Los_Angeles"
    },
    "service": {
      "type": "string", 
      "description": "Type of service/appointment (e.g., 'General Checkup', 'Vaccination')",
      "default": "General Checkup"
    },
    "pet_ids": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of pet UUIDs for this appointment (optional - will use owner's first pet if not provided)"
    },
    "notes": {
      "type": "string",
      "description": "Additional notes or special requests"
    },
    "assigned_vet_user_id": {
      "type": "string",
      "description": "Specific vet UUID if requested (optional - system will assign if not provided)"
    }
  },
  "required": ["practice_id", "pet_owner_id", "date", "start_time"]
}
```

### Response Schema

```json
{
  "success": true,
  "appointment_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Perfect! I've booked your General Checkup appointment for Monday, September 15 at 02:30 PM. Let me confirm all the details.",
  "details": {
    "appointment_id": "550e8400-e29b-41d4-a716-446655440000",
    "date_time": "Monday, September 15 at 02:30 PM",
    "service": "General Checkup",
    "practice_name": "Downtown Veterinary Clinic",
    "timezone": "America/Los_Angeles"
  }
}
```

### Error Response Schema

```json
{
  "success": false,
  "message": "I'm sorry, that time slot is no longer available. Let me check other options.",
  "conflicts": [
    {
      "appointment_id": "123e4567-e89b-12d3-a456-426614174000",
      "time": "2025-09-15 14:30:00+00:00"
    }
  ]
}
```

## 🎯 **get_available_times** Function Schema (from SchedulingService)

### Request Schema

```json
{
  "type": "object", 
  "properties": {
    "date": {
      "type": "string",
      "description": "The date for availability check (e.g., '9-14', 'September 14', 'tomorrow')"
    },
    "practice_id": {
      "type": "string",
      "description": "Practice UUID - use the practice_id variable exactly as provided"
    },
    "time_preference": {
      "type": "string",
      "description": "Time of day preference (e.g., 'morning', 'afternoon', 'evening', 'any time')",
      "default": "any time"
    },
    "timezone": {
      "type": "string", 
      "description": "Practice timezone (e.g., 'America/New_York', 'US/Pacific', 'US/Mountain')",
      "default": "America/Los_Angeles"
    }
  },
  "required": ["date", "practice_id"]
}
```

### Response Schema

```json
{
  "success": true,
  "available_times": ["7:30 PM", "8:15 PM"],
  "message": "I found 2 available times on Monday, September 15: 7:30 PM, 8:15 PM",
  "date": "2025-09-15",
  "time_preference": "any time",
  "timezone_used": "US/Pacific"
}
```

## 🎯 **confirm_appointment** Function Schema

### Request Schema

```json
{
  "type": "object",
  "properties": {
    "appointment_id": {
      "type": "string",
      "description": "Appointment UUID to confirm"
    }
  },
  "required": ["appointment_id"]
}
```

### Response Schema

```json
{
  "success": true,
  "message": "Perfect! Your appointment is confirmed for Monday, September 15 at 02:30 PM. We'll send you a reminder before your visit. Thank you for choosing HelpPet!",
  "appointment_details": {
    "appointment_id": "550e8400-e29b-41d4-a716-446655440000",
    "date_time": "Monday, September 15 at 02:30 PM",
    "status": "confirmed",
    "title": "General Checkup Appointment"
  }
}
```

## 🌍 **Timezone Support**

### Valid Timezone Values

- `America/Los_Angeles` (PST/PDT)
- `America/New_York` (EST/EDT)  
- `America/Chicago` (CST/CDT)
- `America/Denver` (MST/MDT)
- `US/Pacific` (alias for America/Los_Angeles)
- `US/Eastern` (alias for America/New_York)
- `US/Central` (alias for America/Chicago)
- `US/Mountain` (alias for America/Denver)

### Timezone Behavior

1. **Input**: All date/time inputs are treated as LOCAL to the practice timezone
2. **Storage**: Appointments are stored in UTC in the database
3. **Output**: Times are displayed back to users in the practice's local timezone
4. **Conversion**: The system handles DST transitions automatically

## 📝 **Integration Flow**

### Typical Phone Call Flow

1. **User Lookup**: `check_user` or `check_user_by_email`
2. **Get Available Times**: `get_available_times` 
3. **Book Appointment**: `book_appointment`
4. **Confirm Appointment**: `confirm_appointment`

### Example Integration Code

```python
# 1. Check user exists
user_result = await user_service.check_user("555-123-4567")

# 2. Get available times  
availability = await scheduling_service.get_available_times(
    date="2025-09-15",
    time_preference="evening", 
    practice_id="934c57e7-4f9c-4d28-aa0f-3cb881e3c225",
    timezone="America/Los_Angeles"
)

# 3. Book appointment
booking = await appointment_service.book_appointment(
    pet_owner_id=user_result["user"]["id"],
    practice_id="934c57e7-4f9c-4d28-aa0f-3cb881e3c225",
    date="2025-09-15",
    start_time="7:30 PM",
    timezone="America/Los_Angeles",
    service="General Checkup"
)

# 4. Confirm appointment
confirmation = await appointment_service.confirm_appointment(
    appointment_id=booking["appointment_id"]
)
```

## 🔧 **Architecture Notes**

### Repository Pattern
- Uses `AppointmentRepository` for all database operations
- No direct SQLAlchemy queries in service layer
- Proper separation of concerns

### Timezone Handling
- All local times converted to UTC for storage
- Timezone-aware datetime objects throughout
- Proper DST handling via pytz

### Error Handling
- Comprehensive validation of UUIDs
- Graceful fallbacks for parsing errors
- Detailed logging for debugging

### Performance
- Efficient conflict checking
- Optimized database queries with proper indexing
- Minimal database round trips

## 🚀 **Testing**

To test the appointment booking system:

```bash
# Test imports
python3 -c "from src.services.phone.appointment_service import AppointmentService; print('✅ Ready')"

# Test via webhook (requires valid auth token)
curl -X POST "https://api.helppet.ai/api/v1/webhook/phone" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "function_call": {
      "name": "book_appointment",
      "arguments": {
        "pet_owner_id": "USER_UUID",
        "practice_id": "PRACTICE_UUID", 
        "date": "2025-09-15",
        "start_time": "2:30 PM",
        "timezone": "America/Los_Angeles"
      }
    }
  }'
```

## 🐕 **Multi-Pet Support**

### **Problem:** Users with Multiple Pets (Amira and Winston)

When a user has multiple pets, the system needs to know which pet the appointment is for.

### **Solution 1: check_user Response Includes All Pets**

The `check_user` function now returns ALL pets in **Retell AI-compatible format**:

```json
{
  "success": true,
  "user_exists": true,
  "user": {
    "id": "pet_owner_uuid",
    "phone_number": "555-123-4567",
    "owner_name": "John Smith",
    "pet_count": 2,
    
    // Flattened pet fields for Retell AI compatibility
    "pet_1_id": "pet_uuid_1",
    "pet_1_name": "Amira", 
    "pet_1_species": "Dog",
    "pet_2_id": "pet_uuid_2",
    "pet_2_name": "Winston",
    "pet_2_species": "Cat",
    
    // Legacy fields for backward compatibility
    "pet_name": "Amira",
    "pet_type": "Dog",
    
    // Array format for advanced integrations
    "pets": [
      {"id": "pet_uuid_1", "name": "Amira", "species": "Dog"},
      {"id": "pet_uuid_2", "name": "Winston", "species": "Cat"}
    ]
  },
  "message": "Welcome back John Smith! I found you by your phone. I see you have 2 pets in our system: Amira and Winston."
}
```

### **Solution 2: get_user_pets Function**

New function to get pets when needed:

```json
{
  "function_call": {
    "name": "get_user_pets",
    "arguments": {
      "pet_owner_id": "USER_UUID"
    }
  }
}
```

**Response (Retell AI-compatible):**
```json
{
  "success": true,
  "pet_count": 2,
  
  // Flattened pet fields for Retell AI
  "pet_1_id": "pet_uuid_1",
  "pet_1_name": "Amira",
  "pet_1_species": "Dog", 
  "pet_2_id": "pet_uuid_2",
  "pet_2_name": "Winston",
  "pet_2_species": "Cat",
  
  "message": "You have 2 pets: Amira and Winston. Which pet is this appointment for?",
  "owner_name": "John Smith",
  
  // Array format for advanced integrations
  "pets": [
    {"id": "pet_uuid_1", "name": "Amira", "species": "Dog"},
    {"id": "pet_uuid_2", "name": "Winston", "species": "Cat"}
  ]
}
```

### **Solution 3: book_appointment with pet_ids**

When booking, specify which pets:

```json
{
  "function_call": {
    "name": "book_appointment",
    "arguments": {
      "pet_owner_id": "USER_UUID",
      "practice_id": "PRACTICE_UUID",
      "date": "2025-09-15",
      "start_time": "2:30 PM",
      "timezone": "America/Los_Angeles",
      "pet_ids": ["pet_uuid_1"]
    }
  }
}
```

### **Multi-Pet Error Response**

If no `pet_ids` provided and user has multiple pets:

```json
{
  "success": false,
  "message": "I see you have multiple pets: Amira and Winston. Which pet is this appointment for? Please let me know and I'll book the appointment.",
  "pet_count": 2,
  
  // Flattened pet fields for Retell AI
  "pet_1_id": "pet_uuid_1",
  "pet_1_name": "Amira",
  "pet_1_species": "Dog",
  "pet_2_id": "pet_uuid_2", 
  "pet_2_name": "Winston",
  "pet_2_species": "Cat",
  
  "requires_pet_selection": true,
  
  // Array format for advanced integrations
  "pets": [
    {"id": "pet_uuid_1", "name": "Amira", "species": "Dog"},
    {"id": "pet_uuid_2", "name": "Winston", "species": "Cat"}
  ]
}
```

### **Phone App Integration Flow**

```javascript
// 1. Check user
const userResult = await checkUser("555-123-4567");
const pets = userResult.response.user.pets;

// 2. If multiple pets, ask which one
if (pets.length > 1) {
  speak("Which pet is this appointment for?");
  const petName = await getUserInput();
  const selectedPet = pets.find(p => p.name.toLowerCase() === petName.toLowerCase());
  
  // 3. Book with specific pet
  await bookAppointment({
    pet_owner_id: userResult.response.user.id,
    pet_ids: [selectedPet.id],
    // ... other booking details
  });
}
```

## 📋 **Key Response Variables for Multi-Pet**

### **For Retell AI (Recommended):**
- `response.user.pet_count` - Number of pets
- `response.user.pet_1_name` - First pet name
- `response.user.pet_1_id` - First pet UUID
- `response.user.pet_2_name` - Second pet name (if exists)
- `response.user.pet_2_id` - Second pet UUID (if exists)
- `response.requires_pet_selection` - Boolean indicating pet selection needed
- `response.user.id` - This is the `pet_owner_id` for booking!

### **For Advanced Integrations:**
- `response.user.pets[]` - Array of all user's pets
- `response.pets[]` - Pets list from get_user_pets

## 🤖 **Retell AI Compatibility**

### **Problem with Arrays:**
Retell AI's function calling system may have limitations with complex nested objects and arrays. The `user.pets[]` structure might not work reliably.

### **Solution: Flattened Fields**
We provide **both formats**:

1. **Flattened fields** (Retell AI-friendly):
   ```
   pet_count: 2
   pet_1_name: "Amira"
   pet_1_id: "uuid1" 
   pet_2_name: "Winston"
   pet_2_id: "uuid2"
   ```

2. **Array format** (for advanced integrations):
   ```json
   "pets": [
     {"id": "uuid1", "name": "Amira", "species": "Dog"},
     {"id": "uuid2", "name": "Winston", "species": "Cat"}
   ]
   ```

### **Retell AI Variable Extraction:**
```javascript
// Extract flattened pet variables in Retell AI
const petCount = response.user.pet_count;
const pet1Name = response.user.pet_1_name;
const pet1Id = response.user.pet_1_id;
const pet2Name = response.user.pet_2_name;
const pet2Id = response.user.pet_2_id;

// Use in conversation flow
if (petCount > 1) {
  speak(`Which pet is this for: ${pet1Name} or ${pet2Name}?`);
}
```

### **Recommended Approach:**
- **Use flattened fields** (`pet_1_name`, `pet_2_name`) for Retell AI
- **Use array format** (`pets[]`) only for custom integrations
- **Always check `pet_count`** to determine if pet selection is needed
