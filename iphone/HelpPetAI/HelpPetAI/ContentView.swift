// MARK: - 21. ContentView.swift (Main App Entry Point)
import SwiftUI

enum MainViewSelection {
    case dashboard
    case petOwners
    case scheduleEditing
    case frontDesk
}

struct MainContainerView: View {
    @State private var showSidebar = false
    @State private var selectedView: MainViewSelection = .dashboard
    @State private var sidebarOffset: CGFloat = -UIScreen.main.bounds.width * 0.8
    @State private var overlayOpacity: Double = 0
    @State private var dragOffset: CGFloat = 0
    
    private let sidebarWidth = UIScreen.main.bounds.width * 0.8
    
    var body: some View {
        NavigationView {
            ZStack {
                // Main content
                Group {
                    switch selectedView {
                    case .dashboard:
                        DashboardView(onToggleSidebar: {
                            openSidebar()
                        })
                    case .petOwners:
                        PetOwnersView(
                            onNavigateToAppointments: {
                                selectedView = .dashboard
                            },
                            onToggleSidebar: {
                                openSidebar()
                            }
                        )
                    case .scheduleEditing:
                        ScheduleEditingView(onToggleSidebar: {
                            openSidebar()
                        })
                    case .frontDesk:
                        FrontDeskView(onToggleSidebar: {
                            openSidebar()
                        })
                    }
                }
                .offset(x: (showSidebar ? sidebarWidth : 0) + dragOffset)
                .scaleEffect(
                    x: showSidebar ? 0.9 : 1.0,
                    y: 1.0,
                    anchor: .topLeading
                )
                .gesture(mainContentGesture)
                
                // Dimming overlay
                if showSidebar {
                    Color.black
                        .opacity(overlayOpacity)
                        .ignoresSafeArea()
                        .onTapGesture {
                            closeSidebar()
                        }
                        .gesture(overlayGesture)
                }
                
                // Sidebar
                HStack {
                    SidebarMenu(
                        onNavigateToAppointments: {
                            selectedView = .dashboard
                        },
                        onNavigateToPetOwners: {
                            selectedView = .petOwners
                        },
                        onNavigateToScheduleEditing: {
                            selectedView = .scheduleEditing
                        },
                        onNavigateToFrontDesk: {
                            selectedView = .frontDesk
                        },
                        onClose: closeSidebar
                    )
                    .frame(width: sidebarWidth)
                    .offset(x: sidebarOffset + dragOffset)
                    .gesture(sidebarGesture)
                    
                    Spacer()
                }
            }
            .ignoresSafeArea(.container, edges: .leading)
        }
    }
    
    // MARK: - Gesture Handlers
    
    private var mainContentGesture: some Gesture {
        DragGesture()
            .onChanged { gesture in
                handleDragChanged(gesture)
            }
            .onEnded { gesture in
                handleDragEnded(gesture)
            }
    }
    
    private var sidebarGesture: some Gesture {
        DragGesture()
            .onChanged { gesture in
                handleDragChanged(gesture)
            }
            .onEnded { gesture in
                handleDragEnded(gesture)
            }
    }
    
    private var overlayGesture: some Gesture {
        DragGesture()
            .onChanged { gesture in
                handleDragChanged(gesture)
            }
            .onEnded { gesture in
                handleDragEnded(gesture)
            }
    }
    
    private func handleDragChanged(_ gesture: DragGesture.Value) {
        let translation = gesture.translation.width
        
        if showSidebar {
            // Sidebar is open - handle left swipe to close
            if translation < 0 {
                dragOffset = max(translation, -sidebarWidth)
                overlayOpacity = max(0, 0.3 + Double(translation / sidebarWidth) * 0.3)
            }
        } else {
            // Sidebar is closed - handle right swipe to open
            if translation > 0 {
                dragOffset = min(translation, sidebarWidth)
                overlayOpacity = min(0.3, Double(translation / sidebarWidth) * 0.3)
            }
        }
    }
    
    private func handleDragEnded(_ gesture: DragGesture.Value) {
        let translation = gesture.translation.width
        let threshold: CGFloat = 50
        
        withAnimation(.easeOut(duration: 0.3)) {
            if showSidebar {
                // Sidebar is open
                if translation < -threshold {
                    // Close sidebar
                    closeSidebar()
                } else {
                    // Stay open
                    dragOffset = 0
                    overlayOpacity = 0.3
                }
            } else {
                // Sidebar is closed
                if translation > threshold {
                    // Open sidebar
                    openSidebar()
                } else {
                    // Stay closed
                    dragOffset = 0
                    overlayOpacity = 0
                }
            }
        }
    }
    
    private func openSidebar() {
        withAnimation(.easeOut(duration: 0.3)) {
            showSidebar = true
            sidebarOffset = 0
            dragOffset = 0
            overlayOpacity = 0.3
        }
    }
    
    private func closeSidebar() {
        withAnimation(.easeOut(duration: 0.3)) {
            showSidebar = false
            sidebarOffset = -sidebarWidth
            dragOffset = 0
            overlayOpacity = 0
        }
    }
}

struct ContentView: View {
    @StateObject private var apiManager = APIManager.shared
    @StateObject private var pushNotificationService = PushNotificationService.shared
    
    var body: some View {
        Group {
            if apiManager.isAuthenticated {
                AuthenticatedContentView()
                    .onAppear {
                        print("🔐 ContentView: User is authenticated, showing AuthenticatedContentView")
                    }
                    .task {
                        // Initialize push notifications after successful login
                        await pushNotificationService.initializeForAuthenticatedUser()
                    }
            } else {
                LoginView()
                    .onAppear {
                        print("🔐 ContentView: User is NOT authenticated, showing LoginView")
                    }
                    .task {
                        // Unregister push notifications on logout
                        await pushNotificationService.unregisterForLogout()
                    }
            }
        }
        .animation(.easeInOut(duration: 0.3), value: apiManager.isAuthenticated)
    }
}

struct AuthenticatedContentView: View {
    @StateObject private var apiManager = APIManager.shared
    @State private var showingPracticeSelection = false
    
    var body: some View {
        Group {
            if let currentUser = apiManager.currentUser {
                if currentUser.practiceId == nil {
                    // User is authenticated but has no practice association
                    PracticeSelectionView()
                        .navigationBarHidden(true)
                        .onAppear {
                            print("🏥 AuthenticatedContentView: Showing PracticeSelectionView for user \(currentUser.username) (no practice)")
                        }
                } else {
                    // User has practice association, show main app
                    MainContainerView()
                        .onAppear {
                            print("🏥 AuthenticatedContentView: Showing MainContainerView for user \(currentUser.username) (practice: \(currentUser.practiceId!))")
                        }
                }
            } else {
                // Still loading user data, show loading
                VStack {
                    ProgressView()
                    Text("Loading...")
                        .padding(.top, 8)
                }
                .onAppear {
                    print("🏥 AuthenticatedContentView: No currentUser, showing loading...")
                }
                .task {
                    // Fetch current user data to check practice association
                    await loadCurrentUser()
                }
            }
        }
    }
    
    private func loadCurrentUser() async {
        do {
            _ = try await apiManager.getCurrentUser()
            print("✅ User data loaded successfully")
        } catch {
            print("❌ Failed to load user data: \(error)")
            // If we can't load user data, APIManager will handle logout
        }
    }
}

#Preview {
    ContentView()
}