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
    
    var body: some View {
        VStack(spacing: 0) {
            // Navigation Bar
            HStack {
                Button(action: {
                    dismiss()
                }) {
                    HStack(spacing: 8) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 18, weight: .medium))
                        Text("Back")
                            .font(.system(size: 17, weight: .medium))
                    }
                    .foregroundColor(.primary)
                }
                
                Spacer()
            }
            .padding(.horizontal, 20)
            .padding(.top, 10)
            .padding(.bottom, 20)
            
            VStack(spacing: 20) {
                // Header
                VStack(spacing: 8) {
                    Image(systemName: "cross.case.fill")
                        .font(.system(size: 60))
                        .foregroundColor(.blue)
                    
                    Text("HelpPet")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    
                    Text("Veterinary Practice Management")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .padding(.bottom, 40)
                
                // Login Form
                VStack(spacing: 20) {
                    VStack(spacing: 16) {
                        TextField("Username", text: $username)
                            .textFieldStyle(ModernTextFieldStyle())
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                            .textContentType(.username)
                            .onTapGesture {
                                // Select all text when tapping
                                DispatchQueue.main.async {
                                    UIApplication.shared.sendAction(#selector(UIResponder.selectAll(_:)), to: nil, from: nil, for: nil)
                                }
                            }
                        
                        SecureField("Password", text: $password)
                            .textFieldStyle(ModernTextFieldStyle())
                            .textContentType(.password)
                            .onTapGesture {
                                // Select all text when tapping
                                DispatchQueue.main.async {
                                    UIApplication.shared.sendAction(#selector(UIResponder.selectAll(_:)), to: nil, from: nil, for: nil)
                                }
                            }
                            .onSubmit {
                                // Login when user presses return on password field
                                if !username.isEmpty && !password.isEmpty && !isLoading {
                                    login()
                                }
                            }
                    }
                    
                    Button(action: login) {
                        HStack(spacing: 12) {
                            if isLoading {
                                ProgressView()
                                    .scaleEffect(0.9)
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                Text("Signing In...")
                                    .fontWeight(.semibold)
                            } else {
                                Image(systemName: "person.crop.circle.fill")
                                    .font(.system(size: 16))
                                Text("Sign In")
                                    .fontWeight(.semibold)
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .frame(height: 50)
                        .background(
                            Group {
                                if isLoading {
                                    Color.blue.opacity(0.8)
                                } else if username.isEmpty || password.isEmpty {
                                    Color.gray.opacity(0.5)
                                } else {
                                    Color.blue
                                }
                            }
                        )
                        .foregroundColor(.white)
                        .cornerRadius(12)
                        .shadow(color: Color.blue.opacity(0.3), radius: isLoading ? 0 : 4, x: 0, y: 2)
                        .scaleEffect(isLoading ? 0.98 : 1.0)
                        .animation(.easeInOut(duration: 0.1), value: isLoading)
                    }
                    .disabled(isLoading || username.isEmpty || password.isEmpty)
                    .buttonStyle(TactileButtonStyle())
                }
                .padding(.horizontal, 40)
                
                // Sign Up Link
                VStack(spacing: 16) {
                    HStack {
                        Text("New to HelpPetAI?")
                            .foregroundColor(.secondary)
                        
                        Button("Sign Up") {
                            showingSignUp = true
                        }
                        .foregroundColor(.blue)
                        .fontWeight(.medium)
                    }
                }
                .padding(.top, 32)
                
                Spacer()
                
            }
        }
        .navigationBarHidden(true)
            .alert("Login Error", isPresented: $showError) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
        .background(
            NavigationLink(
                destination: SignUpView(),
                isActive: $showingSignUp
            ) {
                EmptyView()
            }
            .hidden()
        )
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
