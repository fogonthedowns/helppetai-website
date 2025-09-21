//
//  VisitRecordingView.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

import SwiftUI
import AVFoundation

// MARK: - Audio Manager Protocol
protocol AudioManagerProtocol: ObservableObject {
    var isPlaying: Bool { get }
    var currentlyPlayingVisitId: String? { get }
    var currentPlaybackTime: TimeInterval { get }
    var totalPlaybackTime: TimeInterval { get }
    
    func playVisitRecording(visitId: String) async throws
    func stopPlayback()
    func pausePlayback()
    func resumePlayback()
    func seekTo(time: TimeInterval)
    func skipForward(seconds: TimeInterval)
}

extension AudioManager: AudioManagerProtocol {}

struct VisitRecordingView: View {
    let appointment: Appointment
    @State private var visitTranscripts: [VisitTranscriptResponse] = []
    @State private var isLoadingRecordings = false
    @State private var selectedPetForRecording: PetSummary?
    @State private var errorMessage: String?
    @State private var showingError = false
    @ObservedObject private var audioManager = AudioManager.shared
    
    var body: some View {
        ScrollView {
            if isLoadingRecordings {
                VStack {
                    ProgressView("Loading recordings...")
                        .padding()
                    Spacer()
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                VStack(spacing: 24) {
                    // Visit Header
                    VStack(spacing: 12) {
                        Text("\(appointment.title) - \(appointment.appointmentDate, style: .date)")
                            .font(.headline)
                            .foregroundColor(.secondary)
                    }
                    .padding(.top)
                    
                    // Pets Section
                    VStack(spacing: 16) {
                        ForEach(appointment.pets, id: \.id) { pet in
                            PetRecordingCard(
                                pet: pet,
                                appointment: appointment,
                                visitTranscripts: getPetVisitTranscripts(for: pet.id),
                                audioManager: audioManager
                            ) {
                                selectedPetForRecording = pet
                            }
                        }
                    }
                    .padding(.horizontal)
                    
                    // Pet Information Section
                    petInformationSection
                    
                    Spacer()
                }
            }
        }
        .navigationTitle("Visit Recording")
        .navigationBarTitleDisplayMode(.large)
        .onAppear {
            loadRecordings()
        }
        // Removed stopPlayback() to allow continuous playback
        .alert("Recording Error", isPresented: $showingError) {
            Button("OK") { showingError = false }
        } message: {
            Text(errorMessage ?? "An unknown error occurred")
        }
        .sheet(item: $selectedPetForRecording) { selectedPet in
            AudioRecordingView(
                appointmentId: appointment.id,
                petId: selectedPet.id,
                petName: selectedPet.name,
                visitId: nil
            ) { result in
                loadRecordings()
                selectedPetForRecording = nil
            }
        }
    }
    
    // MARK: - Pet Information Section
    private var petInformationSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Pet Information")
                    .font(.headline)
                    .fontWeight(.semibold)
                Spacer()
            }
            .padding(.horizontal)
            
            VStack(spacing: 12) {
                ForEach(appointment.pets, id: \.id) { pet in
                    NavigationLink(destination: PetDetailView(petId: pet.id)) {
                        PetRow(
                            pet: pet,
                            subtitle: "\(pet.species.capitalized) • \(pet.breed ?? "Mixed")",
                            trailingText: "Medical Record"
                        )
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding(.horizontal)
        }
        .padding(.vertical)
    }
    
    private func loadRecordings() {
        isLoadingRecordings = true
        
        Task {
            do {
                let appointmentTranscripts = try await APIManager.shared.getVisitTranscriptsByAppointment(
                    appointmentId: appointment.id
                )
                
                await MainActor.run {
                    self.visitTranscripts = appointmentTranscripts
                    self.isLoadingRecordings = false
                }
            } catch {
                print("⚠️ New endpoint failed, falling back to old method: \(error)")
                await loadRecordingsFallback()
            }
        }
    }
    
    private func loadRecordingsFallback() async {
        do {
            // Parallelize API calls for better performance
            async let allPetTranscripts = withThrowingTaskGroup(of: [VisitTranscript].self) { group in
                for pet in appointment.pets {
                    group.addTask {
                        try await APIManager.shared.getVisitTranscripts(petId: pet.id, limit: 50)
                    }
                }
                
                var allTranscripts: [VisitTranscript] = []
                for try await petTranscripts in group {
                    allTranscripts.append(contentsOf: petTranscripts)
                }
                return allTranscripts
            }
            
            let transcripts = try await allPetTranscripts
            let currentAppointmentTranscripts = transcripts.filter { transcript in
                isTranscriptFromCurrentAppointment(transcript: transcript)
            }
            
            // Convert to VisitTranscriptResponse for UI consistency
            let responses = currentAppointmentTranscripts.compactMap { convertToResponse(from: $0) }
            
            await MainActor.run {
                self.visitTranscripts = responses
                self.isLoadingRecordings = false
            }
        } catch {
            await MainActor.run {
                self.isLoadingRecordings = false
                self.handleError(error)
            }
        }
    }
    
    // Simplified appointment matching - only use appointment_id
    private func isTranscriptFromCurrentAppointment(transcript: VisitTranscript) -> Bool {
        guard let metadata = transcript.metadata,
              let appointmentId = extractString(from: metadata["appointment_id"]) else {
            print("❌ Missing appointment_id for transcript \(transcript.uuid)")
            return false
        }
        return appointmentId == appointment.id
    }
    
    // Type-safe metadata extraction
    private func extractString(from value: AnyCodable?) -> String? {
        guard let value = value?.value else { return nil }
        
        if let stringValue = value as? String {
            return stringValue
        } else if let intValue = value as? Int {
            return String(intValue)
        } else if let doubleValue = value as? Double {
            return String(doubleValue)
        }
        return nil
    }
    
    // Safe conversion from VisitTranscript to VisitTranscriptResponse
    private func convertToResponse(from transcript: VisitTranscript) -> VisitTranscriptResponse? {
        do {
            return VisitTranscriptResponse(
                uuid: transcript.uuid,
                petId: transcript.petId,
                visitDate: transcript.visitDate.timeIntervalSince1970,
                fullText: transcript.fullText,
                audioTranscriptUrl: transcript.audioTranscriptUrl,
                state: transcript.state,
                metadata: transcript.metadata ?? [:]
            )
        } catch {
            print("⚠️ Failed to convert transcript \(transcript.uuid): \(error)")
            return nil
        }
    }
    
    private func getPetVisitTranscripts(for petId: String) -> [VisitTranscriptResponse] {
        return visitTranscripts.filter { $0.petId == petId }
    }
    
    private func handleError(_ error: Error) {
        print("❌ Recording error: \(error)")
        
        if let audioError = error as? AudioError {
            errorMessage = audioError.localizedDescription
        } else if let apiError = error as? APIError {
            switch apiError {
            case .unauthorized:
                errorMessage = "Please log in again to access recordings"
            case .networkError:
                errorMessage = "Network connection failed. Please check your internet connection"
            case .serverError(let code):
                errorMessage = code == 500 ? 
                    "The recording service is temporarily unavailable. Please try again later." :
                    "Server error (\(code)). Please try again later"
            default:
                errorMessage = "Failed to load recordings. Please try again"
            }
        } else {
            errorMessage = "An unexpected error occurred: \(error.localizedDescription)"
        }
        
        showingError = true
    }
}

// MARK: - Reusable Pet Row Component
struct PetRow: View {
    let pet: PetSummary
    let subtitle: String
    let trailingText: String?
    
    init(pet: PetSummary, subtitle: String, trailingText: String? = nil) {
        self.pet = pet
        self.subtitle = subtitle
        self.trailingText = trailingText
    }
    
    var body: some View {
        HStack(spacing: 16) {
            Image(systemName: pet.species.lowercased() == "dog" ? "pawprint.fill" : "cat.fill")
                .font(.title2)
                .foregroundColor(.blue)
                .frame(width: 32, height: 32)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(trailingText != nil ? "\(pet.name) \(trailingText!)" : pet.name)
                    .font(.headline)
                    .fontWeight(.semibold)
                    .foregroundColor(.primary)
                
                Text(subtitle)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.gray)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color(.systemGray5), lineWidth: 0.5)
        )
    }
}

// MARK: - Pet Recording Card Component
struct PetRecordingCard<AudioManager: AudioManagerProtocol>: View {
    let pet: PetSummary
    let appointment: Appointment
    let visitTranscripts: [VisitTranscriptResponse]
    let audioManager: AudioManager
    let onStartRecording: () -> Void
    
    var body: some View {
        VStack(spacing: 16) {
            // Pet Header
            HStack {
                Image(systemName: pet.species.lowercased() == "dog" ? "pawprint.fill" : "cat.fill")
                    .font(.title2)
                    .foregroundColor(.blue)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(pet.name)
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text("\(pet.species.capitalized) • \(pet.breed ?? "Mixed")")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                // Recording Status Indicator
                Image(systemName: visitTranscripts.isEmpty ? "circle" : "checkmark.circle.fill")
                    .font(.title3)
                    .foregroundColor(visitTranscripts.isEmpty ? .gray : .green)
            }
            
            // Recording Interface
            if visitTranscripts.isEmpty {
                Button(action: onStartRecording) {
                    HStack {
                        Image(systemName: "mic.fill")
                        Text("Start Recording")
                            .fontWeight(.semibold)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.red)
                    .foregroundColor(.white)
                    .cornerRadius(12)
                }
            } else {
                ForEach(visitTranscripts.filter { $0.state == .processed && $0.audioTranscriptUrl != nil }, id: \.uuid) { visitTranscript in
                    MacStyleAudioPlayer(visitTranscript: visitTranscript, audioManager: audioManager)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.1), radius: 4, x: 0, y: 2)
    }
}

// MARK: - Mac-Style Audio Player Component
struct MacStyleAudioPlayer<AudioManager: AudioManagerProtocol>: View {
    let visitTranscript: VisitTranscriptResponse
    let audioManager: AudioManager
    @State private var showingDeleteAlert = false
    
    private var isCurrentlyPlaying: Bool {
        audioManager.currentlyPlayingVisitId == visitTranscript.uuid && audioManager.isPlaying
    }
    
    private var isCurrentVisit: Bool {
        audioManager.currentlyPlayingVisitId == visitTranscript.uuid
    }
    
    private var recordingDuration: Double {
        extractDouble(from: visitTranscript.metadata["duration_seconds"]) ?? 0
    }
    
    var body: some View {
        VStack(spacing: 12) {
            // Progress Bar
            VStack(spacing: 8) {
                GeometryReader { geometry in
                    ZStack(alignment: .leading) {
                        // Background track
                        RoundedRectangle(cornerRadius: 2)
                            .fill(Color(.systemGray4))
                            .frame(height: 4)
                        
                        // Progress track
                        RoundedRectangle(cornerRadius: 2)
                            .fill(Color.blue)
                            .frame(width: progressWidth(for: geometry.size.width), height: 4)
                        
                        // Scrubber handle - always visible
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 16, height: 16)
                            .offset(x: progressWidth(for: geometry.size.width) - 8)
                            .shadow(color: .black.opacity(0.1), radius: 1, x: 0, y: 1)
                            .opacity(isCurrentVisit ? 1.0 : 0.6) // Visual feedback for inactive state
                    }
                    .contentShape(Rectangle())
                    .gesture(
                        DragGesture()
                            .onChanged { value in
                                if isCurrentVisit {
                                    let progress = max(0, min(1, value.location.x / geometry.size.width))
                                    let newTime = progress * recordingDuration
                                    audioManager.seekTo(time: newTime)
                                }
                            }
                    )
                    .disabled(!isCurrentVisit) // Disable interaction when not current
                }
                .frame(height: 20)
                
                // Time display
                HStack {
                    Text(formatTime(isCurrentVisit ? audioManager.currentPlaybackTime : 0))
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                        .monospacedDigit()
                    
                    Spacer()
                    
                    let timeLeft = isCurrentVisit ? 
                        max(0, audioManager.totalPlaybackTime - audioManager.currentPlaybackTime) : 
                        recordingDuration
                    Text("-\(formatTime(timeLeft))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .monospacedDigit()
                }
            }
            .onReceive(Timer.publish(every: 0.1, on: .main, in: .common).autoconnect()) { _ in
                // Only update during active playback
                if !isCurrentVisit || !audioManager.isPlaying {
                    return
                }
            }
            
            // Control buttons
            HStack {
                Spacer()
                
                // Skip back 15 seconds
                Button(action: {
                    audioManager.skipForward(seconds: -15)
                }) {
                    Image(systemName: "gobackward.15")
                        .font(.system(size: 20, weight: .medium))
                        .foregroundColor(isCurrentVisit ? .blue : .gray)
                }
                .disabled(!isCurrentVisit)
                
                // Main play/pause button
                Button(action: togglePlayback) {
                    Image(systemName: isCurrentlyPlaying ? "pause.circle.fill" : "play.circle.fill")
                        .font(.system(size: 40))
                        .foregroundColor(.blue)
                }
                .padding(.horizontal, 24)
                
                // Skip forward 15 seconds
                Button(action: {
                    audioManager.skipForward(seconds: 15)
                }) {
                    Image(systemName: "goforward.15")
                        .font(.system(size: 20, weight: .medium))
                        .foregroundColor(isCurrentVisit ? .blue : .gray)
                }
                .disabled(!isCurrentVisit)
                
                Spacer()
                
                // Delete button
                Button(action: {
                    showingDeleteAlert = true
                }) {
                    Image(systemName: "trash")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(.red)
                }
            }
        }
        .padding(16)
        .background(Color(.systemGray6))
        .cornerRadius(12)
        .alert("Delete Recording", isPresented: $showingDeleteAlert) {
            Button("Cancel", role: .cancel) { }
            Button("Delete", role: .destructive) {
                deleteRecording()
            }
        } message: {
            Text("Are you sure you want to delete this recording? This action cannot be undone.")
        }
    }
    
    private func togglePlayback() {
        if isCurrentlyPlaying {
            audioManager.pausePlayback()
        } else if isCurrentVisit {
            audioManager.resumePlayback()
        } else {
            Task {
                do {
                    try await audioManager.playVisitRecording(visitId: visitTranscript.uuid)
                } catch {
                    print("❌ Playback error: \(error)")
                }
            }
        }
    }
    
    private func deleteRecording() {
        Task {
            do {
                try await APIManager.shared.deleteVisitTranscript(visitId: visitTranscript.uuid)
                print("✅ Recording deleted: \(visitTranscript.uuid)")
            } catch {
                print("❌ Delete failed: \(error)")
            }
        }
    }
    
    private func progressWidth(for totalWidth: CGFloat) -> CGFloat {
        if isCurrentVisit && audioManager.totalPlaybackTime > 0 {
            let progress = audioManager.currentPlaybackTime / audioManager.totalPlaybackTime
            return max(0, min(totalWidth, totalWidth * progress))
        } else {
            return 0 // Dot at start when not playing
        }
    }
    
    private func extractDouble(from value: AnyCodable?) -> Double? {
        guard let value = value?.value else { return nil }
        
        if let doubleValue = value as? Double {
            return doubleValue
        } else if let intValue = value as? Int {
            return Double(intValue)
        } else if let stringValue = value as? String {
            return Double(stringValue)
        }
        return nil
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}