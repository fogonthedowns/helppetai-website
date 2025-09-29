import SwiftUI

struct FinalView: View {
    let userName: String
    let practiceId: String
    let email: String
    let password: String
    let selectedPracticeType: String
    let selectedCallVolume: String
    let selectedRole: String
    let selectedMotivations: Set<String>
    
    @Environment(\.colorScheme) var colorScheme
    @Environment(\.dismiss) private var dismiss
    @State private var showingWelcomeView = false
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Background gradient (adaptive for dark mode)
                LinearGradient(
                    gradient: Gradient(colors: colorScheme == .dark ? [
                        Color(red: 0.1, green: 0.1, blue: 0.15),
                        Color(red: 0.15, green: 0.15, blue: 0.2)
                    ] : [
                        Color(red: 0.85, green: 0.95, blue: 1.0),
                        Color(red: 0.95, green: 0.98, blue: 1.0)
                    ]),
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
                
                VStack(spacing: 0) {
                    // Custom Back Button
                    HStack {
                        Button(action: {
                            dismiss()
                        }) {
                            HStack(spacing: 8) {
                                Image(systemName: "chevron.left")
                                    .font(.system(size: 16, weight: .medium))
                                    .foregroundColor(.primary)
                            }
                        }
                        .padding(.leading, 20)
                        
                        Spacer()
                    }
                    .padding(.top, 10)
                    
                    // Progress Bar (completed)
                    HStack {
                        ForEach(0..<7) { index in
                            Rectangle()
                                .fill(Color.green)
                                .frame(height: 4)
                                .cornerRadius(2)
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 20)
                    
                    Spacer()
                    
                    // Main Content
                    VStack(spacing: 30) {
                        // Character Image (smaller)
                        Image("Welcome")
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(width: 160, height: 160)
                            .scaleEffect(1.0)
                        
                        // Title and Message
                        VStack(spacing: 16) {
                            Text("You're all set!")
                                .font(.system(size: 28, weight: .bold))
                                .foregroundColor(primaryTextColor)
                                .multilineTextAlignment(.center)
                            
                            Text("Check your email!")
                                .font(.system(size: 20, weight: .semibold))
                                .foregroundColor(primaryTextColor)
                                .multilineTextAlignment(.center)
                            
                            VStack(spacing: 8) {
                                Text("We sent a confirmation link to")
                                    .font(.system(size: 18, weight: .medium))
                                    .foregroundColor(secondaryTextColor)
                                    .multilineTextAlignment(.center)
                                
                                Text(email)
                                    .font(.system(size: 18, weight: .semibold))
                                    .foregroundColor(.green)
                                    .multilineTextAlignment(.center)
                            }
                            .padding(.horizontal, 40)
                        }
                    }
                    
                    Spacer()
                    
                    // Open Email App Button
                    VStack(spacing: 16) {
                        Button(action: {
                            openEmailApp()
                        }) {
                            HStack {
                                Image(systemName: "mail.fill")
                                    .font(.system(size: 18))
                                Text("Open Email App")
                                    .font(.system(size: 18, weight: .semibold))
                            }
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 56)
                            .background(
                                RoundedRectangle(cornerRadius: 28)
                                    .fill(
                                        LinearGradient(
                                            gradient: Gradient(colors: [
                                                Color.green,
                                                Color.green.opacity(0.8)
                                            ]),
                                            startPoint: .topLeading,
                                            endPoint: .bottomTrailing
                                        )
                                    )
                                    .shadow(
                                        color: Color.green.opacity(0.4),
                                        radius: 12,
                                        x: 0,
                                        y: 6
                                    )
                            )
                        }
                        .padding(.horizontal, 28)
                        
                        // Secondary action - Back to login
                        Button(action: {
                            // Navigate back to the very first screen (WelcomeView)
                            showingWelcomeView = true
                        }) {
                            Text("Back to Home")
                                .font(.system(size: 16, weight: .medium))
                                .foregroundColor(.green)
                        }
                        .padding(.bottom, 40)
                    }
                }
            }
        }
        .navigationBarHidden(true)
        .onTapGesture {
            // Dismiss keyboard when tapping outside of text fields
            UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
        }
        .fullScreenCover(isPresented: $showingWelcomeView) {
            WelcomeView()
        }
        .onAppear {
            // Add any entrance animations here if needed
            let successFeedback = UINotificationFeedbackGenerator()
            successFeedback.notificationOccurred(.success)
        }
    }
    
    // MARK: - Computed Properties
    private var primaryTextColor: Color {
        colorScheme == .dark ? Color.white : Color.black
    }
    
    private var secondaryTextColor: Color {
        colorScheme == .dark ? Color.gray : Color.gray
    }
    
    private var shadowColor: Color {
        colorScheme == .dark ? Color.black.opacity(0.3) : Color.black.opacity(0.15)
    }
    
    // MARK: - Email Functions
    private func openEmailApp() {
        // Try to open the Mail app
        if let mailURL = URL(string: "message://") {
            if UIApplication.shared.canOpenURL(mailURL) {
                UIApplication.shared.open(mailURL)
            } else {
                // Fallback to mailto if Mail app is not available
                if let mailtoURL = URL(string: "mailto:") {
                    UIApplication.shared.open(mailtoURL)
                }
            }
        }
        
        // Haptic feedback
        let impactFeedback = UIImpactFeedbackGenerator(style: .medium)
        impactFeedback.impactOccurred()
    }
}

#Preview {
    NavigationView {
        FinalView(
            userName: "John Doe",
            practiceId: "practice123",
            email: "john@example.com",
            password: "password123",
            selectedPracticeType: "solo",
            selectedCallVolume: "25-50",
            selectedRole: "owner",
            selectedMotivations: ["pets", "calls"]
        )
    }
}
