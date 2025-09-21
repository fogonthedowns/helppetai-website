
// MARK: - 22. HelpPetAIApp.swift (App Entry Point)
import SwiftUI
import BackgroundTasks

@main
struct HelpPetAIApp: App {
    init() {
        // Initialize medical recording system for corruption prevention
        _ = MedicalRecordingManager.shared
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .onReceive(NotificationCenter.default.publisher(for: UIApplication.didEnterBackgroundNotification)) { _ in
                    // Schedule background upload when app enters background
                    MedicalRecordingManager.shared.scheduleBackgroundUpload()
                }
        }
    }
}
