import SwiftUI

struct AddPetView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var apiManager = APIManager.shared
    
    let ownerId: String
    let onComplete: () -> Void
    
    // Form state
    @State private var name = ""
    @State private var species = "Dog"
    @State private var breed = ""
    @State private var color = ""
    @State private var gender = "Male"
    @State private var weight = ""
    @State private var dateOfBirth = Date()
    @State private var microchipId = ""
    @State private var spayedNeutered: Bool? = nil
    @State private var allergies = ""
    @State private var medications = ""
    @State private var medicalNotes = ""
    @State private var emergencyContact = ""
    @State private var emergencyPhone = ""
    
    // UI state
    @State private var isCreating = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var showSpayedNeuteredPicker = false
    
    private let speciesOptions = ["Dog", "Cat", "Bird", "Rabbit", "Other"]
    private let genderOptions = ["Male", "Female"]
    private let spayedNeuteredOptions = ["Yes", "No", "Unknown"]
    
    var body: some View {
        NavigationView {
            Form {
                // Basic Information Section
                basicInfoSection
                
                // Physical Details Section
                physicalDetailsSection
                
                // Medical Information Section
                medicalInfoSection
                
                // Emergency Contact Section
                emergencyContactSection
                
                // Create Button Section
                createButtonSection
            }
            .navigationTitle("Add Pet")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .disabled(isCreating)
                }
            }
            .alert("Error", isPresented: $showError) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
        }
    }
    
    // MARK: - View Sections
    
    private var basicInfoSection: some View {
        Section("Basic Information") {
            TextField("Pet Name", text: $name)
                .autocapitalization(.words)
            
            Picker("Species", selection: $species) {
                ForEach(speciesOptions, id: \.self) { species in
                    Text(species).tag(species)
                }
            }
            .pickerStyle(.menu)
            
            TextField("Breed (Optional)", text: $breed)
                .autocapitalization(.words)
            
            Picker("Gender", selection: $gender) {
                ForEach(genderOptions, id: \.self) { gender in
                    Text(gender).tag(gender)
                }
            }
            .pickerStyle(.segmented)
        }
    }
    
    private var physicalDetailsSection: some View {
        Section("Physical Details") {
            TextField("Color (Optional)", text: $color)
                .autocapitalization(.words)
            
            TextField("Weight in lbs (Optional)", text: $weight)
                .keyboardType(.decimalPad)
            
            DatePicker("Date of Birth", selection: $dateOfBirth, displayedComponents: .date)
                .datePickerStyle(.compact)
            
            TextField("Microchip ID (Optional)", text: $microchipId)
            
            HStack {
                Text("Spayed/Neutered")
                Spacer()
                Button(spayedNeuteredDisplayText) {
                    showSpayedNeuteredPicker = true
                }
                .foregroundColor(.blue)
            }
            .confirmationDialog("Spayed/Neutered Status", isPresented: $showSpayedNeuteredPicker) {
                Button("Yes") { spayedNeutered = true }
                Button("No") { spayedNeutered = false }
                Button("Unknown") { spayedNeutered = nil }
                Button("Cancel", role: .cancel) { }
            }
        }
    }
    
    private var medicalInfoSection: some View {
        Section("Medical Information") {
            TextField("Allergies (Optional)", text: $allergies, axis: .vertical)
                .lineLimit(3, reservesSpace: true)
            
            TextField("Current Medications (Optional)", text: $medications, axis: .vertical)
                .lineLimit(3, reservesSpace: true)
            
            TextField("Medical Notes (Optional)", text: $medicalNotes, axis: .vertical)
                .lineLimit(4, reservesSpace: true)
        }
    }
    
    private var emergencyContactSection: some View {
        Section("Emergency Contact") {
            TextField("Emergency Contact Name (Optional)", text: $emergencyContact)
                .autocapitalization(.words)
            
            TextField("Emergency Phone (Optional)", text: $emergencyPhone)
                .keyboardType(.phonePad)
        }
    }
    
    private var createButtonSection: some View {
        Section {
            Button(action: createPet) {
                HStack {
                    if isCreating {
                        ProgressView()
                            .scaleEffect(0.8)
                            .padding(.trailing, 8)
                    }
                    Text(isCreating ? "Creating Pet..." : "Create Pet")
                }
                .frame(maxWidth: .infinity)
            }
            .disabled(name.isEmpty || isCreating)
            .buttonStyle(.borderedProminent)
        }
        .listRowInsets(EdgeInsets())
        .listRowBackground(Color.clear)
    }
    
    // MARK: - Computed Properties
    
    private var spayedNeuteredDisplayText: String {
        switch spayedNeutered {
        case true: return "Yes"
        case false: return "No"
        case nil: return "Unknown"
        case .some(_):
            return "No"
        }
    }
    
    // MARK: - Actions
    
    private func createPet() {
        Task {
            await performCreatePet()
        }
    }
    
    @MainActor
    private func performCreatePet() async {
        guard !name.isEmpty else {
            errorMessage = "Pet name is required"
            showError = true
            return
        }
        
        isCreating = true
        
        do {
            let request = CreatePetRequest(
                name: name,
                species: species,
                breed: breed.isEmpty ? nil : breed,
                color: color.isEmpty ? nil : color,
                gender: gender,
                weight: Double(weight),
                dateOfBirth: dateOfBirth,
                microchipId: microchipId.isEmpty ? nil : microchipId,
                spayedNeutered: spayedNeutered,
                allergies: allergies.isEmpty ? nil : allergies,
                medications: medications.isEmpty ? nil : medications,
                medicalNotes: medicalNotes.isEmpty ? nil : medicalNotes,
                emergencyContact: emergencyContact.isEmpty ? nil : emergencyContact,
                emergencyPhone: emergencyPhone.isEmpty ? nil : emergencyPhone,
                ownerId: ownerId
            )
            
            let _ = try await apiManager.createPet(request)
            
            print("✅ Pet created successfully: \(name)")
            onComplete()
            dismiss()
            
        } catch {
            errorMessage = "Failed to create pet: \(error.localizedDescription)"
            showError = true
            print("❌ Failed to create pet: \(error)")
        }
        
        isCreating = false
    }
}

// MARK: - Create Pet Request Model
struct CreatePetRequest: Codable {
    let name: String
    let species: String
    let breed: String?
    let color: String?
    let gender: String
    let weight: Double?
    let dateOfBirth: Date
    let microchipId: String?
    let spayedNeutered: Bool?
    let allergies: String?
    let medications: String?
    let medicalNotes: String?
    let emergencyContact: String?
    let emergencyPhone: String?
    let ownerId: String
    
    enum CodingKeys: String, CodingKey {
        case name, species, breed, color, gender, weight, allergies, medications
        case dateOfBirth = "date_of_birth"
        case microchipId = "microchip_id"
        case spayedNeutered = "spayed_neutered"
        case medicalNotes = "medical_notes"
        case emergencyContact = "emergency_contact"
        case emergencyPhone = "emergency_phone"
        case ownerId = "owner_id"
    }
}

#Preview {
    AddPetView(ownerId: "sample-owner-id", onComplete: {})
}
