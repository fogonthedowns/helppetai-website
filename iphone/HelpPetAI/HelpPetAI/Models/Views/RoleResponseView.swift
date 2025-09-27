// MARK: - RoleResponseView.swift
import SwiftUI

struct RoleResponseView: View {
    let userName: String
    let selectedPracticeType: String
    let selectedCallVolume: String
    let selectedRole: String
    @State private var displayedText = ""
    @State private var showContinueButton = false
    @State private var isTyping = false
    @Environment(\.colorScheme) var colorScheme
    @Environment(\.dismiss) private var dismiss
    
    private let typingSpeed: Double = 0.015
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Background gradient (same as previous screens)
                LinearGradient(
                    gradient: Gradient(colors: backgroundColors),
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
                
                VStack(spacing: 0) {
                    // Progress Bar (4/4 complete!)
                    VStack(spacing: 16) {
                        HStack {
                            Button(action: {
                                dismiss()
                            }) {
                                Image(systemName: "chevron.left")
                                    .font(.system(size: 18, weight: .medium))
                                    .foregroundColor(primaryTextColor)
                            }
                            
                            Spacer()
                        }
                        
                        // Progress bar (4/4 complete)
                        VStack(spacing: 8) {
                            HStack {
                                Circle()
                                    .fill(Color.green)
                                    .frame(width: 12, height: 12)
                                
                                Rectangle()
                                    .fill(Color.green)
                                    .frame(height: 4)
                                
                                Circle()
                                    .fill(Color.green)
                                    .frame(width: 12, height: 12)
                                
                                Rectangle()
                                    .fill(Color.green)
                                    .frame(height: 4)
                                
                                Circle()
                                    .fill(Color.green)
                                    .frame(width: 12, height: 12)
                                
                                Rectangle()
                                    .fill(Color.green)
                                    .frame(height: 4)
                                
                                Circle()
                                    .fill(Color.green)
                                    .frame(width: 12, height: 12)
                                
                                Spacer()
                            }
                            .padding(.horizontal, 40)
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 10)
                    .padding(.bottom, 30)
                    
                    Spacer()
                    
                    // Character and Dialog
                    VStack(spacing: 32) {
                        // Dialog box with character (centered)
                        VStack(spacing: 20) {
                            // Speech bubble (centered with downward tail)
                            ZStack {
                                // Complete speech bubble with attached tail pointing down
                                Path { path in
                                    let bubbleWidth: CGFloat = 340
                                    let bubbleHeight: CGFloat = 120
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
                                .frame(width: 340, height: 132) // Height includes tail
                                
                                // Animated text positioned in the bubble
                                Text(displayedText)
                                    .font(.system(size: 16, weight: .medium))
                                    .foregroundColor(primaryTextColor)
                                    .multilineTextAlignment(.center)
                                    .padding(.horizontal, 20)
                                    .padding(.vertical, 16)
                                    .frame(width: 320, height: 120)
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
                    }
                    
                    Spacer()
                    
                    // Continue Button
                    if showContinueButton {
                        NavigationLink(destination: MotivationView(userName: userName, selectedPracticeType: selectedPracticeType, selectedCallVolume: selectedCallVolume, selectedRole: selectedRole)) {
                            Text("GET STARTED!")
                                .font(.system(size: 18, weight: .bold))
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .frame(height: 56)
                                .background(
                                    LinearGradient(
                                        gradient: Gradient(colors: [Color.green, Color.green.opacity(0.8)]),
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                                .cornerRadius(16)
                                .shadow(
                                    color: Color.green.opacity(0.3),
                                    radius: 8,
                                    x: 0,
                                    y: 4
                                )
                        }
                        .buttonStyle(WelcomeButtonStyle())
                        .padding(.horizontal, 28)
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
    
    private var responseMessage: String {
        switch selectedRole {
        case "owner":
            return "Perfect! As the owner, you'll love seeing the ROI."
        case "manager":
            return "Excellent! As practice manager, you're in the perfect position to drive this transformation."
        case "veterinarian":
            return "Fantastic! As a vet, you know how interruptions kill productivity."
        case "front_desk":
            return "Amazing! You're trying this out - that's great initiative! You'll be the star employee!"
        case "technician":
            return "Perfect! As a tech, Your manager will be impressed with you!"
        default:
            return "Great choice! You're going to love how this transforms your practice. Let's get you set up for success!"
        }
    }
    
    private func startTypingAnimation() {
        isTyping = true
        displayedText = ""
        let fullText = responseMessage
        
        // Add haptic feedback at the start
        let impactFeedback = UIImpactFeedbackGenerator(style: .light)
        impactFeedback.impactOccurred()
        
        for (index, character) in fullText.enumerated() {
            DispatchQueue.main.asyncAfter(deadline: .now() + Double(index) * typingSpeed) {
                displayedText += String(character)
                
                // Add subtle haptic feedback for each character (every 5th character)
                if index % 5 == 0 {
                    let lightFeedback = UIImpactFeedbackGenerator(style: .light)
                    lightFeedback.impactOccurred()
                }
                
                // When typing is complete
                if index == fullText.count - 1 {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                        isTyping = false
                        withAnimation(.easeInOut(duration: 0.6)) {
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
    
    // MARK: - Color Schemes (same as previous screens)
    
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
    
    private var shadowColor: Color {
        colorScheme == .dark ? 
            Color.black.opacity(0.6) : 
            Color.black.opacity(0.15)
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
}

#Preview("Light Mode - Front Desk") {
    RoleResponseView(userName: "John Doe", selectedPracticeType: "solo", selectedCallVolume: "25-50", selectedRole: "front_desk")
        .preferredColorScheme(.light)
}

#Preview("Dark Mode - Owner") {
    RoleResponseView(userName: "Jane Smith", selectedPracticeType: "corporate", selectedCallVolume: "100-200", selectedRole: "owner")
        .preferredColorScheme(.dark)
}
