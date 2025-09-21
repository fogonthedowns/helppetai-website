import SwiftUI

struct PetOwnersView: View {
    let onNavigateToAppointments: () -> Void
    let onToggleSidebar: () -> Void
    
    @StateObject private var apiManager = APIManager.shared
    @State private var petOwners: [PetOwnerDetails] = []
    @State private var isLoading = true
    @State private var errorMessage = ""
    @State private var showError = false
    @State private var searchText = ""
    @State private var showAddPetOwner = false
    
    private var filteredPetOwners: [PetOwnerDetails] {
        if searchText.isEmpty {
            return petOwners
        } else {
            return petOwners.filter { owner in
                owner.fullName.localizedCaseInsensitiveContains(searchText) ||
                owner.email.localizedCaseInsensitiveContains(searchText) ||
                (owner.phone?.localizedCaseInsensitiveContains(searchText) ?? false)
            }
        }
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Header view with hamburger menu button
            HStack {
                Button(action: {
                    onToggleSidebar()
                }) {
                    Image(systemName: "line.3.horizontal")
                        .font(.title3)
                        .foregroundColor(.blue)
                }
                
                Spacer()
                
                Text("Pet Owners")
                    .font(.headline)
                    .fontWeight(.medium)
                
                Spacer()
                
                Button(action: {
                    showAddPetOwner = true
                }) {
                    Image(systemName: "plus")
                        .font(.title3)
                        .foregroundColor(.blue)
                }
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 10)
            .background(Color(.systemGray6))
            .overlay(
                Rectangle()
                    .frame(height: 0.5)
                    .foregroundColor(Color(.separator)),
                alignment: .bottom
            )
            
            // Search bar
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.secondary)
                
                TextField("Search pet owners...", text: $searchText)
                    .textFieldStyle(PlainTextFieldStyle())
                
                if !searchText.isEmpty {
                    Button("Clear") {
                        searchText = ""
                    }
                    .font(.caption)
                    .foregroundColor(.secondary)
                }
            }
            .padding(12)
            .background(Color(.systemGray6))
            .clipShape(RoundedRectangle(cornerRadius: 8))
            .padding(.horizontal, 16)
            .padding(.top, 8)
            
            // Main content
            if isLoading {
                Spacer()
                ProgressView("Loading pet owners...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                Spacer()
            } else if filteredPetOwners.isEmpty && !searchText.isEmpty {
                // Search results empty
                VStack(spacing: 16) {
                    Spacer()
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: 48))
                        .foregroundColor(.secondary)
                    
                    Text("No Results Found")
                        .font(.title2)
                        .fontWeight(.medium)
                    
                    Text("No pet owners match '\(searchText)'")
                        .font(.body)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                    
                    Spacer()
                }
            } else if petOwners.isEmpty {
                // No pet owners at all
                VStack(spacing: 16) {
                    Spacer()
                    Image(systemName: "heart")
                        .font(.system(size: 48))
                        .foregroundColor(.secondary)
                    
                    Text("No Pet Owners")
                        .font(.title2)
                        .fontWeight(.medium)
                    
                    Text("No pet owners found in the system")
                        .font(.body)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                }
            } else {
                // Pet owners list
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(filteredPetOwners) { owner in
                            NavigationLink(destination: PetOwnerDetailView(petOwner: owner)) {
                                PetOwnerRow(petOwner: owner)
                                    .padding(.horizontal, 16)
                            }
                        }
                    }
                    .padding(.vertical, 16)
                }
                .refreshable {
                    await loadPetOwners()
                }
            }
        }
        .alert("Error", isPresented: $showError) {
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
        .sheet(isPresented: $showAddPetOwner) {
            AddPetOwnerView {
                Task {
                    await loadPetOwners()
                }
            }
        }
        .onAppear {
            if petOwners.isEmpty {
                Task {
                    await loadPetOwners()
                }
            }
        }
    }
    
    @MainActor
    private func loadPetOwners() async {
        isLoading = true
        
        do {
            let owners = try await apiManager.getPetOwnersDetailed()
            self.petOwners = owners
            print("✅ Loaded \(owners.count) pet owners")
        } catch {
            errorMessage = "Failed to load pet owners: \(error.localizedDescription)"
            showError = true
            print("❌ Failed to load pet owners: \(error)")
        }
        
        isLoading = false
    }
}

#Preview {
    PetOwnersView(
        onNavigateToAppointments: {},
        onToggleSidebar: {}
    )
}