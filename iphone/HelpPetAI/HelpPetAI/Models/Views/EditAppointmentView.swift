//
//  EditAppointmentView.swift
//  HelpPetAI
//
//  Created by Claude on 9/15/25.
//

import SwiftUI

struct EditAppointmentView: View {
    let appointment: Appointment
    let onAppointmentUpdated: (Appointment) -> Void
    
    @State private var title: String
    @State private var description: String
    @State private var notes: String
    @State private var appointmentDate: Date
    @State private var durationMinutes: Int
    @State private var appointmentType: String
    @State private var status: AppointmentStatus
    @State private var selectedPetIds: Set<String>
    
    @State private var isLoading = false
    @State private var errorMessage = ""
    @State private var showError = false
    @State private var showSuccess = false
    
    @Environment(\.dismiss) private var dismiss
    
    // Available appointment types
    private let appointmentTypes = ["checkup", "surgery", "vaccination", "grooming", "emergency", "consultation"]
    
    // Available statuses
    private let statuses: [AppointmentStatus] = [.scheduled, .confirmed, .inProgress, .completed, .cancelled]
    
    init(appointment: Appointment, onAppointmentUpdated: @escaping (Appointment) -> Void) {
        self.appointment = appointment
        self.onAppointmentUpdated = onAppointmentUpdated
        
        // Initialize state with current appointment values
        self._title = State(initialValue: appointment.title)
        self._description = State(initialValue: appointment.description ?? "")
        self._notes = State(initialValue: appointment.notes ?? "")
        self._appointmentDate = State(initialValue: appointment.appointmentDate)
        self._durationMinutes = State(initialValue: appointment.durationMinutes)
        self._appointmentType = State(initialValue: appointment.appointmentType)
        self._status = State(initialValue: appointment.status)
        self._selectedPetIds = State(initialValue: Set(appointment.pets.map { $0.id }))
    }
    
    var body: some View {
        NavigationView {
            Form {
                Section("Appointment Details") {
                    TextField("Title", text: $title)
                    
                    TextField("Description", text: $description, axis: .vertical)
                        .lineLimit(3...6)
                    
                    TextField("Notes", text: $notes, axis: .vertical)
                        .lineLimit(3...6)
                }
                
                Section("Schedule") {
                    DatePicker("Date & Time", selection: $appointmentDate)
                    
                    Picker("Duration", selection: $durationMinutes) {
                        Text("15 minutes").tag(15)
                        Text("30 minutes").tag(30)
                        Text("45 minutes").tag(45)
                        Text("1 hour").tag(60)
                        Text("1.5 hours").tag(90)
                        Text("2 hours").tag(120)
                    }
                }
                
                Section("Type & Status") {
                    Picker("Type", selection: $appointmentType) {
                        ForEach(appointmentTypes, id: \.self) { type in
                            Text(type.capitalized).tag(type)
                        }
                    }
                    
                    Picker("Status", selection: $status) {
                        ForEach(statuses, id: \.self) { status in
                            Text(status.displayName).tag(status)
                        }
                    }
                }
                
                Section("Pets") {
                    ForEach(appointment.pets, id: \.id) { pet in
                        HStack {
                            Image(systemName: pet.species.lowercased() == "dog" ? "pawprint.fill" : "cat.fill")
                                .foregroundColor(.blue)
                            
                            VStack(alignment: .leading) {
                                Text(pet.name)
                                    .fontWeight(.medium)
                                Text("\(pet.species.capitalized) • \(pet.breed ?? "Mixed")")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            
                            Spacer()
                            
                            if selectedPetIds.contains(pet.id) {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.blue)
                            } else {
                                Image(systemName: "circle")
                                    .foregroundColor(.gray)
                            }
                        }
                        .contentShape(Rectangle())
                        .onTapGesture {
                            if selectedPetIds.contains(pet.id) {
                                selectedPetIds.remove(pet.id)
                            } else {
                                selectedPetIds.insert(pet.id)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Edit Appointment")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        saveAppointment()
                    }
                    .disabled(isLoading || title.isEmpty || selectedPetIds.isEmpty)
                }
            }
            .disabled(isLoading)
            .overlay {
                if isLoading {
                    ProgressView("Saving...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(Color.black.opacity(0.3))
                }
            }
        }
        .alert("Error", isPresented: $showError) {
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
        .alert("Success", isPresented: $showSuccess) {
            Button("OK") {
                dismiss()
            }
        } message: {
            Text("Appointment updated successfully")
        }
    }
    
    private func saveAppointment() {
        guard !title.isEmpty, !selectedPetIds.isEmpty else {
            errorMessage = "Please fill in all required fields"
            showError = true
            return
        }
        
        isLoading = true
        
        Task {
            do {
                let updateRequest = UpdateAppointmentRequest(
                    assignedVetUserId: appointment.assignedVetUserId,
                    appointmentDate: appointmentDate,
                    durationMinutes: durationMinutes,
                    appointmentType: appointmentType,
                    status: status,
                    title: title,
                    description: description.isEmpty ? nil : description,
                    notes: notes.isEmpty ? nil : notes,
                    petIds: Array(selectedPetIds)
                )
                
                let updatedAppointment = try await APIManager.shared.updateAppointment(
                    appointmentId: appointment.id,
                    request: updateRequest
                )
                
                await MainActor.run {
                    isLoading = false
                    showSuccess = true
                    onAppointmentUpdated(updatedAppointment)
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                    errorMessage = "Failed to update appointment: \(error.localizedDescription)"
                    showError = true
                }
            }
        }
    }
}

// MARK: - Update Appointment Request Model

struct UpdateAppointmentRequest: Codable {
    let assignedVetUserId: String?
    let appointmentDate: Date
    let durationMinutes: Int
    let appointmentType: String
    let status: AppointmentStatus
    let title: String
    let description: String?
    let notes: String?
    let petIds: [String]
}

// MARK: - Appointment Status Extension

//extension AppointmentStatus {
//    var displayName: String {
//        switch self {
//        case .scheduled:
//            return "Scheduled"
//        case .confirmed:
//            return "Confirmed"
//        case .inProgress:
//            return "In Progress"
//        case .completed:
//            return "Completed"
//        case .cancelled:
//            return "Cancelled"
//        }
//    }
//}

// MARK: - Preview

struct EditAppointmentView_Previews: PreviewProvider {
    static var previews: some View {
        let sampleAppointment = Appointment(
            id: "1",
            practiceId: "practice1",
            petOwnerId: "owner1",
            assignedVetUserId: "vet1",
            appointmentDate: Date(),
            durationMinutes: 30,
            appointmentType: "checkup",
            status: .scheduled,
            title: "Sample Appointment",
            description: "Sample description",
            notes: "Sample notes",
            pets: [
                PetSummary(id: "pet1", name: "Fluffy", species: "Dog", breed: "Golden Retriever")
            ],
            createdAt: Date(),
            updatedAt: Date()
        )
        
        EditAppointmentView(appointment: sampleAppointment) { _ in }
    }
}
