import SwiftUI

struct PetOwnerDetailView: View {
    @State private var petOwner: PetOwnerDetails
    let onBack: (() -> Void)?
    
    // Initializer for NavigationLink usage (no onBack needed)
    init(petOwner: PetOwnerDetails) {
        self._petOwner = State(initialValue: petOwner)
        self.onBack = nil
    }
    
    // Initializer for sheet usage (with onBack)
    init(petOwner: PetOwnerDetails, onBack: @escaping () -> Void) {
        self._petOwner = State(initialValue: petOwner)
        self.onBack = onBack
    }
    
    @StateObject private var apiManager = APIManager.shared
    @State private var pets: [Pet] = []
    @State private var isLoading = true
    @State private var errorMessage = ""
    @State private var showError = false
    @State private var showAddPet = false
    @State private var showEditPetOwner = false
    
    var body: some View {
        VStack(spacing: 0) {
            
            // Pet owner info card
            VStack(alignment: .leading, spacing: 16) {
                // Header with avatar and name
                HStack(spacing: 16) {
                    ZStack {
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 60, height: 60)
                        
                        Text(String(petOwner.fullName.prefix(1)))
                            .font(.title)
                            .fontWeight(.medium)
                            .foregroundColor(.white)
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text(petOwner.fullName)
                            .font(.title2)
                            .fontWeight(.medium)
                        
                        Text(petOwner.email)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                }
                
                // Contact information
                VStack(alignment: .leading, spacing: 8) {
                    if let phone = petOwner.phone, !phone.isEmpty {
                        ContactInfoRow(icon: "phone.fill", title: "Phone", value: formatPhoneNumber(phone), color: .green)
                    }
                    
                    if let secondaryPhone = petOwner.secondaryPhone, !secondaryPhone.isEmpty {
                        ContactInfoRow(icon: "phone.badge.plus", title: "Secondary", value: formatPhoneNumber(secondaryPhone), color: .orange)
                    }
                    
                    if let address = petOwner.address, !address.isEmpty {
                        ContactInfoRow(icon: "location.fill", title: "Address", value: address, color: .blue)
                    }
                    
                    if let emergency = petOwner.emergencyContact, !emergency.isEmpty {
                        ContactInfoRow(icon: "exclamationmark.triangle.fill", title: "Emergency", value: formatPhoneNumber(emergency), color: .red)
                    }
                }
            }
            .padding(20)
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color(.separator), lineWidth: 0.5)
            )
            .padding(.horizontal, 16)
            .padding(.top, 16)
            
            // Pets section
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text("Pets")
                        .font(.headline)
                        .fontWeight(.medium)
                    
                    Spacer()
                    
                    if !pets.isEmpty {
                        Text("\(pets.count) pet\(pets.count == 1 ? "" : "s")")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.top, 20)
                
                if isLoading {
                    HStack {
                        Spacer()
                        ProgressView("Loading pets...")
                        Spacer()
                    }
                    .padding(.vertical, 40)
                } else if pets.isEmpty {
                    VStack(spacing: 12) {
                        Image(systemName: "pawprint")
                            .font(.system(size: 32))
                            .foregroundColor(.secondary)
                        
                        Text("No Pets")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        
                        Text("This owner has no registered pets")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 40)
                } else {
                    ScrollView {
                        LazyVStack(spacing: 8) {
                            ForEach(pets) { pet in
                                NavigationLink(destination: PetDetailView(
                                    pet: pet,
                                    backButtonTitle: "Pet Owner",
                                    onBack: { },
                                    onPetUpdated: {
                                        Task {
                                            await loadPets()
                                        }
                                    }
                                )) {
                                    PetRow(pet: pet)
                                        .padding(.horizontal, 16)
                                }
                                .buttonStyle(PlainButtonStyle())
                            }
                        }
                        .padding(.vertical, 8)
                    }
                }
            }
            
            Spacer()
            
            // Add Pet button
            VStack {
                Button(action: {
                    showAddPet = true
                }) {
                    HStack {
                        Image(systemName: "plus.circle.fill")
                        Text("Add Pet")
                    }
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .cornerRadius(12)
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 20)
            }
        }
        .navigationTitle(petOwner.fullName)
        .navigationBarTitleDisplayMode(.large)
        .navigationBarItems(trailing: 
            Button("Edit") {
                showEditPetOwner = true
            }
            .foregroundColor(.blue)
        )
        .alert("Error", isPresented: $showError) {
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
        .sheet(isPresented: $showAddPet) {
            AddPetView(ownerId: petOwner.uuid) {
                Task {
                    await loadPets()
                }
            }
        }
        .sheet(isPresented: $showEditPetOwner) {
            EditPetOwnerView(petOwner: petOwner) { updatedPetOwner in
                // Update the local pet owner state with the updated data
                self.petOwner = updatedPetOwner
                showEditPetOwner = false
            }
        }
        .onAppear {
            Task {
                await loadPets()
            }
        }
    }
    
    @MainActor
    private func loadPets() async {
        isLoading = true
        
        do {
            let fetchedPets = try await apiManager.getPetsByOwner(ownerId: petOwner.uuid)
            self.pets = fetchedPets
            print("✅ Loaded \(fetchedPets.count) pets for owner \(petOwner.fullName)")
        } catch {
            errorMessage = "Failed to load pets: \(error.localizedDescription)"
            showError = true
            print("❌ Failed to load pets: \(error)")
        }
        
        isLoading = false
    }
    
    private func formatPhoneNumber(_ phone: String) -> String {
        // Simple phone number formatting
        let digits = phone.components(separatedBy: CharacterSet.decimalDigits.inverted).joined()
        
        if digits.count == 10 {
            return String(format: "(%@) %@-%@",
                         String(digits.prefix(3)),
                         String(digits.dropFirst(3).prefix(3)),
                         String(digits.suffix(4)))
        }
        
        return phone // Return original if not standard format
    }
}

struct ContactInfoRow: View {
    let icon: String
    let title: String
    let value: String
    let color: Color
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.subheadline)
                .foregroundColor(color)
                .frame(width: 20)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text(value)
                    .font(.subheadline)
                    .foregroundColor(.primary)
            }
            
            Spacer()
        }
        .padding(.vertical, 4)
    }
}

struct PetRow: View {
    let pet: Pet
    
    var body: some View {
        HStack(spacing: 12) {
            // Pet type icon
            Image(systemName: pet.species.lowercased() == "dog" ? "pawprint.fill" : "cat.fill")
                .font(.title2)
                .foregroundColor(.blue)
                .frame(width: 30)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(pet.name)
                    .font(.headline)
                    .fontWeight(.medium)
                
                HStack(spacing: 4) {
                    Text(pet.species)
                    
                    if let breed = pet.breed {
                        Text("• \(breed)")
                    }
                    
                    if let age = pet.ageYears {
                        Text("• \(age)y")
                    }
                }
                .font(.caption)
                .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color(.separator), lineWidth: 0.5)
        )
    }
}

#Preview {
    let sampleOwner = PetOwnerDetails(
        uuid: "1",
        userId: nil,
        fullName: "Justin Zollars",
        email: "justin@jz.io",
        phone: "4157549214",
        secondaryPhone: "4192831624",
        address: "1248 Military West Benicia CA, 94510",
        emergencyContact: "4192831624",
        preferredCommunication: "email",
        notificationsEnabled: true,
        createdAt: Date(),
        updatedAt: Date()
    )
    
    PetOwnerDetailView(petOwner: sampleOwner, onBack: {})
}