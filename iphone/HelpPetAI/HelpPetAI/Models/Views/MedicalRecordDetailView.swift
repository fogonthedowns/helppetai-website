import SwiftUI

struct MedicalRecordDetailView: View {
    let medicalRecord: MedicalRecord
    let pet: Pet
    let onRecordUpdated: (() -> Void)?
    
    @StateObject private var apiManager = APIManager.shared
    @State private var showEditRecord = false
    @State private var refreshTrigger = UUID()
    
    // Initializer for NavigationLink usage
    init(medicalRecord: MedicalRecord, pet: Pet, onRecordUpdated: (() -> Void)? = nil) {
        self.medicalRecord = medicalRecord
        self.pet = pet
        self.onRecordUpdated = onRecordUpdated
    }
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Header Card
                VStack(alignment: .leading, spacing: 16) {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(medicalRecord.title)
                                .font(.title2)
                                .fontWeight(.bold)
                            
                            HStack(spacing: 8) {
                                Text(medicalRecord.recordType.capitalized)
                                    .font(.caption)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 2)
                                    .background(Color.blue.opacity(0.2))
                                    .foregroundColor(.blue)
                                    .cornerRadius(4)
                                
                                if medicalRecord.isCurrent {
                                    Text("v\(medicalRecord.version) • Current")
                                        .font(.caption)
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 2)
                                        .background(Color.green.opacity(0.2))
                                        .foregroundColor(.green)
                                        .cornerRadius(4)
                                }
                            }
                        }
                        
                        Spacer()
                        
                        VStack(alignment: .trailing, spacing: 2) {
                            Text(medicalRecord.visitDate, formatter: DateFormatter.mediumDate)
                                .font(.headline)
                                .fontWeight(.medium)
                            
                            Text(medicalRecord.visitDate, formatter: DateFormatter.shortTime)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    if let description = medicalRecord.description, !description.isEmpty {
                        Text(description)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
                .padding()
                .background(Color(.systemBackground))
                .cornerRadius(12)
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color(.separator), lineWidth: 0.5)
                )
                
                // Veterinarian & Clinic Information
                if medicalRecord.veterinarianName != nil || medicalRecord.clinicName != nil {
                    InfoSection(title: "Veterinarian & Clinic") {
                        if let veterinarianName = medicalRecord.veterinarianName, !veterinarianName.isEmpty {
                            InfoRow(title: "Veterinarian", value: veterinarianName, icon: "person.fill")
                        }
                        
                        if let clinicName = medicalRecord.clinicName, !clinicName.isEmpty {
                            InfoRow(title: "Clinic", value: clinicName, icon: "building.2.fill")
                        }
                    }
                }
                
                // Vital Signs
                if hasVitalSigns {
                    InfoSection(title: "Vital Signs") {
                        if let weight = medicalRecord.weight {
                            InfoRow(title: "Weight", value: String(format: "%.1f lbs", weight), icon: "scalemass.fill")
                        }
                        
                        if let temperature = medicalRecord.temperature {
                            InfoRow(title: "Temperature", value: String(format: "%.1f°F", temperature), icon: "thermometer")
                        }
                        
                        if let medicalData = medicalRecord.medicalData {
                            if let heartRate = medicalData.heartRate, !heartRate.isEmpty {
                                InfoRow(title: "Heart Rate", value: heartRate, icon: "heart.fill")
                            }
                            
                            if let respiratoryRate = medicalData.respiratoryRate, !respiratoryRate.isEmpty {
                                InfoRow(title: "Respiratory Rate", value: respiratoryRate, icon: "lungs.fill")
                            }
                            
                            if let bloodPressure = medicalData.bloodPressure, !bloodPressure.isEmpty {
                                InfoRow(title: "Blood Pressure", value: bloodPressure, icon: "drop.fill")
                            }
                        }
                    }
                }
                
                // Physical Examination
                if hasPhysicalExamData {
                    InfoSection(title: "Physical Examination") {
                        if let medicalData = medicalRecord.medicalData {
                            if let bodyConditionScore = medicalData.bodyConditionScore, !bodyConditionScore.isEmpty {
                                InfoRow(title: "Body Condition Score", value: bodyConditionScore, icon: "figure.walk")
                            }
                            
                            if let dentalCondition = medicalData.dentalCondition, !dentalCondition.isEmpty {
                                InfoRow(title: "Dental Condition", value: dentalCondition, icon: "mouth.fill")
                            }
                            
                            if let skinCondition = medicalData.skinCondition, !skinCondition.isEmpty {
                                InfoRow(title: "Skin Condition", value: skinCondition, icon: "hand.raised.fill")
                            }
                            
                            if let eyeCondition = medicalData.eyeCondition, !eyeCondition.isEmpty {
                                InfoRow(title: "Eye Condition", value: eyeCondition, icon: "eye.fill")
                            }
                            
                            if let earCondition = medicalData.earCondition, !earCondition.isEmpty {
                                InfoRow(title: "Ear Condition", value: earCondition, icon: "ear.fill")
                            }
                        }
                    }
                }
                
                // Clinical Information
                if hasClinicalInfo {
                    InfoSection(title: "Clinical Information") {
                        if let diagnosis = medicalRecord.diagnosis, !diagnosis.isEmpty {
                            InfoRow(title: "Diagnosis", value: diagnosis, icon: "stethoscope")
                        }
                        
                        if let treatment = medicalRecord.treatment, !treatment.isEmpty {
                            InfoRow(title: "Treatment", value: treatment, icon: "cross.case.fill")
                        }
                        
                        if let medications = medicalRecord.medications, !medications.isEmpty {
                            InfoRow(title: "Medications", value: medications, icon: "pills.fill")
                        }
                    }
                }
                
                // Follow-up Information
                if medicalRecord.followUpRequired {
                    InfoSection(title: "Follow-up") {
                        InfoRow(title: "Follow-up Required", value: "Yes", icon: "calendar.badge.clock")
                        
                        if let followUpDate = medicalRecord.followUpDate {
                            InfoRow(title: "Follow-up Date", value: DateFormatter.mediumDate.string(from: followUpDate), icon: "calendar")
                        }
                        
                        if medicalRecord.isFollowUpDue {
                            InfoRow(title: "Status", value: "Follow-up Due", icon: "exclamationmark.triangle.fill", valueColor: .orange)
                        }
                    }
                }
                
                // Cost Information
                if let cost = medicalRecord.cost {
                    InfoSection(title: "Cost") {
                        InfoRow(title: "Total Cost", value: String(format: "$%.2f", cost), icon: "dollarsign.circle.fill")
                    }
                }
                
                // Record Information
                InfoSection(title: "Record Information") {
                    InfoRow(title: "Created", value: DateFormatter.mediumDateTime.string(from: medicalRecord.createdAt), icon: "clock.fill")
                    InfoRow(title: "Updated", value: DateFormatter.mediumDateTime.string(from: medicalRecord.updatedAt), icon: "arrow.clockwise")
                    InfoRow(title: "Days Since Visit", value: "\(medicalRecord.daysSinceVisit) days", icon: "calendar.badge.clock")
                }
            }
            .padding()
        }
        .navigationTitle("Medical Record")
        .navigationBarTitleDisplayMode(.large)
        .navigationBarItems(trailing: 
            Button("Edit") {
                showEditRecord = true
            }
            .foregroundColor(.blue)
        )
        .sheet(isPresented: $showEditRecord) {
            EditMedicalRecordView(existingRecord: medicalRecord, pet: pet) { updatedRecord in
                // Handle the updated record
                onRecordUpdated?()
                showEditRecord = false
            }
        }
        .id(refreshTrigger)
    }
    
    // Computed properties to check if sections have data
    private var hasVitalSigns: Bool {
        return medicalRecord.weight != nil || 
               medicalRecord.temperature != nil ||
               (medicalRecord.medicalData?.heartRate?.isEmpty == false) ||
               (medicalRecord.medicalData?.respiratoryRate?.isEmpty == false) ||
               (medicalRecord.medicalData?.bloodPressure?.isEmpty == false)
    }
    
    private var hasPhysicalExamData: Bool {
        guard let medicalData = medicalRecord.medicalData else { return false }
        return (medicalData.bodyConditionScore?.isEmpty == false) ||
               (medicalData.dentalCondition?.isEmpty == false) ||
               (medicalData.skinCondition?.isEmpty == false) ||
               (medicalData.eyeCondition?.isEmpty == false) ||
               (medicalData.earCondition?.isEmpty == false)
    }
    
    private var hasClinicalInfo: Bool {
        return (medicalRecord.diagnosis?.isEmpty == false) ||
               (medicalRecord.treatment?.isEmpty == false) ||
               (medicalRecord.medications?.isEmpty == false)
    }
}

struct InfoSection<Content: View>: View {
    let title: String
    let content: Content
    
    init(title: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.content = content()
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
                .fontWeight(.medium)
            
            VStack(spacing: 8) {
                content
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color(.separator), lineWidth: 0.5)
        )
    }
}

struct InfoRow: View {
    let title: String
    let value: String
    let icon: String
    let valueColor: Color
    
    init(title: String, value: String, icon: String, valueColor: Color = .primary) {
        self.title = title
        self.value = value
        self.icon = icon
        self.valueColor = valueColor
    }
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.subheadline)
                .foregroundColor(.blue)
                .frame(width: 20)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text(value)
                    .font(.subheadline)
                    .foregroundColor(valueColor)
            }
            
            Spacer()
        }
        .padding(.vertical, 2)
    }
}

extension DateFormatter {
    static let mediumDate: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return formatter
    }()
    
    static let shortTime: DateFormatter = {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter
    }()
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
    
    NavigationView {
        MedicalRecordDetailView(medicalRecord: sampleRecord, pet: samplePet)
    }
}
