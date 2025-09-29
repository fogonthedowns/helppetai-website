import SwiftUI

struct MotivationView: View {
    let userName: String
    let practiceId: String
    let selectedPracticeType: String
    let selectedCallVolume: String
    let selectedRole: String
    
    @State private var displayedText = ""
    @State private var showOptions = false
    @State private var selectedMotivations: Set<String> = []
    @State private var lastSelectedMotivation: String = ""
    @State private var showContinueButton = false
    @State private var isTyping = false
    @Environment(\.colorScheme) var colorScheme
    @Environment(\.dismiss) private var dismiss
    
    private let fullText = "Why are you introducing a Front Desk AI?"
    private let typingSpeed: Double = 0.015
    
    private let motivationOptions = [
        ("🐾", "Spend more time with pets", "pets"),
        ("📞", "Miss fewer calls", "calls"),
        ("⭐", "Make my manager look good", "manager"),
        ("🏥", "Support my practice", "practice"),
        ("💭", "Other", "other")
    ]
    
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
                    
                    // Progress Bar (5/6 complete)
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
                                    .font(.system(size: 14, weight: .medium))
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
                        
                        // Options (show after typing is complete)
                        if showOptions {
                            VStack(spacing: 16) {
                                ForEach(motivationOptions, id: \.2) { option in
                                    Button(action: {
                                        toggleSelection(option.2)
                                    }) {
                                        HStack(spacing: 16) {
                                            // Icon
                                            Text(option.0)
                                                .font(.system(size: 24))
                                                .frame(width: 40, height: 40)
                                                .background(
                                                    Circle()
                                                        .fill(colorScheme == .dark ? Color(red: 0.4, green: 0.4, blue: 0.45) : Color.white.opacity(0.8))
                                                        .shadow(color: Color.black.opacity(colorScheme == .dark ? 0.3 : 0.1), radius: 2, x: 0, y: 1)
                                                )
                                            
                                            // Text
                                            Text(option.1)
                                                .font(.system(size: 16, weight: .medium))
                                                .foregroundColor(.primary)
                                                .multilineTextAlignment(.leading)
                                            
                                            Spacer()
                                            
                                            // Selection indicator
                                            if selectedMotivations.contains(option.2) {
                                                Image(systemName: "checkmark.circle.fill")
                                                    .foregroundColor(.green)
                                                    .font(.system(size: 20))
                                            }
                                        }
                                        .padding(.horizontal, 20)
                                        .padding(.vertical, 16)
                                        .background(
                                            RoundedRectangle(cornerRadius: 12)
                                                .fill(colorScheme == .dark ? Color(red: 0.2, green: 0.2, blue: 0.25) : Color.white)
                                                .shadow(
                                                    color: selectedMotivations.contains(option.2) ? Color.green.opacity(0.3) : Color.black.opacity(colorScheme == .dark ? 0.3 : 0.1),
                                                    radius: selectedMotivations.contains(option.2) ? 8 : 4,
                                                    x: 0,
                                                    y: 2
                                                )
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 12)
                                                        .stroke(
                                                            selectedMotivations.contains(option.2) ? Color.green : Color.clear,
                                                            lineWidth: 2
                                                        )
                                                        .clipped()
                                                )
                                        )
                                    }
                                    .buttonStyle(PlainButtonStyle())
                                }
                            }
                            .padding(.horizontal, 28)
                            .transition(.opacity.combined(with: .scale))
                        }
                    }
                    
                    Spacer()
                    
                    // Continue Button (show when at least one option is selected)
                    if !selectedMotivations.isEmpty {
                        NavigationLink(destination: AccountCreationView(
                            userName: userName,
                            practiceId: practiceId,
                            selectedPracticeType: selectedPracticeType,
                            selectedCallVolume: selectedCallVolume,
                            selectedRole: selectedRole,
                            selectedMotivations: selectedMotivations
                        )) {
                            Text("Continue")
                                .font(.system(size: 18, weight: .semibold))
                                .foregroundColor(.white)
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
    
    private var shadowColor: Color {
        colorScheme == .dark ? Color.black.opacity(0.3) : Color.black.opacity(0.15)
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
                        showOptions = true
                    }
                }
            }
        }
    }
    
    private func toggleSelection(_ motivation: String) {
        if selectedMotivations.contains(motivation) {
            selectedMotivations.remove(motivation)
            // If deselecting, clear the last selected if it was this one
            if lastSelectedMotivation == motivation {
                lastSelectedMotivation = ""
            }
        } else {
            selectedMotivations.insert(motivation)
            lastSelectedMotivation = motivation
        }
        updateResponseText()
    }
    
    private func updateResponseText() {
        let responseText = getCombinedResponseText()
        displayedText = ""
        isTyping = true
        
        for (index, character) in responseText.enumerated() {
            DispatchQueue.main.asyncAfter(deadline: .now() + Double(index) * typingSpeed) {
                displayedText += String(character)
                
                // Haptic feedback for each character
                let lightFeedback = UIImpactFeedbackGenerator(style: .light)
                lightFeedback.impactOccurred()
            }
            
            // When typing is complete
            if index == responseText.count - 1 {
                DispatchQueue.main.asyncAfter(deadline: .now() + Double(index) * typingSpeed + 0.1) {
                    isTyping = false
                }
            }
        }
    }
    
    private func getCombinedResponseText() -> String {
        if selectedMotivations.isEmpty || lastSelectedMotivation.isEmpty {
            return fullText
        }
        
        // Return response for the most recently selected item
        switch lastSelectedMotivation {
        case "pets":
            return "Perfect! More pet time!"
        case "calls":
            return "Perfect! Never miss calls!"
        case "manager":
            return "Perfect! Impress your manager!"
        case "practice":
            return "Perfect! Support the team!"
        case "other":
            return "Perfect! Your unique goals!"
        default:
            return fullText
        }
    }
}

#Preview {
    NavigationView {
        MotivationView(
            userName: "John Doe",
            practiceId: "practice123",
            selectedPracticeType: "solo",
            selectedCallVolume: "25-50",
            selectedRole: "owner"
        )
    }
}
