import SwiftUI

struct EditMedicalRecordView: View {
    let existingRecord: MedicalRecord
    let pet: Pet
    let onSave: (MedicalRecord) -> Void
    
    @StateObject private var apiManager = APIManager.shared
    @Environment(\.presentationMode) var presentationMode
    
    // Basic Information
    @State private var recordType: String
    @State private var title: String
    @State private var description: String
    @State private var visitDate: Date
    @State private var veterinarianName: String
    @State private var clinicName: String
    
    // Medical Data
    @State private var heartRate: String
    @State private var respiratoryRate: String
    @State private var bloodPressure: String
    @State private var bodyConditionScore: String
    @State private var dentalCondition: String
    @State private var skinCondition: String
    @State private var eyeCondition: String
    @State private var earCondition: String
    
    // Clinical Information
    @State private var diagnosis: String
    @State private var treatment: String
    @State private var medications: String
    @State private var weight: String
    @State private var temperature: String
    @State private var cost: String
    
    // Follow-up
    @State private var followUpRequired: Bool
    @State private var followUpDate: Date
    
    @State private var isLoading = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var showDatePicker = false
    @State private var showFollowUpDatePicker = false
    
    // Record type options
    private let recordTypeOptions = ["checkup", "vaccination", "surgery", "emergency", "dental", "grooming", "other"]
    
    init(existingRecord: MedicalRecord, pet: Pet, onSave: @escaping (MedicalRecord) -> Void) {
        self.existingRecord = existingRecord
        self.pet = pet
        self.onSave = onSave
        
        // Pre-populate with existing record data
        _recordType = State(initialValue: existingRecord.recordType)
        _title = State(initialValue: existingRecord.title)
        _description = State(initialValue: existingRecord.description ?? "")
        _visitDate = State(initialValue: existingRecord.visitDate)
        _veterinarianName = State(initialValue: existingRecord.veterinarianName ?? "")
        _clinicName = State(initialValue: existingRecord.clinicName ?? "")
        
        // Medical Data
        _heartRate = State(initialValue: existingRecord.medicalData?.heartRate ?? "")
        _respiratoryRate = State(initialValue: existingRecord.medicalData?.respiratoryRate ?? "")
        _bloodPressure = State(initialValue: existingRecord.medicalData?.bloodPressure ?? "")
        _bodyConditionScore = State(initialValue: existingRecord.medicalData?.bodyConditionScore ?? "")
        _dentalCondition = State(initialValue: existingRecord.medicalData?.dentalCondition ?? "")
        _skinCondition = State(initialValue: existingRecord.medicalData?.skinCondition ?? "")
        _eyeCondition = State(initialValue: existingRecord.medicalData?.eyeCondition ?? "")
        _earCondition = State(initialValue: existingRecord.medicalData?.earCondition ?? "")
        
        // Clinical Information
        _diagnosis = State(initialValue: existingRecord.diagnosis ?? "")
        _treatment = State(initialValue: existingRecord.treatment ?? "")
        _medications = State(initialValue: existingRecord.medications ?? "")
        _weight = State(initialValue: existingRecord.weight != nil ? String(format: "%.1f", existingRecord.weight!) : "")
        _temperature = State(initialValue: existingRecord.temperature != nil ? String(format: "%.1f", existingRecord.temperature!) : "")
        _cost = State(initialValue: existingRecord.cost != nil ? String(format: "%.2f", existingRecord.cost!) : "")
        
        // Follow-up
        _followUpRequired = State(initialValue: existingRecord.followUpRequired)
        _followUpDate = State(initialValue: existingRecord.followUpDate ?? Date())
    }
    
    var body: some View {
        NavigationView {
            Form {
                // Header Info
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Editing Medical Record")
                            .font(.headline)
                            .foregroundColor(.primary)
                        
                        Text("This will create a new version (v\(existingRecord.version + 1)) and mark it as current")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        HStack {
                            Text("Previous Version:")
                            Text("v\(existingRecord.version)")
                                .fontWeight(.medium)
                            Spacer()
                            Text(DateFormatter.mediumDate.string(from: existingRecord.visitDate))
                                .foregroundColor(.secondary)
                        }
                        .font(.caption)
                    }
                    .padding(.vertical, 4)
                }
                
                Section(header: Text("Basic Information")) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Record Type")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Picker("Record Type", selection: $recordType) {
                            ForEach(recordTypeOptions, id: \.self) { type in
                                Text(type.capitalized).tag(type)
                            }
                        }
                        .pickerStyle(MenuPickerStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Title")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter record title", text: $title)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Description")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter description (optional)", text: $description, axis: .vertical)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .lineLimit(2...4)
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Visit Date")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Button(action: {
                            showDatePicker = true
                        }) {
                            HStack {
                                Text(DateFormatter.mediumDateTime.string(from: visitDate))
                                    .foregroundColor(.primary)
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
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Veterinarian Name")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter veterinarian name (optional)", text: $veterinarianName)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Clinic Name")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter clinic name (optional)", text: $clinicName)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                }
                
                Section(header: Text("Vital Signs & Physical Exam")) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Weight (lbs)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter weight", text: $weight)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .keyboardType(.decimalPad)
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Temperature (°F)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter temperature", text: $temperature)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .keyboardType(.decimalPad)
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Heart Rate (bpm)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter heart rate", text: $heartRate)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Respiratory Rate")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter respiratory rate", text: $respiratoryRate)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Blood Pressure")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter blood pressure", text: $bloodPressure)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Body Condition Score")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter body condition score", text: $bodyConditionScore)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                }
                
                Section(header: Text("Physical Examination")) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Dental Condition")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter dental condition", text: $dentalCondition)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Skin Condition")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter skin condition", text: $skinCondition)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Eye Condition")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter eye condition", text: $eyeCondition)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Ear Condition")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter ear condition", text: $earCondition)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                }
                
                Section(header: Text("Clinical Information")) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Diagnosis")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter diagnosis (optional)", text: $diagnosis, axis: .vertical)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .lineLimit(2...4)
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Treatment")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter treatment (optional)", text: $treatment, axis: .vertical)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .lineLimit(2...4)
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Medications")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter medications (optional)", text: $medications, axis: .vertical)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .lineLimit(2...4)
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Cost")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter cost (optional)", text: $cost)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .keyboardType(.decimalPad)
                    }
                }
                
                Section(header: Text("Follow-up")) {
                    Toggle("Follow-up Required", isOn: $followUpRequired)
                    
                    if followUpRequired {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Follow-up Date")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            
                            Button(action: {
                                showFollowUpDatePicker = true
                            }) {
                                HStack {
                                    Text(DateFormatter.mediumDateTime.string(from: followUpDate))
                                        .foregroundColor(.primary)
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
                        }
                    }
                }
            }
            .navigationTitle("Edit Medical Record")
            .navigationBarTitleDisplayMode(.inline)
            .navigationBarItems(
                leading: Button("Cancel") {
                    presentationMode.wrappedValue.dismiss()
                },
                trailing: Button("Save New Version") {
                    Task {
                        await saveNewVersion()
                    }
                }
                .disabled(isLoading || title.isEmpty)
            )
            .alert("Error", isPresented: $showError) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
            .sheet(isPresented: $showDatePicker) {
                DateTimePickerSheet(selectedDate: $visitDate, showDatePicker: $showDatePicker, title: "Visit Date")
            }
            .sheet(isPresented: $showFollowUpDatePicker) {
                DateTimePickerSheet(selectedDate: $followUpDate, showDatePicker: $showFollowUpDatePicker, title: "Follow-up Date")
            }
        }
    }
    
    @MainActor
    private func saveNewVersion() async {
        isLoading = true
        
        // Parse numeric values
        let parsedWeight: Double? = weight.isEmpty ? nil : Double(weight)
        let parsedTemperature: Double? = temperature.isEmpty ? nil : Double(temperature)
        let parsedCost: Double? = cost.isEmpty ? nil : Double(cost)
        
        // Create medical data
        let medicalData = MedicalData(
            heartRate: heartRate.isEmpty ? nil : heartRate,
            respiratoryRate: respiratoryRate.isEmpty ? nil : respiratoryRate,
            bloodPressure: bloodPressure.isEmpty ? nil : bloodPressure,
            bodyConditionScore: bodyConditionScore.isEmpty ? nil : bodyConditionScore,
            dentalCondition: dentalCondition.isEmpty ? nil : dentalCondition,
            skinCondition: skinCondition.isEmpty ? nil : skinCondition,
            eyeCondition: eyeCondition.isEmpty ? nil : eyeCondition,
            earCondition: earCondition.isEmpty ? nil : earCondition
        )
        
        // Create update request (backend handles versioning automatically)
        let updateRequest = UpdateMedicalRecordRequest(
            recordType: recordType,
            title: title.trimmingCharacters(in: .whitespacesAndNewlines),
            description: description.isEmpty ? "" : description.trimmingCharacters(in: .whitespacesAndNewlines),
            medicalData: medicalData,
            visitDate: visitDate,
            veterinarianName: veterinarianName.isEmpty ? "" : veterinarianName.trimmingCharacters(in: .whitespacesAndNewlines),
            clinicName: clinicName.isEmpty ? "" : clinicName.trimmingCharacters(in: .whitespacesAndNewlines),
            diagnosis: diagnosis.isEmpty ? "" : diagnosis.trimmingCharacters(in: .whitespacesAndNewlines),
            treatment: treatment.isEmpty ? "" : treatment.trimmingCharacters(in: .whitespacesAndNewlines),
            medications: medications.isEmpty ? "" : medications.trimmingCharacters(in: .whitespacesAndNewlines),
            followUpRequired: followUpRequired,
            followUpDate: followUpRequired ? followUpDate : nil,
            weight: parsedWeight,
            temperature: parsedTemperature,
            cost: parsedCost
        )
        
        do {
            let updatedRecord = try await apiManager.updateMedicalRecord(recordId: existingRecord.id, request: updateRequest)
            print("✅ Updated medical record: \(updatedRecord.id)")
            onSave(updatedRecord)
            presentationMode.wrappedValue.dismiss()
        } catch {
            errorMessage = "Failed to update medical record: \(error.localizedDescription)"
            showError = true
            print("❌ Failed to update medical record: \(error)")
        }
        
        isLoading = false
    }
}

#Preview {
    let sampleRecord = MedicalRecord(
        id: "sample-record-id",
        petId: "sample-pet-id",
        recordType: "vaccination",
        title: "Annual Vaccinations",
        description: "DHPP and Rabies vaccines administered. Pet showed no adverse reactions during or after vaccination.",
        medicalData: MedicalData(
            heartRate: "120",
            respiratoryRate: "24",
            bloodPressure: "Normal",
            bodyConditionScore: "5/9",
            dentalCondition: "Good",
            skinCondition: "Normal",
            eyeCondition: "Clear",
            earCondition: "Clean"
        ),
        visitDate: Date(),
        veterinarianName: "Dr. Sarah Johnson",
        clinicName: "Happy Paws Veterinary Clinic",
        diagnosis: nil,
        treatment: "Monitor for any delayed reactions. Follow up in 1 year for next annual vaccinations.",
        medications: "DHPP Vaccine, Rabies Vaccine",
        followUpRequired: true,
        followUpDate: Calendar.current.date(byAdding: .year, value: 1, to: Date()),
        weight: 45.2,
        temperature: 101.5,
        cost: 125.00,
        version: 1,
        isCurrent: true,
        createdByUserId: "vet-user-id",
        createdAt: Date(),
        updatedAt: Date(),
        isFollowUpDue: false,
        daysSinceVisit: 0
    )
    
    let samplePet = Pet(
        id: "sample-pet-id",
        name: "Buddy",
        species: "Dog",
        breed: "Golden Retriever",
        color: "Golden",
        gender: "Male",
        weight: 65.5,
        dateOfBirth: Calendar.current.date(byAdding: .year, value: -3, to: Date()),
        microchipId: "123456789012345",
        spayedNeutered: true,
        allergies: "None known",
        medications: "Heartworm prevention",
        medicalNotes: "Friendly and well-behaved",
        emergencyContact: "Jane Smith",
        emergencyPhone: "+1-555-123-4567",
        ownerId: "owner-id-1",
        isActive: true,
        createdAt: Date(),
        updatedAt: Date(),
        ageYears: 3,
        displayName: "Buddy (Dog)",
        owner: PetOwner(
            id: "owner-id-1",
            userId: nil,
            fullName: "John Smith",
            email: "john.smith@email.com",
            phone: "+1-555-123-4567"
        )
    )
    
    EditMedicalRecordView(existingRecord: sampleRecord, pet: samplePet) { _ in }
}
