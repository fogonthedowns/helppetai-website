import SwiftUI
import WebKit

extension View {
    func placeholder<Content: View>(
        when shouldShow: Bool,
        alignment: Alignment = .leading,
        @ViewBuilder placeholder: () -> Content) -> some View {

        ZStack(alignment: alignment) {
            placeholder().opacity(shouldShow ? 1 : 0)
            self
        }
    }
}

struct SignUpView: View {
    @State private var username = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var email = ""
    @State private var fullName = ""
    @State private var isLoading = false
    @State private var errorMessage = ""
    @State private var showingTerms = false
    @State private var showingPrivacy = false
    @State private var showingPracticeSelection = false
    @Environment(\.dismiss) private var dismiss
    
    private var termsAndPrivacyText: Text {
        Text("By continuing you agree to our ")
            .font(.system(size: 12))
            .foregroundColor(.secondary)
        + 
        Text("Terms of Service")
            .font(.system(size: 12))
            .foregroundColor(.blue)
            .underline()
        + 
        Text(" and acknowledge that you have read our ")
            .font(.system(size: 12))
            .foregroundColor(.secondary)
        + 
        Text("Privacy Policy")
            .font(.system(size: 12))
            .foregroundColor(.blue)
            .underline()
        + 
        Text(" to learn how we collect, use, and share your data.")
            .font(.system(size: 12))
            .foregroundColor(.secondary)
    }
    
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
            
            // Content
            ScrollView {
                VStack(alignment: .leading, spacing: 32) {
                    // Title and Description
                    VStack(alignment: .leading, spacing: 16) {
                        Text("Sign up for HelpPetAI")
                            .font(.system(size: 30, weight: .bold))
                            .foregroundColor(.primary)
                        
                        Text("Create a profile, Add your Practice (private by design!), Configure your Front Desk AI agent and more!")
                            .font(.system(size: 16, weight: .regular))
                            .foregroundColor(.secondary)
                            .lineLimit(nil)
                            .multilineTextAlignment(.leading)
                    }
                    .padding(.top, 40)
                    
                    // Form Fields
                    VStack(spacing: 24) {
                        // Full Name
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Full Name")
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(.primary)
                            
                            TextField("", text: $fullName)
                                .placeholder(when: fullName.isEmpty) {
                                    Text("Enter your full name")
                                        .foregroundColor(.gray)
                                        .font(.system(size: 16))
                                }
                                .font(.system(size: 16))
                                .padding(.horizontal, 0)
                                .padding(.vertical, 16)
                                .overlay(
                                    Rectangle()
                                        .frame(height: 1)
                                        .foregroundColor(.gray.opacity(0.3)),
                                    alignment: .bottom
                                )
                                .textContentType(.name)
                                .autocapitalization(.words)
                        }
                        
                        // Email
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Email")
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(.primary)
                            
                            TextField("", text: $email)
                                .placeholder(when: email.isEmpty) {
                                    Text("Enter your email")
                                        .foregroundColor(.gray)
                                        .font(.system(size: 16))
                                }
                                .font(.system(size: 16))
                                .padding(.horizontal, 0)
                                .padding(.vertical, 16)
                                .overlay(
                                    Rectangle()
                                        .frame(height: 1)
                                        .foregroundColor(.gray.opacity(0.3)),
                                    alignment: .bottom
                                )
                                .textContentType(.emailAddress)
                                .keyboardType(.emailAddress)
                                .autocapitalization(.none)
                                .autocorrectionDisabled()
                        }
                        
                        // Username
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Username")
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(.primary)
                            
                            TextField("", text: $username)
                                .placeholder(when: username.isEmpty) {
                                    Text("Choose a username")
                                        .foregroundColor(.gray)
                                        .font(.system(size: 16))
                                }
                                .font(.system(size: 16))
                                .padding(.horizontal, 0)
                                .padding(.vertical, 16)
                                .overlay(
                                    Rectangle()
                                        .frame(height: 1)
                                        .foregroundColor(.gray.opacity(0.3)),
                                    alignment: .bottom
                                )
                                .textContentType(.username)
                                .autocapitalization(.none)
                                .autocorrectionDisabled()
                        }
                        
                        // Password
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Password")
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(.primary)
                            
                            SecureField("", text: $password)
                                .placeholder(when: password.isEmpty) {
                                    Text("Choose a password")
                                        .foregroundColor(.gray)
                                        .font(.system(size: 16))
                                }
                                .font(.system(size: 16))
                                .padding(.horizontal, 0)
                                .padding(.vertical, 16)
                                .overlay(
                                    Rectangle()
                                        .frame(height: 1)
                                        .foregroundColor(.gray.opacity(0.3)),
                                    alignment: .bottom
                                )
                                .textContentType(.newPassword)
                        }
                        
                        // Confirm Password
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Confirm Password")
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(.primary)
                            
                            SecureField("", text: $confirmPassword)
                                .placeholder(when: confirmPassword.isEmpty) {
                                    Text("Confirm your password")
                                        .foregroundColor(.gray)
                                        .font(.system(size: 16))
                                }
                                .font(.system(size: 16))
                                .padding(.horizontal, 0)
                                .padding(.vertical, 16)
                                .overlay(
                                    Rectangle()
                                        .frame(height: 1)
                                        .foregroundColor(.gray.opacity(0.3)),
                                    alignment: .bottom
                                )
                                .textContentType(.newPassword)
                        }
                    }
                    
                    // Error Message
                    if !errorMessage.isEmpty {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                    
                    // Terms and Privacy
                    termsAndPrivacyText
                        .multilineTextAlignment(.center)
                        .fixedSize(horizontal: false, vertical: true)
                        .padding(.horizontal, 16)
                        .onTapGesture {
                            // Handle taps on the specific links
                            showingTerms = true
                        }
                    
                    // TODO: Implement AttributedString solution for better link handling:
                    /*
                    Alternative solution using AttributedString (iOS 15+):
                    VStack(spacing: 4) {
                        Text(termsAttributedString)
                            .font(.system(size: 12))
                            .multilineTextAlignment(.center)
                            .fixedSize(horizontal: false, vertical: true)
                            .padding(.horizontal, 16)
                            .environment(\.openURL, OpenURLAction { url in
                                if url.absoluteString.contains("terms") {
                                    showingTerms = true
                                } else if url.absoluteString.contains("privacy") {
                                    showingPrivacy = true
                                }
                                return .handled
                            })
                    }
                    */
                    
                    // Sign Up Button
                    Button(action: signUp) {
                        HStack {
                            if isLoading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    .scaleEffect(0.9)
                            }
                            Text(isLoading ? "Creating Account..." : "Sign Up")
                                .font(.system(size: 17, weight: .semibold))
                        }
                        .frame(maxWidth: .infinity)
                        .frame(height: 50)
                        .background(
                            LinearGradient(
                                gradient: Gradient(colors: [Color.blue, Color.blue.opacity(0.8)]),
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .foregroundColor(.white)
                        .cornerRadius(12)
                        .shadow(color: Color.blue.opacity(0.3), radius: 6, x: 0, y: 3)
                    }
                    .disabled(isLoading || !isFormValid)
                    .opacity((isLoading || !isFormValid) ? 0.6 : 1.0)
                    
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 20)
            }
            
            // Login Link in Gray Box (full width footer)
            HStack {
                Spacer()
                Text("Already have an account? ")
                    .font(.system(size: 14))
                    .foregroundColor(.secondary)
                + Text("Log in")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.red)
                Spacer()
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 20)
            .background(Color(.systemGray6))
            .onTapGesture {
                dismiss()
            }
        }
        .navigationBarHidden(true)
        .navigationBarBackButtonHidden(true)
        .ignoresSafeArea(.all, edges: .bottom)
        .sheet(isPresented: $showingTerms) {
            WebView(url: URL(string: "https://helppet.ai/terms")!)
                .navigationTitle("Terms of Service")
                .navigationBarTitleDisplayMode(.inline)
        }
        .sheet(isPresented: $showingPrivacy) {
            WebView(url: URL(string: "https://helppet.ai/privacy")!)
                .navigationTitle("Privacy Policy")
                .navigationBarTitleDisplayMode(.inline)
        }
        .fullScreenCover(isPresented: $showingPracticeSelection) {
            PracticeSelectionView()
        }
    }
    
    private var isFormValid: Bool {
        !fullName.isEmpty &&
        !email.isEmpty &&
        !username.isEmpty &&
        !password.isEmpty &&
        !confirmPassword.isEmpty &&
        password == confirmPassword &&
        email.contains("@") &&
        password.count >= 6
    }
    
    private func signUp() {
        guard isFormValid else {
            errorMessage = "Please fill in all fields correctly"
            return
        }
        
        guard password == confirmPassword else {
            errorMessage = "Passwords don't match"
            return
        }
        
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                let success = await APIManager.shared.signUp(
                    username: username,
                    password: password,
                    email: email,
                    fullName: fullName,
                    role: "VET_STAFF"
                )
                
                await MainActor.run {
                    isLoading = false
                    if success {
                        print("✅ Sign up successful!")
                        showingPracticeSelection = true
                    } else {
                        errorMessage = "Sign up failed. Please try again."
                    }
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                    errorMessage = "Network error. Please check your connection."
                    print("❌ Sign up error: \(error)")
                }
            }
        }
    }
}

// MARK: - WebView for Terms and Privacy

struct WebView: UIViewRepresentable {
    let url: URL
    
    func makeUIView(context: Context) -> WKWebView {
        return WKWebView()
    }
    
    func updateUIView(_ webView: WKWebView, context: Context) {
        let request = URLRequest(url: url)
        webView.load(request)
    }
}

#Preview {
    SignUpView()
}
