import SwiftUI

struct FinalView: View {
    let userName: String
    let email: String
    let password: String
    let selectedPracticeType: String
    let selectedCallVolume: String
    let selectedRole: String
    let selectedMotivations: Set<String>
    
    @State private var isCreatingAccount = false
    @State private var accountCreated = false
    @State private var showingPracticeSelection = false
    @Environment(\.colorScheme) var colorScheme
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Background gradient (same as previous screens)
                LinearGradient(
                    gradient: Gradient(colors: [
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
                        ForEach(0..<6) { index in
                            Rectangle()
                                .fill(Color.green)
                                .frame(height: 4)
                                .cornerRadius(2)
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 20)
                    
                    Spacer()
                    
                    // Centered Done Image
                    VStack(spacing: 40) {
                        Image("done")
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(width: 200, height: 200)
                            .shadow(
                                color: shadowColor,
                                radius: 20,
                                x: 0,
                                y: 10
                            )
                            .scaleEffect(1.0)
                            .animation(.easeInOut(duration: 0.8), value: 1.0)
                        
                        // Success message
                        VStack(spacing: 16) {
                            Text("You're all set, \(userName.components(separatedBy: " ").first ?? "")!")
                                .font(.system(size: 28, weight: .bold))
                                .foregroundColor(primaryTextColor)
                                .multilineTextAlignment(.center)
                            
                            Text("Your AI Front Desk Agent is ready to transform your practice!")
                                .font(.system(size: 18, weight: .medium))
                                .foregroundColor(secondaryTextColor)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal, 40)
                        }
                    }
                    
                    Spacer()
                    
                    // Continue Button
                    VStack(spacing: 16) {
                        Button(action: {
                            createUserAccount()
                        }) {
                            HStack {
                                if isCreatingAccount {
                                    ProgressView()
                                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                        .scaleEffect(0.8)
                                    Text("Creating Account...")
                                        .font(.system(size: 18, weight: .semibold))
                                        .foregroundColor(.white)
                                } else {
                                    Text("Continue")
                                        .font(.system(size: 18, weight: .semibold))
                                        .foregroundColor(.white)
                                }
                            }
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
                        .disabled(isCreatingAccount)
                        .padding(.horizontal, 28)
                        .padding(.bottom, 40)
                    }
                }
            }
        }
        .navigationBarHidden(true)
        .fullScreenCover(isPresented: $showingPracticeSelection) {
            PracticeSelectionView()
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
    
    // MARK: - User Creation
    private func createUserAccount() {
        isCreatingAccount = true
        
        Task {
            do {
                let success = await APIManager.shared.signUp(
                    username: email, // Use email as username as requested
                    password: password,
                    email: email,
                    fullName: userName,
                    role: "VET_STAFF"
                )
                
                await MainActor.run {
                    isCreatingAccount = false
                    if success {
                        print("✅ Sign up successful!")
                        print("User created successfully:")
                        print("Email: \(email)")
                        print("Name: \(userName)")
                        print("Practice Type: \(selectedPracticeType)")
                        print("Call Volume: \(selectedCallVolume)")
                        print("Role: \(selectedRole)")
                        print("Motivations: \(selectedMotivations)")
                        
                        // Success haptic feedback
                        let successFeedback = UINotificationFeedbackGenerator()
                        successFeedback.notificationOccurred(.success)
                        
                        // Navigate to practice selection (same as old SignUpView)
                        showingPracticeSelection = true
                    } else {
                        print("❌ Sign up failed")
                        // Handle error - could show alert
                    }
                }
            } catch {
                await MainActor.run {
                    isCreatingAccount = false
                    print("❌ Sign up error: \(error)")
                    // Handle error - could show alert
                }
            }
        }
    }
}

#Preview {
    NavigationView {
        FinalView(
            userName: "John Doe",
            email: "john@example.com",
            password: "password123",
            selectedPracticeType: "solo",
            selectedCallVolume: "25-50",
            selectedRole: "owner",
            selectedMotivations: ["pets", "calls"]
        )
    }
}
