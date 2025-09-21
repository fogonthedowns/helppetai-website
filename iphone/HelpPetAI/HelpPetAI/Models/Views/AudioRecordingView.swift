// MARK: - Views/AudioRecordingView.swift (Updated for S3 Architecture)
import SwiftUI
import AVFoundation

struct AudioRecordingView: View {
    let appointmentId: String
    let petId: String
    let petName: String
    let visitId: String?
    let onRecordingComplete: (AudioUploadResult) -> Void
    
    @StateObject private var audioManager = AudioManager.shared
    @State private var currentRecordingURL: URL?
    @State private var showingPermissionAlert = false
    @State private var uploadError: String?
    @State private var showingUploadError = false
    
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            VStack(spacing: 30) {
                // Header
                VStack(spacing: 8) {
                    Image(systemName: audioManager.isRecording ? "waveform" : "mic.circle")
                        .font(.system(size: 80))
                        .foregroundColor(audioManager.isRecording ? .red : .blue)
                        .symbolEffect(.pulse, isActive: audioManager.isRecording)
                    
                    Text(audioManager.isRecording ? "Recording..." : "Ready to Record")
                        .font(.title2)
                        .fontWeight(.medium)
                    
                    // Pet-specific info
                    Text("Recording for \(petName)")
                        .font(.subheadline)
                        .foregroundColor(.blue)
                        .fontWeight(.medium)
                }
                .padding(.top, 40)
                
                // Recording Duration
                if audioManager.isRecording || audioManager.recordingDuration > 0 {
                    VStack(spacing: 4) {
                        Text("Duration")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Text(audioManager.formatTime(audioManager.recordingDuration))
                            .font(.title)
                            .fontWeight(.semibold)
                            .monospacedDigit()
                    }
                }
                
                Spacer()
                
                // Recording Controls
                VStack(spacing: 20) {
                    // Main Record Button
                    Button(action: toggleRecording) {
                        ZStack {
                            Circle()
                                .fill(audioManager.isRecording ? Color.red : Color.blue)
                                .frame(width: 100, height: 100)
                            
                            Image(systemName: audioManager.isRecording ? "stop.fill" : "mic.fill")
                                .font(.system(size: 40))
                                .foregroundColor(.white)
                        }
                    }
                    .disabled(!audioManager.hasPermission)
                    .scaleEffect(audioManager.isRecording ? 1.1 : 1.0)
                    .animation(.easeInOut(duration: 0.1), value: audioManager.isRecording)
                    
                    Text(audioManager.isRecording ? "Tap to Stop" : "Tap to Record")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                // Playback and Upload Controls
                if currentRecordingURL != nil && !audioManager.isRecording {
                    VStack(spacing: 16) {
                        // Playback Button
                        Button(action: togglePlayback) {
                            HStack {
                                Image(systemName: audioManager.isPlaying ? "stop.fill" : "play.fill")
                                Text(audioManager.isPlaying ? "Stop Playback" : "Play Recording")
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.green.opacity(0.1))
                            .foregroundColor(.green)
                            .cornerRadius(12)
                        }
                        
                        // Upload Button with Progress
                        VStack(spacing: 8) {
                            Button(action: uploadRecording) {
                                HStack {
                                    if audioManager.isUploading {
                                        ProgressView()
                                            .scaleEffect(0.8)
                                    } else {
                                        Image(systemName: "icloud.and.arrow.up")
                                    }
                                    Text(audioManager.isUploading ? "Uploading..." : "Save Recording")
                                }
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(audioManager.isUploading ? Color.gray : Color.blue)
                                .foregroundColor(.white)
                                .cornerRadius(12)
                            }
                            .disabled(audioManager.isUploading)
                            
                            // Upload Progress Bar
                            if audioManager.isUploading {
                                VStack(spacing: 4) {
                                    ProgressView(value: audioManager.uploadProgress)
                                        .progressViewStyle(LinearProgressViewStyle(tint: .blue))
                                    
                                    Text(String(format: "%.0f%%", audioManager.uploadProgress * 100))
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                .padding(.horizontal)
                            }
                        }
                    }
                    .padding(.horizontal)
                }
                
                // Permission Message
                if !audioManager.hasPermission {
                    VStack(spacing: 12) {
                        Image(systemName: "mic.slash")
                            .font(.system(size: 40))
                            .foregroundColor(.orange)
                        
                        Text("Microphone Access Required")
                            .font(.headline)
                        
                        Text("This app needs microphone access to record visit notes.")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                        
                        Button("Enable Microphone") {
                            requestPermission()
                        }
                        .buttonStyle(.borderedProminent)
                    }
                    .padding()
                }
                
                Spacer()
            }
            .navigationTitle("Record Visit - \(petName)")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        if audioManager.isRecording {
                            Task {
                                _ = await audioManager.stopRecording()
                            }
                        }
                        dismiss()
                    }
                }
                
                if currentRecordingURL != nil && !audioManager.isRecording && !audioManager.isUploading {
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Button("Delete") {
                            deleteRecording()
                        }
                        .foregroundColor(.red)
                    }
                }
            }
            .alert("Microphone Permission", isPresented: $showingPermissionAlert) {
                Button("Settings") {
                    if let settingsURL = URL(string: UIApplication.openSettingsURLString) {
                        UIApplication.shared.open(settingsURL)
                    }
                }
                Button("Cancel", role: .cancel) { }
            } message: {
                Text("Please enable microphone access in Settings to record audio.")
            }
            .alert("Upload Error", isPresented: $showingUploadError) {
                Button("Retry Upload") { 
                    uploadRecording()
                }
                Button("Cancel", role: .cancel) { }
            } message: {
                Text(uploadError ?? "Unknown error occurred")
            }
            .onAppear {
                // Reset recording state when view appears for new pet
                audioManager.resetRecordingState()
            }
            .onDisappear {
                // CRITICAL: Stop all audio when leaving recording view
                audioManager.stopPlayback()
                audioManager.resetRecordingState()
            }
        }
    }
    
    private func toggleRecording() {
        if audioManager.isRecording {
            // Stop recording
            Task {
                currentRecordingURL = await audioManager.stopRecording()
            }
        } else {
            // Start recording
            Task {
                do {
                    currentRecordingURL = try await audioManager.startRecording(
                        appointmentId: appointmentId,
                        visitId: visitId ?? ""
                    )
                } catch AudioError.permissionDenied {
                    showingPermissionAlert = true
                } catch {
                    uploadError = error.localizedDescription
                    showingUploadError = true
                }
            }
        }
    }
    
    private func togglePlayback() {
        guard let url = currentRecordingURL else { return }
        
        if audioManager.isPlaying {
            audioManager.stopPlayback()
        } else {
            Task {
                do {
                    try await audioManager.playRecording(from: url)
                } catch {
                    uploadError = error.localizedDescription
                    showingUploadError = true
                }
            }
        }
    }
    
    private func uploadRecording() {
        guard let url = currentRecordingURL else { return }
        
        Task {
            do {
                let result = try await audioManager.uploadRecording(
                    fileURL: url,
                    appointmentId: appointmentId,
                    petId: petId,
                    visitId: visitId
                )
                
                await MainActor.run {
                    self.onRecordingComplete(result)
                    self.dismiss()
                }
                
            } catch {
                await MainActor.run {
                    // Provide user-friendly error messages
                    if let audioError = error as? AudioError {
                        self.uploadError = audioError.localizedDescription
                    } else if let apiError = error as? APIError,
                              case .serverError(let code) = apiError,
                              code == 500 {
                        self.uploadError = "The recording service is temporarily down. Your recording has been saved locally. Please try uploading again in a few moments."
                    } else {
                        self.uploadError = "Upload failed: \(error.localizedDescription)"
                    }
                    self.showingUploadError = true
                }
            }
        }
    }
    
    private func deleteRecording() {
        if let url = currentRecordingURL {
            audioManager.deleteLocalRecording(at: url)
            currentRecordingURL = nil
        }
    }
    
    private func requestPermission() {
        Task {
            await audioManager.requestMicrophonePermission()
        }
    }
}
