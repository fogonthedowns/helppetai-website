//
//  VisitRecordingView.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

import SwiftUI
import AVFoundation
import Combine

struct VisitRecordingView: View {
    let appointment: Appointment
    @State private var visitTranscripts: [VisitTranscript] = []
    @State private var visitTranscriptResponses: [VisitTranscriptResponse] = []
    @State private var isLoadingRecordings = false
    @State private var selectedPetForRecording: PetSummary?
    @State private var errorMessage: String?
    @State private var showingError = false
    @State private var showEditAppointment = false

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Visit Header
                VStack(spacing: 12) {
                    Text("\(appointment.appointmentDate, style: .date) - \(appointment.appointmentDate, style: .time)")
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
                            visitTranscripts: getPetVisitTranscripts(for: pet.id)
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
        .navigationTitle("Appointment")
        .navigationBarTitleDisplayMode(.large)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("Edit") {
                    showEditAppointment = true
                }
            }
        }
        .onAppear {
            loadRecordings()
        }
        .onDisappear {
            // Allow playback to continue across views
        }
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
                // Handle recording completion
                loadRecordings()
                // Sheet will dismiss automatically when selectedPetForRecording becomes nil
                selectedPetForRecording = nil
            }
        }
        .sheet(isPresented: $showEditAppointment) {
            EditAppointmentView(appointment: appointment) { updatedAppointment in
                // Handle appointment update
                showEditAppointment = false
                // Note: We would need to pass a callback to update the parent view
                // For now, the sheet will just dismiss
            }
        }
    }

    // MARK: - Pet Information Section

    private var petInformationSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Section Header
            HStack {
                Text("Pet Information")
                    .font(.headline)
                    .fontWeight(.semibold)

                Spacer()
            }
            .padding(.horizontal)

            // Pet Information Cards
            VStack(spacing: 12) {
                ForEach(appointment.pets, id: \.id) { pet in
                    NavigationLink(destination: PetDetailView(petId: pet.id)) {
                        PetInformationRow(pet: pet)
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
                // Try the new endpoint first
                let appointmentTranscripts = try await APIManager.shared.getVisitTranscriptsByAppointment(
                    appointmentId: appointment.id
                )

                // Convert VisitTranscriptResponse to VisitTranscript for compatibility
                let convertedTranscripts = appointmentTranscripts.map { response in
                    convertToVisitTranscript(from: response)
                }

                await MainActor.run {
                    self.visitTranscriptResponses = appointmentTranscripts
                    self.visitTranscripts = convertedTranscripts
                    self.isLoadingRecordings = false

                    // Debug: Print transcript info
                    print("✅ NEW ENDPOINT: Loaded \(appointmentTranscripts.count) visit transcripts for appointment \(appointment.id)")
                    for transcript in appointmentTranscripts.prefix(3) {
                        print("🎵 Visit \(transcript.uuid): petId=\(transcript.petId), state=\(transcript.state), hasAudio=\(transcript.audioTranscriptUrl != nil), summary=\(transcript.summary != nil)")
                    }

                    // Validate visit transcripts have proper pet associations
                    validateVisitTranscriptPetAssociations(convertedTranscripts)
                }
            } catch {
                print("⚠️ New endpoint failed, falling back to old method: \(error)")

                // Fallback to the old method if new endpoint fails
                await loadRecordingsFallback()
            }
        }
    }

    /// Fallback method using the old approach when new endpoint is not available
    private func loadRecordingsFallback() async {
        do {
            var allVisitTranscripts: [VisitTranscript] = []

            // Load visit transcripts for each pet in the appointment
            for pet in appointment.pets {
                let petTranscripts = try await APIManager.shared.getVisitTranscripts(
                    petId: pet.id,
                    limit: 50
                )
                allVisitTranscripts.append(contentsOf: petTranscripts)
                print("🎵 FALLBACK: Found \(petTranscripts.count) total visit transcripts for pet \(pet.id)")
            }

            // Filter to only show transcripts from current appointment
            let currentAppointmentTranscripts = allVisitTranscripts.filter { transcript in
                isTranscriptFromCurrentAppointment(transcript: transcript, appointment: appointment)
            }

            await MainActor.run {
                self.visitTranscripts = currentAppointmentTranscripts
                self.isLoadingRecordings = false

                // Debug: Print filtered transcript info
                print("✅ FALLBACK: Loaded \(allVisitTranscripts.count) total transcripts, \(currentAppointmentTranscripts.count) from current appointment \(appointment.id)")
                for visitTranscript in currentAppointmentTranscripts.prefix(3) {
                    print("🎵 Current Visit \(visitTranscript.uuid): petId=\(visitTranscript.petId), state=\(visitTranscript.state), hasAudio=\(visitTranscript.audioTranscriptUrl != nil)")
                }

                // Validate visit transcripts have proper pet associations
                validateVisitTranscriptPetAssociations(currentAppointmentTranscripts)
            }
        } catch {
            await MainActor.run {
                self.isLoadingRecordings = false
                self.handleError(error)
            }
        }
    }

    // MARK: - Helper Methods

    /// Convert VisitTranscriptResponse to VisitTranscript for compatibility with existing UI components
    private func convertToVisitTranscript(from response: VisitTranscriptResponse) -> VisitTranscript {
        // Create a decoder to handle the conversion properly
        let decoder = JSONDecoder()

        // Set up date decoding strategy to match the one in APIManager
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()

            // Handle Unix timestamp (from VisitTranscriptResponse)
            if let timestamp = try? container.decode(TimeInterval.self) {
                return Date(timeIntervalSince1970: timestamp)
            }

            // Handle string dates
            let dateString = try container.decode(String.self)
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss'Z'"
            formatter.timeZone = TimeZone(abbreviation: "UTC")

            if let date = formatter.date(from: dateString) {
                return date
            }

            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode date string \(dateString)")
        }

        do {
            // Create a temporary struct that matches VisitTranscript structure
            let tempData: [String: Any] = [
                "uuid": response.uuid,
                "pet_id": response.petId,
                "visit_date": response.visitDate, // Unix timestamp
                "full_text": response.fullText as Any,
                "audio_transcript_url": response.audioTranscriptUrl as Any,
                "state": response.state.rawValue,
                "metadata": response.metadata.mapValues { $0.value }
            ]

            let jsonData = try JSONSerialization.data(withJSONObject: tempData)
            let visitTranscript = try decoder.decode(VisitTranscript.self, from: jsonData)

            return visitTranscript
        } catch {
            print("⚠️ Error converting VisitTranscriptResponse to VisitTranscript: \(error)")

            // Fallback: create a simple conversion with available data
            // Since VisitTranscript uses custom decoder, we'll create a minimal JSON structure
            let fallbackData: [String: Any] = [
                "uuid": response.uuid,
                "pet_id": response.petId,
                "visit_date": response.visitDate,
                "full_text": response.fullText ?? "",
                "audio_transcript_url": response.audioTranscriptUrl as Any,
                "state": response.state.rawValue,
                "metadata": [:]
            ]

            do {
                let fallbackJsonData = try JSONSerialization.data(withJSONObject: fallbackData)
                return try decoder.decode(VisitTranscript.self, from: fallbackJsonData)
            } catch {
                print("❌ Fallback conversion also failed: \(error)")
                // This shouldn't happen, but if it does, we'll need to handle it gracefully
                fatalError("Unable to convert VisitTranscriptResponse to VisitTranscript")
            }
        }
    }

    /// Check if a transcript belongs to the current appointment using existing data (fallback method)
    private func isTranscriptFromCurrentAppointment(transcript: VisitTranscript, appointment: Appointment) -> Bool {
        // 🎯 CRITICAL FIX: Check appointment_id from metadata FIRST!
        if let metadata = transcript.metadata {
            let appointmentIdFromMetadata = extractStringFromAnyCodable(metadata["appointment_id"])

            if let metadataAppointmentId = appointmentIdFromMetadata {
                let matches = metadataAppointmentId == appointment.id
                print("🔍 CRITICAL CHECK: Visit \(transcript.uuid) metadata appointment_id: \(metadataAppointmentId)")
                print("🔍 CRITICAL CHECK: Current appointment_id: \(appointment.id)")
                print("🔍 CRITICAL CHECK: Match result: \(matches)")

                if !matches {
                    print("❌ FALLBACK: Visit \(transcript.uuid) belongs to different appointment: \(metadataAppointmentId) != \(appointment.id)")
                    return false
                }

                print("✅ FALLBACK: Visit \(transcript.uuid) matches appointment via metadata")
                return true
            } else {
                print("⚠️ FALLBACK: Visit \(transcript.uuid) has no appointment_id in metadata, falling back to heuristics")
            }
        }

        // FALLBACK: Only use heuristics if metadata doesn't contain appointment_id
        print("🔍 FALLBACK: Using heuristic matching for visit \(transcript.uuid)")

        // 1. Same vet uploaded the recording
        guard let assignedVetId = appointment.assignedVetUserId else {
            print("🔍 FALLBACK: No assigned vet for appointment \(appointment.id)")
            return false
        }

        // Check if transcript was created by the assigned vet (using metadata if available)
        if let metadata = transcript.metadata {
            let uploadedBy = extractStringFromAnyCodable(metadata["uploaded_by"]) ??
                extractStringFromAnyCodable(metadata["recorded_by"])

            if let uploadedBy = uploadedBy {
                guard uploadedBy == assignedVetId else {
                    print("🔍 FALLBACK: Transcript \(transcript.uuid) not from assigned vet: \(uploadedBy) != \(assignedVetId)")
                    return false
                }
            }
        }

        // 2. Same date (use created_at since visit_date has timestamp issues)
        let calendar = Calendar.current
        let transcriptDate = calendar.startOfDay(for: transcript.visitDate)
        let appointmentDate = calendar.startOfDay(for: appointment.appointmentDate)

        guard transcriptDate == appointmentDate else {
            print("🔍 FALLBACK: Transcript \(transcript.uuid) from different date: \(transcriptDate) != \(appointmentDate)")
            return false
        }

        // 3. Pet is part of this appointment
        guard appointment.pets.contains(where: { $0.id == transcript.petId }) else {
            print("🔍 FALLBACK: Transcript \(transcript.uuid) pet not in appointment: \(transcript.petId)")
            return false
        }

        print("✅ FALLBACK: Transcript \(transcript.uuid) matches current appointment via heuristics")
        return true
    }

    /// Helper to extract string value from AnyCodable (fallback method)
    private func extractStringFromAnyCodable(_ value: AnyCodable?) -> String? {
        guard let value = value else { return nil }

        if let stringValue = value.value as? String {
            return stringValue
        }

        // Handle other types that can be converted to string
        return String(describing: value.value)
    }

    /// Get visit transcripts specifically for a pet
    ///
    /// CORRECT DATA MODEL: Each visit transcript belongs to exactly ONE pet.
    /// This filtering ensures we show only recordings for the specific pet.
    private func getPetVisitTranscripts(for petId: String) -> [VisitTranscript] {
        let petVisitTranscripts = visitTranscripts.filter { visitTranscript in
            visitTranscript.petId == petId
        }

        print("🎵 CORRECT FILTERING: Found \(petVisitTranscripts.count) visit transcripts for pet \(petId)")

        // Validation: Ensure we're not accidentally sharing visits across pets
        for transcript in petVisitTranscripts {
            if transcript.petId != petId {
                print("❌ DATA MODEL ERROR: Visit \(transcript.uuid) has petId \(transcript.petId) but was filtered for pet \(petId)")
            }
        }

        return petVisitTranscripts
    }

    /// Validate that all visit transcripts have proper pet associations
    private func validateVisitTranscriptPetAssociations(_ visitTranscripts: [VisitTranscript]) {
        // Check for visit transcripts with invalid pet associations
        let appointmentPetIds = Set(appointment.pets.map { $0.id })
        let invalidVisitTranscripts = visitTranscripts.filter { visitTranscript in
            !appointmentPetIds.contains(visitTranscript.petId)
        }

        if !invalidVisitTranscripts.isEmpty {
            print("⚠️ Warning: Found \(invalidVisitTranscripts.count) visit transcripts with pets not in this appointment")

            // Show warning to user about data inconsistency
            errorMessage = "Some visit records may not display correctly due to data inconsistencies. Please contact support if this persists."
            showingError = true
        }

        // Check for failed states
        let failedVisitTranscripts = visitTranscripts.filter { $0.state == .failed }
        if !failedVisitTranscripts.isEmpty {
            print("⚠️ Found \(failedVisitTranscripts.count) failed visit transcripts")
        }
    }

    /// Handle errors with user-friendly messages
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
                if code == 500 {
                    errorMessage = "The recording service is temporarily unavailable. The app will continue to work, but some features may be limited."
                } else {
                    errorMessage = "Server error (\(code)). Please try again later"
                }
            default:
                errorMessage = "Failed to load recordings. Please try again"
            }
        } else {
            errorMessage = "An unexpected error occurred: \(error.localizedDescription)"
        }

        // Only show error for critical failures, not for fallback scenarios
        var shouldShowError = true

        if let apiError = error as? APIError,
           case .serverError(let code) = apiError,
           code == 500 {
            // For 500 errors, we're falling back gracefully, so just log it
            shouldShowError = false
            print("ℹ️ Using fallback method due to server error, user experience should be unaffected")
        }

        if shouldShowError {
            showingError = true
        }
    }
}

// MARK: - Pet Recording Card Component (Voice Memos Style)
struct PetRecordingCard: View {
    let pet: PetSummary
    let appointment: Appointment
    let visitTranscripts: [VisitTranscript]
    let onStartRecording: () -> Void

    @ObservedObject private var audioManager = AudioManager.shared
    @State private var expandedVisitId: String? = nil

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
                if visitTranscripts.isEmpty {
                    Image(systemName: "circle")
                        .font(.title3)
                        .foregroundColor(.gray)
                } else {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.title3)
                        .foregroundColor(.green)
                }
            }

            // Recording Interface
            if visitTranscripts.isEmpty {
                // No recordings - show record button
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
                // Show collapsible audio players (like Voice Memos)
                VStack(spacing: 8) {
                    ForEach(visitTranscripts.filter { $0.audioTranscriptUrl != nil }, id: \.uuid) { visitTranscript in
                        if expandedVisitId == visitTranscript.uuid || audioManager.currentlyPlayingVisitId == visitTranscript.uuid {
                            // Show full player for expanded/playing item
                            MacStyleAudioPlayer(visitTranscript: visitTranscript)
                        } else {
                            // Show collapsed header for other items
                            CollapsedAudioHeader(
                                visitTranscript: visitTranscript,
                                onTap: {
                                    withAnimation(.easeInOut(duration: 0.3)) {
                                        expandedVisitId = visitTranscript.uuid
                                    }
                                }
                            )
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.1), radius: 4, x: 0, y: 2)
        .onChange(of: audioManager.currentlyPlayingVisitId) { newValue in
            // Auto-expand the currently playing item
            if let playingId = newValue {
                withAnimation(.easeInOut(duration: 0.3)) {
                    expandedVisitId = playingId
                }
            }
        }
    }
}

// MARK: - Collapsed Audio Header
struct CollapsedAudioHeader: View {
    let visitTranscript: VisitTranscript
    let onTap: () -> Void
    @ObservedObject private var audioManager = AudioManager.shared
    
    private var isCurrentlyPlaying: Bool {
        audioManager.currentlyPlayingVisitId == visitTranscript.uuid && audioManager.isPlaying
    }
    
    private var displayTitle: String {
        return "Audio Recording"
    }
    
    private var recordedAt: String {
        if let fileSizeBytes = visitTranscript.metadata?["file_size_bytes"]?.value as? Int {
            let sizeKB = fileSizeBytes / 1024
            return "\(sizeKB) KB"
        }
        return "Recording"
    }
    
    private func formatTimestamp(_ timestamp: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        
        if let date = formatter.date(from: timestamp) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateStyle = .short
            displayFormatter.timeStyle = .short
            return displayFormatter.string(from: date)
        }
        return timestamp
    }
    
    private func formatDuration(_ duration: TimeInterval) -> String {
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
    
    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 12) {
                // Audio waveform icon
                ZStack {
                    Circle()
                        .fill(isCurrentlyPlaying ? Color.blue : Color.gray.opacity(0.1))
                        .frame(width: 36, height: 36)
                    
                    Image(systemName: "waveform")
                        .font(.system(size: 16))
                        .foregroundColor(isCurrentlyPlaying ? .white : .gray)
                }
                
                // Audio info
                VStack(alignment: .leading, spacing: 2) {
                    Text(displayTitle)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                    
                    Text(recordedAt)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                // Duration
                if let duration = visitTranscript.metadata?["duration_seconds"]?.value as? Double {
                    Text(formatDuration(duration))
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .monospacedDigit()
                }
                
                // Chevron indicator
                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.gray)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .contentShape(Rectangle())
        }
        .buttonStyle(PlainButtonStyle())
        .background(Color(.secondarySystemBackground))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isCurrentlyPlaying ? Color.blue.opacity(0.3) : Color.clear, lineWidth: 2)
        )
    }
}

// MARK: - Mac-Style Audio Player Component
struct MacStyleAudioPlayer: View {
    let visitTranscript: VisitTranscript
    @ObservedObject private var audioManager = AudioManager.shared
    @State private var showingDeleteAlert = false
    @State private var errorMessage: String?
    @State private var showingError = false
    
    // Polled UI state (keeps UI responsive)
    @State private var polledCurrentlyPlayingVisitId: String?
    @State private var polledIsPlaying: Bool = false
    @State private var polledCurrentPlaybackTime: TimeInterval = 0
    @State private var polledTotalPlaybackTime: TimeInterval = 0
    
    // Timer to poll the audio manager
    @State private var pollTimer: Timer?
    @Environment(\.scenePhase) private var scenePhase
    
    private var isCurrentlyPlaying: Bool {
        return polledCurrentlyPlayingVisitId == visitTranscript.uuid && polledIsPlaying
    }
    
    private var isCurrentVisit: Bool {
        return polledCurrentlyPlayingVisitId == visitTranscript.uuid
    }
    
    private var shouldShowPauseIcon: Bool {
        return audioManager.currentlyPlayingVisitId == visitTranscript.uuid && audioManager.isPlaying
    }
    
    private func debugButtonState() {
        let currentId = audioManager.currentlyPlayingVisitId
        let thisId = visitTranscript.uuid
        let isPlaying = audioManager.isPlaying
        let showPause = shouldShowPauseIcon
        print("🔘 Button render - currentId: \(currentId ?? "nil"), thisId: \(thisId), isPlaying: \(isPlaying), showPause: \(showPause)")
    }
    
    var body: some View {
        VStack(spacing: 12) {
            // Waveform/Progress Bar (Mac-style)
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
                        
                        // Scrubber handle - ALWAYS show for current visit
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 16, height: 16)
                            .offset(x: max(0, progressWidth(for: geometry.size.width) - 8))
                            .shadow(color: .black.opacity(0.1), radius: 1, x: 0, y: 1)
                    }
                    .contentShape(Rectangle())
                    .gesture(
                        DragGesture()
                            .onChanged { value in
                                guard polledTotalPlaybackTime > 0 else { return }
                                let progress = max(0, min(1, value.location.x / geometry.size.width))
                                let newTime = progress * polledTotalPlaybackTime
                                polledCurrentPlaybackTime = newTime
                                if polledCurrentlyPlayingVisitId == visitTranscript.uuid {
                                    audioManager.seekTo(time: newTime)
                                }
                            }
                            .onEnded { value in
                                guard polledTotalPlaybackTime > 0 else { return }
                                let progress = max(0, min(1, value.location.x / geometry.size.width))
                                let newTime = progress * polledTotalPlaybackTime
                                audioManager.seekTo(time: newTime)
                            }
                    )
                    .disabled(polledCurrentlyPlayingVisitId != visitTranscript.uuid)
                }
                .frame(height: 20)
                
                // Time display
                HStack {
                    Text(formatTime(isCurrentVisit ? polledCurrentPlaybackTime : 0))
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                        .monospacedDigit()
                    
                    Spacer()
                    
                    if polledTotalPlaybackTime > 0 {
                        let timeLeft = isCurrentVisit ? max(0, polledTotalPlaybackTime - polledCurrentPlaybackTime) : polledTotalPlaybackTime
                        Text("-\(formatTime(timeLeft))")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .monospacedDigit()
                    } else {
                        Text("-0:00")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .monospacedDigit()
                    }
                }
            }
            
            // Control buttons (Mac-style centered layout)
            HStack {
                Spacer()
                
                // Skip back 15 seconds
                Button(action: {
                    audioManager.skipForward(seconds: -15)
                    polledCurrentPlaybackTime = max(0, polledCurrentPlaybackTime - 15)
                }) {
                    Image(systemName: "gobackward.15")
                        .font(.system(size: 20, weight: .medium))
                        .foregroundColor(.blue)
                }
                .disabled(polledCurrentlyPlayingVisitId != visitTranscript.uuid)
                
                // Main play/pause button
                Button(action: togglePlayback) {
                    let _ = debugButtonState() // Call debug function
                    Image(systemName: shouldShowPauseIcon ? "pause.circle.fill" : "play.circle.fill")
                        .font(.system(size: 40))
                        .foregroundColor(.blue)
                }
                .padding(.horizontal, 24)
                
                // Skip forward 15 seconds
                Button(action: {
                    audioManager.skipForward(seconds: 15)
                    polledCurrentPlaybackTime = min(polledTotalPlaybackTime, polledCurrentPlaybackTime + 15)
                }) {
                    Image(systemName: "goforward.15")
                        .font(.system(size: 20, weight: .medium))
                        .foregroundColor(.blue)
                }
                .disabled(polledCurrentlyPlayingVisitId != visitTranscript.uuid)
                
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
        .onAppear {
            startPolling()
            // Initialize values
            if let metadata = visitTranscript.metadata,
               let duration = metadata["duration_seconds"]?.value as? Double {
                polledTotalPlaybackTime = duration
            } else if polledTotalPlaybackTime == 0 {
                if audioManager.totalPlaybackTime > 0 {
                    polledTotalPlaybackTime = audioManager.totalPlaybackTime
                }
            }
            
            polledCurrentlyPlayingVisitId = audioManager.currentlyPlayingVisitId
            polledIsPlaying = audioManager.isPlaying
            polledCurrentPlaybackTime = audioManager.currentPlaybackTime
        }
        .onChange(of: scenePhase) { newPhase in
            if newPhase != .active {
                stopPolling()
            } else {
                startPolling()
            }
        }
        .onDisappear {
            stopPolling()
        }
        .alert("Playback Error", isPresented: $showingError) {
            Button("OK") { }
        } message: {
            Text(errorMessage ?? "An unknown error occurred")
        }
    }
    
    private func togglePlayback() {
        print("🎵 TOGGLE START: visitId=\(visitTranscript.uuid)")
        print("🎵 AudioManager state: currentId=\(audioManager.currentlyPlayingVisitId ?? "nil"), isPlaying=\(audioManager.isPlaying)")
        
        if audioManager.currentlyPlayingVisitId == visitTranscript.uuid {
            // This visit is currently playing, toggle pause/resume
            if audioManager.isPlaying {
                print("🎵 PAUSING playback")
                audioManager.pausePlayback()
            } else {
                print("🎵 RESUMING playback")
                audioManager.resumePlayback()
            }
        } else {
            // Start new playback for this visit
            print("🎵 STARTING new playback")
            Task {
                do {
                    try await audioManager.playVisitRecording(visitId: visitTranscript.uuid)
                    print("🎵 Started successfully")
                } catch {
                    print("❌ Playback error: \(error)")
                    
                    // Show user-friendly error message
                    await MainActor.run {
                        if let audioError = error as? AudioError {
                            switch audioError {
                            case .fileNotFound:
                                errorMessage = "This recording is no longer available. It may have been archived or deleted from the server."
                            case .permissionDenied:
                                errorMessage = "You don't have permission to play this recording. Please contact your administrator."
                            default:
                                errorMessage = audioError.localizedDescription
                            }
                        } else {
                            errorMessage = "Unable to play this recording. Please try again or contact support if the issue persists."
                        }
                        showingError = true
                    }
                }
            }
        }
        
        // Force UI update
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            print("🎵 After toggle: currentId=\(self.audioManager.currentlyPlayingVisitId ?? "nil"), isPlaying=\(self.audioManager.isPlaying)")
        }
    }
    
    private func deleteRecording() {
        print("Delete recording requested for visit: \(visitTranscript.uuid)")
    }
    
    private func progressWidth(for totalWidth: CGFloat) -> CGFloat {
        if polledTotalPlaybackTime > 0 {
            let progress = polledCurrentPlaybackTime / polledTotalPlaybackTime
            return max(0, min(totalWidth, totalWidth * progress))
        } else {
            return 0
        }
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
    
    private func startPolling() {
        stopPolling()
        pollTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { _ in
            DispatchQueue.main.async {
                let wasPlaying = self.polledIsPlaying
                self.polledCurrentlyPlayingVisitId = self.audioManager.currentlyPlayingVisitId
                self.polledIsPlaying = self.audioManager.isPlaying
                self.polledCurrentPlaybackTime = self.audioManager.currentPlaybackTime
                
                // Update total time if we're the current visit
                if self.polledCurrentlyPlayingVisitId == self.visitTranscript.uuid {
                    if self.audioManager.totalPlaybackTime > 0 {
                        self.polledTotalPlaybackTime = self.audioManager.totalPlaybackTime
                    }
                }
                
                // Debug output when state changes
                if wasPlaying != self.polledIsPlaying {
                    print("🎵 State change: isPlaying=\(self.polledIsPlaying), visitId=\(self.visitTranscript.uuid)")
                }
            }
        }
        if let t = pollTimer { RunLoop.main.add(t, forMode: .common) }
    }
    
    private func stopPolling() {
        pollTimer?.invalidate()
        pollTimer = nil
    }
}


// MARK: - Pet Information Row Component

struct PetInformationRow: View {
    let pet: PetSummary

    var body: some View {
        HStack(spacing: 16) {
            // Pet Icon
            Image(systemName: pet.species.lowercased() == "dog" ? "pawprint.fill" : "cat.fill")
                .font(.title2)
                .foregroundColor(.blue)
                .frame(width: 32, height: 32)

            // Pet Details
            VStack(alignment: .leading, spacing: 4) {
                Text("\(pet.name) Medical Record")
                    .font(.headline)
                    .fontWeight(.semibold)
                    .foregroundColor(.primary)

                Text("\(pet.species.capitalized) • \(pet.breed ?? "Mixed")")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }

            Spacer()

            // Arrow Icon
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
