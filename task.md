# Webhook 404 Issue - Current State & Solution Plan

## Problem Summary
Lambda successfully extracts SOAP data but webhook calls fail with 404 "Not Found" due to FastAPI route matching issues with URL-encoded slashes.

## What Lambda Has
- **Extracted Visit UUID**: `8d657acf-8c9c-4bbf-8dee-49bc91ae604e` (from S3 filename)
- **Original S3 Key**: `visit-recordings/2025/09/09/pet-6ba1a0be-f00e-4e13-9637-41b38d9a0711/8d657acf-8c9c-4bbf-8dee-49bc91ae604e.m4a`
- **SOAP Data**: 20 key/value pairs extracted via Anthropic AI
- **Webhook Call**: `PUT https://api.helppet.ai/api/v1/webhook/visit-metadata/visit-recordings%2F2025%2F09%2F09%2Fpet-6ba1a0be-f00e-4e13-9637-41b38d9a0711%2F8d657acf-8c9c-4bbf-8dee-49bc91ae604e.m4a`
- **Authentication**: ✅ Working with token `HelpPetWebhook2024`

## What Database Has
From debug information provided:

```json
{
  "visit_id": "dec1f1bc-c731-4e05-96c1-f25f0426f772",
  "visit_state": "processed",
  "audio_transcript_url": "https://helppetai-visit-recordings.s3.us-west-1.amazonaws.com/visit-recordings/2025/09/09/pet-6ba1a0be-f00e-4e13-9637-41b38d9a0711/8d657acf-8c9c-4bbf-8dee-49bc91ae604e.m4a",
  "additional_data": {
    "s3_key": "visit-recordings/2025/09/09/pet-6ba1a0be-f00e-4e13-9637-41b38d9a0711/8d657acf-8c9c-4bbf-8dee-49bc91ae604e.m4a",
    "s3_bucket": "helppetai-visit-recordings",
    "filename": "recording_20250908_225250.m4a",
    "transcription_job_name": "helppet-transcribe-8d657acf-8c9c-4bbf-8dee-49bc91ae604e-20250909_055344-7d85a87f",
    "transcription_completed_at": "2025-09-09T05:53:57.596917"
  }
}
```

**Key Points**:
- ✅ Visit record exists
- ✅ S3 key matches Lambda extraction
- ✅ Transcription already completed
- ❌ Visit UUID mismatch: DB has `dec1f1bc-c731-4e05-96c1-f25f0426f772`, Lambda extracted `8d657acf-8c9c-4bbf-8dee-49bc91ae604e`

## Root Cause
FastAPI cannot match routes with URL-encoded slashes in path parameters. The webhook route `/webhook/visit-metadata/{visit_id}` fails when `visit_id` contains encoded slashes (`%2F`).

## Solution: Use Custom Header Approach

**Benefits:**
- Minimal changes required
- No new routes needed  
- Cleaner than URL encoding
- Headers handle special characters naturally
- Keeps existing endpoint structure

**Lambda Changes:**
```python
# Add X-S3-Key header instead of URL encoding
headers = {
    'X-Webhook-Token': webhook_token,
    'X-S3-Key': s3_key,  # No encoding needed
    'Content-Type': 'application/json'
}
url = f"{api_base_url}/api/v1/webhook/visit-metadata/s3-lookup"
```

**Backend Changes:**
```python
# Modify existing route to check for X-S3-Key header
def update_visit_metadata(
    visit_id: str,
    payload: SOAPMetadataUpdatePayload,
    x_s3_key: Optional[str] = Header(None),
    ...
):
    if x_s3_key:
        # Use S3 key lookup (existing logic)
        # Find visit by audio_transcript_url matching S3 key
    else:
        # Use UUID lookup (existing logic)
```

## Implementation Steps
1. **Update Lambda**: Change webhook call to use `X-S3-Key` header with simple URL path
2. **Update Backend**: Modify existing webhook route to check for header first
3. **Test**: Verify webhook successfully updates visit `dec1f1bc-c731-4e05-96c1-f25f0426f772`
4. **Deploy**: Redeploy both Lambda and backend

## Current Status
- ✅ Authentication working
- ✅ SOAP extraction working  
- ✅ Visit record exists with matching S3 key
- ❌ FastAPI routing issue prevents webhook completion

**Next Step**: Implement header-based solution