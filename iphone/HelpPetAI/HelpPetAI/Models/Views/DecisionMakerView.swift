// MARK: - DecisionMakerView.swift
import SwiftUI

struct DecisionMakerView: View {
    let userName: String
    let practiceId: String
    let selectedPracticeType: String
    let selectedCallVolume: String
    
    @State private var displayedText = ""
    @State private var showOptions = false
    @State private var isTyping = false
    @State private var selectedRole: String?
    @Environment(\.colorScheme) var colorScheme
    @Environment(\.dismiss) private var dismiss
    
    private let fullText = "What's your role at the practice?"
    private let typingSpeed: Double = 0.015
    
    private let roleOptions = [
        ("👑", "Practice Owner", "owner"),
        ("💼", "Practice Manager", "manager"),
        ("👩‍⚕️", "Veterinarian", "veterinarian"),
        ("📞", "Front Desk Staff", "front_desk"),
        ("🔧", "Veterinary Technician", "technician")
    ]
    
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
                    // Progress Bar
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
                        
                        // Progress bar (4/6 complete)
                        VStack(spacing: 8) {
                            HStack {
                                ForEach(0..<7) { index in
                                    Rectangle()
                                        .fill(index < 5 ? Color.green : Color.gray.opacity(0.3))
                                        .frame(height: 4)
                                        .cornerRadius(2)
                                }
                            }
                            .padding(.horizontal, 40)
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 10)
                    .padding(.bottom, 30)
                    
                    Spacer()
                    
                    // Character and Dialog (centered layout)
                    VStack(spacing: 32) {
                        // Dialog box with character (centered)
                        VStack(spacing: 20) {
                            // Speech bubble (centered with downward tail)
                            ZStack {
                                // Complete speech bubble with attached tail
                                Path { path in
                                    let bubbleWidth: CGFloat = 220
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
                                .frame(width: 220, height: 72) // Height includes tail
                                
                                // Animated text positioned in the bubble
                                Text(displayedText)
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(primaryTextColor)
                                    .multilineTextAlignment(.center)
                                    .padding(.horizontal, 16)
                                    .padding(.vertical, 10)
                                    .frame(width: 200, height: 60)
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
                    
                    // Options (show after typing completes)
                    if showOptions {
                        VStack(spacing: 16) {
                            ForEach(roleOptions.indices, id: \.self) { index in
                                let option = roleOptions[index]
                                
                                Button(action: {
                                    selectedRole = option.2
                                    // Add haptic feedback
                                    let impactFeedback = UIImpactFeedbackGenerator(style: .medium)
                                    impactFeedback.impactOccurred()
                                }) {
                                    HStack(spacing: 16) {
                                        // Icon/Emoji
                                        Text(option.0)
                                            .font(.system(size: 24))
                                        
                                        // Option text
                                        Text(option.1)
                                            .font(.system(size: 16, weight: .medium))
                                            .foregroundColor(primaryTextColor)
                                            .multilineTextAlignment(.leading)
                                        
                                        Spacer()
                                        
                                        // Selection indicator
                                        if selectedRole == option.2 {
                                            Image(systemName: "checkmark.circle.fill")
                                                .font(.system(size: 20))
                                                .foregroundColor(.green)
                                        }
                                    }
                                    .padding(.horizontal, 20)
                                    .padding(.vertical, 16)
                                    .background(optionButtonBackground)
                                    .cornerRadius(12)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 12)
                                            .stroke(selectedRole == option.2 ? Color.green : optionButtonBorder, lineWidth: selectedRole == option.2 ? 2 : 1)
                                    )
                                    .shadow(
                                        color: optionButtonShadow,
                                        radius: 4,
                                        x: 0,
                                        y: 2
                                    )
                                }
                                .buttonStyle(PlainButtonStyle())
                            }
                        }
                        .padding(.horizontal, 28)
                        .transition(.opacity.combined(with: .move(edge: .bottom)))
                    }
                    
                    Spacer()
                    
                    // Continue Button
                    if selectedRole != nil {
                        NavigationLink(destination: RoleResponseView(userName: userName, practiceId: practiceId, selectedPracticeType: selectedPracticeType, selectedCallVolume: selectedCallVolume, selectedRole: selectedRole!)) {
                            Text("CONTINUE")
                                .font(.system(size: 18, weight: .bold))
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .frame(height: 56)
                                .background(
                                    LinearGradient(
                                        gradient: Gradient(colors: [Color.blue, Color.blue.opacity(0.8)]),
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                                .cornerRadius(16)
                                .shadow(
                                    color: Color.blue.opacity(0.3),
                                    radius: 8,
                                    x: 0,
                                    y: 4
                                )
                        }
                        .buttonStyle(WelcomeButtonStyle())
                        .padding(.horizontal, 20)
                        .padding(.bottom, 50)
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
                
                // Add subtle haptic feedback for each character (every 4th character)
                if index % 4 == 0 {
                    let lightFeedback = UIImpactFeedbackGenerator(style: .light)
                    lightFeedback.impactOccurred()
                }
                
                // When typing is complete
                if index == fullText.count - 1 {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                        isTyping = false
                        withAnimation(.easeInOut(duration: 0.6)) {
                            showOptions = true
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
    
    private var optionButtonBackground: Color {
        colorScheme == .dark ? 
            Color(red: 0.15, green: 0.15, blue: 0.25) : 
            Color.white.opacity(0.9)
    }
    
    private var optionButtonBorder: Color {
        colorScheme == .dark ? 
            Color.white.opacity(0.2) : 
            Color.gray.opacity(0.2)
    }
    
    private var optionButtonShadow: Color {
        colorScheme == .dark ? 
            Color.black.opacity(0.3) : 
            Color.black.opacity(0.1)
    }
}

#Preview("Light Mode") {
    DecisionMakerView(userName: "John Doe", practiceId: "practice123", selectedPracticeType: "solo", selectedCallVolume: "25-50")
        .preferredColorScheme(.light)
}

#Preview("Dark Mode") {
    DecisionMakerView(userName: "John Doe", practiceId: "practice123", selectedPracticeType: "solo", selectedCallVolume: "25-50")
        .preferredColorScheme(.dark)
}
