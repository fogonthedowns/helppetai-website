// MARK: - Views/LoginView.swift
import SwiftUI

struct LoginView: View {
    @StateObject private var apiManager = APIManager.shared
    @State private var username = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var loginAttempted = false
    @State private var errorMessage = ""
    @State private var showError = false
    @State private var showingSignUp = false
    @Environment(\.dismiss) private var dismiss
    @Environment(\.colorScheme) var colorScheme
    
    // Color scheme variables (matching NameCollectionView)
    private var primaryTextColor: Color {
        colorScheme == .dark ? .white : .black
    }
    
    private var secondaryTextColor: Color {
        colorScheme == .dark ? .gray : Color(red: 0.4, green: 0.4, blue: 0.4)
    }
    
    private var speechBubbleBackground: Color {
        colorScheme == .dark ? Color(red: 0.2, green: 0.2, blue: 0.25) : .white
    }
    
    private var speechBubbleBorder: Color {
        colorScheme == .dark ? Color(red: 0.3, green: 0.3, blue: 0.35) : Color(red: 0.9, green: 0.9, blue: 0.9)
    }
    
    private var shadowColor: Color {
        colorScheme == .dark ? Color.black.opacity(0.6) : Color.black.opacity(0.15)
    }
    
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
                    // Custom Back Button (matching NameCollectionView)
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

                                // Text positioned in the bubble
                                Text("Welcome back! Please sign in.")
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
                        
                        // Login Form (matching NameCollectionView field style)
                        VStack(spacing: 16) {
                            // Username Field
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Username")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(secondaryTextColor)
                                    .padding(.leading, 4)
                                
                                TextField("Enter your username", text: $username)
                                    .font(.system(size: 16, weight: .medium))
                                    .foregroundColor(primaryTextColor)
                                    .autocorrectionDisabled(true)
                                    .autocapitalization(.none)
                                    .textContentType(.username)
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
                            }
                            
                            // Password Field
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Password")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(secondaryTextColor)
                                    .padding(.leading, 4)
                                
                                SecureField("Enter your password", text: $password)
                                    .font(.system(size: 16, weight: .medium))
                                    .foregroundColor(primaryTextColor)
                                    .textContentType(.password)
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
                                    .onSubmit {
                                        // Login when user presses return on password field
                                        if !username.isEmpty && !password.isEmpty && !isLoading {
                                            login()
                                        }
                                    }
                            }
                        }
                        .padding(.horizontal, 28)
                    }
                    
                    Spacer()
                    
                    // Sign In Button (matching NameCollectionView continue button style)
                    VStack(spacing: 16) {
                        Button(action: login) {
                            HStack(spacing: 12) {
                                if isLoading {
                                    ProgressView()
                                        .scaleEffect(0.9)
                                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    Text("SIGNING IN...")
                                        .font(.system(size: 16, weight: .bold))
                                } else {
                                    Text("SIGN IN")
                                        .font(.system(size: 16, weight: .bold))
                                }
                            }
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 56)
                            .background(
                                RoundedRectangle(cornerRadius: 28)
                                    .fill(
                                        username.isEmpty || password.isEmpty || isLoading
                                        ? Color.gray.opacity(0.5)
                                        : Color.green
                                    )
                            )
                            .shadow(
                                color: username.isEmpty || password.isEmpty || isLoading
                                ? Color.clear
                                : Color.green.opacity(0.3),
                                radius: 8,
                                x: 0,
                                y: 4
                            )
                        }
                        .disabled(isLoading || username.isEmpty || password.isEmpty)
                        .padding(.horizontal, 28)
                        
                        // Sign Up Link
                        HStack {
                            Text("New to HelpPetAI?")
                                .font(.system(size: 16, weight: .medium))
                                .foregroundColor(secondaryTextColor)
                            
                            Button("Sign Up") {
                                showingSignUp = true
                            }
                            .font(.system(size: 16, weight: .bold))
                            .foregroundColor(.green)
                        }
                        .padding(.top, 8)
                    }
                    .padding(.bottom, 40)
                }
            }
        }
        .navigationBarHidden(true)
        .onTapGesture {
            // Dismiss keyboard when tapping outside of text fields
            UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
        }
        .alert("Login Error", isPresented: $showError) {
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
        .fullScreenCover(isPresented: $showingSignUp) {
            NavigationView {
                NameCollectionView()
            }
        }
    }
    
    private func login() {
        // Prevent multiple simultaneous login attempts
        guard !isLoading && !loginAttempted else { 
            print("🔐 Login already in progress, ignoring tap")
            return 
        }
        
        isLoading = true
        loginAttempted = true
        errorMessage = ""
        
        // Add haptic feedback for tactile response
        let impactFeedback = UIImpactFeedbackGenerator(style: .medium)
        impactFeedback.impactOccurred()
        
        Task {
            do {
                print("🔐 Starting login attempt for user: \(username)")
                _ = try await apiManager.login(username: username, password: password)
                print("🔐 Login successful!")
                
                // Success haptic feedback
                await MainActor.run {
                    let successFeedback = UINotificationFeedbackGenerator()
                    successFeedback.notificationOccurred(.success)
                    self.isLoading = false
                    self.loginAttempted = false
                }
                
                // Login successful, APIManager will update isAuthenticated
            } catch {
                print("🔐 Login failed: \(error)")
                
                await MainActor.run {
                    // Error haptic feedback
                    let errorFeedback = UINotificationFeedbackGenerator()
                    errorFeedback.notificationOccurred(.error)
                    
                    self.errorMessage = self.getUserFriendlyErrorMessage(error)
                    self.showError = true
                    self.isLoading = false
                    self.loginAttempted = false
                }
            }
        }
    }
    
    private func getUserFriendlyErrorMessage(_ error: Error) -> String {
        if let apiError = error as? APIError {
            switch apiError {
            case .unauthorized:
                return "Invalid username or password. Please try again."
            case .networkError:
                return "Network connection failed. Please check your internet connection."
            case .serverError(let code):
                return "Server error (\(code)). Please try again later."
            default:
                return "Login failed. Please try again."
            }
        }
        return error.localizedDescription
    }
}

// MARK: - Modern UI Styles
struct TactileButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.96 : 1.0)
            .opacity(configuration.isPressed ? 0.9 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

struct ModernTextFieldStyle: TextFieldStyle {
    func _body(configuration: TextField<Self._Label>) -> some View {
        configuration
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
            .background(Color(.systemGray6))
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color.blue.opacity(0.2), lineWidth: 1)
            )
            .font(.system(size: 16))
    }
}
