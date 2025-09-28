import SwiftUI

struct NameCollectionView: View {
    @State private var displayedText = ""
    @State private var showTextField = false
    @State private var firstName = ""
    @State private var lastName = ""
    @State private var showContinueButton = false
    @State private var isTyping = false
    @Environment(\.colorScheme) var colorScheme
    @Environment(\.dismiss) private var dismiss
    
    private let fullText = "Hi there! What's your name?"
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
                    
                    // Progress Bar (first step)
                    HStack {
                        ForEach(0..<6) { index in
                            Rectangle()
                                .fill(index < 1 ? Color.green : Color.gray.opacity(0.3))
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
                                    let bubbleWidth: CGFloat = 240
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
                                .frame(width: 240, height: 72) // Height includes tail

                                // Animated text positioned in the bubble
                                Text(displayedText)
                                    .font(.system(size: 16, weight: .medium))
                                    .foregroundColor(primaryTextColor)
                                    .multilineTextAlignment(.center)
                                    .padding(.horizontal, 16)
                                    .padding(.vertical, 10)
                                    .frame(width: 220, height: 60)
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
                        
                        // Name Input Fields (show after typing is complete)
                        if showTextField {
                            VStack(spacing: 16) {
                                // First Name
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("First Name")
                                        .font(.system(size: 14, weight: .medium))
                                        .foregroundColor(secondaryTextColor)
                                        .padding(.leading, 4)
                                    
                                    TextField("Enter your first name", text: $firstName)
                                        .font(.system(size: 16, weight: .medium))
                                        .foregroundColor(primaryTextColor)
                                        .autocorrectionDisabled(true)
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
                                        .onChange(of: firstName) { _ in
                                            updateContinueButton()
                                        }
                                }
                                
                                // Last Name
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("Last Name")
                                        .font(.system(size: 14, weight: .medium))
                                        .foregroundColor(secondaryTextColor)
                                        .padding(.leading, 4)
                                    
                                    TextField("Enter your last name", text: $lastName)
                                        .font(.system(size: 16, weight: .medium))
                                        .foregroundColor(primaryTextColor)
                                        .autocorrectionDisabled(true)
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
                                        .onChange(of: lastName) { _ in
                                            updateContinueButton()
                                        }
                                }
                            }
                            .padding(.horizontal, 28)
                            .transition(.opacity.combined(with: .scale))
                        }
                    }
                    
                    Spacer()
                    
                    // Continue Button
                    if showContinueButton {
                        NavigationLink(destination: PracticeSizeView(userName: "\(firstName) \(lastName)")) {
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
    
    private var secondaryTextColor: Color {
        colorScheme == .dark ? Color.gray : Color.gray
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
                        showTextField = true
                    }
                }
            }
        }
    }
    
    private func updateContinueButton() {
        let shouldShow = !firstName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && 
                        !lastName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        
        if shouldShow != showContinueButton {
            withAnimation(.easeInOut(duration: 0.3)) {
                showContinueButton = shouldShow
            }
        }
    }
}

#Preview {
    NavigationView {
        NameCollectionView()
    }
}
