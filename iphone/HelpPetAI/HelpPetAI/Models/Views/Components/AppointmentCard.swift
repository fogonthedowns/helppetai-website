// MARK: - Updated Views/Components/AppointmentCard.swift (S3 Integration)
import SwiftUI

struct PetCountChips: View {
    let pets: [PetSummary]
    
    private var petCounts: [(species: String, count: Int)] {
        let groupedPets = Dictionary(grouping: pets) { pet in
            pet.species.lowercased()
        }
        
        return groupedPets.map { (species, petArray) in
            (species: species, count: petArray.count)
        }.sorted { $0.species < $1.species }
    }
    
    var body: some View {
        HStack(spacing: 8) {
            ForEach(petCounts, id: \.species) { item in
                HStack(spacing: 4) {
                    Image(systemName: item.species == "dog" ? "pawprint.fill" : "cat.fill")
                        .font(.caption)
                        .foregroundColor(.blue)
                    
                    Text("\(item.count) \(item.species)\(item.count == 1 ? "" : "s")")
                        .font(.caption)
                        .fontWeight(.medium)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.blue.opacity(0.1))
                .foregroundColor(.blue)
                .cornerRadius(12)
            }
            
            Spacer()
        }
    }
}

struct AppointmentCard: View {
    let appointment: Appointment
    let status: AppointmentStatus
    let onStatusChanged: () -> Void
    

    
    var body: some View {
        NavigationLink(destination: VisitRecordingView(appointment: appointment)) {
            VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(appointment.appointmentDate, style: .time)
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    Text("\(appointment.durationMinutes) min")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                StatusBadge(status: status)
            }
            
            // Title and Pet Info
            VStack(alignment: .leading, spacing: 8) {
                Text(appointment.title)
                    .font(.headline)
                
                // Pet count chips
                PetCountChips(pets: appointment.pets)
                
                if let description = appointment.description {
                    Text(description)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color(.separator), lineWidth: 0.5)
        )
        .shadow(color: Color.black.opacity(0.1), radius: 2, x: 0, y: 1)
        }
    }
}

// MARK: - Visit Transcripts Section Component (v2.0)
struct VisitTranscriptsSection: View {
    let visitTranscripts: [VisitTranscript]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "waveform")
                    .foregroundColor(.blue)
                    .font(.caption)
                
                Text("Visit Recordings (\(visitTranscripts.count))")
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.secondary)
                
                Spacer()
            }
            
            LazyVStack(spacing: 6) {
                ForEach(visitTranscripts) { visitTranscript in
                    VisitTranscriptRow(visitTranscript: visitTranscript)
                }
            }
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 12)
        .background(Color(.systemGray6))
        .cornerRadius(8)
    }
}

// MARK: - Individual Visit Transcript Row (v2.0)
struct VisitTranscriptRow: View {
    let visitTranscript: VisitTranscript
    @StateObject private var audioManager = AudioManager.shared
    @State private var showingError = false
    @State private var errorMessage = ""
    @State private var showingDeleteAlert = false
    
    private var isCurrentlyPlaying: Bool {
        audioManager.currentlyPlayingVisitId == visitTranscript.uuid && audioManager.isPlaying
    }
    
    private var isCurrentVisit: Bool {
        audioManager.currentlyPlayingVisitId == visitTranscript.uuid
    }
    
    var body: some View {
        VStack(spacing: 8) {
            // Main row
            HStack(spacing: 8) {
                // Status indicator
                Circle()
                    .fill(statusColor)
                    .frame(width: 8, height: 8)
                
                // Visit info
                VStack(alignment: .leading, spacing: 2) {
                    HStack {
                        Text(visitTranscript.state.displayName)
                            .font(.caption)
                            .fontWeight(.medium)
                            .lineLimit(1)
                        
                        Spacer()
                        
                        if let metadata = visitTranscript.metadata,
                           let duration = metadata["duration_seconds"]?.value as? Double {
                            Text(AudioManager.shared.formatTime(duration))
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    HStack {
                        Text(visitTranscript.visitDate, style: .time)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
                
                // Basic play button (only if has audio URL)
                if visitTranscript.audioTranscriptUrl != nil {
                    Button(action: togglePlayback) {
                        Image(systemName: isCurrentlyPlaying ? "pause.circle.fill" : "play.circle.fill")
                            .foregroundColor(.blue)
                            .font(.system(size: 16))
                    }
                }
            }
            
            // Enhanced player controls (shown when this visit is playing)
            if isCurrentVisit && audioManager.totalPlaybackTime > 0 {
                EnhancedAudioPlayerControls(
                    visitTranscript: visitTranscript,
                    onDelete: {
                        showingDeleteAlert = true
                    }
                )
            }
        }
        .alert("Playback Error", isPresented: $showingError) {
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
        .alert("Delete Recording", isPresented: $showingDeleteAlert) {
            Button("Cancel", role: .cancel) { }
            Button("Delete", role: .destructive) {
                deleteRecording()
            }
        } message: {
            Text("Are you sure you want to delete this recording? This action cannot be undone.")
        }
    }
    
    private var statusColor: Color {
        switch visitTranscript.state {
        case .new: return .gray
        case .processing: return .blue
        case .processed: return .green
        case .failed: return .red
        }
    }
    
    private func togglePlayback() {
        if isCurrentlyPlaying {
            // Pause playback
            AudioManager.shared.pausePlayback()
        } else if isCurrentVisit {
            // Resume playback
            AudioManager.shared.resumePlayback()
        } else {
            // Start playback using v2.0 visit-based approach
            Task {
                do {
                    try await AudioManager.shared.playVisitRecording(visitId: visitTranscript.uuid)
                } catch {
                    await MainActor.run {
                        if let audioError = error as? AudioError {
                            switch audioError {
                            case .fileNotFound:
                                self.errorMessage = "This recording is no longer available. It may have been archived or deleted from the server."
                            case .permissionDenied:
                                self.errorMessage = "You don't have permission to play this recording. Please contact your administrator."
                            default:
                                self.errorMessage = audioError.localizedDescription
                            }
                        } else {
                            self.errorMessage = "Unable to play this recording. Please try again or contact support if the issue persists."
                        }
                        self.showingError = true
                    }
                }
            }
        }
    }
    
    private func deleteRecording() {
        // Only allow deletion of non-uploaded recordings
        // For now, we'll just show an error since we don't track local recordings
        errorMessage = "Recording deletion is only available for local recordings that haven't been uploaded."
        showingError = true
    }
}

// MARK: - Enhanced Audio Player Controls
struct EnhancedAudioPlayerControls: View {
    let visitTranscript: VisitTranscript
    let onDelete: () -> Void
    @StateObject private var audioManager = AudioManager.shared
    
    var body: some View {
        VStack(spacing: 12) {
            // Time display and progress bar
            VStack(spacing: 8) {
                // Progress bar
                GeometryReader { geometry in
                    ZStack(alignment: .leading) {
                        // Background track
                        Rectangle()
                            .fill(Color(.systemGray4))
                            .frame(height: 4)
                            .cornerRadius(2)
                        
                        // Progress track
                        Rectangle()
                            .fill(Color.blue)
                            .frame(width: progressWidth(for: geometry.size.width), height: 4)
                            .cornerRadius(2)
                        
                        // Scrub handle
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 16, height: 16)
                            .offset(x: progressWidth(for: geometry.size.width) - 8)
                    }
                    .contentShape(Rectangle())
                    .gesture(
                        DragGesture()
                            .onChanged { value in
                                let progress = value.location.x / geometry.size.width
                                let clampedProgress = max(0, min(1, progress))
                                let newTime = clampedProgress * audioManager.totalPlaybackTime
                                audioManager.seekTo(time: newTime)
                            }
                    )
                }
                .frame(height: 16)
                
                // Time labels
                HStack {
                    Text(AudioManager.shared.formatTime(audioManager.currentPlaybackTime))
                        .font(.caption2)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                    
                    Spacer()
                    
                    Text("-\(AudioManager.shared.formatTime(audioManager.totalPlaybackTime - audioManager.currentPlaybackTime))")
                        .font(.caption2)
                        .fontWeight(.medium)
                        .foregroundColor(.secondary)
                }
            }
            
            // Control buttons
            HStack(spacing: 20) {
                // Skip 15 seconds button
                Button(action: {
                    AudioManager.shared.skipForward(seconds: 15)
                }) {
                    HStack(spacing: 4) {
                        Image(systemName: "goforward.15")
                            .font(.system(size: 14))
                        Text("15s")
                            .font(.caption2)
                    }
                    .foregroundColor(.blue)
                }
                
                Spacer()
                
                // Delete button (only for non-uploaded recordings)
                Button(action: onDelete) {
                    HStack(spacing: 4) {
                        Image(systemName: "trash")
                            .font(.system(size: 14))
                        Text("Delete")
                            .font(.caption2)
                    }
                    .foregroundColor(.red)
                }
            }
        }
        .padding(12)
        .background(Color(.systemGray6))
        .cornerRadius(8)
    }
    
    private func progressWidth(for totalWidth: CGFloat) -> CGFloat {
        guard audioManager.totalPlaybackTime > 0 else { return 0 }
        let progress = audioManager.currentPlaybackTime / audioManager.totalPlaybackTime
        return max(0, min(totalWidth, totalWidth * progress))
    }
}

// MARK: - Record Button Styles
struct RecordButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.subheadline)
            .fontWeight(.medium)
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(Color.red.opacity(0.1))
            .foregroundColor(.red)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.red.opacity(0.3), lineWidth: 1)
            )
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
    }
}

struct PetRecordButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.subheadline)
            .fontWeight(.medium)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .frame(maxWidth: .infinity)
            .background(Color.red.opacity(0.1))
            .foregroundColor(.red)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.red.opacity(0.3), lineWidth: 1)
            )
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
    }
}
