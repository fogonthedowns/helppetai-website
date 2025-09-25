import SwiftUI

struct PracticeSelectionView: View {
    @State private var searchText = ""
    @State private var searchResults: [PracticeSearchResult] = []
    @State private var isSearching = false
    @State private var showingCreatePractice = false
    @State private var selectedPractice: PracticeSearchResult?
    @State private var isJoining = false
    @State private var errorMessage = ""
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            VStack(spacing: 24) {
                // Header
                VStack(spacing: 16) {
                    Image(systemName: "building.2.crop.circle")
                        .font(.system(size: 60))
                        .foregroundColor(.blue)
                    
                    Text("Choose Your Practice")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .foregroundColor(.primary)
                    
                    Text("Search for your veterinary practice or create a new one")
                        .font(.body)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 16)
                }
                .padding(.top, 32)
                
                // Search Section
                VStack(spacing: 16) {
                    // Search Bar
                    HStack {
                        Image(systemName: "magnifyingglass")
                            .foregroundColor(.secondary)
                        
                        TextField("Search for your practice...", text: $searchText)
                            .textFieldStyle(PlainTextFieldStyle())
                            .onChange(of: searchText) { newValue in
                                searchForPractices(query: newValue)
                            }
                        
                        if !searchText.isEmpty {
                            Button(action: {
                                searchText = ""
                                searchResults = []
                            }) {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                    .padding(.horizontal, 24)
                    
                    // Search Results
                    if isSearching {
                        ProgressView("Searching...")
                            .frame(maxWidth: .infinity, minHeight: 100)
                    } else if !searchText.isEmpty && searchResults.isEmpty {
                        VStack(spacing: 16) {
                            Image(systemName: "building.2")
                                .font(.system(size: 40))
                                .foregroundColor(.secondary)
                            
                            Text("No practices found")
                                .font(.headline)
                                .foregroundColor(.secondary)
                            
                            Text("Try a different search term or create a new practice")
                                .font(.caption)
                                .foregroundColor(.secondary)
                                .multilineTextAlignment(.center)
                        }
                        .frame(maxWidth: .infinity, minHeight: 100)
                        .padding()
                    } else if !searchResults.isEmpty {
                        ScrollView {
                            LazyVStack(spacing: 12) {
                                ForEach(searchResults, id: \.id) { practice in
                                    PracticeRow(practice: practice) {
                                        selectedPractice = practice
                                        joinPractice(practice)
                                    }
                                }
                            }
                            .padding(.horizontal, 24)
                        }
                        .frame(maxHeight: 300)
                    }
                }
                
                Spacer()
                
                // Error Message
                if !errorMessage.isEmpty {
                    Text(errorMessage)
                        .foregroundColor(.red)
                        .font(.caption)
                        .padding(.horizontal, 24)
                }
                
                // Create New Practice Button
                VStack(spacing: 16) {
                    Text("Don't see your practice?")
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    Button(action: {
                        showingCreatePractice = true
                    }) {
                        HStack {
                            Image(systemName: "plus.circle.fill")
                            Text("Create New Practice")
                                .fontWeight(.semibold)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.green)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }
                    .padding(.horizontal, 24)
                }
                .padding(.bottom, 32)
            }
            .navigationTitle("Setup")
            .navigationBarTitleDisplayMode(.inline)
            .navigationBarBackButtonHidden(true)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        print("🔙 PracticeSelectionView: Logout button tapped - calling APIManager.logout()")
                        APIManager.shared.logout()
                        print("🔙 PracticeSelectionView: logout() completed")
                    }
                }
            }
        }
        .sheet(isPresented: $showingCreatePractice) {
            CreatePracticeView()
        }
        .overlay {
            if isJoining {
                Color.black.opacity(0.3)
                    .ignoresSafeArea()
                
                VStack(spacing: 16) {
                    ProgressView()
                        .scaleEffect(1.2)
                    Text("Joining practice...")
                        .font(.headline)
                }
                .padding(32)
                .background(Color(.systemBackground))
                .cornerRadius(12)
                .shadow(radius: 8)
            }
        }
    }
    
    private func searchForPractices(query: String) {
        guard !query.isEmpty else {
            searchResults = []
            return
        }
        
        // Debounce search to avoid too many API calls
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            guard searchText == query else { return } // Only search if text hasn't changed
            
            isSearching = true
            
            Task {
                do {
                    let results = await APIManager.shared.searchPractices(query: query)
                    
                    await MainActor.run {
                        isSearching = false
                        searchResults = results
                    }
                } catch {
                    await MainActor.run {
                        isSearching = false
                        searchResults = []
                        print("❌ Search error: \(error)")
                    }
                }
            }
        }
    }
    
    private func joinPractice(_ practice: PracticeSearchResult) {
        isJoining = true
        errorMessage = ""
        
        Task {
            do {
                let success = await APIManager.shared.joinPractice(practiceId: practice.id)
                
                await MainActor.run {
                    isJoining = false
                    if success {
                        print("✅ Successfully joined practice: \(practice.name)")
                        // Navigate to main app
                        dismiss()
                    } else {
                        errorMessage = "Failed to join practice. Please try again."
                    }
                }
            } catch {
                await MainActor.run {
                    isJoining = false
                    errorMessage = "Network error. Please check your connection."
                    print("❌ Join practice error: \(error)")
                }
            }
        }
    }
}

// MARK: - Practice Row Component

struct PracticeRow: View {
    let practice: PracticeSearchResult
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 16) {
                // Practice Icon
                Image(systemName: "building.2.crop.circle.fill")
                    .font(.system(size: 40))
                    .foregroundColor(.blue)
                
                // Practice Info
                VStack(alignment: .leading, spacing: 4) {
                    Text(practice.name)
                        .font(.headline)
                        .foregroundColor(.primary)
                        .multilineTextAlignment(.leading)
                    
                    if let address = practice.address {
                        Text(address)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.leading)
                    }
                    
                    if let phone = practice.phone {
                        Text(phone)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                // Join Arrow
                Image(systemName: "arrow.right.circle.fill")
                    .font(.system(size: 24))
                    .foregroundColor(.blue)
            }
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

#Preview {
    PracticeSelectionView()
}
