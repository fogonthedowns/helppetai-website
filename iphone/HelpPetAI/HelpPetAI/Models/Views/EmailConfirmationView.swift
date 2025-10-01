import SwiftUI
import MessageUI

struct EmailConfirmationView: View {
    let userEmail: String
    @Environment(\.colorScheme) var colorScheme
    @Environment(\.dismiss) private var dismiss
    
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
                    
                    Spacer()
                    
                    // Main Content
                    VStack(spacing: 40) {
                        // Email Icon
                        ZStack {
                            Circle()
                                .fill(Color.green.opacity(0.2))
                                .frame(width: 120, height: 120)
                            
                            Image(systemName: "envelope.circle.fill")
                                .font(.system(size: 80))
                                .foregroundColor(.green)
                        }
                        
                        // Title and Message
                        VStack(spacing: 16) {
                            Text("Email Sent")
                                .font(.system(size: 32, weight: .bold))
                                .foregroundColor(primaryTextColor)
                                .multilineTextAlignment(.center)
                            
                            Text("Check your email!")
                                .font(.system(size: 24, weight: .semibold))
                                .foregroundColor(primaryTextColor)
                                .multilineTextAlignment(.center)
                            
                            VStack(spacing: 8) {
                                Text("We sent a confirmation link to")
                                    .font(.system(size: 18, weight: .medium))
                                    .foregroundColor(secondaryTextColor)
                                    .multilineTextAlignment(.center)
                                
                                Text(userEmail)
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
                            // Navigate back to login/welcome
                            dismiss()
                        }) {
                            Text("Back to Login")
                                .font(.system(size: 16, weight: .medium))
                                .foregroundColor(.green)
                        }
                        .padding(.bottom, 40)
                    }
                }
            }
        }
        .navigationBarHidden(true)
        .onAppear {
            // Success haptic feedback
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
        EmailConfirmationView(userEmail: "john.doe@example.com")
    }
}
