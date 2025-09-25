# Push Notifications Integration Guide

## Overview

This document outlines the complete push notification integration for the HelpPet.ai iOS app. The system is designed to notify veterinary staff when new appointments are booked through the voice endpoint.

## Architecture

### Backend Components (Already Implemented)
- **PushNotificationService**: Handles APNs integration and notification sending
- **DeviceToken Model**: Stores device tokens for users
- **Device Token API Endpoints**: Registration, unregistration, and management
- **Appointment Service Integration**: Sends notifications on successful booking

### iOS Components (Newly Implemented)

#### 1. PushNotificationService.swift
- **Location**: `Services/PushNotificationService.swift`
- **Purpose**: Manages all push notification functionality
- **Key Features**:
  - Request notification permissions
  - Handle device token registration with APNs
  - Register device tokens with backend API
  - Process incoming notifications
  - Handle notification taps and deep linking

#### 2. APIManager Extensions
- **Location**: `Services/APIManager.swift`
- **New Methods**:
  - `registerDeviceToken(_:)`: Register device token with backend
  - `unregisterDeviceToken(_:)`: Remove device token on logout
  - `getMyDeviceTokens()`: Retrieve user's registered tokens

#### 3. App Lifecycle Integration
- **Location**: `HelpPetAIApp.swift`
- **Features**:
  - Push notification delegate setup
  - Automatic initialization for authenticated users
  - Remote notification callback handling

#### 4. User Interface Components
- **NotificationSettingsView**: Complete settings interface
- **SidebarMenu**: Added notifications menu item
- **DashboardView**: Real-time notification handling

## Configuration

### Info.plist Updates
```xml
<key>UIBackgroundModes</key>
<array>
    <string>audio</string>
    <string>remote-notification</string>
</array>
<key>NSUserNotificationAlertStyle</key>
<string>alert</string>
```

### Environment Variables (Backend)
- `APNS_KEY_ID`: M8A86NFUK4
- `APNS_TEAM_ID`: 6QH7LZMFLB
- `APNS_BUNDLE_ID`: ai.helppet.HelpPetAI
- `APNS_USE_SANDBOX`: true (development) / false (production)
- `APNS_KEY_PATH`: Path to AuthKey_M8A86NFUK4.p8

## Notification Flow

### 1. User Authentication
```swift
// Automatic setup after login
await pushNotificationService.initializeForAuthenticatedUser()
```

### 2. Permission Request
- Requests authorization for alerts, sounds, and badges
- Handles user acceptance/denial gracefully
- Provides settings link for denied permissions

### 3. Device Token Registration
```swift
// APNs provides device token
func didRegisterForRemoteNotifications(with deviceToken: Data)

// Register with backend
POST /api/v1/device-tokens/register
{
    "device_token": "abc123...",
    "device_type": "ios"
}
```

### 4. Appointment Booking Trigger
When a new appointment is successfully booked via voice:
1. Backend identifies practice staff users
2. Retrieves their device tokens
3. Sends APNs notification with appointment details

### 5. Notification Payload
```json
{
    "aps": {
        "alert": {
            "title": "New Appointment Booked",
            "body": "Fluffy (John Doe) - 2:00 PM"
        },
        "sound": "default",
        "badge": 1
    },
    "type": "appointment_booked",
    "appointment_id": "uuid-123",
    "pet_owner_name": "John Doe",
    "pet_name": "Fluffy",
    "appointment_time": "2:00 PM"
}
```

### 6. Notification Handling
- **Foreground**: Shows banner with sound
- **Background**: Standard notification
- **Tap Action**: Navigates to appointment in dashboard

## User Experience

### Permission Flow
1. User logs in successfully
2. App automatically requests notification permissions
3. User grants/denies permissions
4. Device token registered with backend (if granted)

### Settings Management
- Access via sidebar menu → "Notifications"
- View permission status and registration status
- Link to system settings if permissions denied
- Debug test notification (development builds)

### Notification Types
- **New Appointments**: Primary notification type
- **Future Extensions**: Appointment changes, visit transcripts ready

## API Endpoints

### Device Token Management
```
POST /api/v1/device-tokens/register
DELETE /api/v1/device-tokens/unregister
GET /api/v1/device-tokens/
```

### Request/Response Models
```swift
struct DeviceTokenRegistrationRequest: Codable {
    let deviceToken: String
    let deviceType: String
}

struct DeviceTokenResponse: Codable {
    let id: String
    let deviceToken: String
    let deviceType: String
    let isActive: Bool
    let createdAt: String
    let updatedAt: String
}
```

## Security Considerations

### APNs Certificate Management
- Production certificate: AuthKey_M8A86NFUK4.p8
- Secure storage in deployment environment
- Regular rotation as per Apple guidelines

### Device Token Security
- Tokens stored securely in backend database
- Automatic cleanup of inactive tokens
- User-specific token association

### Privacy
- Only veterinary staff receive notifications (B2B)
- No pet owner personal data in notifications
- Minimal payload information

## Testing

### Development Testing
1. Use sandbox APNs environment (`APNS_USE_SANDBOX=true`)
2. Test notification in NotificationSettingsView (debug builds)
3. Verify token registration in backend logs

### Production Verification
1. Switch to production APNs (`APNS_USE_SANDBOX=false`)
2. Test with real appointment bookings
3. Monitor notification delivery rates

## Troubleshooting

### Common Issues
1. **No device token**: Check Info.plist configuration
2. **Registration fails**: Verify backend API endpoints
3. **Notifications not received**: Check APNs environment setting
4. **Permission denied**: Guide user to system settings

### Debug Information
- Device token displayed in notification settings
- Registration status visible in UI
- Comprehensive logging throughout the flow

## Future Enhancements

### Planned Features
1. **Rich Notifications**: Images, actions, custom UI
2. **Notification Categories**: Different types with custom actions
3. **Silent Notifications**: Background data updates
4. **Notification History**: In-app notification center

### Analytics Integration
- Track notification open rates
- Monitor permission grant rates
- Measure user engagement with notifications

## Deployment Checklist

### iOS App
- [ ] Push notification entitlement enabled in Xcode
- [ ] Production APNs certificate configured
- [ ] Bundle ID matches certificate (ai.helppet.HelpPetAI)
- [ ] Info.plist includes remote-notification background mode

### Backend
- [ ] APNs environment variables set correctly
- [ ] AuthKey_M8A86NFUK4.p8 file accessible
- [ ] Device token endpoints deployed
- [ ] Push notification service integrated with appointment booking

### Testing
- [ ] Permission flow tested on device
- [ ] Device token registration verified
- [ ] End-to-end notification flow tested
- [ ] Settings UI functionality confirmed

## Support

For issues or questions regarding push notification integration:
1. Check device logs for APNs registration errors
2. Verify backend API responses in network logs
3. Test with sandbox environment first
4. Monitor APNs feedback service for delivery issues
