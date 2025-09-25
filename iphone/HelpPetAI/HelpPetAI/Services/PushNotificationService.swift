//
//  PushNotificationService.swift
//  HelpPetAI
//
//  TL;DR: Manages push notification registration, device token handling, and notification processing.
//
//  Features:
//  - Request push notification permissions from user
//  - Register device token with APNs and backend API
//  - Handle incoming push notifications
//  - Manage notification settings and preferences
//  - Auto-register on app launch for authenticated users
//  - Handle notification tap actions and deep linking
//
//  Usage: Access via `PushNotificationService.shared` (singleton).
//

import Foundation
import UserNotifications
import UIKit

@MainActor
class PushNotificationService: NSObject, ObservableObject {
    static let shared = PushNotificationService()
    
    @Published var isRegistered = false
    @Published var deviceToken: String?
    @Published var notificationPermissionStatus: UNAuthorizationStatus = .notDetermined
    
    private let apiManager = APIManager.shared
    
    private override init() {
        super.init()
        checkNotificationSettings()
    }
    
    // MARK: - Permission Management
    
    /// Request push notification permissions from the user
    func requestPermissions() async -> Bool {
        let center = UNUserNotificationCenter.current()
        
        do {
            let granted = try await center.requestAuthorization(options: [.alert, .sound, .badge])
            
            await MainActor.run {
                self.notificationPermissionStatus = granted ? .authorized : .denied
            }
            
            if granted {
                print("✅ Push notification permissions granted")
                await registerForRemoteNotifications()
                return true
            } else {
                print("❌ Push notification permissions denied")
                return false
            }
        } catch {
            print("❌ Error requesting push notification permissions: \(error)")
            return false
        }
    }
    
    /// Check current notification settings
    func checkNotificationSettings() {
        Task {
            let center = UNUserNotificationCenter.current()
            let settings = await center.notificationSettings()
            
            await MainActor.run {
                self.notificationPermissionStatus = settings.authorizationStatus
                
                // Debug logging
                print("🔔 Current notification permission status: \(settings.authorizationStatus.debugDescription)")
                print("🔔 Alert setting: \(settings.alertSetting.debugDescription)")
                print("🔔 Sound setting: \(settings.soundSetting.debugDescription)")
                print("🔔 Badge setting: \(settings.badgeSetting.debugDescription)")
                
                // If we have permission but no device token, try to register
                if settings.authorizationStatus == .authorized && deviceToken == nil {
                    Task {
                        await registerForRemoteNotifications()
                    }
                }
            }
        }
    }
    
    // MARK: - Device Token Registration
    
    /// Register for remote notifications with APNs
    private func registerForRemoteNotifications() async {
        print("🔔 Registering for remote notifications with APNs...")
        print("🔔 Bundle ID: \(Bundle.main.bundleIdentifier ?? "unknown")")
        
        #if targetEnvironment(simulator)
        print("🔔 Running on iOS Simulator - APNs will NOT work!")
        #else
        print("🔔 Running on physical device - APNs should work")
        #endif
        
        await UIApplication.shared.registerForRemoteNotifications()
        print("🔔 registerForRemoteNotifications() call completed")
        
        // Wait a bit to see if we get a device token
        print("🔔 Waiting 5 seconds for device token callback...")
        try? await Task.sleep(nanoseconds: 5_000_000_000) // 5 seconds
        
        if deviceToken == nil {
            print("⚠️ No device token received after 5 seconds")
            print("⚠️ Possible issues:")
            print("   - Running on iOS Simulator (APNs doesn't work)")
            print("   - Provisioning profile doesn't include Push Notifications")
            print("   - Network connectivity issues")
            print("   - Apple's APNs servers are slow/down")
        } else {
            print("✅ Device token received within 5 seconds!")
        }
    }
    
    /// Handle successful device token registration
    func didRegisterForRemoteNotifications(with deviceToken: Data) {
        let tokenString = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        
        Task { @MainActor in
            self.deviceToken = tokenString
            print("✅ Device token received: \(tokenString)")
            
            // Register with backend if user is authenticated
            if apiManager.isAuthenticated {
                await registerDeviceTokenWithBackend(tokenString)
            }
        }
    }
    
    /// Handle device token registration failure
    func didFailToRegisterForRemoteNotifications(with error: Error) {
        print("❌ Failed to register for remote notifications: \(error)")
        Task { @MainActor in
            self.isRegistered = false
        }
    }
    
    /// Register device token with backend API
    private func registerDeviceTokenWithBackend(_ token: String) async {
        do {
            let request = DeviceTokenRegistrationRequest(
                deviceToken: token,
                deviceType: "ios"
            )
            
            let response = try await apiManager.registerDeviceToken(request)
            
            await MainActor.run {
                self.isRegistered = true
                print("✅ Device token registered with backend: \(response.id)")
            }
        } catch {
            print("❌ Failed to register device token with backend: \(error)")
            await MainActor.run {
                self.isRegistered = false
            }
        }
    }
    
    // MARK: - Notification Handling
    
    /// Handle incoming push notification when app is in foreground
    nonisolated func handleForegroundNotification(_ notification: UNNotification) -> UNNotificationPresentationOptions {
        let userInfo = notification.request.content.userInfo
        
        print("📱 Received foreground notification: \(userInfo)")
        
        // Parse notification data
        if let notificationData = parseNotificationData(userInfo) {
            handleNotificationData(notificationData)
        }
        
        // Show notification even when app is in foreground
        return [.banner, .sound, .badge]
    }
    
    /// Handle notification tap (when user taps notification)
    nonisolated func handleNotificationTap(_ response: UNNotificationResponse) {
        let userInfo = response.notification.request.content.userInfo
        
        print("👆 User tapped notification: \(userInfo)")
        
        // Parse notification data and handle deep linking
        if let notificationData = parseNotificationData(userInfo) {
            handleNotificationTap(notificationData)
        }
    }
    
    // MARK: - Notification Data Processing
    
    private nonisolated func parseNotificationData(_ userInfo: [AnyHashable: Any]) -> NotificationData? {
        guard let type = userInfo["type"] as? String else {
            print("❌ No notification type found")
            return nil
        }
        
        switch type {
        case "appointment_booked":
            return parseAppointmentBookedNotification(userInfo)
        default:
            print("❌ Unknown notification type: \(type)")
            return nil
        }
    }
    
    private nonisolated func parseAppointmentBookedNotification(_ userInfo: [AnyHashable: Any]) -> NotificationData? {
        guard let appointmentId = userInfo["appointment_id"] as? String,
              let petOwnerName = userInfo["pet_owner_name"] as? String,
              let petName = userInfo["pet_name"] as? String,
              let appointmentTime = userInfo["appointment_time"] as? String else {
            print("❌ Missing required appointment notification data")
            return nil
        }
        
        return NotificationData(
            type: .appointmentBooked,
            appointmentId: appointmentId,
            petOwnerName: petOwnerName,
            petName: petName,
            appointmentTime: appointmentTime
        )
    }
    
    private nonisolated func handleNotificationData(_ data: NotificationData) {
        switch data.type {
        case .appointmentBooked:
            // Update UI to show new appointment
            print("📅 New appointment booked: \(data.petName) for \(data.petOwnerName) at \(data.appointmentTime)")
            
            // Trigger dashboard refresh
            NotificationCenter.default.post(
                name: .appointmentBookedNotification,
                object: data
            )
        }
    }
    
    private nonisolated func handleNotificationTap(_ data: NotificationData) {
        switch data.type {
        case .appointmentBooked:
            // Navigate to appointment details or dashboard
            print("🔗 Navigating to appointment: \(data.appointmentId)")
            
            // Post navigation notification
            NotificationCenter.default.post(
                name: .navigateToAppointmentNotification,
                object: data.appointmentId
            )
        }
    }
    
    // MARK: - Public Methods
    
    /// Force request permissions (for testing - will only work if status is .notDetermined)
    func forceRequestPermissions() async -> Bool {
        print("🔔 Force requesting permissions...")
        return await requestPermissions()
    }
    
    /// Initialize push notifications for authenticated user
    func initializeForAuthenticatedUser() async {
        guard apiManager.isAuthenticated else {
            print("❌ User not authenticated, skipping push notification setup")
            return
        }
        
        print("🔔 Initializing push notifications for authenticated user")
        print("🔔 Current permission status: \(notificationPermissionStatus)")
        print("🔔 Current device token: \(deviceToken?.prefix(20) ?? "nil")")
        print("🔔 Is registered: \(isRegistered)")
        
        // Check if we already have permissions
        if notificationPermissionStatus == .authorized {
            // Register for remote notifications if we haven't already
            if deviceToken == nil {
                print("🔔 No device token yet, registering for remote notifications...")
                await registerForRemoteNotifications()
            } else if let token = deviceToken, !isRegistered {
                // Re-register with backend if needed
                print("🔔 Have device token but not registered, registering with backend...")
                await registerDeviceTokenWithBackend(token)
            } else {
                print("🔔 Already have device token and registered")
            }
        } else if notificationPermissionStatus == .notDetermined {
            // Request permissions
            print("🔔 Permissions not determined, requesting...")
            _ = await requestPermissions()
        } else {
            print("🔔 Permissions denied or other status: \(notificationPermissionStatus)")
        }
    }
    
    /// Unregister device token when user logs out
    func unregisterForLogout() async {
        guard let token = deviceToken else {
            print("ℹ️ No device token to unregister")
            return
        }
        
        do {
            try await apiManager.unregisterDeviceToken(token)
            
            await MainActor.run {
                self.isRegistered = false
                print("✅ Device token unregistered from backend")
            }
        } catch {
            print("❌ Failed to unregister device token: \(error)")
        }
    }
}

// MARK: - Models

struct NotificationData {
    let type: NotificationType
    let appointmentId: String
    let petOwnerName: String
    let petName: String
    let appointmentTime: String
}

enum NotificationType {
    case appointmentBooked
}

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

// MARK: - Notification Names

extension Notification.Name {
    static let appointmentBookedNotification = Notification.Name("appointmentBookedNotification")
    static let navigateToAppointmentNotification = Notification.Name("navigateToAppointmentNotification")
}

// MARK: - Debug Extensions

extension UNAuthorizationStatus {
    var debugDescription: String {
        switch self {
        case .notDetermined:
            return "notDetermined (can request permission)"
        case .denied:
            return "denied (user said no - need to go to Settings)"
        case .authorized:
            return "authorized (user said yes)"
        case .provisional:
            return "provisional (quiet notifications)"
        case .ephemeral:
            return "ephemeral (temporary)"
        @unknown default:
            return "unknown(\(rawValue))"
        }
    }
}

extension UNNotificationSetting {
    var debugDescription: String {
        switch self {
        case .notSupported:
            return "notSupported"
        case .disabled:
            return "disabled"
        case .enabled:
            return "enabled"
        @unknown default:
            return "unknown(\(rawValue))"
        }
    }
}
