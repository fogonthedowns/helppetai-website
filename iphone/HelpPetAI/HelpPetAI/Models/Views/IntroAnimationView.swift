// MARK: - IntroAnimationView.swift
import SwiftUI

struct IntroAnimationView: View {
    @State private var displayedText = ""
    @State private var showContinueButton = false
    @State private var isTyping = false
    @Environment(\.colorScheme) var colorScheme
    @Environment(\.dismiss) private var dismiss
    
    private let fullText = "Just a few quick questions before we create your AI Front Desk Agent!"
    private let typingSpeed: Double = 0.05 // seconds per character
    
    var body: some View {
        GeometryReader { geometry in
                ZStack {
                    // Background gradient (same as WelcomeView)
                    LinearGradient(
                        gradient: Gradient(colors: backgroundColors),
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                    .ignoresSafeArea()
                    
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
                                .foregroundColor(primaryTextColor)
                            }
                            
                            Spacer()
                        }
                        .padding(.horizontal, 20)
                        .padding(.top, 10)
                        .padding(.bottom, 20)
                        
                        Spacer()
                        
                        // Content (same layout as WelcomeView)
                        VStack(spacing: 32) {
                            // Small cartoon dialog box above the image
                            ZStack {
                                // Complete speech bubble with attached tail
                                Path { path in
                                    let bubbleWidth: CGFloat = 320
                                    let bubbleHeight: CGFloat = 80
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
                                .frame(width: 320, height: 92) // Height includes tail
                                
                                // Animated text positioned in the bubble
                                Text(displayedText)
                                    .font(.system(size: 15, weight: .medium))
                                    .foregroundColor(primaryTextColor)
                                    .multilineTextAlignment(.center)
                                    .padding(.horizontal, 20)
                                    .padding(.vertical, 12)
                                    .frame(width: 300, height: 80)
                                    .offset(y: -6) // Offset up to center in bubble part only
                            }
                            
                            // Welcome Image (same as WelcomeView)
                            VStack(spacing: 32) {
                                // Use the welcome image asset with proper scaling
                                Image("Welcome")
                                    .resizable()
                                    .aspectRatio(contentMode: .fit)
                                    .frame(maxWidth: min(geometry.size.width * 0.8, 300))
                                    .frame(maxHeight: min(geometry.size.height * 0.4, 250))
                                    .shadow(
                                        color: shadowColor,
                                        radius: 20,
                                        x: 0,
                                        y: 10
                                    )
                                
                                // App Title and Tagline (same as WelcomeView)
                                VStack(spacing: 16) {
                                    Text("HelpPetAI")
                                        .font(.system(size: 42, weight: .bold, design: .rounded))
                                        .foregroundColor(primaryTextColor)
                                        .shadow(
                                            color: textShadowColor,
                                            radius: 2,
                                            x: 0,
                                            y: 1
                                        )
                                }
                            }
                        }
                        
                        Spacer()
                        
                        // Continue Button
                        if showContinueButton {
                            NavigationLink(destination: SignUpView()) {
                                Text("CONTINUE")
                                    .font(.system(size: 18, weight: .bold))
                                    .foregroundColor(signUpButtonForeground)
                                    .frame(maxWidth: .infinity)
                                    .frame(height: 56)
                                    .background(signUpButtonBackground)
                                    .cornerRadius(16)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 16)
                                            .stroke(signUpButtonBorder, lineWidth: 2)
                                    )
                                    .shadow(
                                        color: signUpButtonShadow,
                                        radius: 4,
                                        x: 0,
                                        y: 2
                                    )
                            }
                            .buttonStyle(WelcomeButtonStyle())
                            .padding(.horizontal, 32)
                            .padding(.bottom, 50)
                            .transition(.opacity.combined(with: .move(edge: .bottom)))
                        }
                    }
                }
        }
        .navigationBarHidden(true)
        .onAppear {
            startTypingAnimation()
        }
    }
    
    private func startTypingAnimation() {
        isTyping = true
        displayedText = ""
        
        // Add haptic feedback at the start
        let impactFeedback = UIImpactFeedbackGenerator(style: .light)
        impactFeedback.impactOccurred()
        
        for (index, character) in fullText.enumerated() {
            DispatchQueue.main.asyncAfter(deadline: .now() + Double(index) * typingSpeed) {
                displayedText += String(character)
                
                // Add subtle haptic feedback for each character (every 3rd character to avoid overwhelming)
                if index % 3 == 0 {
                    let lightFeedback = UIImpactFeedbackGenerator(style: .light)
                    lightFeedback.impactOccurred()
                }
                
                // When typing is complete
                if index == fullText.count - 1 {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                        isTyping = false
                        withAnimation(.easeInOut(duration: 0.5)) {
                            showContinueButton = true
                        }
                        
                        // Success haptic feedback
                        let successFeedback = UINotificationFeedbackGenerator()
                        successFeedback.notificationOccurred(.success)
                    }
                }
            }
        }
    }
    
    // MARK: - Color Schemes (same as WelcomeView)
    
    private var backgroundColors: [Color] {
        if colorScheme == .dark {
            return [
                Color(red: 0.05, green: 0.05, blue: 0.1),
                Color(red: 0.1, green: 0.1, blue: 0.2),
                Color(red: 0.15, green: 0.1, blue: 0.25)
            ]
        } else {
            return [
                Color(red: 0.95, green: 0.97, blue: 1.0),
                Color(red: 0.9, green: 0.95, blue: 1.0),
                Color(red: 0.85, green: 0.9, blue: 0.98)
            ]
        }
    }
    
    private var primaryTextColor: Color {
        colorScheme == .dark ? .white : Color(red: 0.1, green: 0.1, blue: 0.2)
    }
    
    private var secondaryTextColor: Color {
        colorScheme == .dark ? 
            Color(red: 0.8, green: 0.8, blue: 0.9) : 
            Color(red: 0.3, green: 0.3, blue: 0.5)
    }
    
    private var shadowColor: Color {
        colorScheme == .dark ? 
            Color.black.opacity(0.6) : 
            Color.black.opacity(0.15)
    }
    
    private var textShadowColor: Color {
        colorScheme == .dark ? 
            Color.black.opacity(0.3) : 
            Color.white.opacity(0.8)
    }
    
    private var speechBubbleBackground: Color {
        colorScheme == .dark ? 
            Color(red: 0.2, green: 0.2, blue: 0.3) : 
            Color.white.opacity(0.9)
    }
    
    private var speechBubbleBorder: Color {
        colorScheme == .dark ? 
            Color.white.opacity(0.2) : 
            Color.gray.opacity(0.2)
    }
    
    // Sign Up Button Colors (same as WelcomeView)
    private var signUpButtonBackground: Color {
        colorScheme == .dark ? 
            Color.clear : 
            Color.white.opacity(0.9)
    }
    
    private var signUpButtonForeground: Color {
        colorScheme == .dark ? 
            .white : 
            Color.blue
    }
    
    private var signUpButtonBorder: Color {
        colorScheme == .dark ? 
            Color.white.opacity(0.3) : 
            Color.blue.opacity(0.3)
    }
    
    private var signUpButtonShadow: Color {
        colorScheme == .dark ? 
            Color.white.opacity(0.1) : 
            Color.black.opacity(0.1)
    }
}

#Preview("Light Mode") {
    IntroAnimationView()
        .preferredColorScheme(.light)
}

#Preview("Dark Mode") {
    IntroAnimationView()
        .preferredColorScheme(.dark)
}
