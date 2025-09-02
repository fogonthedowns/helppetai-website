# iOS Swift App Development Guide for HelpPet API

## Overview
This document provides the complete API specification for building a Swift iOS application that interfaces with the HelpPet veterinary practice management system. The app allows veterinarians to manage their daily schedule, start/end visits, view pet information, and access medical records.

## Base Configuration
- **API Base URL**: `https://api.helppet.ai`
- **Authentication**: Bearer token (JWT)
- **Content Type**: `application/json`

## Core User Flow
1. **Login** → Get access token
2. **View Schedule** → See today's appointments
3. **Start Visit** → Update appointment status to "in_progress"
4. **View Pet Details** → Access pet info, medical records, visit history
5. **End Visit** → Update appointment status to "completed"
6. **Record Transcript** → Create visit transcript/recording

## Authentication Endpoints

### Login
```
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

Body:
username=vet1&password=password123

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Get Current User Info
```
GET /api/v1/auth/me
Authorization: Bearer <access_token>

Response:
{
  "id": "uuid",
  "username": "vet1",
  "email": "vet1@helppet.ai",
  "full_name": "Dr. Sarah Johnson",
  "role": "VET_STAFF",
  "is_active": true,
  "practice_id": "uuid"
}
```

## Schedule/Dashboard Endpoints

### Get Vet's Daily Schedule
```
GET /api/v1/dashboard/vet/{vet_user_uuid}?date=2024-01-15
Authorization: Bearer <access_token>

Response:
{
  "today_appointments": [
    {
      "id": "appointment-uuid",
      "practice_id": "practice-uuid",
      "pet_owner_id": "owner-uuid",
      "assigned_vet_user_id": "vet-uuid",
      "appointment_date": "2024-01-15T10:30:00",
      "duration_minutes": 30,
      "appointment_type": "checkup",
      "status": "scheduled",
      "title": "Routine Checkup - Bella",
      "description": "Annual wellness exam",
      "notes": "First time visitor",
      "pets": [
        {
          "id": "pet-uuid",
          "name": "Bella",
          "species": "dog",
          "breed": "Golden Retriever"
        }
      ],
      "created_at": "2024-01-10T09:00:00",
      "updated_at": "2024-01-10T09:00:00"
    }
  ],
  "stats": {
    "appointments_today": 5,
    "completed_visits": 2
  }
}
```

### Get Today's Work Summary
```
GET /api/v1/dashboard/vet/{vet_user_uuid}/today
Authorization: Bearer <access_token>

Response:
{
  "appointments_today": [...], // Same format as above
  "next_appointment": {...}, // Next scheduled appointment
  "current_appointment": {...}, // Currently in-progress appointment
  "completed_count": 2,
  "remaining_count": 3
}
```

## Visit Management (Start/End Visits)

### Update Appointment Status
```
PUT /api/v1/appointments/{appointment_uuid}
Authorization: Bearer <access_token>
Content-Type: application/json

// To start a visit:
{
  "status": "in_progress"
}

// To end a visit:
{
  "status": "completed"
}

Response:
{
  "id": "appointment-uuid",
  "status": "in_progress", // or "completed"
  // ... other appointment fields
}
```

## Pet Information Endpoints

### Get Pet Details
```
GET /api/v1/pets/{pet_uuid}
Authorization: Bearer <access_token>

Response:
{
  "id": "pet-uuid",
  "name": "Bella",
  "species": "dog",
  "breed": "Golden Retriever",
  "date_of_birth": "2020-03-15",
  "weight": 65.5,
  "microchip_number": "123456789012345",
  "is_active": true,
  "registration_date": "2020-04-01",
  "owner": {
    "id": "owner-uuid",
    "first_name": "John",
    "last_name": "Smith",
    "email": "john.smith@email.com",
    "phone": "+1-555-123-4567"
  },
  "created_at": "2020-04-01T10:00:00",
  "updated_at": "2024-01-10T14:30:00"
}
```

## Medical Records Endpoints

### Get Pet's Medical Records
```
GET /api/v1/medical-records/pet/{pet_uuid}?include_historical=true
Authorization: Bearer <access_token>

Response:
{
  "records": [
    {
      "id": "record-uuid",
      "pet_id": "pet-uuid",
      "record_type": "vaccination",
      "title": "Annual Vaccinations",
      "description": "DHPP and Rabies vaccines administered",
      "diagnosis": null,
      "treatment_plan": "Follow up in 1 year",
      "medications": ["DHPP Vaccine", "Rabies Vaccine"],
      "notes": "No adverse reactions observed",
      "follow_up_date": "2025-01-15",
      "is_current": true,
      "created_by": "vet-uuid",
      "created_at": "2024-01-15T10:45:00",
      "updated_at": "2024-01-15T10:45:00"
    }
  ],
  "total": 1,
  "current_records_count": 1,
  "historical_records_count": 0
}
```

### Get Medical Record History
```
GET /api/v1/medical-records/pet/{pet_uuid}/history
Authorization: Bearer <access_token>

Response: // Same format as above but includes all historical versions
```

### Get Specific Medical Record
```
GET /api/v1/medical-records/{record_uuid}
Authorization: Bearer <access_token>

Response:
{
  "id": "record-uuid",
  "pet_id": "pet-uuid",
  // ... all medical record fields with full details
  "pet": {
    "id": "pet-uuid",
    "name": "Bella",
    "species": "dog"
  },
  "created_by_user": {
    "id": "vet-uuid",
    "full_name": "Dr. Sarah Johnson"
  }
}
```

## Visit Transcripts Endpoints

### Get Pet's Visit Transcripts
```
GET /api/v1/visit-transcripts/pet/{pet_uuid}
Authorization: Bearer <access_token>

Response:
[
  {
    "uuid": "transcript-uuid",
    "pet_id": "pet-uuid",
    "visit_date": 1705312800, // Unix timestamp
    "full_text": "Patient presented for routine wellness exam...",
    "audio_transcript_url": "https://s3.amazonaws.com/bucket/audio.mp3",
    "metadata": {
      "duration_minutes": 25,
      "recording_quality": "high"
    },
    "summary": "Routine wellness exam completed. No issues found.",
    "state": "processed",
    "created_at": "2024-01-15T11:00:00",
    "updated_at": "2024-01-15T11:30:00",
    "created_by": "vet-uuid"
  }
]
```

### Get Specific Visit Transcript
```
GET /api/v1/visit-transcripts/{transcript_uuid}
Authorization: Bearer <access_token>

Response:
{
  "uuid": "transcript-uuid",
  "pet_id": "pet-uuid",
  "visit_date": 1705312800,
  "full_text": "Complete transcript text here...",
  "audio_transcript_url": "https://s3.amazonaws.com/bucket/audio.mp3",
  "metadata": {...},
  "summary": "Visit summary",
  "state": "processed",
  "created_at": "2024-01-15T11:00:00",
  "updated_at": "2024-01-15T11:30:00",
  "created_by": "vet-uuid"
}
```

### Create Visit Transcript
```
POST /api/v1/visit-transcripts
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "pet_id": "pet-uuid",
  "visit_date": 1705312800,
  "full_text": "Transcript content...",
  "audio_transcript_url": "https://s3.amazonaws.com/bucket/audio.mp3",
  "metadata": {
    "duration_minutes": 25
  },
  "summary": "Visit summary"
}

Response:
{
  "uuid": "new-transcript-uuid",
  // ... transcript details
}
```

## Audio Upload Endpoint

### Upload Audio File
```
POST /api/v1/upload/audio
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

Form Data:
- audio: [audio file]
- appointment_id: "appointment-uuid" (optional)
- pet_id: "pet-uuid" (optional)
- bucket_name: "custom-bucket" (optional)

Response:
{
  "message": "File uploaded successfully",
  "file_url": "https://s3.amazonaws.com/bucket/filename.mp3",
  "file_key": "uploads/audio/filename.mp3"
}
```

## Key Enums and Constants

### Appointment Status
- `scheduled` - Appointment is scheduled
- `confirmed` - Appointment confirmed by owner
- `in_progress` - Visit is currently happening
- `completed` - Visit finished
- `cancelled` - Appointment cancelled

### Appointment Types
- `checkup` - Routine wellness exam
- `vaccination` - Vaccination appointment
- `surgery` - Surgical procedure
- `emergency` - Emergency visit
- `follow_up` - Follow-up appointment

### Visit States
- `recording` - Currently being recorded
- `processing` - Audio being transcribed
- `processed` - Transcript completed

### User Roles
- `VET_STAFF` - Veterinary staff member
- `VET` - Licensed veterinarian
- `ADMIN` - System administrator
- `PET_OWNER` - Pet owner

## Error Handling

All endpoints return standard HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid data)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

Error Response Format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Authentication Headers

All API calls (except login) require:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Test Credentials

For development/testing:
- **Username**: `vet1`, **Password**: `password123` (Dr. Sarah Johnson - VET_STAFF)
- **Username**: `vet2`, **Password**: `password123` (Dr. Michael Chen - VET_STAFF)
- **Username**: `admin`, **Password**: `admin123` (System Administrator - ADMIN)

## Sample App Workflow

1. **App Launch**: Present login screen
2. **Login**: POST to `/auth/token` with credentials
3. **Store Token**: Save access token securely
4. **Get User Info**: GET `/auth/me` to get user details
5. **Load Dashboard**: GET `/dashboard/vet/{user_id}/today` for today's schedule
6. **Display Appointments**: Show list of appointments with status
7. **Start Visit**: When vet taps "Start", PUT to `/appointments/{id}` with `{"status": "in_progress"}`
8. **View Pet**: When tapping pet name, GET `/pets/{pet_id}` for details
9. **View Medical Records**: GET `/medical-records/pet/{pet_id}` for history
10. **View Transcripts**: GET `/visit-transcripts/pet/{pet_id}` for past visits
11. **End Visit**: PUT to `/appointments/{id}` with `{"status": "completed"}`
12. **Record Visit**: Optionally POST to `/visit-transcripts` with visit notes

This provides a complete veterinary workflow through the mobile app interface.

## Swift Code Examples

### Network Manager Setup
```swift
import Foundation

class APIManager {
    static let shared = APIManager()
    private let baseURL = "https://api.helppet.ai"
    private var accessToken: String?
    
    func setAccessToken(_ token: String) {
        accessToken = token
    }
    
    private var authHeaders: [String: String] {
        guard let token = accessToken else { return [:] }
        return [
            "Authorization": "Bearer \(token)",
            "Content-Type": "application/json"
        ]
    }
}
```

### Login Function
```swift
func login(username: String, password: String) async throws -> LoginResponse {
    let url = URL(string: "\(baseURL)/api/v1/auth/token")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
    
    let body = "username=\(username)&password=\(password)"
    request.httpBody = body.data(using: .utf8)
    
    let (data, _) = try await URLSession.shared.data(for: request)
    let response = try JSONDecoder().decode(LoginResponse.self, from: data)
    
    setAccessToken(response.accessToken)
    return response
}
```

### Get Today's Schedule
```swift
func getTodaySchedule(vetId: String) async throws -> DashboardResponse {
    let url = URL(string: "\(baseURL)/api/v1/dashboard/vet/\(vetId)/today")!
    var request = URLRequest(url: url)
    request.httpMethod = "GET"
    authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
    
    let (data, _) = try await URLSession.shared.data(for: request)
    return try JSONDecoder().decode(DashboardResponse.self, from: data)
}
```

### Update Appointment Status
```swift
func updateAppointmentStatus(appointmentId: String, status: AppointmentStatus) async throws {
    let url = URL(string: "\(baseURL)/api/v1/appointments/\(appointmentId)")!
    var request = URLRequest(url: url)
    request.httpMethod = "PUT"
    authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
    
    let body = ["status": status.rawValue]
    request.httpBody = try JSONEncoder().encode(body)
    
    let (_, _) = try await URLSession.shared.data(for: request)
}
```

## Data Models

```swift
struct LoginResponse: Codable {
    let accessToken: String
    let tokenType: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
    }
}

struct User: Codable {
    let id: String
    let username: String
    let email: String
    let fullName: String
    let role: UserRole
    let isActive: Bool
    let practiceId: String?
    
    enum CodingKeys: String, CodingKey {
        case id, username, email, role
        case fullName = "full_name"
        case isActive = "is_active"
        case practiceId = "practice_id"
    }
}

enum UserRole: String, Codable {
    case vetStaff = "VET_STAFF"
    case vet = "VET"
    case admin = "ADMIN"
    case petOwner = "PET_OWNER"
}

enum AppointmentStatus: String, Codable {
    case scheduled = "scheduled"
    case confirmed = "confirmed"
    case inProgress = "in_progress"
    case completed = "completed"
    case cancelled = "cancelled"
}

struct Appointment: Codable {
    let id: String
    let practiceId: String
    let petOwnerId: String
    let assignedVetUserId: String?
    let appointmentDate: Date
    let durationMinutes: Int
    let appointmentType: String
    let status: AppointmentStatus
    let title: String
    let description: String?
    let notes: String?
    let pets: [PetSummary]
    let createdAt: Date
    let updatedAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id
        case practiceId = "practice_id"
        case petOwnerId = "pet_owner_id"
        case assignedVetUserId = "assigned_vet_user_id"
        case appointmentDate = "appointment_date"
        case durationMinutes = "duration_minutes"
        case appointmentType = "appointment_type"
        case status, title, description, notes, pets
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

struct PetSummary: Codable {
    let id: String
    let name: String
    let species: String
    let breed: String?
}

struct DashboardResponse: Codable {
    let appointmentsToday: [Appointment]
    let nextAppointment: Appointment?
    let currentAppointment: Appointment?
    let completedCount: Int
    let remainingCount: Int
    
    enum CodingKeys: String, CodingKey {
        case appointmentsToday = "appointments_today"
        case nextAppointment = "next_appointment"
        case currentAppointment = "current_appointment"
        case completedCount = "completed_count"
        case remainingCount = "remaining_count"
    }
}
```

This comprehensive guide provides everything needed to build a Swift iOS app that integrates with the HelpPet API for veterinary practice management.
