// MARK: - CallVolumeResponseView.swift
import SwiftUI

struct CallVolumeResponseView: View {
    let userName: String
    let selectedPracticeType: String
    let selectedCallVolume: String
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
                    // Progress Bar (same as CallVolumeView - 3/4 complete)
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
                        
                        // Progress bar (3/4 complete)
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
                                    .fill(Color.gray.opacity(0.3))
                                    .frame(height: 4)
                                
                                Circle()
                                    .fill(Color.gray.opacity(0.3))
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
                                    let bubbleWidth: CGFloat = 320
                                    let bubbleHeight: CGFloat = 100
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
                                .frame(width: 320, height: 112) // Height includes tail
                                
                                // Animated text positioned in the bubble
                                Text(displayedText)
                                    .font(.system(size: 16, weight: .medium))
                                    .foregroundColor(primaryTextColor)
                                    .multilineTextAlignment(.center)
                                    .padding(.horizontal, 20)
                                    .padding(.vertical, 16)
                                    .frame(width: 300, height: 100)
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
                        NavigationLink(destination: DecisionMakerView(userName: userName, selectedPracticeType: selectedPracticeType, selectedCallVolume: selectedCallVolume)) {
                            Text("CONTINUE")
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
        let callRange = selectedCallVolume
        
        switch callRange {
        case "10-25":
            return "We could help you get back 100+ hours in your first year!"
        case "25-50":
            return "We could save your team 5+ hours per week! That's over 250 hours in your first year"
        case "50-100":
            return "Wow! We could save your team 10+ hours per week! That's over 500 hours annually"
        case "100-200":
            return "Amazing! We could save your team 20+ hours per week! That's 1,000+ hours annually"
        case "200+":
            return "Incredible volume! We could save your team 40+ hours per week! That's 2,000+ hours annually"
        default:
            return "We can help save your team significant time every week!"
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

#Preview("Light Mode") {
    CallVolumeResponseView(userName: "John Doe", selectedPracticeType: "solo", selectedCallVolume: "100-200")
        .preferredColorScheme(.light)
}

#Preview("Dark Mode") {
    CallVolumeResponseView(userName: "John Doe", selectedPracticeType: "corporate", selectedCallVolume: "200+")
        .preferredColorScheme(.dark)
}
