//
//  ResponsiveAudioManager.swift
//  HelpPetAI
//
//  TL;DR: High-performance audio manager optimized for instant UI responsiveness.
//
//  Features:
//  - Ultra-fast start/stop recording with non-blocking UI updates
//  - Lightweight recording settings (reduced bitrate, medium quality) for speed
//  - Background queues for audio processing & uploads
//  - Lightning-fast S3 upload flow with progress tracking
//  - Upload lifecycle states: idle → securing → uploading → completed/failed
//  - Instant file cleanup after successful upload
//  - Optimized playback (direct local or auto-download remote)
//  - Safe concurrency with MainActor for UI-bound state
//  - Utility: live timer, duration formatting, reset state
//  - Observable state for SwiftUI (`isRecording`, `isPlaying`, `uploadProgress`, etc.)
//
//  Usage: Access via `ResponsiveAudioManager.shared` (singleton).
//

import Foundation
import AVFoundation
import CryptoKit
import UIKit

/// Ultra-responsive audio manager that never blocks the UI
class ResponsiveAudioManager: NSObject, ObservableObject {
    static let shared = ResponsiveAudioManager()
    
    @Published var isRecording = false
    @Published var isPlaying = false
    @Published var recordingDuration: TimeInterval = 0
    @Published var hasPermission = false
    @Published var uploadProgress: Double = 0.0
    @Published var uploadStatus: UploadStatus = .idle
    
    private var audioRecorder: AVAudioRecorder?
    private var audioPlayer: AVAudioPlayer?
    private var recordingTimer: Timer?
    private var currentRecordingURL: URL?
    
    // Background processing
    private let backgroundQueue = DispatchQueue(label: "audio.processing", qos: .userInitiated)
    private let uploadQueue = DispatchQueue(label: "audio.upload", qos: .utility)
    
    enum UploadStatus: String {
        case idle = "idle"
        case securing = "securing"
        case uploading = "uploading" 
        case completed = "completed"
        case failed = "failed"
    }
    
    private override init() {
        super.init()
        checkMicrophonePermission()
    }
    
    // MARK: - Permission Management (Same as before)
    func requestMicrophonePermission() async -> Bool {
        return await withCheckedContinuation { continuation in
            AVAudioApplication.requestRecordPermission { granted in
                DispatchQueue.main.async {
                    self.hasPermission = granted
                    continuation.resume(returning: granted)
                }
            }
        }
    }
    
    private func checkMicrophonePermission() {
        switch AVAudioApplication.shared.recordPermission {
        case .granted:
            hasPermission = true
        case .denied, .undetermined:
            hasPermission = false
        @unknown default:
            hasPermission = false
        }
    }
    
    // MARK: - INSTANT Recording Start/Stop
    func startRecording(appointmentId: String, visitId: String? = nil) async throws -> URL? {
        // INSTANT UI update - no blocking operations
        await MainActor.run {
            self.resetRecordingState()
            self.uploadStatus = .idle
        }
        
        // Quick permission check (cached)
        if !hasPermission {
            let granted = await requestMicrophonePermission()
            if !granted {
                throw AudioError.permissionDenied
            }
        }
        
        // INSTANT audio session setup (minimal blocking)
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker])
        try audioSession.setActive(true)
        
        // Create recording URL instantly
        let timestamp = DateFormatter().apply {
            $0.dateFormat = "yyyyMMdd_HHmmss"
        }.string(from: Date())
        
        let fileName = "recording_\(timestamp).m4a"
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let audioURL = documentsPath.appendingPathComponent(fileName)
        
        // Optimized recording settings for speed
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 44100,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.medium.rawValue, // Changed from high for speed
            AVEncoderBitRateKey: 96000 // Reduced from 128k for faster processing
        ]
        
        // INSTANT recorder creation and start
        audioRecorder = try AVAudioRecorder(url: audioURL, settings: settings)
        audioRecorder?.delegate = self
        audioRecorder?.isMeteringEnabled = false // Disable for performance
        audioRecorder?.prepareToRecord()
        
        if audioRecorder?.record() == true {
            await MainActor.run {
                self.isRecording = true
                self.recordingDuration = 0
                self.currentRecordingURL = audioURL
                self.startTimer()
            }
            
            print("✅ INSTANT recording started: \(audioURL.lastPathComponent)")
            return audioURL
        } else {
            throw AudioError.recordingFailed
        }
    }
    
    func stopRecording() async -> URL? {
        guard let recorder = audioRecorder, recorder.isRecording else {
            return nil
        }
        
        let audioURL = recorder.url
        recorder.stop()
        
        // INSTANT UI update
        await MainActor.run {
            self.isRecording = false
            self.stopTimer()
        }
        
        // Quick cleanup
        try? AVAudioSession.sharedInstance().setActive(false)
        
        print("✅ INSTANT recording stopped: \(audioURL.lastPathComponent)")
        return audioURL
    }
    
    // MARK: - Lightning-Fast Upload with Background Processing
    func uploadRecording(
        fileURL: URL,
        appointmentId: String,
        petId: String,
        visitId: String? = nil
    ) async throws -> AudioUploadResult {
        
        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            throw AudioError.fileNotFound
        }
        
        // INSTANT UI feedback - no blocking
        await MainActor.run {
            self.uploadStatus = .securing
            self.uploadProgress = 0.1
        }
        
        print("🚀 LIGHTNING upload starting for: \(fileURL.lastPathComponent)")
        
        // Generate unique upload ID immediately
        let uploadId = UUID().uuidString
        
        // ALL heavy operations moved to background
        return try await withCheckedThrowingContinuation { continuation in
            backgroundQueue.async {
                self.performBackgroundUpload(
                    fileURL: fileURL,
                    appointmentId: appointmentId,
                    petId: petId,
                    uploadId: uploadId,
                    continuation: continuation
                )
            }
        }
    }
    
    private func performBackgroundUpload(
        fileURL: URL,
        appointmentId: String,
        petId: String,
        uploadId: String,
        continuation: CheckedContinuation<AudioUploadResult, Error>
    ) {
        
        do {
            // Step 1: Fast file read and basic validation
            let fileData = try Data(contentsOf: fileURL)
            let fileName = fileURL.lastPathComponent
            
            // Update progress (non-blocking)
            DispatchQueue.main.async {
                self.uploadStatus = .uploading
                self.uploadProgress = 0.3
            }
            
            // Step 2: Create upload request (minimal data)
            let initiateRequest = AudioUploadRequest(
                petId: petId,
                filename: fileName,
                contentType: "audio/m4a",
                estimatedDurationSeconds: self.recordingDuration,
                appointmentId: appointmentId
            )
            
            print("🚀 Background upload request: \(fileName)")
            
            // Step 3: Async API calls (don't block)
            Task {
                do {
                    // Initiate upload
                    let initiateResponse = try await APIManager.shared.initiateAudioUpload(initiateRequest)
                    
                    await MainActor.run {
                        self.uploadProgress = 0.5
                    }
                    
                    // S3 Upload (optimized for speed)
                    try await self.fastS3Upload(
                        fileData: fileData,
                        uploadResponse: initiateResponse
                    )
                    
                    await MainActor.run {
                        self.uploadProgress = 0.8
                    }
                    
                    // Complete upload with minimal metadata
                    let completeRequest = AudioUploadCompleteRequest(
                        fileSizeBytes: fileData.count,
                        durationSeconds: self.recordingDuration,
                        deviceMetadata: [
                            "device_model": UIDevice.current.model,
                            "ios_version": UIDevice.current.systemVersion,
                            "upload_id": uploadId
                        ]
                    )
                    
                    let visitTranscript = try await APIManager.shared.completeAudioUpload(
                        visitId: initiateResponse.visitId,
                        request: completeRequest
                    )
                    
                    // Success!
                    await MainActor.run {
                        self.uploadStatus = .completed
                        self.uploadProgress = 1.0
                    }
                    
                    // Clean up local file
                    try? FileManager.default.removeItem(at: fileURL)
                    
                    let result = AudioUploadResult(
                        visitId: initiateResponse.visitId,
                        audioUrl: visitTranscript.audioTranscriptUrl
                    )
                    
                    continuation.resume(returning: result)
                    print("✅ LIGHTNING upload completed: \(initiateResponse.visitId)")
                    
                } catch {
                    await MainActor.run {
                        self.uploadStatus = .failed
                        self.uploadProgress = 0.0
                    }
                    
                    continuation.resume(throwing: error)
                    print("❌ Upload failed: \(error.localizedDescription)")
                }
            }
            
        } catch {
            DispatchQueue.main.async {
                self.uploadStatus = .failed
                self.uploadProgress = 0.0
            }
            continuation.resume(throwing: error)
        }
    }
    
    // MARK: - Optimized S3 Upload
    private func fastS3Upload(
        fileData: Data,
        uploadResponse: AudioUploadResponse
    ) async throws {
        
        let boundary = UUID().uuidString
        
        var request = URLRequest(url: URL(string: uploadResponse.uploadUrl)!)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 60 // Reduced from 300 seconds
        
        var body = Data()
        
        // Add upload fields (optimized creation)
        for (key, value) in uploadResponse.uploadFields {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }
        
        // Add file data
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        let filename = uploadResponse.uploadFields["key"] ?? "recording.m4a"
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/m4a\r\n\r\n".data(using: .utf8)!)
        body.append(fileData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        
        request.httpBody = body
        
        // Fast upload with optimized session
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 60
        config.timeoutIntervalForResource = 120
        let session = URLSession(configuration: config)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw AudioError.s3UploadFailed
        }
        
        guard httpResponse.statusCode >= 200 && httpResponse.statusCode < 300 else {
            print("❌ S3 upload failed: \(httpResponse.statusCode)")
            if let responseBody = String(data: data, encoding: .utf8) {
                print("❌ Response: \(responseBody)")
            }
            throw AudioError.s3UploadFailed
        }
        
        print("✅ FAST S3 upload completed")
    }
    
    // MARK: - Playback (Same as before, but optimized)
    func playRecording(from url: URL) async throws {
        if url.scheme == "https" || url.scheme == "http" {
            try await downloadAndPlay(from: url)
        } else {
            try await playDirectly(from: url)
        }
    }
    
    private func playDirectly(from url: URL) async throws {
        guard FileManager.default.fileExists(atPath: url.path) else {
            throw AudioError.fileNotFound
        }
        
        audioPlayer = try AVAudioPlayer(contentsOf: url)
        audioPlayer?.delegate = self
        audioPlayer?.prepareToPlay()
        
        if let player = audioPlayer {
            await MainActor.run {
                self.isPlaying = true
            }
            
            if !player.play() {
                throw AudioError.playbackFailed
            }
        }
    }
    
    private func downloadAndPlay(from url: URL) async throws {
        let (data, response) = try await URLSession.shared.data(from: url)
        
        if let httpResponse = response as? HTTPURLResponse {
            guard httpResponse.statusCode == 200 else {
                throw AudioError.playbackFailed
            }
        }
        
        let tempURL = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension("m4a")
        
        try data.write(to: tempURL)
        
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.playback, mode: .default)
        try audioSession.setActive(true)
        
        audioPlayer = try AVAudioPlayer(contentsOf: tempURL)
        audioPlayer?.delegate = self
        audioPlayer?.prepareToPlay()
        
        if let player = audioPlayer {
            await MainActor.run {
                self.isPlaying = true
            }
            
            if !player.play() {
                throw AudioError.playbackFailed
            }
        }
    }
    
    func stopPlayback() {
        audioPlayer?.stop()
        DispatchQueue.main.async {
            self.isPlaying = false
        }
    }
    
    // MARK: - Timer Management
    private func startTimer() {
        recordingTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { _ in
            if let recorder = self.audioRecorder, recorder.isRecording {
                DispatchQueue.main.async {
                    self.recordingDuration = recorder.currentTime
                }
            }
        }
    }
    
    private func stopTimer() {
        recordingTimer?.invalidate()
        recordingTimer = nil
    }
    
    // MARK: - State Reset
    func resetRecordingState() {
        recordingDuration = 0
        isRecording = false
        isPlaying = false
        uploadProgress = 0.0
        uploadStatus = .idle
        stopTimer()
        stopPlayback()
        audioRecorder = nil
        currentRecordingURL = nil
    }
    
    // MARK: - Utility Functions
    func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }
}

// MARK: - AVAudioRecorderDelegate
extension ResponsiveAudioManager: AVAudioRecorderDelegate {
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        DispatchQueue.main.async {
            self.isRecording = false
            self.stopTimer()
        }
    }
    
    func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) {
        DispatchQueue.main.async {
            self.isRecording = false
            self.stopTimer()
        }
        print("❌ Recording error: \(error?.localizedDescription ?? "Unknown")")
    }
}

// MARK: - AVAudioPlayerDelegate
extension ResponsiveAudioManager: AVAudioPlayerDelegate {
    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        DispatchQueue.main.async {
            self.isPlaying = false
        }
    }
}

// MARK: - Helper Extension
extension DateFormatter {
    func apply(_ closure: (DateFormatter) -> Void) -> DateFormatter {
        closure(self)
        return self
    }
}
