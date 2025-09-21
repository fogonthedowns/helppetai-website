import SwiftUI

struct EditPetView: View {
    let pet: Pet
    let onSave: (Pet) -> Void
    
    @StateObject private var apiManager = APIManager.shared
    @Environment(\.presentationMode) var presentationMode
    
    @State private var name: String
    @State private var species: String
    @State private var breed: String
    @State private var color: String
    @State private var gender: String
    @State private var weight: String
    @State private var dateOfBirth: Date?
    @State private var microchipId: String
    @State private var spayedNeutered: Bool?
    @State private var allergies: String
    @State private var medications: String
    @State private var medicalNotes: String
    @State private var emergencyContact: String
    @State private var emergencyPhone: String
    
    @State private var isLoading = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var showDatePicker = false
    
    // Gender options
    private let genderOptions = ["Male", "Female", "Unknown"]
    private let speciesOptions = ["Dog", "Cat", "Bird", "Rabbit", "Other"]
    
    init(pet: Pet, onSave: @escaping (Pet) -> Void) {
        self.pet = pet
        self.onSave = onSave
        
        // Initialize state variables with current values
        _name = State(initialValue: pet.name)
        _species = State(initialValue: pet.species)
        _breed = State(initialValue: pet.breed ?? "")
        _color = State(initialValue: pet.color ?? "")
        _gender = State(initialValue: pet.gender ?? "Unknown")
        _weight = State(initialValue: pet.weight != nil ? String(format: "%.1f", pet.weight!) : "")
        _dateOfBirth = State(initialValue: pet.dateOfBirth)
        _microchipId = State(initialValue: pet.microchipId ?? "")
        _spayedNeutered = State(initialValue: pet.spayedNeutered)
        _allergies = State(initialValue: pet.allergies ?? "")
        _medications = State(initialValue: pet.medications ?? "")
        _medicalNotes = State(initialValue: pet.medicalNotes ?? "")
        _emergencyContact = State(initialValue: pet.emergencyContact ?? "")
        _emergencyPhone = State(initialValue: pet.emergencyPhone ?? "")
    }
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Basic Information")) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Name")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter pet name", text: $name)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Species")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Picker("Species", selection: $species) {
                            ForEach(speciesOptions, id: \.self) { option in
                                Text(option).tag(option)
                            }
                        }
                        .pickerStyle(SegmentedPickerStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Breed")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter breed (optional)", text: $breed)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Color")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter color (optional)", text: $color)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                }
                
                Section(header: Text("Physical Details")) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Gender")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Picker("Gender", selection: $gender) {
                            ForEach(genderOptions, id: \.self) { option in
                                Text(option).tag(option)
                            }
                        }
                        .pickerStyle(SegmentedPickerStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Weight (lbs)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter weight", text: $weight)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .keyboardType(.decimalPad)
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Date of Birth")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Button(action: {
                            showDatePicker = true
                        }) {
                            HStack {
                                Text(dateOfBirth != nil ? DateFormatter.shortDate.string(from: dateOfBirth!) : "Select date (optional)")
                                    .foregroundColor(dateOfBirth != nil ? .primary : .secondary)
                                Spacer()
                                Image(systemName: "calendar")
                                    .foregroundColor(.blue)
                            }
                            .padding(.vertical, 8)
                            .padding(.horizontal, 12)
                            .background(Color(.systemGray6))
                            .cornerRadius(8)
                        }
                        .buttonStyle(PlainButtonStyle())
                        
                        if dateOfBirth != nil {
                            Button("Clear Date") {
                                dateOfBirth = nil
                            }
                            .font(.caption)
                            .foregroundColor(.red)
                        }
                    }
                    
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Spayed/Neutered")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        HStack(spacing: 20) {
                            Button(action: {
                                spayedNeutered = true
                            }) {
                                HStack {
                                    Image(systemName: spayedNeutered == true ? "checkmark.circle.fill" : "circle")
                                        .foregroundColor(spayedNeutered == true ? .blue : .gray)
                                    Text("Yes")
                                }
                            }
                            .buttonStyle(PlainButtonStyle())
                            
                            Button(action: {
                                spayedNeutered = false
                            }) {
                                HStack {
                                    Image(systemName: spayedNeutered == false ? "checkmark.circle.fill" : "circle")
                                        .foregroundColor(spayedNeutered == false ? .blue : .gray)
                                    Text("No")
                                }
                            }
                            .buttonStyle(PlainButtonStyle())
                            
                            Button(action: {
                                spayedNeutered = nil
                            }) {
                                HStack {
                                    Image(systemName: spayedNeutered == nil ? "checkmark.circle.fill" : "circle")
                                        .foregroundColor(spayedNeutered == nil ? .blue : .gray)
                                    Text("Unknown")
                                }
                            }
                            .buttonStyle(PlainButtonStyle())
                        }
                    }
                }
                
                Section(header: Text("Identification")) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Microchip ID")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter microchip ID (optional)", text: $microchipId)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                }
                
                Section(header: Text("Medical Information")) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Allergies")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter allergies (optional)", text: $allergies, axis: .vertical)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .lineLimit(2...4)
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Medications")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter current medications (optional)", text: $medications, axis: .vertical)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .lineLimit(2...4)
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Medical Notes")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter medical notes (optional)", text: $medicalNotes, axis: .vertical)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .lineLimit(3...6)
                    }
                }
                
                Section(header: Text("Emergency Contact")) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Emergency Contact Name")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter emergency contact (optional)", text: $emergencyContact)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Emergency Phone")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter emergency phone (optional)", text: $emergencyPhone)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .keyboardType(.phonePad)
                    }
                }
            }
            .navigationTitle("Edit Pet")
            .navigationBarTitleDisplayMode(.inline)
            .navigationBarItems(
                leading: Button("Cancel") {
                    presentationMode.wrappedValue.dismiss()
                },
                trailing: Button("Save") {
                    Task {
                        await savePet()
                    }
                }
                .disabled(isLoading || name.isEmpty || species.isEmpty)
            )
            .alert("Error", isPresented: $showError) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
            .sheet(isPresented: $showDatePicker) {
                DatePickerSheet(selectedDate: $dateOfBirth, showDatePicker: $showDatePicker)
            }
        }
    }
    
    @MainActor
    private func savePet() async {
        isLoading = true
        
        // Parse weight
        let parsedWeight: Double? = weight.isEmpty ? nil : Double(weight)
        
        let updateRequest = UpdatePetRequest(
            name: name.trimmingCharacters(in: .whitespacesAndNewlines),
            species: species,
            breed: breed.isEmpty ? nil : breed.trimmingCharacters(in: .whitespacesAndNewlines),
            color: color.isEmpty ? nil : color.trimmingCharacters(in: .whitespacesAndNewlines),
            gender: gender == "Unknown" ? nil : gender,
            weight: parsedWeight,
            dateOfBirth: dateOfBirth,
            microchipId: microchipId.isEmpty ? nil : microchipId.trimmingCharacters(in: .whitespacesAndNewlines),
            spayedNeutered: spayedNeutered,
            allergies: allergies.isEmpty ? nil : allergies.trimmingCharacters(in: .whitespacesAndNewlines),
            medications: medications.isEmpty ? nil : medications.trimmingCharacters(in: .whitespacesAndNewlines),
            medicalNotes: medicalNotes.isEmpty ? nil : medicalNotes.trimmingCharacters(in: .whitespacesAndNewlines),
            emergencyContact: emergencyContact.isEmpty ? nil : emergencyContact.trimmingCharacters(in: .whitespacesAndNewlines),
            emergencyPhone: emergencyPhone.isEmpty ? nil : emergencyPhone.trimmingCharacters(in: .whitespacesAndNewlines)
        )
        
        do {
            let updatedPet = try await apiManager.updatePet(petId: pet.id, request: updateRequest)
            onSave(updatedPet)
            presentationMode.wrappedValue.dismiss()
        } catch {
            errorMessage = "Failed to update pet: \(error.localizedDescription)"
            showError = true
            print("❌ Failed to update pet: \(error)")
        }
        
        isLoading = false
    }
}

struct DatePickerSheet: View {
    @Binding var selectedDate: Date?
    @Binding var showDatePicker: Bool
    @State private var tempDate: Date = Date()
    
    var body: some View {
        NavigationView {
            VStack {
                DatePicker(
                    "Select Date",
                    selection: $tempDate,
                    in: ...Date(),
                    displayedComponents: .date
                )
                .datePickerStyle(WheelDatePickerStyle())
                .padding()
                
                Spacer()
            }
            .navigationTitle("Date of Birth")
            .navigationBarTitleDisplayMode(.inline)
            .navigationBarItems(
                leading: Button("Cancel") {
                    showDatePicker = false
                },
                trailing: Button("Done") {
                    selectedDate = tempDate
                    showDatePicker = false
                }
            )
        }
        .onAppear {
            tempDate = selectedDate ?? Date()
        }
    }
}

extension DateFormatter {
    static let shortDate: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return formatter
    }()
}

#Preview {
    let samplePet = Pet(
        id: "1",
        name: "Fido",
        species: "Dog",
        breed: "Golden Retriever",
        color: "Golden",
        gender: "Male",
        weight: 52.0,
        dateOfBirth: Date(),
        microchipId: "123456789",
        spayedNeutered: true,
        allergies: "Corn flakes",
        medications: "Diarrhea meds",
        medicalNotes: "Healthy dog",
        emergencyContact: "John Doe",
        emergencyPhone: "555-1234",
        ownerId: "owner1",
        isActive: true,
        createdAt: Date(),
        updatedAt: Date(),
        ageYears: 5,
        displayName: "Fido (Dog)",
        owner: nil
    )
    
    EditPetView(pet: samplePet) { _ in }
}
