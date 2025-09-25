# Voice Agent API Documentation

## Overview

The Voice Agent API provides endpoints for managing Retell voice agents integrated with HelpPetAI. It reads the `voice/HelpPetAI.json` configuration file and creates voice agents on the Retell platform.

## Base URL

```
https://api.helppet.ai/api/v1/voice-agent/register
```

## Authentication

All endpoints require authentication using a Bearer JWT token:

```bash
Authorization: Bearer YOUR_JWT_TOKEN
```

## Endpoints

### 1. Create Voice Agent

**POST** `/`

Creates a new voice agent using the HelpPetAI.json configuration.

**Request Body:**
```json
{
  "practice_id": "934c57e7-4f9c-4d28-aa0f-3cb881e3c225",
  "timezone": "US/Pacific",
  "metadata": {
    "description": "Voice agent for practice",
    "custom_field": "value"
  }
}
```

**Note**: The agent name will automatically be set to `"{Practice Name} - HelpPetAI"` based on the practice information.

**Response (201):**
```json
{
  "id": "2e347f5e-a1be-4d9d-9de7-c5e11da81f23",
  "practice_id": "934c57e7-4f9c-4d28-aa0f-3cb881e3c225",
  "agent_id": "agent_11583fd62e3ba8128cb73fcb0e",
  "timezone": "US/Pacific",
  "metadata": {},
  "is_active": true,
  "created_at": "2025-09-20T04:25:22.314788+00:00",
  "updated_at": "2025-09-20T04:25:22.314788+00:00"
}
```

### 2. Get All Voice Agents

**GET** `/`

Retrieves all voice agents, optionally filtered by practice.

**Query Parameters:**
- `practice_id` (optional): Filter by practice UUID
- `is_active` (optional): Filter by active status (default: true)

**Response (200):**
```json
[
  {
    "id": "2e347f5e-a1be-4d9d-9de7-c5e11da81f23",
    "practice_id": "934c57e7-4f9c-4d28-aa0f-3cb881e3c225",
    "agent_id": "agent_11583fd62e3ba8128cb73fcb0e",
    "timezone": "US/Pacific",
    "metadata": {},
    "is_active": true,
    "created_at": "2025-09-20T04:25:22.314788+00:00",
    "updated_at": "2025-09-20T04:25:22.314788+00:00"
  }
]
```

### 3. Get Voice Agent by ID

**GET** `/{voice_config_id}`

Retrieves a specific voice agent by its UUID.

**Path Parameters:**
- `voice_config_id`: UUID of the voice configuration

**Response (200):**
```json
{
  "id": "2e347f5e-a1be-4d9d-9de7-c5e11da81f23",
  "practice_id": "934c57e7-4f9c-4d28-aa0f-3cb881e3c225",
  "agent_id": "agent_11583fd62e3ba8128cb73fcb0e",
  "timezone": "US/Pacific",
  "metadata": {},
  "is_active": true,
  "created_at": "2025-09-20T04:25:22.314788+00:00",
  "updated_at": "2025-09-20T04:25:22.314788+00:00"
}
```

### 4. Update Voice Agent

**PUT** `/{voice_config_id}`

Updates an existing voice agent.

**Path Parameters:**
- `voice_config_id`: UUID of the voice configuration

**Request Body:**
```json
{
  "timezone": "US/Eastern",
  "metadata": {
    "description": "Updated description"
  },
  "is_active": true
}
```

**Response (200):**
```json
{
  "id": "2e347f5e-a1be-4d9d-9de7-c5e11da81f23",
  "practice_id": "934c57e7-4f9c-4d28-aa0f-3cb881e3c225",
  "agent_id": "agent_11583fd62e3ba8128cb73fcb0e",
  "timezone": "US/Eastern",
  "metadata": {
    "description": "Updated description"
  },
  "is_active": true,
  "created_at": "2025-09-20T04:25:22.314788+00:00",
  "updated_at": "2025-09-20T04:25:22.314788+00:00"
}
```

### 5. Soft Delete Voice Agent

**DELETE** `/{voice_config_id}`

Soft deletes a voice agent by setting `is_active` to `false`. Does not delete the agent from Retell.

**Path Parameters:**
- `voice_config_id`: UUID of the voice configuration

**Response (200):**
```json
{
  "id": "2e347f5e-a1be-4d9d-9de7-c5e11da81f23",
  "practice_id": "934c57e7-4f9c-4d28-aa0f-3cb881e3c225",
  "agent_id": "agent_11583fd62e3ba8128cb73fcb0e",
  "timezone": "US/Pacific",
  "metadata": {},
  "is_active": false,
  "created_at": "2025-09-20T04:25:22.314788+00:00",
  "updated_at": "2025-09-20T04:25:22.314788+00:00"
}
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "Voice agent with ID {id} not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to load HelpPetAI.json configuration"
}
```

## Implementation Details

1. **HelpPetAI.json Loading**: The API reads the configuration from `voice/HelpPetAI.json` and uses it to create agents on Retell.

2. **Practice ID Injection**: The `practice_id` from the request is injected into the conversation flow's global prompt, replacing the hardcoded practice ID.

3. **Timezone Updates**: When updating timezone, the API also updates the Retell agent configuration.

4. **Soft Delete**: The DELETE endpoint only sets `is_active=false` in the database and does not delete the agent from Retell.

5. **No Phone Association**: Phone number association with agents is handled by separate endpoints (to be implemented later).

## Environment Variables

Required environment variables:
- `RETELL_API_KEY`: API key for Retell service

## Testing

Use the provided test scripts:
- `test_voice_agent_api.py`: Python test script
- `test_voice_agent_curl.sh`: Bash curl test script

Make sure to set your JWT token in the test files before running.
