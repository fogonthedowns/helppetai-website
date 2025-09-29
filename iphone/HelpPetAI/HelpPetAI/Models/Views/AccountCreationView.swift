import SwiftUI

struct AccountCreationView: View {
    let userName: String
    let practiceId: String
    let selectedPracticeType: String
    let selectedCallVolume: String
    let selectedRole: String
    let selectedMotivations: Set<String>
    
    @State private var displayedText = ""
    @State private var showFields = false
    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var showContinueButton = false
    @State private var isCreatingAccount = false
    @State private var showingFinalView = false
    @State private var isTyping = false
    @State private var isPasswordVisible = false
    @State private var isConfirmPasswordVisible = false
    @Environment(\.colorScheme) var colorScheme
    @Environment(\.dismiss) private var dismiss
    
    private let fullText = "Let's Sign in with your work email."
    private let typingSpeed: Double = 0.015
    
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
                    
                    // Progress Bar (almost complete)
                    HStack {
                                ForEach(0..<7) { index in
                                    Rectangle()
                                        .fill(index < 6 ? Color.green : Color.gray.opacity(0.3))
                                .frame(height: 4)
                                .cornerRadius(2)
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 20)
                    
                    Spacer()
                    
                    // Character and Dialog
                    VStack(spacing: 32) {
                        // Dialog box with character (centered)
                        VStack(spacing: 20) {
                            // Speech bubble (centered with downward tail)
                            ZStack {
                                // Complete speech bubble with attached tail pointing down
                                Path { path in
                                    let bubbleWidth: CGFloat = 280
                                    let bubbleHeight: CGFloat = 60
                                    let cornerRadius: CGFloat = 8
                                    let tailWidth: CGFloat = 16
                                    let tailHeight: CGFloat = 12
                                    
                                    // Start from top-left corner
                                    path.move(to: CGPoint(x: cornerRadius, y: 0))
                                    
                                    // Top edge
                                    path.addLine(to: CGPoint(x: bubbleWidth - cornerRadius, y: 0))
                                    path.addQuadCurve(to: CGPoint(x: bubbleWidth, y: cornerRadius), 
                                                     control: CGPoint(x: bubbleWidth, y: 0))
                                    
                                    // Right edge
                                    path.addLine(to: CGPoint(x: bubbleWidth, y: bubbleHeight - cornerRadius))
                                    path.addQuadCurve(to: CGPoint(x: bubbleWidth - cornerRadius, y: bubbleHeight), 
                                                     control: CGPoint(x: bubbleWidth, y: bubbleHeight))
                                    
                                    // Bottom edge to tail start
                                    path.addLine(to: CGPoint(x: (bubbleWidth / 2) + (tailWidth / 2), y: bubbleHeight))
                                    
                                    // Tail pointing down
                                    path.addLine(to: CGPoint(x: bubbleWidth / 2, y: bubbleHeight + tailHeight))
                                    path.addLine(to: CGPoint(x: (bubbleWidth / 2) - (tailWidth / 2), y: bubbleHeight))
                                    
                                    // Continue bottom edge
                                    path.addLine(to: CGPoint(x: cornerRadius, y: bubbleHeight))
                                    path.addQuadCurve(to: CGPoint(x: 0, y: bubbleHeight - cornerRadius), 
                                                     control: CGPoint(x: 0, y: bubbleHeight))
                                    
                                    // Left edge
                                    path.addLine(to: CGPoint(x: 0, y: cornerRadius))
                                    path.addQuadCurve(to: CGPoint(x: cornerRadius, y: 0), 
                                                     control: CGPoint(x: 0, y: 0))
                                    
                                    path.closeSubpath()
                                }
                                .fill(speechBubbleBackground)
                                .stroke(speechBubbleBorder, lineWidth: 1)
                                .frame(width: 280, height: 72) // Height includes tail

                                // Animated text positioned in the bubble
                                Text(displayedText)
                                    .font(.system(size: 16, weight: .medium))
                                    .foregroundColor(primaryTextColor)
                                    .multilineTextAlignment(.center)
                                    .padding(.horizontal, 16)
                                    .padding(.vertical, 10)
                                    .frame(width: 260, height: 60)
                                    .offset(y: -6) // Offset up to center in bubble part only
                            }

                            // Character (centered below speech bubble)
                            Image("OnBoarding")
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(width: 120, height: 120)
                                .shadow(
                                    color: shadowColor,
                                    radius: 15,
                                    x: 0,
                                    y: 8
                                )
                        }
                        .padding(.horizontal, 20)
                        
                        // Account Creation Fields (show after typing is complete)
                        if showFields {
                            VStack(spacing: 16) {
                                // Email
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("Email Address")
                                        .font(.system(size: 14, weight: .medium))
                                        .foregroundColor(secondaryTextColor)
                                        .padding(.leading, 4)
                                    
                                    TextField("Enter your email", text: $email)
                                        .font(.system(size: 16, weight: .medium))
                                        .foregroundColor(primaryTextColor)
                                        .keyboardType(.emailAddress)
                                        .autocapitalization(.none)
                                        .padding(.horizontal, 20)
                                        .padding(.vertical, 16)
                                        .background(
                                            RoundedRectangle(cornerRadius: 12)
                                                .fill(colorScheme == .dark ? Color(red: 0.2, green: 0.2, blue: 0.25) : Color.white)
                                                .shadow(
                                                    color: Color.black.opacity(colorScheme == .dark ? 0.3 : 0.1),
                                                    radius: 4,
                                                    x: 0,
                                                    y: 2
                                                )
                                        )
                                        .onChange(of: email) { _ in
                                            updateContinueButton()
                                        }
                                }
                                
                                // Password
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("Password")
                                        .font(.system(size: 14, weight: .medium))
                                        .foregroundColor(secondaryTextColor)
                                        .padding(.leading, 4)
                                    
                                    HStack {
                                        if isPasswordVisible {
                                            TextField("Create a password", text: $password)
                                                .font(.system(size: 16, weight: .medium))
                                                .foregroundColor(primaryTextColor)
                                        } else {
                                            SecureField("Create a password", text: $password)
                                                .font(.system(size: 16, weight: .medium))
                                                .foregroundColor(primaryTextColor)
                                        }
                                        
                                        Button(action: {
                                            isPasswordVisible.toggle()
                                        }) {
                                            Image(systemName: isPasswordVisible ? "eye.slash" : "eye")
                                                .foregroundColor(.gray)
                                                .font(.system(size: 16))
                                        }
                                    }
                                    .padding(.horizontal, 20)
                                    .padding(.vertical, 16)
                                    .background(
                                        RoundedRectangle(cornerRadius: 12)
                                            .fill(colorScheme == .dark ? Color(red: 0.2, green: 0.2, blue: 0.25) : Color.white)
                                            .shadow(
                                                color: Color.black.opacity(colorScheme == .dark ? 0.3 : 0.1),
                                                radius: 4,
                                                x: 0,
                                                y: 2
                                            )
                                    )
                                    .onChange(of: password) { _ in
                                        updateContinueButton()
                                    }
                                }
                                
                                // Confirm Password
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("Confirm Password")
                                        .font(.system(size: 14, weight: .medium))
                                        .foregroundColor(secondaryTextColor)
                                        .padding(.leading, 4)
                                    
                                    HStack {
                                        if isConfirmPasswordVisible {
                                            TextField("Confirm your password", text: $confirmPassword)
                                                .font(.system(size: 16, weight: .medium))
                                                .foregroundColor(primaryTextColor)
                                        } else {
                                            SecureField("Confirm your password", text: $confirmPassword)
                                                .font(.system(size: 16, weight: .medium))
                                                .foregroundColor(primaryTextColor)
                                        }
                                        
                                        Button(action: {
                                            isConfirmPasswordVisible.toggle()
                                        }) {
                                            Image(systemName: isConfirmPasswordVisible ? "eye.slash" : "eye")
                                                .foregroundColor(.gray)
                                                .font(.system(size: 16))
                                        }
                                    }
                                    .padding(.horizontal, 20)
                                    .padding(.vertical, 16)
                                    .background(
                                        RoundedRectangle(cornerRadius: 12)
                                            .fill(colorScheme == .dark ? Color(red: 0.2, green: 0.2, blue: 0.25) : Color.white)
                                            .shadow(
                                                color: passwordsMatch ? Color.black.opacity(colorScheme == .dark ? 0.3 : 0.1) : Color.red.opacity(0.2),
                                                radius: 4,
                                                x: 0,
                                                y: 2
                                            )
                                            .overlay(
                                                RoundedRectangle(cornerRadius: 12)
                                                    .stroke(
                                                        passwordsMatch ? Color.clear : Color.red.opacity(0.5),
                                                        lineWidth: 1
                                                    )
                                            )
                                    )
                                    .onChange(of: confirmPassword) { _ in
                                        updateContinueButton()
                                    }
                                }
                                
                                // Password match indicator
                                if !confirmPassword.isEmpty && !passwordsMatch {
                                    Text("Passwords don't match")
                                        .font(.system(size: 12, weight: .medium))
                                        .foregroundColor(.red)
                                        .padding(.leading, 4)
                                }
                            }
                            .padding(.horizontal, 28)
                            .transition(.opacity.combined(with: .scale))
                        }
                    }
                    
                    Spacer()
                    
                    // Continue Button
                    if showContinueButton {
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
                                    Text("Sign In with Email")
                                        .font(.system(size: 18, weight: .semibold))
                                        .foregroundColor(.white)
                                }
                            }
                            .frame(maxWidth: .infinity)
                            .frame(height: 56)
                            .background(
                                RoundedRectangle(cornerRadius: 28)
                                    .fill(Color.green)
                                    .shadow(
                                        color: Color.green.opacity(0.3),
                                        radius: 8,
                                        x: 0,
                                        y: 4
                                    )
                            )
                        }
                        .disabled(isCreatingAccount)
                        .padding(.horizontal, 28)
                        .padding(.bottom, 40)
                        .transition(.opacity.combined(with: .move(edge: .bottom)))
                    }
                }
            }
        }
        .navigationBarHidden(true)
        .onTapGesture {
            // Dismiss keyboard when tapping outside of text fields
            UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
        }
        .fullScreenCover(isPresented: $showingFinalView) {
            FinalView(
                userName: userName,
                practiceId: practiceId,
                email: email,
                password: password,
                selectedPracticeType: selectedPracticeType,
                selectedCallVolume: selectedCallVolume,
                selectedRole: selectedRole,
                selectedMotivations: selectedMotivations
            )
        }
        .onAppear {
            startTypingAnimation()
        }
    }
    
    // MARK: - Computed Properties
    private var speechBubbleBackground: Color {
        colorScheme == .dark ? Color(red: 0.15, green: 0.15, blue: 0.15) : Color.white
    }
    
    private var speechBubbleBorder: Color {
        colorScheme == .dark ? Color(red: 0.3, green: 0.3, blue: 0.3) : Color(red: 0.9, green: 0.9, blue: 0.9)
    }
    
    private var primaryTextColor: Color {
        colorScheme == .dark ? Color.white : Color.black
    }
    
    private var secondaryTextColor: Color {
        colorScheme == .dark ? Color.gray : Color.gray
    }
    
    private var shadowColor: Color {
        colorScheme == .dark ? Color.black.opacity(0.3) : Color.black.opacity(0.15)
    }
    
    private var passwordsMatch: Bool {
        confirmPassword.isEmpty || password == confirmPassword
    }
    
    private var isValidEmail: Bool {
        email.contains("@") && email.contains(".")
    }
    
    // MARK: - Animation Methods
    private func startTypingAnimation() {
        displayedText = ""
        isTyping = true
        
        for (index, character) in fullText.enumerated() {
            DispatchQueue.main.asyncAfter(deadline: .now() + Double(index) * typingSpeed) {
                displayedText += String(character)
                
                // Haptic feedback for each character
                let lightFeedback = UIImpactFeedbackGenerator(style: .light)
                lightFeedback.impactOccurred()
            }
            
            // When typing is complete
            if index == fullText.count - 1 {
                DispatchQueue.main.asyncAfter(deadline: .now() + Double(index) * typingSpeed + 0.2) {
                    isTyping = false
                    withAnimation(.easeInOut(duration: 0.6)) {
                        showFields = true
                    }
                }
            }
        }
    }
    
    private func updateContinueButton() {
        let shouldShow = isValidEmail && 
                        password.count >= 6 && 
                        passwordsMatch && 
                        !confirmPassword.isEmpty
        
        if shouldShow != showContinueButton {
            withAnimation(.easeInOut(duration: 0.3)) {
                showContinueButton = shouldShow
            }
        }
    }
    
    // MARK: - User Creation
    private func createUserAccount() {
        isCreatingAccount = true
        
        Task {
            do {
                // Create survey data (practice_id is separate top-level field)
                let surveyData: [String: Any] = [
                    "practice_type": selectedPracticeType,
                    "call_volume": selectedCallVolume,
                    "role": selectedRole,
                    "motivations": Array(selectedMotivations)
                ]
                
                let success = await APIManager.shared.signUpWithSurvey(
                    username: email, // Use email as username as requested
                    password: password,
                    email: email,
                    fullName: userName,
                    role: "VET_STAFF",
                    practiceId: practiceId,
                    survey: surveyData
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
                        
                        // Navigate to final "You're all set!" screen
                        showingFinalView = true
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
        AccountCreationView(
            userName: "John Doe",
            practiceId: "practice123",
            selectedPracticeType: "solo",
            selectedCallVolume: "25-50",
            selectedRole: "owner",
            selectedMotivations: ["pets", "calls"]
        )
    }
}
