import SwiftUI

struct SidebarMenu: View {
    @StateObject private var apiManager = APIManager.shared
    @State private var showingNotificationSettings = false
    @State private var showingConfigureSettings = false
    @State private var practiceName: String = "Loading..."
    let onNavigateToAppointments: () -> Void
    let onNavigateToPetOwners: () -> Void
    let onNavigateToScheduleEditing: () -> Void
    let onNavigateToFrontDesk: () -> Void
    let onClose: () -> Void
    
    // MARK: - Helper Methods
    
    private func loadPracticeName() async {
        guard apiManager.currentUser?.practiceId != nil else {
            await MainActor.run {
                self.practiceName = ""
            }
            return
        }
        
        do {
            // Use cached practice data or load from API
            if let practice = try await apiManager.getCurrentPractice() {
                await MainActor.run {
                    self.practiceName = practice.name
                    print("✅ Loaded practice name: \(practice.name)")
                }
            } else {
                await MainActor.run {
                    self.practiceName = ""
                }
            }
        } catch {
            await MainActor.run {
                self.practiceName = "Practice"
                print("❌ Failed to load practice name: \(error.localizedDescription)")
            }
        }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header with avatar and name
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    // Avatar circle
                    ZStack {
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 60, height: 60)
                        
                        if let user = apiManager.currentUser {
                            Text(String(user.fullName.prefix(1)))
                                .font(.title)
                                .fontWeight(.medium)
                                .foregroundColor(.white)
                        } else {
                            Image(systemName: "person.fill")
                                .font(.title2)
                                .foregroundColor(.white)
                        }
                    }
                    
                    Spacer()
                }
                
                // User name
                if let user = apiManager.currentUser {
                    Text(user.fullName)
                        .font(.title2)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                    
                    // Practice name (small text below user name)
                    if let practiceId = user.practiceId {
                        Text(practiceName)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .padding(.top, 2)
                    }
                }
            }
            .padding(.horizontal, 24)
            .padding(.top, 24)
            .padding(.bottom, 32)
            
            // Divider
            Rectangle()
                .fill(Color(.separator))
                .frame(height: 0.5)
                .padding(.horizontal, 24)
            
            // Menu items
            VStack(alignment: .leading, spacing: 0) {
                // Appointments
                MenuButton(
                    icon: "calendar",
                    title: "Appointments",
                    action: {
                        onNavigateToAppointments()
                        onClose()
                    }
                )
                
                // Pet Owners
                MenuButton(
                    icon: "heart.fill",
                    title: "Pet Owners",
                    action: {
                        onNavigateToPetOwners()
                        onClose()
                    }
                )
                
                // Edit Schedule
                MenuButton(
                    icon: "calendar.badge.plus",
                    title: "Work Schedule",
                    action: {
                        onNavigateToScheduleEditing()
                        onClose()
                    }
                )
                
                // Front Desk
                MenuButton(
                    icon: "phone.badge.waveform",
                    title: "Front Desk",
                    action: {
                        onNavigateToFrontDesk()
                        onClose()
                    }
                )
                
                // Notification Settings
                MenuButton(
                    icon: "bell",
                    title: "Notifications",
                    action: {
                        showingNotificationSettings = true
                        onClose()
                    }
                )
                
                // Configure Voice Agent
                MenuButton(
                    icon: "gear",
                    title: "Configure Voice Agent",
                    action: {
                        showingConfigureSettings = true
                        onClose()
                    }
                )
            }
            .padding(.top, 16)
            
            Spacer()
            
            // Logout button at bottom
            VStack(spacing: 0) {
                Rectangle()
                    .fill(Color(.separator))
                    .frame(height: 0.5)
                    .padding(.horizontal, 24)
                
                Button(action: {
                    apiManager.logout()
                }) {
                    HStack(spacing: 16) {
                        Image(systemName: "power")
                            .font(.title3)
                            .foregroundColor(.red)
                            .frame(width: 24, height: 24)
                        
                        Text("Logout")
                            .font(.body)
                            .fontWeight(.medium)
                            .foregroundColor(.red)
                        
                        Spacer()
                    }
                    .padding(.horizontal, 24)
                    .padding(.vertical, 16)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
            }
            .padding(.bottom, 24)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color(.systemBackground))
        .sheet(isPresented: $showingNotificationSettings) {
            NotificationSettingsView()
        }
        .sheet(isPresented: $showingConfigureSettings) {
            VoiceAgentConfigureView()
        }
        .task {
            await loadPracticeName()
        }
    }
}

struct MenuButton: View {
    let icon: String
    let title: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 16) {
                Image(systemName: icon)
                    .font(.title3)
                    .foregroundColor(.primary)
                    .frame(width: 24, height: 24)
                
                Text(title)
                    .font(.body)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                
                Spacer()
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 16)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    SidebarMenu(
        onNavigateToAppointments: {},
        onNavigateToPetOwners: {},
        onNavigateToScheduleEditing: {},
        onNavigateToFrontDesk: {},
        onClose: {}
    )
}
