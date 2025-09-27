//
//  NotificationSettingsView.swift
//  HelpPetAI
//
//  TL;DR: Settings view for managing push notification preferences.
//
//  Features:
//  - Display current notification permission status
//  - Allow users to enable/disable push notifications
//  - Show device token registration status
//  - Link to system settings if permissions are denied
//  - Test notification functionality (debug mode)
//
//  Usage: Navigate to from settings menu or sidebar.
//

import SwiftUI
import UserNotifications

struct NotificationSettingsView: View {
    @StateObject private var pushService = PushNotificationService.shared
    @State private var showingSystemSettings = false
    
    var body: some View {
        NavigationView {
            List {
                Section(header: Text("Push Notifications")) {
                    HStack {
                        Image(systemName: notificationIcon)
                            .foregroundColor(notificationColor)
                            .frame(width: 24)
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Appointment Notifications")
                                .font(.headline)
                            Text(notificationStatusText)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        if pushService.notificationPermissionStatus == .notDetermined {
                            Button("Enable") {
                                Task {
                                    await pushService.requestPermissions()
                                }
                            }
                            .buttonStyle(.borderedProminent)
                        } else if pushService.notificationPermissionStatus == .denied {
                            Button("Settings") {
                                openSystemSettings()
                            }
                            .buttonStyle(.bordered)
                        }
                    }
                    .padding(.vertical, 4)
                }
                
                if pushService.notificationPermissionStatus == .authorized {
                    Section(header: Text("Registration Status")) {
                        HStack {
                            Image(systemName: registrationIcon)
                                .foregroundColor(registrationColor)
                                .frame(width: 24)
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Device Registration")
                                    .font(.headline)
                                Text(registrationStatusText)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            
                            Spacer()
                            
                            if !pushService.isRegistered && pushService.deviceToken != nil {
                                Button("Retry") {
                                    Task {
                                        await pushService.initializeForAuthenticatedUser()
                                    }
                                }
                                .buttonStyle(.bordered)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                    
                    Section(header: Text("Device Information")) {
                        if let deviceToken = pushService.deviceToken {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Device Token")
                                    .font(.headline)
                                Text(deviceToken)
                                    .font(.system(.caption, design: .monospaced))
                                    .foregroundColor(.secondary)
                                    .lineLimit(nil)
                                    .textSelection(.enabled)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
                                
                #if DEBUG
                Section(header: Text("Debug")) {
                    Button("Test Local Notification") {
                        testLocalNotification()
                    }
                    .foregroundColor(.blue)
                    
                    Button("Force Request Permissions") {
                        Task {
                            let result = await pushService.forceRequestPermissions()
                            print("🔔 Force permission result: \(result)")
                        }
                    }
                    .foregroundColor(.orange)
                    
                    Button("Check Permission Status") {
                        pushService.checkNotificationSettings()
                    }
                    .foregroundColor(.purple)
                }
                #endif
            }
            .navigationTitle("Notifications")
            .navigationBarTitleDisplayMode(.large)
        }
    }
    
    // MARK: - Computed Properties
    
    private var notificationIcon: String {
        switch pushService.notificationPermissionStatus {
        case .authorized:
            return "bell.fill"
        case .denied:
            return "bell.slash.fill"
        case .notDetermined:
            return "bell"
        case .provisional:
            return "bell.badge"
        case .ephemeral:
            return "bell.badge"
        @unknown default:
            return "bell"
        }
    }
    
    private var notificationColor: Color {
        switch pushService.notificationPermissionStatus {
        case .authorized:
            return .green
        case .denied:
            return .red
        case .notDetermined:
            return .orange
        default:
            return .gray
        }
    }
    
    private var notificationStatusText: String {
        switch pushService.notificationPermissionStatus {
        case .authorized:
            return "Enabled - You'll receive appointment notifications"
        case .denied:
            return "Disabled - Tap Settings to enable in System Preferences"
        case .notDetermined:
            return "Not configured - Tap Enable to allow notifications"
        case .provisional:
            return "Provisional - Limited notifications enabled"
        case .ephemeral:
            return "Temporary - Limited time notifications"
        @unknown default:
            return "Unknown status"
        }
    }
    
    private var registrationIcon: String {
        if pushService.isRegistered {
            return "checkmark.circle.fill"
        } else if pushService.deviceToken != nil {
            return "exclamationmark.triangle.fill"
        } else {
            return "xmark.circle.fill"
        }
    }
    
    private var registrationColor: Color {
        if pushService.isRegistered {
            return .green
        } else if pushService.deviceToken != nil {
            return .orange
        } else {
            return .red
        }
    }
    
    private var registrationStatusText: String {
        if pushService.isRegistered {
            return "Successfully registered with HelpPet.ai servers"
        } else if pushService.deviceToken != nil {
            return "Device token received, but not registered with server"
        } else {
            return "No device token received from Apple"
        }
    }
    
    // MARK: - Actions
    
    private func openSystemSettings() {
        if let settingsUrl = URL(string: UIApplication.openSettingsURLString) {
            UIApplication.shared.open(settingsUrl)
        }
    }
    
    #if DEBUG
    private func testLocalNotification() {
        let content = UNMutableNotificationContent()
        content.title = "Test Notification"
        content.body = "New appointment booked for Fluffy with Dr. Smith at 2:00 PM"
        content.sound = .default
        content.userInfo = [
            "type": "appointment_booked",
            "appointment_id": "test-123",
            "pet_owner_name": "John Doe",
            "pet_name": "Fluffy",
            "appointment_time": "2:00 PM"
        ]
        
        let request = UNNotificationRequest(
            identifier: UUID().uuidString,
            content: content,
            trigger: UNTimeIntervalNotificationTrigger(timeInterval: 2, repeats: false)
        )
        
        UNUserNotificationCenter.current().add(request) { error in
            if let error = error {
                print("❌ Failed to schedule test notification: \(error)")
            } else {
                print("✅ Test notification scheduled")
            }
        }
    }
    #endif
}

// MARK: - Notification Type Row

struct NotificationTypeRow: View {
    let title: String
    let description: String
    let icon: String
    let isEnabled: Bool
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(isEnabled ? .blue : .gray)
                .frame(width: 24)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.headline)
                    .foregroundColor(isEnabled ? .primary : .secondary)
                
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Image(systemName: isEnabled ? "checkmark.circle.fill" : "circle")
                .foregroundColor(isEnabled ? .green : .gray)
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    NotificationSettingsView()
}
