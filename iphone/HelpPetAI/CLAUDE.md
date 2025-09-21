# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

This is an iOS project using Xcode. Key commands:

- **Build**: Open `HelpPetAI.xcodeproj` in Xcode, then Cmd+B to build
- **Run**: Cmd+R in Xcode to build and run on simulator/device  
- **Test**: Cmd+U in Xcode to run unit and UI tests
- **Clean**: Cmd+Shift+K to clean build artifacts

For CI/CD or command line builds:
```bash
xcodebuild -project HelpPetAI.xcodeproj -scheme HelpPetAI -destination 'platform=iOS Simulator,name=iPhone 15' build
xcodebuild -project HelpPetAI.xcodeproj -scheme HelpPetAI -destination 'platform=iOS Simulator,name=iPhone 15' test
```

## Architecture Overview

HelpPetAI is a SwiftUI-based iOS veterinary practice management app with a clear MVVM architecture:

### Core Architecture Patterns
- **MVVM**: Views observe `@StateObject` managers (APIManager, AudioManager) 
- **Singleton Services**: APIManager.shared and AudioManager.shared provide centralized state
- **Repository Pattern**: APIManager acts as single source of truth for all backend API calls
- **Reactive UI**: Uses `@Published` properties for automatic UI updates

### Data Flow
1. **Authentication**: ContentView routes between LoginView/DashboardView based on APIManager.isAuthenticated
2. **API Layer**: All network requests go through APIManager with JWT token auth stored in Keychain
3. **Audio Pipeline**: AudioManager handles recording → S3 upload → transcription backend processing
4. **State Management**: Views observe published properties and update automatically

### Key Architectural Components

**API Integration (APIManager.swift)**
- Centralized HTTP client with automatic token refresh
- Custom date decoding strategy for flexible API date formats  
- Retry logic with exponential backoff for network failures
- Comprehensive error handling with specific error types

**Audio System (AudioManager.swift)**
- AVFoundation-based recording with M4A format
- S3 multipart upload with presigned URLs
- Visit-based data model (one visit per pet per recording)
- Robust permission handling and audio session management

**Data Models**
- Pet/Owner/Appointment models with proper Codable implementation
- Visit transcript system for audio recordings tied to specific pets
- Dashboard aggregation models for appointment statistics
- Error types with localized descriptions for user feedback

### Critical Data Model Concepts

**Visit-Centric Architecture**: Each audio recording creates a Visit record for ONE specific pet. This is crucial - multiple pets in an appointment require multiple separate visits/recordings. The relationship is:
- Appointment (1) → Pets (many) 
- Pet (1) → Visits (many)
- Visit (1) → Audio Recording (1)

**Authentication Flow**: 
- Token stored securely in iOS Keychain via KeychainManager
- APIManager.isAuthenticated drives main app navigation
- Automatic logout on 401 responses with token cleanup

## Development Guidelines

### File Organization
```
HelpPetAI/
├── Models/              # Data structures and Codable models
│   ├── Views/          # SwiftUI view files
│   └── Components/     # Reusable UI components
├── Services/           # Business logic and external service integration
└── Supporting Files    # App entry point, assets, etc.
```

### API Endpoints
The app connects to `https://api.helppet.ai` with these key endpoints:
- `POST /api/v1/auth/token` - Authentication
- `GET /api/v1/auth/me` - Current user profile
- `GET /api/v1/dashboard/vet/{vetId}/today` - Daily schedule
- `POST /api/v1/visit-transcripts/audio/upload/initiate` - Audio upload start
- `POST /api/v1/visit-transcripts/audio/upload/complete/{visitId}` - Audio upload finish

### Medical-Grade Audio Recording System
- **Format**: M4A (native iOS, smaller than WAV)
- **Quality**: Records at 44.1kHz, mono channel, 128kbps  
- **Corruption Prevention**: SHA256 integrity verification before and after operations
- **Secure Storage**: FileProtectionType.complete encryption for all medical recordings
- **Upload Resilience**: Automatic retry with exponential backoff (2min, 4min, 8min, 16min, 32min)
- **Network Recovery**: Handles network loss, app suspension, power loss scenarios
- **Background Uploads**: Continues uploads when app is backgrounded or terminated
- **Queue Management**: Persistent upload queue survives app restarts
- Each recording is associated with a specific pet + appointment combination

**MedicalRecordingManager.swift**: Core medical upload system with:
- Local secure persistence BEFORE any upload attempt
- File integrity checks prevent corrupted uploads
- Automatic retry logic for failed uploads
- Background task support for power loss scenarios
- Upload queue persistence across app restarts

### Key Dependencies
- SwiftUI for declarative UI
- AVFoundation for audio recording/playback
- Foundation URLSession for networking
- Security framework for Keychain access
- No external package dependencies (intentional for stability)

## Testing Notes

- Unit tests in `HelpPetAITests/`
- UI tests in `HelpPetAIUITests/`
- Test credentials: username `vet1`, password `password123`
- Audio recording requires device or simulator with microphone access

## Development Environment

- iOS 15.0+ required (for SwiftUI features)
- Xcode 14.0+ recommended
- Swift 5.7+ language features used
- Runs on iPhone and iPad (universal app)