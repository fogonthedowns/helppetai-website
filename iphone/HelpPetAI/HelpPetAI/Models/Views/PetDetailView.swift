//
//  PetDetailView.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

// MARK: - Views/PetDetailView.swift
import SwiftUI

struct PetDetailView: View {
    let petId: String?
    @State private var pet: Pet?
    let backButtonTitle: String?
    let onBack: (() -> Void)?
    let onPetUpdated: (() -> Void)?
    
    @State private var loadedPet: Pet?
    @State private var medicalRecords: MedicalRecordsResponse?
    @State private var transcripts: [VisitTranscriptListItem] = []
    @State private var isLoading = true
    @State private var errorMessage = ""
    @State private var showError = false
    @State private var showEditPet = false
    @State private var showAddMedicalRecord = false
    @State private var refreshTrigger = UUID()
    
    // Computed property to get the current pet
    private var currentPet: Pet? {
        return pet ?? loadedPet
    }
    
    private var aiBriefText: String? {
        guard let records = medicalRecords,
              let currentRecord = records.records.first,
              let description = currentRecord.description,
              !description.isEmpty else {
            return nil
        }
        return description
    }
    
    // Initializer for existing usage (with petId)
    init(petId: String) {
        self.petId = petId
        self.pet = nil
        self.backButtonTitle = nil
        self.onBack = nil
        self.onPetUpdated = nil
    }
    
    // New initializer for Pet Owner detail usage
    init(pet: Pet, backButtonTitle: String? = nil, onBack: (() -> Void)? = nil, onPetUpdated: (() -> Void)? = nil) {
        self.petId = nil
        self._pet = State(initialValue: pet)
        self.backButtonTitle = backButtonTitle
        self.onBack = onBack
        self.onPetUpdated = onPetUpdated
    }
    
    var body: some View {
        ScrollView {
            if isLoading {
                ProgressView("Loading pet details...")
                    .padding()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let currentPet = currentPet {
                VStack(spacing: 20) {
                    // Pet Header
                    PetHeaderCard(pet: currentPet)
                    
                    // Medical Records Section
                    if let records = medicalRecords, !records.records.isEmpty {
                        MedicalRecordsSection(records: records, pet: currentPet, onRecordUpdated: {
                            Task {
                                await refreshMedicalRecords()
                            }
                        }, showOnlyCurrent: true)
                    } else {
                        // Show + button when no records exist
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Text("Medical Record")
                                    .font(.headline)
                                    .fontWeight(.medium)
                                
                                Spacer()
                            }
                            .padding(.horizontal, 16)
                            .padding(.top, 16)
                            
                            Button(action: {
                                showAddMedicalRecord = true
                            }) {
                                HStack(spacing: 12) {
                                    Image(systemName: "plus.circle.fill")
                                        .font(.title2)
                                        .foregroundColor(.blue)
                                        .frame(width: 30)
                                    
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text("Add Medical Record")
                                            .font(.headline)
                                            .fontWeight(.medium)
                                            .foregroundColor(.primary)
                                        
                                        Text("Create the first medical record for this pet")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                    
                                    Spacer()
                                }
                                .padding()
                                .background(Color(.systemBackground))
                                .cornerRadius(8)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(Color(.separator), lineWidth: 0.5)
                                )
                            }
                            .buttonStyle(PlainButtonStyle())
                            .padding(.horizontal, 16)
                            .padding(.bottom, 16)
                        }
                        .background(Color(.secondarySystemBackground))
                        .cornerRadius(12)
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(Color(.separator), lineWidth: 0.5)
                        )
                    }
                    
                    // AI Brief Section
                    if let briefText = aiBriefText {
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Text("AI Brief")
                                    .font(.headline)
                                    .fontWeight(.medium)
                                
                                Spacer()
                            }
                            .padding(.horizontal, 16)
                            .padding(.top, 16)
                            
                            Text(briefText)
                                .font(.body)
                                .foregroundColor(.primary)
                                .padding(.horizontal, 16)
                                .padding(.bottom, 16)
                        }
                        .background(Color(.secondarySystemBackground))
                        .cornerRadius(12)
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(Color(.separator), lineWidth: 0.5)
                        )
                    }
                    
                    // Transcripts Section
                    if !transcripts.isEmpty {
                        TranscriptsSection(transcripts: transcripts)
                    }
                }
                .padding()
                .id(refreshTrigger) // Force refresh of entire content when pet data changes
            }
        }
        .sheet(isPresented: $showAddMedicalRecord) {
            if let currentPet = currentPet {
                AddMedicalRecordView(pet: currentPet) { newMedicalRecord in
                    // Refresh medical records after adding a new one
                    Task {
                        await refreshMedicalRecords()
                    }
                    showAddMedicalRecord = false
                }
            }
        }
        .navigationTitle(currentPet?.name ?? "Pet Details")
        .navigationBarTitleDisplayMode(.large)
        .navigationBarItems(trailing: 
            Group {
                if currentPet != nil {
                    Button("Edit") {
                        showEditPet = true
                    }
                    .foregroundColor(.blue)
                }
            }
        )
        .onAppear {
            loadPetDetails()
        }
        .alert("Error", isPresented: $showError) {
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
        .sheet(isPresented: $showEditPet) {
            if let currentPet = currentPet {
                EditPetView(pet: currentPet) { updatedPet in
                    // Update the pet state with the updated data
                    if self.pet != nil {
                        self.pet = updatedPet
                    } else {
                        self.loadedPet = updatedPet
                    }
                    showEditPet = false
                    
                    // Reload the pet details to get fresh data and update the UI
                    Task {
                        await refreshPetData()
                    }
                    
                    // Notify parent view that pet was updated
                    onPetUpdated?()
                }
            }
        }
    }
    
    private func loadPetDetails() {
        // If we already have a pet object, just load additional data
        if let existingPet = pet {
            print("🐕 Loading additional data for existing pet: \(existingPet.name)")
            isLoading = true
            
            Task {
                do {
                    print("🐕 Starting async requests for medical data and transcripts...")
                    async let medicalData = APIManager.shared.getCurrentMedicalRecords(petId: existingPet.id)
                    async let transcriptData = APIManager.shared.getPetTranscriptList(petId: existingPet.id)
                    
                    let (medicalResult, transcriptResult) = try await (medicalData, transcriptData)
                    print("🐕 Medical records loaded: \(medicalResult.records.count) records")
                    print("🐕 Transcripts loaded: \(transcriptResult.count) transcripts")
                    
                    await MainActor.run {
                        self.medicalRecords = medicalResult
                        self.transcripts = transcriptResult
                        self.isLoading = false
                        self.refreshTrigger = UUID() // Ensure UI refreshes with new data
                        print("🐕 UI updated with additional data")
                    }
                } catch {
                    print("🐕 Error loading additional pet data: \(error)")
                    await MainActor.run {
                        self.errorMessage = error.localizedDescription
                        self.showError = true
                        self.isLoading = false
                        print("🐕 UI updated with error: \(error.localizedDescription)")
                    }
                }
            }
        } else if let petId = petId {
            // Load everything from petId
            print("🐕 Loading pet details for ID: \(petId)")
            isLoading = true
            
            Task {
                do {
                    print("🐕 Starting async pet data requests...")
                    async let petData = APIManager.shared.getPetDetails(petId: petId)
                    async let medicalData = APIManager.shared.getCurrentMedicalRecords(petId: petId)
                    async let transcriptData = APIManager.shared.getPetTranscriptList(petId: petId)
                    
                    let (petResult, medicalResult, transcriptResult) = try await (petData, medicalData, transcriptData)
                    print("🐕 Pet data loaded successfully: \(petResult.name)")
                    print("🐕 Medical records loaded: \(medicalResult.records.count) records")
                    print("🐕 Transcripts loaded: \(transcriptResult.count) transcripts")
                    
                    await MainActor.run {
                        self.loadedPet = petResult
                        self.medicalRecords = medicalResult
                        self.transcripts = transcriptResult
                        self.isLoading = false
                        self.refreshTrigger = UUID() // Ensure UI refreshes with new data
                        print("🐕 UI updated with pet data")
                    }
                } catch {
                    print("🐕 Error loading pet details: \(error)")
                    await MainActor.run {
                        self.errorMessage = error.localizedDescription
                        self.showError = true
                        self.isLoading = false
                        print("🐕 UI updated with error: \(error.localizedDescription)")
                    }
                }
            }
        } else {
            // No petId and no pet object - this shouldn't happen
            print("🐕 Error: No pet ID or pet object provided")
            DispatchQueue.main.async {
                self.errorMessage = "No pet information provided"
                self.showError = true
                self.isLoading = false
            }
        }
    }
    
    @MainActor
    private func refreshPetData() async {
        guard let currentPet = currentPet else { return }
        
        print("🔄 Refreshing pet data for: \(currentPet.name)")
        
        do {
            // Reload the pet data from the API to get the latest information
            let freshPet = try await APIManager.shared.getPetDetails(petId: currentPet.id)
            
            // Update the appropriate state
            if self.pet != nil {
                self.pet = freshPet
            } else {
                self.loadedPet = freshPet
            }
            
            // Force UI refresh by updating the trigger
            self.refreshTrigger = UUID()
            
            print("✅ Pet data refreshed successfully: \(freshPet.name)")
            print("🔄 Updated pet weight: \(freshPet.weight ?? 0) lbs")
            print("🔄 Refresh trigger updated: \(self.refreshTrigger)")
        } catch {
            print("❌ Failed to refresh pet data: \(error)")
            // Don't show error to user for refresh failures, just log it
        }
    }
    
    @MainActor
    private func refreshMedicalRecords() async {
        guard let currentPet = currentPet else { return }
        
        print("🔄 Refreshing medical records for: \(currentPet.name)")
        
        do {
            let freshMedicalRecords = try await APIManager.shared.getCurrentMedicalRecords(petId: currentPet.id)
            self.medicalRecords = freshMedicalRecords
            self.refreshTrigger = UUID() // Force UI refresh
            
            print("✅ Medical records refreshed successfully: \(freshMedicalRecords.records.count) records")
        } catch {
            print("❌ Failed to refresh medical records: \(error)")
            // Don't show error to user for refresh failures, just log it
        }
    }
}
