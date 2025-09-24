# DEPRECATED ENDPOINTS - Return 418 "I'm a teapot" 
# These endpoints have been deprecated due to timezone boundary issues
# Use the Unix timestamp endpoints below instead

# OLD (DEPRECATED): curl -X GET "https://api.helppet.ai/api/v1/scheduling/vet-availability/..."
# NEW (CURRENT): Use Unix timestamp endpoints below

# GET Vet Availability (Unix Timestamp Version)
curl -X GET "https://api.helppet.ai/api/v1/scheduling-unix/vet-availability/e1e3991b-4efa-464b-9bae-f94c74d0a20f?date=2025-09-13&timezone=America/Los_Angeles" \
  -H "Content-Type: application/json"

# Response: Unix timestamp format with proper timezone handling
# [{"id":"...", "vet_user_id":"...", "practice_id":"...", "start_at":"2025-09-13T16:00:00Z", "end_at":"2025-09-14T00:00:00Z", "availability_type":"AVAILABLE", ...}]

# POST Vet Availability (Unix Timestamp Version) 
curl -X POST "https://api.helppet.ai/api/v1/scheduling-unix/vet-availability" \
  -H "Content-Type: application/json" \
  -d '{
    "vet_user_id": "e1e3991b-4efa-464b-9bae-f94c74d0a20f",
    "practice_id": "934c57e7-4f9c-4d28-aa0f-3cb881e3c225",
    "start_at": "2025-09-13T16:00:00Z",
    "end_at": "2025-09-14T00:00:00Z",
    "availability_type": "AVAILABLE"
  }'
