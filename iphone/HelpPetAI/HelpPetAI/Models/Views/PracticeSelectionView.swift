import SwiftUI

struct PracticeSelectionView: View {
    let userName: String
    
    @State private var displayedText = ""
    @State private var showSearchField = false
    @State private var searchText = ""
    @State private var searchResults: [PracticeSearchResult] = []
    @State private var isSearching = false
    @State private var selectedPractice: PracticeSearchResult?
    @State private var showContinueButton = false
    @State private var isTyping = false
    @Environment(\.colorScheme) var colorScheme
    @Environment(\.dismiss) private var dismiss
    
    private let fullText = "Find your practice"
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
                    
                    // Progress Bar (second step)
                    HStack {
                        ForEach(0..<7) { index in
                            Rectangle()
                                .fill(index < 2 ? Color.green : Color.gray.opacity(0.3))
                                .frame(height: 4)
                                .cornerRadius(2)
                        }
                    }
                    .padding(.horizontal, 40)
                    .padding(.top, 20)
                    
                    // Main Content (moved up)
                    VStack(spacing: 20) {
                        // Speech Bubble
                        VStack(spacing: 0) {
                            // Dialog Box
                            ZStack {
                                // Speech bubble background
                                Path { path in
                                    let bubbleWidth: CGFloat = 220
                                    let bubbleHeight: CGFloat = 60
                                    let cornerRadius: CGFloat = 16
                                    let tailWidth: CGFloat = 16
                                    let tailHeight: CGFloat = 12
                                    
                                    // Main bubble rectangle
                                    let rect = CGRect(x: 0, y: 0, width: bubbleWidth, height: bubbleHeight)
                                    path.addRoundedRect(in: rect, cornerSize: CGSize(width: cornerRadius, height: cornerRadius))
                                    
                                    // Speech bubble tail pointing down
                                    let tailStartX = bubbleWidth / 2 - tailWidth / 2
                                    let tailEndX = bubbleWidth / 2 + tailWidth / 2
                                    let tailTipX = bubbleWidth / 2
                                    
                                    path.move(to: CGPoint(x: tailStartX, y: bubbleHeight))
                                    path.addLine(to: CGPoint(x: tailEndX, y: bubbleHeight))
                                    path.addLine(to: CGPoint(x: tailTipX, y: bubbleHeight + tailHeight))
                                    path.closeSubpath()
                                }
                                .fill(colorScheme == .dark ? Color(red: 0.2, green: 0.2, blue: 0.25) : Color.white)
                                .shadow(color: shadowColor, radius: 8, x: 0, y: 4)
                                
                                // Text inside bubble
                                Text(displayedText)
                                    .font(.system(size: 16, weight: .medium))
                                    .foregroundColor(primaryTextColor)
                                    .multilineTextAlignment(.center)
                                    .padding(.horizontal, 16)
                                    .padding(.vertical, 12)
                            }
                            .frame(width: 220, height: 72)
                        }
                        
                        // Character Image (below dialog)
                        Image("Welcome")
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(width: 160, height: 160)
                            .scaleEffect(1.0)
                        
                        // Search Field
                        if showSearchField {
                            VStack(spacing: 16) {
                                TextField("Search for your practice...", text: $searchText)
                                    .font(.system(size: 16))
                                    .padding(.horizontal, 16)
                                    .padding(.vertical, 12)
                                    .background(
                                        RoundedRectangle(cornerRadius: 12)
                                            .fill(colorScheme == .dark ? Color(red: 0.2, green: 0.2, blue: 0.25) : Color.white)
                                            .shadow(color: shadowColor, radius: 4, x: 0, y: 2)
                                    )
                                    .padding(.horizontal, 40)
                                    .onChange(of: searchText) { newValue in
                                        if !newValue.isEmpty {
                                            searchForPractices(query: newValue)
                                        } else {
                                            searchResults = []
                                            selectedPractice = nil
                                            showContinueButton = false
                                        }
                                    }
                                
                                // Search Results
                                if isSearching {
                                    ProgressView("Searching...")
                                        .frame(maxWidth: .infinity, minHeight: 60)
                                } else if !searchText.isEmpty && searchResults.isEmpty {
                                    VStack(spacing: 8) {
                                        Image(systemName: "building.2")
                                            .font(.system(size: 30))
                                            .foregroundColor(.secondary)
                                        
                                        Text("No practices found")
                                            .font(.headline)
                                            .foregroundColor(.secondary)
                                    }
                                    .frame(maxWidth: .infinity, minHeight: 60)
                                } else if !searchResults.isEmpty {
                                    ScrollView {
                                        LazyVStack(spacing: 8) {
                                            ForEach(searchResults, id: \.id) { practice in
                                                PracticeRow(
                                                    practice: practice,
                                                    isSelected: selectedPractice?.id == practice.id
                                                ) {
                                                    selectedPractice = practice
                                                    showContinueButton = true
                                                    
                                                    // Haptic feedback
                                                    let impactFeedback = UIImpactFeedbackGenerator(style: .medium)
                                                    impactFeedback.impactOccurred()
                                                }
                                            }
                                        }
                                        .padding(.horizontal, 40)
                                    }
                                    .frame(maxHeight: 200)
                                }
                            }
                        }
                    }
                    .padding(.top, 40)
                    
                    Spacer()
                    
                    // Bottom Buttons
                    VStack(spacing: 16) {
                        // Continue Button (only show when practice is selected)
                        if showContinueButton, let practice = selectedPractice {
                            NavigationLink(destination: PracticeSizeView(
                                userName: userName,
                                practiceId: practice.id
                            )) {
                                Text("Continue")
                                    .font(.system(size: 18, weight: .semibold))
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
                            .padding(.bottom, 40)
                        }
                        
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
    private var primaryTextColor: Color {
        colorScheme == .dark ? Color.white : Color.black
    }
    
    private var shadowColor: Color {
        colorScheme == .dark ? Color.black.opacity(0.3) : Color.black.opacity(0.15)
    }
    
    // MARK: - Animation Functions
    private func startTypingAnimation() {
        isTyping = true
        displayedText = ""
        
        for (index, character) in fullText.enumerated() {
            DispatchQueue.main.asyncAfter(deadline: .now() + Double(index) * typingSpeed) {
                displayedText += String(character)
                
                if index == fullText.count - 1 {
                    // Finished typing, show search field after a brief pause
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                        withAnimation(.easeInOut(duration: 0.5)) {
                            showSearchField = true
                            isTyping = false
                        }
                    }
                }
            }
        }
    }
    
    // MARK: - Search Functions
    private func searchForPractices(query: String) {
        guard !query.isEmpty else {
            searchResults = []
            return
        }
        
        isSearching = true
        
        Task {
            do {
                let results = try await APIManager.shared.searchPractices(query: query)
                await MainActor.run {
                    self.searchResults = results
                    self.isSearching = false
                }
            } catch {
                await MainActor.run {
                    print("Search error: \(error)")
                    self.searchResults = []
                    self.isSearching = false
                }
            }
        }
    }
}

// MARK: - Practice Row Component

struct PracticeRow: View {
    let practice: PracticeSearchResult
    let isSelected: Bool
    let onTap: () -> Void
    @Environment(\.colorScheme) var colorScheme
    
    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 16) {
                // Practice Icon
                Image(systemName: "building.2.crop.circle.fill")
                    .font(.system(size: 30))
                    .foregroundColor(.blue)
                
                // Practice Info
                VStack(alignment: .leading, spacing: 4) {
                    Text(practice.name)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(colorScheme == .dark ? Color.white : Color.black)
                        .multilineTextAlignment(.leading)
                    
                    if let address = practice.address {
                        Text(address)
                            .font(.system(size: 12))
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.leading)
                    }
                    
                    if let phone = practice.phone {
                        Text(phone)
                            .font(.system(size: 12))
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                // Selection indicator
                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 20))
                        .foregroundColor(.green)
                } else {
                    Image(systemName: "arrow.right.circle")
                        .font(.system(size: 20))
                        .foregroundColor(.blue)
                }
            }
            .padding(16)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(colorScheme == .dark ? Color(red: 0.2, green: 0.2, blue: 0.25) : Color.white)
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(isSelected ? Color.green : Color.clear, lineWidth: 2)
                    )
                    .shadow(color: colorScheme == .dark ? Color.black.opacity(0.3) : Color.black.opacity(0.1), radius: 4, x: 0, y: 2)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

#Preview {
    NavigationView {
        PracticeSelectionView(userName: "John Doe")
    }
}
