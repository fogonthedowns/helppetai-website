# Call Analysis API Documentation

## Overview

The Call Analysis API provides endpoints to retrieve and analyze voice call data for veterinary practices. This system handles high-volume call analysis (150+ calls per day) with proper pagination and detailed AI-generated insights.

## Authentication

All endpoints require JWT authentication via the `Authorization: Bearer <token>` header.

## Base URL

```
https://api.helppet.ai/api/v1/call-analysis
```

---

## Endpoints

### 1. Get Practice Calls (List)

**GET** `/practice/{practice_id}/calls`

Retrieves a paginated list of call analysis data for a veterinary practice.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `practice_id` | UUID | Yes | The veterinary practice ID |
| `limit` | int | No | Number of calls to retrieve (1-50, default: 10) |
| `offset` | int | No | Number of calls to skip for pagination (default: 0) |

#### Response Schema

```typescript
interface CallListResponse {
  practice_id: string;
  calls: CallSummary[];
  pagination: PaginationInfo;
}

interface CallSummary {
  call_id?: string;
  recording_url?: string;
  start_timestamp?: string; // ISO 8601 format
  end_timestamp?: string;   // ISO 8601 format
  call_analysis?: CallAnalysisData;
}

interface CallAnalysisData {
  call_successful?: boolean;
  call_summary?: string;
  user_sentiment?: string; // "positive", "negative", "neutral", "concerned", "urgent"
  in_voicemail?: boolean;
  custom_analysis_data?: {
    appointment_type?: string;
    urgency_level?: string;
    follow_up_needed?: boolean;
    pet_mentioned?: string;
    symptoms_mentioned?: string[];
    appointment_scheduled?: boolean;
    appointment_date?: string;
    [key: string]: any;
  };
}

interface PaginationInfo {
  limit: number;
  offset: number;
  count: number;
  has_more?: boolean;
  total_count?: number;
}
```

#### Example Response

```json
{
  "practice_id": "550e8400-e29b-41d4-a716-446655440000",
  "calls": [
    {
      "call_id": "call_1a2b3c4d5e6f7g8h9i0j",
      "recording_url": "https://recordings.retellai.com/call_1a2b3c4d5e6f7g8h9i0j.mp3",
      "start_timestamp": "2025-09-20T14:30:15.123Z",
      "end_timestamp": "2025-09-20T14:35:42.456Z",
      "call_analysis": {
        "call_successful": true,
        "call_summary": "Customer called to schedule a checkup for their Golden Retriever, Max.",
        "user_sentiment": "concerned",
        "in_voicemail": false,
        "custom_analysis_data": {
          "appointment_type": "checkup",
          "urgency_level": "medium",
          "pet_mentioned": "Golden Retriever named Max",
          "symptoms_mentioned": ["limping"],
          "appointment_scheduled": true
        }
      }
    },
    {
      "call_id": "call_2b3c4d5e6f7g8h9i0j1k",
      "recording_url": "https://recordings.retellai.com/call_2b3c4d5e6f7g8h9i0j1k.mp3",
      "start_timestamp": "2025-09-20T13:15:30.789Z",
      "end_timestamp": "2025-09-20T13:18:45.012Z",
      "call_analysis": {
        "call_successful": false,
        "call_summary": "Customer called about emergency - cat ingested something toxic. Directed to emergency clinic.",
        "user_sentiment": "urgent",
        "in_voicemail": false,
        "custom_analysis_data": {
          "appointment_type": "emergency",
          "urgency_level": "high",
          "emergency_referral": true
        }
      }
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "count": 2,
    "has_more": true,
    "total_count": 847
  }
}
```

---

### 2. Get Call Detail

**GET** `/practice/{practice_id}/calls/{call_id}`

Retrieves detailed information for a specific call.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `practice_id` | UUID | Yes | The veterinary practice ID |
| `call_id` | string | Yes | The specific call ID |

#### Response Schema

```typescript
interface CallDetailResponse {
  practice_id: string;
  call: CallDetail;
}

interface CallDetail extends CallSummary {
  duration_ms?: number;
  agent_id?: string;
  from_number?: string; // Caller's phone number
  to_number?: string;   // Practice's phone number
  call_status?: string; // "completed", "busy", "no-answer", "failed"
  disconnect_reason?: string; // "user_hangup", "agent_hangup", "error", "timeout"
}
```

#### Example Response

```json
{
  "practice_id": "550e8400-e29b-41d4-a716-446655440000",
  "call": {
    "call_id": "call_1a2b3c4d5e6f7g8h9i0j",
    "recording_url": "https://recordings.retellai.com/call_1a2b3c4d5e6f7g8h9i0j.mp3",
    "start_timestamp": "2025-09-20T14:30:15.123Z",
    "end_timestamp": "2025-09-20T14:35:42.456Z",
    "duration_ms": 327000,
    "agent_id": "agent_11583fd62e3ba8128cb73fcb0e",
    "from_number": "+15551234567",
    "to_number": "+15559876543",
    "call_status": "completed",
    "disconnect_reason": "user_hangup",
    "call_analysis": {
      "call_successful": true,
      "call_summary": "Customer called to schedule a checkup for their Golden Retriever, Max. Appointment scheduled for next Tuesday at 2 PM. Customer mentioned Max has been limping slightly.",
      "user_sentiment": "concerned",
      "in_voicemail": false,
      "custom_analysis_data": {
        "appointment_type": "checkup",
        "urgency_level": "medium",
        "follow_up_needed": true,
        "pet_mentioned": "Golden Retriever named Max",
        "symptoms_mentioned": ["limping"],
        "appointment_scheduled": true,
        "appointment_date": "2025-09-27T14:00:00Z",
        "customer_phone": "+15551234567",
        "callback_requested": false
      }
    }
  }
}
```

---

## Error Responses

### Standard Error Format

```typescript
interface ErrorResponse {
  detail: string;
  error_code?: string;
}
```

### Validation Error Format (422)

```typescript
interface ValidationErrorResponse {
  detail: string;
  errors: Array<{
    field: string;
    message: string;
    type: string;
    input?: any;
  }>;
}
```

### Common HTTP Status Codes

| Code | Description | Example |
|------|-------------|---------|
| 200 | Success | Request completed successfully |
| 401 | Unauthorized | Invalid or missing JWT token |
| 404 | Not Found | Practice or call not found |
| 422 | Validation Error | Invalid parameters (limit > 50, etc.) |
| 500 | Internal Server Error | Unexpected server error |

---

## iOS Implementation Guide

### Pagination Implementation

```swift
class CallAnalysisService {
    private var currentOffset = 0
    private let pageSize = 20
    private var hasMore = true
    
    func loadCalls(practiceId: String, refresh: Bool = false) async throws -> [CallSummary] {
        if refresh {
            currentOffset = 0
            hasMore = true
        }
        
        guard hasMore else { return [] }
        
        let response = try await apiClient.getCalls(
            practiceId: practiceId,
            limit: pageSize,
            offset: currentOffset
        )
        
        currentOffset += response.pagination.count
        hasMore = response.pagination.has_more ?? false
        
        return response.calls
    }
}
```

### Audio Playback

```swift
import AVFoundation

class CallRecordingPlayer: ObservableObject {
    private var player: AVPlayer?
    
    func playRecording(url: String) {
        guard let recordingURL = URL(string: url) else { return }
        
        player = AVPlayer(url: recordingURL)
        player?.play()
    }
    
    func stopRecording() {
        player?.pause()
        player = nil
    }
}
```

### Call Analysis Display

```swift
struct CallAnalysisView: View {
    let analysis: CallAnalysisData
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Success indicator
            HStack {
                Image(systemName: analysis.call_successful == true ? "checkmark.circle.fill" : "xmark.circle.fill")
                    .foregroundColor(analysis.call_successful == true ? .green : .red)
                Text(analysis.call_successful == true ? "Successful" : "Unsuccessful")
            }
            
            // Sentiment
            if let sentiment = analysis.user_sentiment {
                HStack {
                    Text("Sentiment:")
                        .fontWeight(.semibold)
                    Text(sentiment.capitalized)
                        .foregroundColor(sentimentColor(sentiment))
                }
            }
            
            // Summary
            if let summary = analysis.call_summary {
                Text("Summary:")
                    .fontWeight(.semibold)
                Text(summary)
                    .font(.body)
            }
            
            // Custom data
            if let appointmentType = analysis.custom_analysis_data?["appointment_type"] as? String {
                HStack {
                    Text("Type:")
                        .fontWeight(.semibold)
                    Text(appointmentType.capitalized)
                }
            }
        }
    }
    
    private func sentimentColor(_ sentiment: String) -> Color {
        switch sentiment.lowercased() {
        case "positive": return .green
        case "negative": return .red
        case "urgent": return .orange
        case "concerned": return .yellow
        default: return .gray
        }
    }
}
```

---

## Rate Limits

- **Call List Endpoint**: Max 50 calls per request
- **API Rate Limit**: 100 requests per minute per practice
- **Recording URLs**: Valid for 24 hours after generation

---

## Data Freshness

- Call analysis data is updated in real-time
- New calls appear within 2-3 minutes of completion
- Recording URLs are generated asynchronously and may take up to 5 minutes to become available

---

## Support

For API support or questions, contact the backend team or refer to the interactive API documentation at `https://api.helppet.ai/docs`.
