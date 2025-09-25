
// MARK: - 22. HelpPetAIApp.swift (App Entry Point)
import SwiftUI
import BackgroundTasks
import UserNotifications
import UIKit

@main
struct HelpPetAIApp: App {
    @StateObject private var pushNotificationService = PushNotificationService.shared
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    
    init() {
        // Initialize medical recording system for corruption prevention
        _ = MedicalRecordingManager.shared
        
        // Set up push notification delegate
        UNUserNotificationCenter.current().delegate = PushNotificationDelegate.shared
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .onReceive(NotificationCenter.default.publisher(for: UIApplication.didEnterBackgroundNotification)) { _ in
                    // Schedule background upload when app enters background
                    MedicalRecordingManager.shared.scheduleBackgroundUpload()
                }
                .onReceive(NotificationCenter.default.publisher(for: UIApplication.didBecomeActiveNotification)) { _ in
                    // Clear badge and check notification settings when app becomes active
                    UIApplication.shared.applicationIconBadgeNumber = 0
                    pushNotificationService.checkNotificationSettings()
                }
                .onReceive(NotificationCenter.default.publisher(for: .appointmentBookedNotification)) { notification in
                    // Handle appointment booked notification
                    if let notificationData = notification.object as? NotificationData {
                        print("📅 Received appointment booked notification: \(notificationData.petName)")
                        // Trigger dashboard refresh or show in-app notification
                    }
                }
                .task {
                    // Initialize push notifications for authenticated users
                    if APIManager.shared.isAuthenticated {
                        await pushNotificationService.initializeForAuthenticatedUser()
                    }
                }
        }
    }
}

// MARK: - Push Notification Delegate

class PushNotificationDelegate: NSObject, UNUserNotificationCenterDelegate {
    static let shared = PushNotificationDelegate()
    
    private override init() {
        super.init()
    }
    
    // Handle notification when app is in foreground
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        let options = PushNotificationService.shared.handleForegroundNotification(notification)
        completionHandler(options)
    }
    
    // Handle notification tap
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        PushNotificationService.shared.handleNotificationTap(response)
        completionHandler()
    }
}

// MARK: - App Delegate for Remote Notifications

class AppDelegate: NSObject, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {
        print("📱 AppDelegate: App finished launching")
        print("📱 AppDelegate: Bundle ID: \(Bundle.main.bundleIdentifier ?? "unknown")")
        print("📱 AppDelegate: App version: \(Bundle.main.infoDictionary?["CFBundleShortVersionString"] ?? "unknown")")
        return true
    }
    
    func application(
        _ application: UIApplication,
        didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
    ) {
        print("📱 AppDelegate: ✅ SUCCESS! Received device token from APNs")
        print("📱 AppDelegate: Token length: \(deviceToken.count) bytes")
        PushNotificationService.shared.didRegisterForRemoteNotifications(with: deviceToken)
    }
    
    func application(
        _ application: UIApplication,
        didFailToRegisterForRemoteNotificationsWithError error: Error
    ) {
        print("❌ AppDelegate: Failed to register for remote notifications")
        print("❌ AppDelegate: Error: \(error)")
        print("❌ AppDelegate: Error domain: \(error._domain)")
        print("❌ AppDelegate: Error code: \(error._code)")
        PushNotificationService.shared.didFailToRegisterForRemoteNotifications(with: error)
    }
}
