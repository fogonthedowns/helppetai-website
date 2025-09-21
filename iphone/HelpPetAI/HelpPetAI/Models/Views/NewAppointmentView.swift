//
//  NewAppointmentView.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/7/25.
//

import SwiftUI

struct NewAppointmentView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject private var apiManager = APIManager.shared
    
    let selectedDate: Date
    let selectedTime: Date?
    let onComplete: () -> Void
    
    // Form state
    @State private var appointmentDate: Date
    @State private var appointmentTime: Date
    @State private var duration: Int = 30
    @State private var appointmentType = "checkup"
    @State private var title: String = ""
    @State private var notes: String = ""
    
    // Data loading state
    @State private var petOwners: [PetOwnerWithPets] = []
    @State private var selectedOwner: PetOwnerWithPets?
    @State private var selectedPets: Set<String> = []
    
    // UI state
    @State private var isLoading = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var isCreating = false
    
    private let appointmentTypes = ["checkup", "emergency", "surgery", "consultation"]
    private let durations = [15, 30, 45, 60, 90, 120]
    
    init(selectedDate: Date, selectedTime: Date? = nil, onComplete: @escaping () -> Void) {
        self.selectedDate = selectedDate
        self.selectedTime = selectedTime
        self.onComplete = onComplete
        self._appointmentDate = State(initialValue: selectedDate)
        
        // If a specific time was selected (from calendar long press), use it
        if let selectedTime = selectedTime {
            self._appointmentTime = State(initialValue: selectedTime)
        } else {
            self._appointmentTime = State(initialValue: Calendar.current.date(bySettingHour: 9, minute: 0, second: 0, of: selectedDate) ?? selectedDate)
        }
    }
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 0) {
                    if isLoading {
                        HStack {
                            ProgressView()
                            Text("Loading...")
                        }
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding()
                    } else {
                        // Header with appointment type chips
                        appointmentTypeHeader
                        
                        Divider()
                        
                        // Title Section
                        titleSection
                        
                        Divider()
                        
                        // Date & Time Section
                        dateTimeSection
                        
                        Divider()
                        
                        // Pet Owner & Pets Section
                        petSelectionSection
                        
                        Divider()
                        
                        // Notes Section
                        notesSection
                        
                        // Create Button
                        createButtonSection
                            .padding(.top, 24)
                    }
                }
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("New Appointment")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        createAppointment()
                    }
                    .disabled(!isFormValid || isCreating)
                    .fontWeight(.medium)
                }
            }
            .alert("Error", isPresented: $showError) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
            .onAppear {
                loadInitialData()
            }
        }
    }
    
    // MARK: - View Sections
    
    private var appointmentTypeHeader: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Appointment Type")
                    .font(.headline)
                    .foregroundColor(.primary)
                Spacer()
            }
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(appointmentTypes, id: \.self) { type in
                        Button(action: {
                            appointmentType = type
                        }) {
                            HStack(spacing: 8) {
                                Image(systemName: iconForAppointmentType(type))
                                    .font(.system(size: 14, weight: .medium))
                                Text(type.capitalized)
                                    .font(.system(size: 14, weight: .medium))
                            }
                            .padding(.horizontal, 16)
                            .padding(.vertical, 10)
                            .background(
                                RoundedRectangle(cornerRadius: 20)
                                    .fill(appointmentType == type ? Color.blue : Color(.systemGray6))
                            )
                            .foregroundColor(appointmentType == type ? .white : .primary)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal, 20)
            }
        }
        .padding(.vertical, 16)
        .background(Color(.systemBackground))
    }
    
    private var titleSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "text.cursor")
                    .foregroundColor(.blue)
                    .frame(width: 24)
                
                TextField("Add title", text: $title)
                    .font(.system(size: 16))
                    .textFieldStyle(.plain)
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
        .background(Color(.systemBackground))
    }
    
    private var dateTimeSection: some View {
        VStack(spacing: 16) {
            // Date picker
            HStack {
                Image(systemName: "calendar")
                    .foregroundColor(.blue)
                    .frame(width: 24)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text("Date")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    DatePicker("", selection: $appointmentDate, displayedComponents: .date)
                        .datePickerStyle(.compact)
                        .labelsHidden()
                }
                
                Spacer()
            }
            
            // Time picker
            HStack {
                Image(systemName: "clock")
                    .foregroundColor(.blue)
                    .frame(width: 24)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text("Time")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    DatePicker("", selection: $appointmentTime, displayedComponents: .hourAndMinute)
                        .datePickerStyle(.compact)
                        .labelsHidden()
                }
                
                Spacer()
            }
            
            // Duration picker
            HStack {
                Image(systemName: "timer")
                    .foregroundColor(.blue)
                    .frame(width: 24)
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Duration")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(durations, id: \.self) { dur in
                                Button(action: {
                                    duration = dur
                                }) {
                                    Text("\(dur) min")
                                        .font(.system(size: 14, weight: .medium))
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 6)
                                        .background(
                                            RoundedRectangle(cornerRadius: 16)
                                                .fill(duration == dur ? Color.blue : Color(.systemGray6))
                                        )
                                        .foregroundColor(duration == dur ? .white : .primary)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                        .padding(.horizontal, 1)
                    }
                }
                
                Spacer()
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
        .background(Color(.systemBackground))
    }
    
    private var petSelectionSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "person.2")
                    .foregroundColor(.blue)
                    .frame(width: 24)
                
                Text("Pet Owner & Pets")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Spacer()
            }
            
            VStack(spacing: 12) {
                petOwnerPicker
                petSelectionList
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
        .background(Color(.systemBackground))
    }
    
    private var notesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "note.text")
                    .foregroundColor(.blue)
                    .frame(width: 24)
                
                Text("Notes")
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Spacer()
            }
            
            TextField("Add notes (optional)", text: $notes, axis: .vertical)
                .textFieldStyle(.plain)
                .padding(.leading, 32)
                .lineLimit(3...6)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
        .background(Color(.systemBackground))
    }
    
    @ViewBuilder
    private var petOwnerPicker: some View {
        if petOwners.isEmpty {
            Text("No pet owners found")
                .foregroundColor(.secondary)
                .padding(.leading, 32)
        } else {
            Menu {
                ForEach(petOwners) { owner in
                    Button(owner.fullName) {
                        selectedOwner = owner
                        selectedPets.removeAll()
                    }
                }
            } label: {
                HStack {
                    Text(selectedOwner?.fullName ?? "Select Pet Owner")
                        .foregroundColor(selectedOwner == nil ? .secondary : .primary)
                    Spacer()
                    Image(systemName: "chevron.down")
                        .foregroundColor(.secondary)
                        .font(.caption)
                }
                .padding(.leading, 32)
                .padding(.vertical, 8)
            }
            .buttonStyle(.plain)
        }
    }
    
    @ViewBuilder
    private var petSelectionList: some View {
        if let owner = selectedOwner, !owner.pets.isEmpty {
            VStack(spacing: 8) {
                ForEach(owner.pets) { pet in
                    Button(action: {
                        if selectedPets.contains(pet.id) {
                            selectedPets.remove(pet.id)
                        } else {
                            selectedPets.insert(pet.id)
                        }
                    }) {
                        HStack(spacing: 12) {
                            Image(systemName: selectedPets.contains(pet.id) ? "checkmark.circle.fill" : "circle")
                                .foregroundColor(selectedPets.contains(pet.id) ? .blue : .secondary)
                                .font(.system(size: 20))
                            
                            VStack(alignment: .leading, spacing: 2) {
                                Text(pet.name)
                                    .font(.system(size: 16, weight: .medium))
                                    .foregroundColor(.primary)
                                Text("\(pet.species) • \(pet.breed ?? "Unknown breed")")
                                    .font(.system(size: 14))
                                    .foregroundColor(.secondary)
                            }
                            
                            Spacer()
                        }
                        .padding(.leading, 32)
                        .padding(.vertical, 8)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }
    
    private var createButtonSection: some View {
        Button(action: createAppointment) {
            HStack {
                if isCreating {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(0.8)
                }
                Text(isCreating ? "Creating..." : "Create Appointment")
                    .fontWeight(.semibold)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(isFormValid && !isCreating ? Color.blue : Color.gray)
            )
            .foregroundColor(.white)
        }
        .disabled(!isFormValid || isCreating)
        .buttonStyle(.plain)
        .padding(.horizontal, 20)
    }
    
    // MARK: - Computed Properties
    
    private var generatedTitle: String {
        // Use custom title if provided, otherwise generate one
        if !title.isEmpty {
            return title
        }
        
        guard let owner = selectedOwner else { return "" }
        
        let petNames = owner.pets
            .filter { selectedPets.contains($0.id) }
            .map { $0.name }
            .joined(separator: ", ")
        
        let typeDisplayName = appointmentType.replacingOccurrences(of: "_", with: " ").capitalized
        
        return "\(petNames) \(typeDisplayName)"
    }
    
    private func iconForAppointmentType(_ type: String) -> String {
        switch type.lowercased() {
        case "checkup":
            return "stethoscope"
        case "emergency":
            return "exclamationmark.triangle.fill"
        case "surgery":
            return "cross.case.fill"
        case "consultation":
            return "bubble.left.and.bubble.right"
        default:
            return "calendar"
        }
    }
    
    private var isFormValid: Bool {
        selectedOwner != nil &&
        !selectedPets.isEmpty &&
        apiManager.currentUser?.practiceId != nil
    }
    
    // MARK: - Data Loading
    
    private func loadInitialData() {
        isLoading = true
        
        Task {
            await loadPetOwners()
        }
    }
    
    private func loadPetOwners() async {
        do {
            let owners = try await apiManager.getPetOwners()
            
            // Load pets for each owner
            var ownersWithPets: [PetOwnerWithPets] = []
            for owner in owners {
                let pets = try await apiManager.getPetsByOwner(ownerId: owner.uuid)
                ownersWithPets.append(PetOwnerWithPets(
                    uuid: owner.uuid,
                    fullName: owner.fullName,
                    email: owner.email,
                    phone: owner.phone,
                    pets: pets
                ))
            }
            
            await MainActor.run {
                self.petOwners = ownersWithPets
                self.isLoading = false
            }
        } catch {
            await MainActor.run {
                showErrorMessage("Failed to load pet owners: \(error.localizedDescription)")
                self.isLoading = false
            }
        }
    }
    
    
    // MARK: - Actions
    
    private func createAppointment() {
        guard let owner = selectedOwner,
              let practiceId = apiManager.currentUser?.practiceId,
              !selectedPets.isEmpty else {
            return
        }
        
        isCreating = true
        
        Task {
            do {
                // Combine date and time
                let calendar = Calendar.current
                let dateComponents = calendar.dateComponents([.year, .month, .day], from: appointmentDate)
                let timeComponents = calendar.dateComponents([.hour, .minute], from: appointmentTime)
                
                let finalDate = calendar.date(from: DateComponents(
                    year: dateComponents.year,
                    month: dateComponents.month,
                    day: dateComponents.day,
                    hour: timeComponents.hour,
                    minute: timeComponents.minute
                )) ?? appointmentDate
                
                let request = CreateAppointmentRequest(
                    practiceId: practiceId,
                    petOwnerId: owner.uuid,
                    assignedVetUserId: apiManager.currentUser?.id,
                    petIds: Array(selectedPets),
                    appointmentDate: finalDate,
                    durationMinutes: duration,
                    appointmentType: appointmentType,
                    title: generatedTitle,
                    description: notes.isEmpty ? nil : notes,
                    notes: notes.isEmpty ? nil : notes
                )
                
                let _ = try await apiManager.createAppointment(request)
                
                await MainActor.run {
                    onComplete()
                    dismiss()
                }
            } catch {
                await MainActor.run {
                    showErrorMessage("Failed to create appointment: \(error.localizedDescription)")
                    isCreating = false
                }
            }
        }
    }
    
    private func showErrorMessage(_ message: String) {
        errorMessage = message
        showError = true
    }
}

// MARK: - Custom Toggle Style

struct CheckboxToggleStyle: ToggleStyle {
    func makeBody(configuration: Configuration) -> some View {
        HStack {
            Image(systemName: configuration.isOn ? "checkmark.square.fill" : "square")
                .foregroundColor(configuration.isOn ? .blue : .gray)
                .onTapGesture {
                    configuration.isOn.toggle()
                }
            
            configuration.label
        }
    }
}