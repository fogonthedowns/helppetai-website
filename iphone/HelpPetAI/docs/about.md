# HelpPetAI - iOS Application Documentation

## Overview

HelpPetAI is a comprehensive iOS veterinary practice management application built with SwiftUI. The app provides veterinarians and veterinary staff with tools to manage appointments, record patient visits, maintain medical records, and capture audio recordings during consultations.

## What This Application Does

The HelpPetAI iOS app serves as the mobile interface for veterinary professionals to:

- **Manage Daily Schedules**: View today's appointments, track completed and remaining visits
- **Record Patient Visits**: Capture high-quality audio recordings during pet consultations
- **Access Pet Information**: View detailed pet profiles including medical history, owner information, and vital statistics
- **Review Medical Records**: Access comprehensive medical records with treatment plans, diagnoses, and medications
- **Upload Audio Data**: Seamlessly upload recordings to cloud storage with automatic transcription processing

### Target Audience
- Veterinarians and veterinary technicians
- Veterinary practice staff
- Pet healthcare professionals requiring mobile access to patient data

## Architecture

### Design Patterns
- **MVVM (Model-View-ViewModel)**: Uses SwiftUI's `@StateObject` and `@ObservableObject` for reactive UI updates
- **Singleton Pattern**: Centralized API and Audio management through shared instances
- **Repository Pattern**: APIManager acts as a single source of truth for all backend communications
- **Dependency Injection**: Services are injected into views via StateObject initialization

### Key Architectural Decisions

1. **SwiftUI Framework**: Chosen for modern iOS development with declarative UI patterns
2. **Async/Await**: Leverages Swift's modern concurrency for all network operations
3. **Keychain Security**: Secure token storage using iOS Keychain Services
4. **AVFoundation Integration**: Native iOS audio recording and playback capabilities
5. **RESTful API Design**: Clean separation between client and server responsibilities

## Project Structure

```
HelpPetAI/
├── HelpPetAIApp.swift          # App entry point
├── ContentView.swift           # Root view with authentication routing
├── Models/                     # Data models and structures
│   ├── User.swift             # User authentication models
│   ├── Pet.swift              # Pet and owner data models
│   ├── Appointment.swift      # Appointment and dashboard models
│   ├── MedicalRecord.swift    # Medical record data models
│   ├── AudioModels.swift      # Audio recording models
│   └── Views/                 # SwiftUI view components
│       ├── LoginView.swift    # Authentication interface
│       ├── DashboardView.swift # Main appointment dashboard
│       ├── PetDetailView.swift # Pet information display
│       ├── VisitRecordingView.swift # Visit recording interface
│       ├── AudioRecordingView.swift # Audio capture interface
│       └── Components/        # Reusable UI components
├── Services/                  # Business logic and API layer
│   ├── APIManager.swift       # HTTP client and API methods
│   ├── AudioManager.swift     # Audio recording and playback
│   ├── KeychainManager.swift  # Secure credential storage
│   └── APIError.swift         # Error handling definitions
└── PreviewSupport.swift       # SwiftUI preview helpers
```

## API Documentation

### Authentication API

#### Login
```swift
func login(username: String, password: String) async throws -> LoginResponse
```
- **Purpose**: Authenticate user credentials and obtain access token
- **Parameters**: 
  - `username`: User's login identifier
  - `password`: User's password
- **Returns**: `LoginResponse` containing access token and token type
- **Example**:
```swift
let response = try await APIManager.shared.login(
    username: "vet1", 
    password: "password123"
)
```

#### Get Current User
```swift
func getCurrentUser() async throws -> User
```
- **Purpose**: Retrieve authenticated user's profile information
- **Returns**: `User` object with role, practice ID, and profile details

### Appointment Management API

#### Get Today's Schedule
```swift
func getTodaySchedule(vetId: String, date: String? = nil) async throws -> DashboardResponse
```
- **Purpose**: Fetch daily appointment schedule and statistics
- **Parameters**:
  - `vetId`: Veterinarian's user ID
  - `date`: Optional date string (defaults to today)
- **Returns**: `DashboardResponse` with appointments, counts, and current/next appointment info

#### Update Appointment Status
```swift
func updateAppointmentStatus(appointmentId: String, status: AppointmentStatus) async throws
```
- **Purpose**: Change appointment status (scheduled, confirmed, in_progress, completed, cancelled)
- **Parameters**:
  - `appointmentId`: Unique appointment identifier
  - `status`: New appointment status enum value

### Pet Information API

#### Get Pet Details
```swift
func getPetDetails(petId: String) async throws -> Pet
```
- **Purpose**: Retrieve comprehensive pet information
- **Returns**: `Pet` object with medical history, owner details, and vital statistics

#### Get Medical Records
```swift
func getMedicalRecords(petId: String) async throws -> MedicalRecordsResponse
```
- **Purpose**: Fetch pet's medical history and treatment records
- **Returns**: `MedicalRecordsResponse` with current and historical records

### Audio Recording API

#### Initiate Recording Upload
```swift
func initiateRecordingUpload(_ request: RecordingUploadInitiateRequest) async throws -> RecordingUploadInitiateResponse
```
- **Purpose**: Begin audio file upload process with pre-signed S3 URLs
- **Parameters**: `RecordingUploadInitiateRequest` with appointment, pet, and file metadata
- **Returns**: Upload URLs, fields, and recording ID

#### Complete Recording Upload
```swift
func completeRecordingUpload(recordingId: String, request: RecordingUploadCompleteRequest) async throws
```
- **Purpose**: Finalize upload and trigger transcription processing
- **Parameters**: Recording ID and completion metadata

#### Get Recordings
```swift
func getRecordings(
    appointmentId: String? = nil,
    visitId: String? = nil, 
    status: String? = nil,
    limit: Int = 50,
    offset: Int = 0
) async throws -> [RecordingResponse]
```
- **Purpose**: Retrieve recordings with flexible filtering options
- **Returns**: Array of `RecordingResponse` objects with metadata and status

## Data Models

### Core Models

#### User
```swift
struct User: Codable, Identifiable {
    let id: String
    let username: String
    let email: String
    let fullName: String
    let role: UserRole
    let isActive: Bool
    let practiceId: String?
}

enum UserRole: String, Codable {
    case vetStaff = "VET_STAFF"
    case vet = "VET"
    case admin = "ADMIN"
    case petOwner = "PET_OWNER"
}
```

#### Pet
```swift
struct Pet: Codable, Identifiable {
    let id: String
    let name: String
    let species: String
    let breed: String?
    let color: String?
    let gender: String?
    let weight: Double?
    let dateOfBirth: Date?
    let microchipId: String?
    let spayedNeutered: Bool?
    let allergies: String?
    let medications: String?
    let medicalNotes: String?
    let emergencyContact: String?
    let emergencyPhone: String?
    let ownerId: String
    let isActive: Bool
    let createdAt: Date
    let updatedAt: Date
    let ageYears: Int?
    let displayName: String?
    let owner: PetOwner?
}
```

#### Appointment
```swift
struct Appointment: Codable, Identifiable {
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
}

enum AppointmentStatus: String, Codable, CaseIterable {
    case scheduled = "scheduled"
    case confirmed = "confirmed" 
    case inProgress = "in_progress"
    case completed = "completed"
    case cancelled = "cancelled"
}
```

## Setup & Installation

### Prerequisites
- iOS 15.0 or later
- Xcode 14.0 or later
- Swift 5.7 or later
- Active internet connection for API access

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-org/HelpPetAI-iOS.git
   cd HelpPetAI-iOS
   ```

2. **Open in Xcode**
   ```bash
   open HelpPetAI.xcodeproj
   ```

3. **Configure API Endpoint**
   - Update `baseURL` in `APIManager.swift` if needed
   - Default: `https://api.helppet.ai`

4. **Build and Run**
   - Select target device or simulator
   - Press Cmd+R to build and run

### Test Credentials
- **Username**: `vet1`
- **Password**: `password123`

## Configuration

### API Configuration
The app connects to the HelpPetAI backend API at `https://api.helppet.ai`. Key configuration options:

- **Base URL**: Configurable in `APIManager.swift`
- **Request Timeout**: 30 seconds for standard requests, 60 seconds for uploads
- **Retry Logic**: Automatic retry with exponential backoff for network failures
- **Authentication**: JWT Bearer token stored securely in iOS Keychain

### Audio Configuration
Audio recording settings optimized for voice capture:

- **Format**: MPEG-4 AAC
- **Sample Rate**: 44.1 kHz
- **Channels**: Mono (1 channel)
- **Quality**: High quality encoding
- **Bit Rate**: 128 kbps

## Dependencies

### iOS Frameworks
- **SwiftUI**: Modern declarative UI framework
- **AVFoundation**: Audio recording and playback
- **Foundation**: Core system services
- **Security**: Keychain access for secure storage

### External Dependencies
None - The app uses only native iOS frameworks for maximum stability and security.

## Authentication & Authorization

### Security Implementation
- **JWT Tokens**: Stateless authentication with Bearer token authorization
- **Keychain Storage**: Secure credential persistence using iOS Keychain Services
- **Automatic Logout**: Session expiration handling with automatic re-authentication prompts
- **Role-Based Access**: User roles determine available functionality (VET, VET_STAFF, ADMIN, PET_OWNER)

### Token Management
- Tokens stored securely in iOS Keychain
- Automatic token refresh on API calls
- Graceful handling of expired sessions
- Secure token deletion on logout

## Error Handling

### API Error Types
```swift
enum APIError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case unauthorized
    case forbidden
    case notFound
    case validationError
    case serverError(Int)
    case decodingError
    case networkError
}
```

### Error Recovery Strategies
- **Network Errors**: Automatic retry with exponential backoff
- **Authentication Errors**: Prompt for re-login
- **Validation Errors**: User-friendly error messages
- **Server Errors**: Graceful degradation with offline capabilities

## Performance Considerations

### Optimization Strategies
- **Async/Await**: Non-blocking network operations
- **Image Caching**: Efficient memory management for pet photos
- **Lazy Loading**: On-demand data fetching for large lists
- **Background Processing**: Audio uploads continue when app is backgrounded

### Audio Optimization
- **Compression**: Efficient AAC encoding reduces file sizes
- **Streaming Upload**: Large files uploaded in chunks
- **Progress Tracking**: Real-time upload progress feedback
- **Retry Logic**: Robust handling of upload failures

## Known Limitations

### Current Constraints
- **Offline Mode**: Limited functionality without internet connectivity
- **File Size Limits**: Audio recordings limited by S3 upload constraints
- **iOS Version**: Requires iOS 15.0+ for full SwiftUI feature support
- **Single Practice**: Currently supports single veterinary practice per user

### Technical Debt
- **Error Handling**: Some edge cases need more specific error messages
- **Accessibility**: Voice-over support could be enhanced
- **Testing**: Unit test coverage could be expanded
- **Localization**: Currently English-only interface

## Future Improvements

### Planned Enhancements
1. **Offline Capabilities**: Local data caching for offline access
2. **Push Notifications**: Real-time appointment reminders and updates
3. **Photo Capture**: In-app camera integration for pet photos
4. **Voice Commands**: Hands-free operation during examinations
5. **Multi-Practice Support**: Support for veterinarians working across multiple practices
6. **Advanced Search**: Full-text search across pets and medical records
7. **Export Features**: PDF generation for medical reports
8. **Integration APIs**: Third-party veterinary software integration
9. **Telemedicine**: Video consultation capabilities
10. **Analytics Dashboard**: Practice performance metrics and insights

### Suggested Technical Improvements
- **Core Data Integration**: Local data persistence layer
- **Combine Framework**: Enhanced reactive programming patterns
- **SwiftUI Navigation**: Adopt iOS 16+ navigation improvements
- **Widget Extensions**: Home screen widgets for quick appointment access
- **Siri Shortcuts**: Voice-activated app functionality
- **Background App Refresh**: Automatic data synchronization
- **Biometric Authentication**: Face ID/Touch ID login options

---

*This documentation was automatically generated based on source code analysis. For questions or updates, please contact the development team.*
