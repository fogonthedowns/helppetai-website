import SwiftUI

struct AddMedicalRecordView: View {
    let pet: Pet
    let onSave: (MedicalRecord) -> Void
    
    @StateObject private var apiManager = APIManager.shared
    @Environment(\.presentationMode) var presentationMode
    
    // Basic Information
    @State private var recordType: String = "checkup"
    @State private var title: String = "Medical Record"
    @State private var description: String = ""
    @State private var visitDate: Date = Date()
    @State private var veterinarianName: String = ""
    @State private var clinicName: String = ""
    
    // Medical Data
    @State private var heartRate: String = ""
    @State private var respiratoryRate: String = ""
    @State private var bloodPressure: String = ""
    @State private var bodyConditionScore: String = ""
    @State private var dentalCondition: String = ""
    @State private var skinCondition: String = ""
    @State private var eyeCondition: String = ""
    @State private var earCondition: String = ""
    
    // Clinical Information
    @State private var diagnosis: String = ""
    @State private var treatment: String = ""
    @State private var medications: String = ""
    @State private var weight: String = ""
    @State private var temperature: String = ""
    @State private var cost: String = ""
    
    // Follow-up
    @State private var followUpRequired: Bool = false
    @State private var followUpDate: Date = Date()
    
    @State private var isLoading = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var showDatePicker = false
    @State private var showFollowUpDatePicker = false
    
    // Record type options
    private let recordTypeOptions = ["checkup", "vaccination", "surgery", "emergency", "dental", "grooming", "other"]
    
    var body: some View {
        NavigationView {
            Form {
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
            .navigationTitle("Add Medical Record")
            .navigationBarTitleDisplayMode(.inline)
            .navigationBarItems(
                leading: Button("Cancel") {
                    presentationMode.wrappedValue.dismiss()
                },
                trailing: Button("Save") {
                    Task {
                        await saveMedicalRecord()
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
    private func saveMedicalRecord() async {
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
        
        let createRequest = CreateMedicalRecordRequest(
            recordType: recordType,
            title: title.trimmingCharacters(in: .whitespacesAndNewlines),
            description: description.isEmpty ? nil : description.trimmingCharacters(in: .whitespacesAndNewlines),
            medicalData: medicalData,
            visitDate: visitDate,
            veterinarianName: veterinarianName.isEmpty ? nil : veterinarianName.trimmingCharacters(in: .whitespacesAndNewlines),
            clinicName: clinicName.isEmpty ? nil : clinicName.trimmingCharacters(in: .whitespacesAndNewlines),
            diagnosis: diagnosis.isEmpty ? nil : diagnosis.trimmingCharacters(in: .whitespacesAndNewlines),
            treatment: treatment.isEmpty ? nil : treatment.trimmingCharacters(in: .whitespacesAndNewlines),
            medications: medications.isEmpty ? nil : medications.trimmingCharacters(in: .whitespacesAndNewlines),
            followUpRequired: followUpRequired,
            followUpDate: followUpRequired ? followUpDate : nil,
            weight: parsedWeight,
            temperature: parsedTemperature,
            cost: parsedCost,
            petId: pet.id
        )
        
        do {
            let newMedicalRecord = try await apiManager.createMedicalRecord(createRequest)
            onSave(newMedicalRecord)
            presentationMode.wrappedValue.dismiss()
        } catch {
            errorMessage = "Failed to create medical record: \(error.localizedDescription)"
            showError = true
            print("❌ Failed to create medical record: \(error)")
        }
        
        isLoading = false
    }
}

struct DateTimePickerSheet: View {
    @Binding var selectedDate: Date
    @Binding var showDatePicker: Bool
    let title: String
    @State private var tempDate: Date = Date()
    
    var body: some View {
        NavigationView {
            VStack {
                DatePicker(
                    "Select Date and Time",
                    selection: $tempDate,
                    displayedComponents: [.date, .hourAndMinute]
                )
                .datePickerStyle(WheelDatePickerStyle())
                .padding()
                
                Spacer()
            }
            .navigationTitle(title)
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
            tempDate = selectedDate
        }
    }
}

extension DateFormatter {
    static let mediumDateTime: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter
    }()
}

#Preview {
    let samplePet = Pet(
        id: "1",
        name: "Jackson",
        species: "Dog",
        breed: "Golden Retriever",
        color: "Golden",
        gender: "Male",
        weight: 71.0,
        dateOfBirth: Date(),
        microchipId: "123456789",
        spayedNeutered: false,
        allergies: nil,
        medications: nil,
        medicalNotes: nil,
        emergencyContact: nil,
        emergencyPhone: nil,
        ownerId: "owner1",
        isActive: true,
        createdAt: Date(),
        updatedAt: Date(),
        ageYears: 5,
        displayName: "Jackson (Dog)",
        owner: nil
    )
    
    AddMedicalRecordView(pet: samplePet) { _ in }
}
