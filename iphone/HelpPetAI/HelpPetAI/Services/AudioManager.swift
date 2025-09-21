//
//  AudioManager.swift
//  HelpPetAI
//
//  TL;DR: Centralized audio recording, playback, and upload manager.
//
//  (cleaned + fixes for main-thread, permissions, and timers)
//

import Foundation
import AVFoundation
import AudioToolbox
import SwiftUI

// MARK: - Notification Extension
extension Notification.Name {
    static let audioPlaybackStopped = Notification.Name("audioPlaybackStopped")
}

@MainActor
final class AudioManager: NSObject, ObservableObject, AVAudioPlayerDelegate, AVAudioRecorderDelegate {
    static let shared = AudioManager()

    // Recording / Uploading state
    @Published var isRecording = false
    @Published var isPlaying = false
    @Published var recordingDuration: TimeInterval = 0
    @Published var hasPermission = false
    @Published var isUploading = false
    @Published var uploadProgress: Double = 0.0

    // Playback state (UI-critical)
    @Published var currentPlaybackTime: TimeInterval = 0
    @Published var totalPlaybackTime: TimeInterval = 0
    @Published var currentlyPlayingVisitId: String?

    private var audioRecorder: AVAudioRecorder?
    private var audioPlayer: AVAudioPlayer?
    private var recordingTimer: Timer?
    private var playbackTimer: Timer?
    private var currentRecordingId: String?

    private override init() {
        super.init()
        checkMicrophonePermission()
    }

    // MARK: - Permission Management

    /// Asks for microphone permission and updates `hasPermission`.
    func requestMicrophonePermission() async -> Bool {
        return await withCheckedContinuation { continuation in
            AVAudioSession.sharedInstance().requestRecordPermission { granted in
                Task { @MainActor in
                    self.hasPermission = granted
                    continuation.resume(returning: granted)
                }
            }
        }
    }

    private func checkMicrophonePermission() {
        // AVAudioSession.recordPermission is the correct API
        switch AVAudioSession.sharedInstance().recordPermission {
        case .granted:
            hasPermission = true
        case .denied, .undetermined:
            hasPermission = false
        @unknown default:
            hasPermission = false
        }
    }

    // MARK: - Recording Functions

    /// Starts recording and returns the local file URL (or throws).
    func startRecording(appointmentId: String, visitId: String? = nil) async throws -> URL? {
        // Instant UI update
        resetRecordingState()
        isRecording = true

        // Check permission quickly
        guard hasPermission else {
            isRecording = false
            throw AudioError.permissionDenied
        }

        // Configure audio session and start recording in a background task
        return try await Task.detached(priority: .userInitiated) {
            try AVAudioSession.sharedInstance().setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker])
            try AVAudioSession.sharedInstance().setActive(true)

            // Create file URL
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyyMMdd_HHmmss"
            let timestamp = formatter.string(from: Date())
            let fileName = "recording_\(timestamp).m4a"
            let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            let audioURL = documentsPath.appendingPathComponent(fileName)

            let settings: [String: Any] = [
                AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
                AVSampleRateKey: 44100,
                AVNumberOfChannelsKey: 1,
                AVEncoderAudioQualityKey: AVAudioQuality.medium.rawValue,
                AVEncoderBitRateKey: 96000
            ]

            let recorder = try AVAudioRecorder(url: audioURL, settings: settings)
            recorder.delegate = self
            recorder.isMeteringEnabled = false
            recorder.prepareToRecord()

            if recorder.record() {
                await MainActor.run {
                    self.audioRecorder = recorder
                    self.recordingDuration = 0
                    self.startRecordingTimer()
                }

                print("✅ INSTANT recording started: \(fileName)")
                return audioURL
            } else {
                await MainActor.run {
                    self.isRecording = false
                }
                throw AudioError.recordingFailed
            }
        }.value
    }

    func stopRecording() async -> URL? {
        guard let recorder = audioRecorder, recorder.isRecording else { return nil }
        let audioURL = recorder.url
        recorder.stop()

        isRecording = false
        stopRecordingTimer()

        try? AVAudioSession.sharedInstance().setActive(false)
        return audioURL
    }

    // MARK: - Upload (unchanged core, but still uses MainActor for published updates)

    func uploadRecording(
        fileURL: URL,
        appointmentId: String,
        petId: String,
        visitId: String? = nil
    ) async throws -> AudioUploadResult {

        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            throw AudioError.fileNotFound
        }

        if isUploading {
            print("⚠️ Upload already in progress, skipping duplicate request")
            throw AudioError.uploadInProgress
        }

        isUploading = true
        uploadProgress = 0.0

        do {
            let fileData = try Data(contentsOf: fileURL)
            let fileName = fileURL.lastPathComponent

            print("🚀 FAST upload starting for: \(fileName)")

            let initiateRequest = AudioUploadRequest(
                petId: petId,
                filename: fileName,
                contentType: "audio/m4a",
                estimatedDurationSeconds: recordingDuration,
                appointmentId: appointmentId
            )

            let initiateResponse = try await APIManager.shared.initiateAudioUpload(initiateRequest)
            currentRecordingId = initiateResponse.visitId

            uploadProgress = 0.2

            try await uploadToS3(fileData: fileData, uploadResponse: initiateResponse)

            uploadProgress = 0.8

            let completeRequest = AudioUploadCompleteRequest(
                fileSizeBytes: fileData.count,
                durationSeconds: recordingDuration,
                deviceMetadata: [
                    "device_model": UIDevice.current.model,
                    "ios_version": UIDevice.current.systemVersion,
                    "app_version": Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "1.0"
                ]
            )

            let visitTranscript = try await APIManager.shared.completeAudioUpload(
                visitId: initiateResponse.visitId,
                request: completeRequest
            )

            uploadProgress = 1.0
            isUploading = false

            try? FileManager.default.removeItem(at: fileURL)

            return AudioUploadResult(
                visitId: initiateResponse.visitId,
                audioUrl: visitTranscript.audioTranscriptUrl
            )
        } catch {
            isUploading = false
            uploadProgress = 0.0
            print("❌ Medical upload failed: \(error)")
            throw error
        }
    }

    private func uploadToS3(fileData: Data, uploadResponse: AudioUploadResponse) async throws {
        let boundary = UUID().uuidString
        guard let uploadURL = URL(string: uploadResponse.uploadUrl) else {
            throw AudioError.s3UploadFailed
        }

        var request = URLRequest(url: uploadURL)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        for (key, value) in uploadResponse.uploadFields {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }

        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        let filename = uploadResponse.uploadFields["key"] ?? "recording.m4a"
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/m4a\r\n\r\n".data(using: .utf8)!)
        body.append(fileData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ S3 Upload: Invalid response")
            throw AudioError.s3UploadFailed
        }

        print("🚀 S3 Response Status: \(httpResponse.statusCode)")
        if let responseString = String(data: data, encoding: .utf8) {
            print("🚀 S3 Response Body: \(responseString)")
        }

        guard httpResponse.statusCode >= 200 && httpResponse.statusCode < 300 else {
            print("❌ S3 Upload failed with status: \(httpResponse.statusCode)")
            throw AudioError.s3UploadFailed
        }

        print("✅ S3 Upload successful!")
    }

    // MARK: - Playback Functions

    func playRecording(from url: URL) async throws {
        print("🎵 Starting playback from URL: \(url)")
        print("🎵 URL scheme: \(url.scheme ?? "none"), path extension: \(url.pathExtension)")

        if url.pathExtension.lowercased() == "webm" {
            print("❌ WebM format not supported by AVAudioPlayer")
            throw AudioError.playbackFailed
        }

        // Stop current player but don't reset currentlyPlayingVisitId
        audioPlayer?.stop()
        stopPlaybackTimer()
        isPlaying = false

        if url.scheme == "https" || url.scheme == "http" {
            print("🎵 Remote URL detected, using download-first approach for reliability")
            try await downloadAndPlay(from: url)
        } else {
            try await playDirectly(from: url)
        }
    }

    private func playDirectly(from url: URL) async throws {
        do {
            print("🎵 Attempting direct playback from local file: \(url)")

            guard FileManager.default.fileExists(atPath: url.path) else {
                print("❌ File does not exist at path: \(url.path)")
                throw AudioError.fileNotFound
            }

            audioPlayer = try AVAudioPlayer(contentsOf: url)
            audioPlayer?.delegate = self
            audioPlayer?.prepareToPlay()

            if let player = audioPlayer {
                isPlaying = true
                totalPlaybackTime = player.duration
                currentPlaybackTime = player.currentTime

                startPlaybackTimer()

                let success = player.play()
                print("🎵 Direct playback started: \(success)")

                if !success { throw AudioError.playbackFailed }
            }
        } catch {
            print("❌ Direct playback failed: \(error)")
            throw AudioError.playbackFailed
        }
    }

    private func downloadAndPlay(from url: URL) async throws {
        do {
            print("🎵 Downloading audio from: \(url)")

            let configuration = URLSessionConfiguration.default
            configuration.timeoutIntervalForRequest = 30.0
            configuration.timeoutIntervalForResource = 60.0
            let session = URLSession(configuration: configuration)

            let (data, response) = try await session.data(from: url)

            if let httpResponse = response as? HTTPURLResponse {
                print("🎵 Download response status: \(httpResponse.statusCode)")
                print("🎵 Content-Type: \(httpResponse.value(forHTTPHeaderField: "Content-Type") ?? "unknown")")
                print("🎵 Content-Length: \(data.count) bytes")

                guard httpResponse.statusCode == 200 else {
                    print("❌ Download failed with status: \(httpResponse.statusCode)")
                    throw AudioError.playbackFailed
                }
            }

            guard data.count > 0 else {
                print("❌ Downloaded file is empty")
                throw AudioError.playbackFailed
            }

            let tempURL = FileManager.default.temporaryDirectory
                .appendingPathComponent(UUID().uuidString)
                .appendingPathExtension("m4a")

            try data.write(to: tempURL)
            print("🎵 Downloaded \(data.count) bytes to: \(tempURL)")

            let audioSession = AVAudioSession.sharedInstance()

            do {
                try audioSession.setCategory(.playback, mode: .default, options: [.defaultToSpeaker, .allowBluetooth])
                try audioSession.setActive(true, options: [.notifyOthersOnDeactivation])
                print("🎵 Audio session configured with .defaultToSpeaker option")
            } catch let audioSessionError {
                print("⚠️ Failed to configure audio session with .defaultToSpeaker, trying basic config: \(audioSessionError)")
                do {
                    try audioSession.setCategory(.playback, mode: .default)
                    try audioSession.setActive(true)
                } catch let basicConfigError {
                    print("❌ Failed to configure basic audio session: \(basicConfigError)")
                }
            }

            audioPlayer = try AVAudioPlayer(contentsOf: tempURL)
            audioPlayer?.delegate = self
            audioPlayer?.prepareToPlay()

            if let player = audioPlayer {
                isPlaying = true
                totalPlaybackTime = player.duration
                currentPlaybackTime = player.currentTime

                startPlaybackTimer()

                player.volume = 1.0
                let success = player.play()
                print("🎵 Downloaded file playback started: \(success)")
                print("🎵 Player duration: \(player.duration) seconds")
                print("🎵 Player current time: \(player.currentTime) seconds")

                if !success { throw AudioError.playbackFailed }

                // Helpful debug after a brief delay
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                    print("🎵 [0.5s later] Player is still playing: \(player.isPlaying)")
                    print("🎵 [0.5s later] Player current time: \(player.currentTime) seconds")
                }
            }
        } catch {
            print("❌ Download and play failed: \(error)")
            if let urlError = error as? URLError {
                print("❌ URL Error code: \(urlError.code.rawValue)")
                print("❌ URL Error description: \(urlError.localizedDescription)")
            }
            throw AudioError.playbackFailed
        }
    }

    func stopPlayback() {
        audioPlayer?.stop()
        stopPlaybackTimer()
        audioPlayer = nil

        // Reset state on main actor
        isPlaying = false
        currentPlaybackTime = 0
        totalPlaybackTime = 0
        currentlyPlayingVisitId = nil

        NotificationCenter.default.post(name: .audioPlaybackStopped, object: nil)
    }

    func pausePlayback() {
        if let player = audioPlayer, player.isPlaying {
            player.pause()
            stopPlaybackTimer()
            isPlaying = false
        }
    }

    func resumePlayback() {
        if let player = audioPlayer, !player.isPlaying {
            player.play()
            startPlaybackTimer()
            isPlaying = true
        }
    }

    func seekTo(time: TimeInterval) {
        if let player = audioPlayer {
            player.currentTime = time
            currentPlaybackTime = time
        }
    }

    func skipForward(seconds: TimeInterval = 15) {
        if let player = audioPlayer {
            let newTime = max(0, min(player.currentTime + seconds, player.duration))
            player.currentTime = newTime
            currentPlaybackTime = newTime
        }
    }

    // MARK: - Play Visit Recording
    func playVisitRecording(visitId: String) async throws {
        do {
            print("🎵 Getting playback URL for visit: \(visitId)")

            currentlyPlayingVisitId = visitId

            let playbackResponse = try await APIManager.shared.getAudioPlaybackUrl(visitId: visitId)

            guard let url = URL(string: playbackResponse.presignedUrl) else {
                print("❌ Invalid playback URL: \(playbackResponse.presignedUrl)")
                throw AudioError.playbackFailed
            }

            print("🎵 Got S3 presigned URL: \(url)")
            try await playRecording(from: url)

        } catch {
            print("❌ Failed to play visit recording \(visitId): \(error)")
            currentlyPlayingVisitId = nil
            
            // Provide more specific error information
            if let apiError = error as? APIError {
                switch apiError {
                case .notFound:
                    print("❌ Audio file not found for visit \(visitId) - may have been deleted or archived")
                    throw AudioError.fileNotFound
                case .unauthorized:
                    print("❌ Unauthorized access to audio file for visit \(visitId)")
                    throw AudioError.permissionDenied
                default:
                    print("❌ API error playing visit \(visitId): \(apiError)")
                    throw AudioError.playbackFailed
                }
            }
            
            throw AudioError.playbackFailed
        }
    }

    // MARK: - Recording Level Debugging (unchanged)
    private func checkRecordingLevels(recorder: AVAudioRecorder, timepoint: String) {
        guard recorder.isRecording else {
            print("🎙️ [\(timepoint)] Recorder is no longer recording")
            return
        }

        recorder.updateMeters()
        let avgPower = recorder.averagePower(forChannel: 0)
        let peakPower = recorder.peakPower(forChannel: 0)

        print("🎙️ [\(timepoint)] Audio levels:")
        print("🎙️ [\(timepoint)] - Average power: \(avgPower) dB")
        print("🎙️ [\(timepoint)] - Peak power: \(peakPower) dB")
        print("🎙️ [\(timepoint)] - Current time: \(recorder.currentTime) seconds")

        if avgPower < -50 {
            print("⚠️ [\(timepoint)] VERY LOW audio levels - microphone might not be working")
        } else if avgPower < -30 {
            print("⚠️ [\(timepoint)] LOW audio levels - check microphone input")
        } else if avgPower < -10 {
            print("✅ [\(timepoint)] GOOD audio levels detected")
        } else {
            print("📢 [\(timepoint)] HIGH audio levels - might be too loud")
        }

        if avgPower <= -160 {
            print("❌ [\(timepoint)] SILENCE DETECTED - No microphone input")
        }
    }

    // MARK: - Timer Management

    private func startRecordingTimer() {
        stopRecordingTimer()
        recordingTimer = Timer(timeInterval: 0.1, repeats: true) { [weak self] _ in
            guard let self = self, let recorder = self.audioRecorder, recorder.isRecording else { return }
            self.recordingDuration = recorder.currentTime
        }
        if let t = recordingTimer { RunLoop.main.add(t, forMode: .common) }
    }

    private func stopRecordingTimer() {
        recordingTimer?.invalidate()
        recordingTimer = nil
    }

    private func startPlaybackTimer() {
        stopPlaybackTimer()
        playbackTimer = Timer(timeInterval: 0.1, repeats: true) { [weak self] _ in
            guard let self = self, let player = self.audioPlayer else { return }
            // Update currentPlaybackTime even if player isn't 'isPlaying' (keeps scrubber accurate)
            self.currentPlaybackTime = player.currentTime
            // Keep isPlaying in sync to publish state (some players may flip isPlaying quickly)
            self.isPlaying = player.isPlaying
        }
        if let t = playbackTimer { RunLoop.main.add(t, forMode: .common) }
    }

    private func stopPlaybackTimer() {
        playbackTimer?.invalidate()
        playbackTimer = nil
    }

    // MARK: - State Reset

    func resetRecordingState() {
        recordingDuration = 0
        isRecording = false
        isPlaying = false
        stopRecordingTimer()
        stopPlaybackTimer()
        audioRecorder = nil
        currentRecordingId = nil
        stopPlayback()
    }

    // MARK: - Utility Functions

    func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }

    func deleteLocalRecording(at url: URL) {
        try? FileManager.default.removeItem(at: url)
    }

    // MARK: - AVAudioRecorderDelegate
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        isRecording = false
        stopRecordingTimer()
    }

    func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) {
        isRecording = false
        stopRecordingTimer()
        print("Recording error: \(error?.localizedDescription ?? "Unknown error")")
    }

    // MARK: - AVAudioPlayerDelegate
    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        stopPlaybackTimer()
        isPlaying = false
        currentPlaybackTime = 0
        totalPlaybackTime = 0
        currentlyPlayingVisitId = nil
        NotificationCenter.default.post(name: .audioPlaybackStopped, object: nil)
        print("🎵 Playback finished successfully: \(flag)")
    }
}
