//
//  MedicalRecordingManager.swift
//  HelpPetAI
//
//  TL;DR: Secure, medical-grade audio recording persistence and upload manager.
//
//  Features:
//  - Secure storage with iOS complete file protection (HIPAA-friendly)
//  - Metadata + SHA256 integrity hashing to prevent corruption
//  - Persistent upload queue with retry + exponential backoff
//  - BackgroundTasks support for uploads when app is suspended
//  - Robust S3 upload (single + placeholder for multipart)
//  - Upload verification via integrity checks before send
//  - Automatic persistence + reload of pending uploads on app launch
//  - Cleans old completed uploads after configurable retention period
//  - Publishes observable state for UI (`uploadQueue`, `isProcessingQueue`)
//  - Exposes helper APIs to retry failed uploads or query upload status
//
//  Usage: Access via `MedicalRecordingManager.shared` (singleton).
//
//
//  MedicalRecordingManager.swift
//  HelpPetAI
//
//  Created for secure medical recording uploads
//

import Foundation
import BackgroundTasks
import CryptoKit
import UIKit

/// Medical-grade recording manager with corruption prevention
class MedicalRecordingManager: ObservableObject {
    static let shared = MedicalRecordingManager()
    
    @Published var uploadQueue: [PendingUpload] = []
    @Published var isProcessingQueue = false
    
    private let persistentStorageURL: URL
    private let uploadRetryLimit = 5
    private let backgroundTaskIdentifier = "ai.helppet.upload-medical-recording"
    
    private init() {
        // Create secure persistent storage directory
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        persistentStorageURL = documentsPath.appendingPathComponent("MedicalRecordings", isDirectory: true)
        
        createPersistentStorage()
        loadPendingUploads()
        registerBackgroundTask()
    }
    
    // MARK: - Secure Storage Setup
    private func createPersistentStorage() {
        try? FileManager.default.createDirectory(
            at: persistentStorageURL,
            withIntermediateDirectories: true,
            attributes: [.protectionKey: FileProtectionType.complete]
        )
        
        // Create subdirectories
        let subdirs = ["recordings", "metadata", "completed"]
        for subdir in subdirs {
            let url = persistentStorageURL.appendingPathComponent(subdir, isDirectory: true)
            try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        }
    }
    
    // MARK: - Medical Recording Persistence
    func secureRecording(
        audioURL: URL,
        appointmentId: String,
        petId: String,
        visitId: String? = nil
    ) async throws -> String {
        
        // Step 1: Generate unique recording ID
        let recordingId = UUID().uuidString
        
        // Step 2: Create recording metadata
        let metadata = RecordingMetadata(
            recordingId: recordingId,
            appointmentId: appointmentId,
            petId: petId,
            visitId: visitId,
            originalFilename: audioURL.lastPathComponent,
            createdAt: Date(),
            fileSize: try FileManager.default.attributesOfItem(atPath: audioURL.path)[.size] as? Int64 ?? 0
        )
        
        // Step 3: Calculate file integrity hash
        let audioData = try Data(contentsOf: audioURL)
        let hash = SHA256.hash(data: audioData)
        let hashString = hash.compactMap { String(format: "%02x", $0) }.joined()
        
        // Step 4: Save to secure persistent storage
        let secureURL = persistentStorageURL
            .appendingPathComponent("recordings")
            .appendingPathComponent("\(recordingId).m4a")
        
        try audioData.write(to: secureURL, options: .completeFileProtection)
        
        // Step 5: Save metadata with integrity hash
        var finalMetadata = metadata
        finalMetadata.integrityHash = hashString
        try saveMetadata(finalMetadata)
        
        // Step 6: Add to upload queue
        let pendingUpload = PendingUpload(
            recordingId: recordingId,
            metadata: finalMetadata,
            status: .pending,
            retryCount: 0,
            secureFileURL: secureURL
        )
        
        await MainActor.run {
            uploadQueue.append(pendingUpload)
        }
        
        print("🔒 Medical recording secured: \(recordingId)")
        print("🔒 File size: \(audioData.count) bytes, Hash: \(hashString.prefix(8))...")
        
        // Step 7: Start upload process
        Task {
            await processUploadQueue()
        }
        
        return recordingId
    }
    
    // MARK: - Upload Queue Processing
    func processUploadQueue() async {
        guard !isProcessingQueue else { return }
        
        await MainActor.run {
            isProcessingQueue = true
        }
        
        defer {
            Task { @MainActor in
                isProcessingQueue = false
            }
        }
        
        print("📤 Processing upload queue: \(uploadQueue.count) items")
        
        for (index, upload) in uploadQueue.enumerated() {
            guard upload.status == .pending || upload.status == .retrying else { continue }
            
            do {
                try await uploadRecording(upload)
                
                // Mark as completed
                await MainActor.run {
                    uploadQueue[index].status = .completed
                    uploadQueue[index].completedAt = Date()
                }
                
                // Move to completed storage
                try moveToCompleted(upload)
                
            } catch {
                print("❌ Upload failed for \(upload.recordingId): \(error)")
                await handleUploadFailure(upload, error: error, index: index)
            }
        }
        
        // Clean completed uploads from queue
        await MainActor.run {
            uploadQueue.removeAll { $0.status == .completed }
        }
        
        savePendingUploads()
    }
    
    // MARK: - Individual Recording Upload
    private func uploadRecording(_ upload: PendingUpload) async throws {
        print("🔄 Starting upload for medical recording: \(upload.recordingId)")
        
        // Step 1: Verify file integrity before upload
        guard let secureData = try? Data(contentsOf: upload.secureFileURL) else {
            throw MedicalRecordingError.fileCorrupted("Cannot read secure file")
        }
        
        let currentHash = SHA256.hash(data: secureData)
        let currentHashString = currentHash.compactMap { String(format: "%02x", $0) }.joined()
        
        guard currentHashString == upload.metadata.integrityHash else {
            throw MedicalRecordingError.fileCorrupted("Integrity hash mismatch")
        }
        
        print("✅ File integrity verified for \(upload.recordingId)")
        
        // Step 2: Initiate upload with backend
        let initiateRequest = AudioUploadRequest(
            petId: upload.metadata.petId,
            filename: upload.metadata.originalFilename,
            contentType: "audio/m4a",
            estimatedDurationSeconds: nil,
            appointmentId: upload.metadata.appointmentId
        )
        
        let initiateResponse = try await APIManager.shared.initiateAudioUpload(initiateRequest)
        
        // Step 3: Upload to S3 with retry logic
        try await robustS3Upload(
            fileData: secureData,
            uploadResponse: initiateResponse,
            recordingId: upload.recordingId
        )
        
        // Step 4: Complete upload
        let completeRequest = AudioUploadCompleteRequest(
            fileSizeBytes: secureData.count,
            durationSeconds: nil,
            deviceMetadata: [
                "device_model": UIDevice.current.model,
                "ios_version": UIDevice.current.systemVersion,
                "integrity_hash": upload.metadata.integrityHash,
                "secured_at": ISO8601DateFormatter().string(from: upload.metadata.createdAt)
            ]
        )
        
        let _ = try await APIManager.shared.completeAudioUpload(
            visitId: initiateResponse.visitId,
            request: completeRequest
        )
        
        print("✅ Medical recording upload completed: \(upload.recordingId)")
    }
    
    // MARK: - Robust S3 Upload with Chunking
    private func robustS3Upload(
        fileData: Data,
        uploadResponse: AudioUploadResponse,
        recordingId: String
    ) async throws {
        
        let chunkSize = 1024 * 1024 * 5  // 5MB chunks for large files
        
        if fileData.count > chunkSize {
            // Use multipart upload for large files
            try await multipartS3Upload(fileData: fileData, uploadResponse: uploadResponse, recordingId: recordingId)
        } else {
            // Use single upload with retry for small files
            try await singleS3UploadWithRetry(fileData: fileData, uploadResponse: uploadResponse, recordingId: recordingId)
        }
    }
    
    private func singleS3UploadWithRetry(
        fileData: Data,
        uploadResponse: AudioUploadResponse,
        recordingId: String,
        retryCount: Int = 0
    ) async throws {
        
        do {
            try await performS3Upload(fileData: fileData, uploadResponse: uploadResponse)
            print("✅ S3 upload successful for \(recordingId)")
            
        } catch {
            print("⚠️ S3 upload attempt \(retryCount + 1) failed for \(recordingId): \(error)")
            
            if retryCount < 3 {
                // Exponential backoff: 2s, 4s, 8s
                let delay = pow(2.0, Double(retryCount + 1))
                try await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                try await singleS3UploadWithRetry(fileData: fileData, uploadResponse: uploadResponse, recordingId: recordingId, retryCount: retryCount + 1)
            } else {
                throw error
            }
        }
    }
    
    private func multipartS3Upload(
        fileData: Data,
        uploadResponse: AudioUploadResponse,
        recordingId: String
    ) async throws {
        
        print("📤 Starting multipart upload for \(recordingId) (\(fileData.count) bytes)")
        
        // For now, fall back to single upload
        // In production, implement proper S3 multipart upload
        try await singleS3UploadWithRetry(fileData: fileData, uploadResponse: uploadResponse, recordingId: recordingId)
    }
    
    private func performS3Upload(fileData: Data, uploadResponse: AudioUploadResponse) async throws {
        let boundary = UUID().uuidString
        
        var request = URLRequest(url: URL(string: uploadResponse.uploadUrl)!)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 300  // 5 minutes for large uploads
        
        var body = Data()
        
        // Add upload fields
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
        
        // Use URLSession with longer timeout
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 300
        config.timeoutIntervalForResource = 600
        let session = URLSession(configuration: config)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw MedicalRecordingError.uploadFailed("Invalid response")
        }
        
        guard httpResponse.statusCode >= 200 && httpResponse.statusCode < 300 else {
            let responseBody = String(data: data, encoding: .utf8) ?? "No response body"
            throw MedicalRecordingError.uploadFailed("S3 upload failed: \(httpResponse.statusCode) - \(responseBody)")
        }
    }
    
    // MARK: - Upload Failure Handling
    private func handleUploadFailure(_ upload: PendingUpload, error: Error, index: Int) async {
        await MainActor.run {
            uploadQueue[index].retryCount += 1
            uploadQueue[index].lastError = error.localizedDescription
            
            if uploadQueue[index].retryCount < uploadRetryLimit {
                uploadQueue[index].status = .retrying
                uploadQueue[index].nextRetryAt = Date().addingTimeInterval(
                    pow(2.0, Double(uploadQueue[index].retryCount)) * 60  // 2min, 4min, 8min, 16min, 32min
                )
                print("⏰ Scheduling retry for \(upload.recordingId) in \(uploadQueue[index].nextRetryAt?.timeIntervalSinceNow ?? 0) seconds")
            } else {
                uploadQueue[index].status = .failed
                print("💀 Upload permanently failed for \(upload.recordingId) after \(uploadRetryLimit) attempts")
            }
        }
    }
    
    // MARK: - Background Task Support
    private func registerBackgroundTask() {
        BGTaskScheduler.shared.register(forTaskWithIdentifier: backgroundTaskIdentifier, using: nil) { task in
            self.handleBackgroundUpload(task: task as! BGProcessingTask)
        }
    }
    
    private func handleBackgroundUpload(task: BGProcessingTask) {
        task.expirationHandler = {
            task.setTaskCompleted(success: false)
        }
        
        Task {
            await processUploadQueue()
            task.setTaskCompleted(success: true)
        }
    }
    
    func scheduleBackgroundUpload() {
        let request = BGProcessingTaskRequest(identifier: backgroundTaskIdentifier)
        request.requiresNetworkConnectivity = true
        request.requiresExternalPower = false
        request.earliestBeginDate = Date(timeIntervalSinceNow: 30)
        
        try? BGTaskScheduler.shared.submit(request)
    }
    
    // MARK: - Persistence Management
    private func saveMetadata(_ metadata: RecordingMetadata) throws {
        let url = persistentStorageURL
            .appendingPathComponent("metadata")
            .appendingPathComponent("\(metadata.recordingId).json")
        
        let data = try JSONEncoder().encode(metadata)
        try data.write(to: url, options: .completeFileProtection)
    }
    
    private func savePendingUploads() {
        let url = persistentStorageURL.appendingPathComponent("upload_queue.json")
        
        do {
            let data = try JSONEncoder().encode(uploadQueue)
            try data.write(to: url, options: .completeFileProtection)
        } catch {
            print("❌ Failed to save upload queue: \(error)")
        }
    }
    
    private func loadPendingUploads() {
        let url = persistentStorageURL.appendingPathComponent("upload_queue.json")
        
        guard let data = try? Data(contentsOf: url) else { return }
        
        do {
            uploadQueue = try JSONDecoder().decode([PendingUpload].self, from: data)
            print("📂 Loaded \(uploadQueue.count) pending uploads from storage")
            
            // Process any pending uploads
            Task {
                await processUploadQueue()
            }
        } catch {
            print("❌ Failed to load upload queue: \(error)")
        }
    }
    
    private func moveToCompleted(_ upload: PendingUpload) throws {
        let completedDir = persistentStorageURL.appendingPathComponent("completed")
        let newURL = completedDir.appendingPathComponent("\(upload.recordingId).m4a")
        
        try FileManager.default.moveItem(at: upload.secureFileURL, to: newURL)
        print("📁 Moved completed recording to: \(newURL)")
    }
    
    // MARK: - Public Interface
    func retryFailedUploads() async {
        await MainActor.run {
            for i in uploadQueue.indices {
                if uploadQueue[i].status == .failed {
                    uploadQueue[i].status = .retrying
                    uploadQueue[i].retryCount = 0
                    uploadQueue[i].nextRetryAt = Date()
                }
            }
        }
        
        await processUploadQueue()
    }
    
    func getUploadStatus(recordingId: String) -> PendingUpload? {
        return uploadQueue.first { $0.recordingId == recordingId }
    }
    
    func cleanCompletedUploads(olderThan days: Int = 7) {
        let cutoffDate = Date().addingTimeInterval(-Double(days * 24 * 60 * 60))
        let completedDir = persistentStorageURL.appendingPathComponent("completed")
        
        do {
            let files = try FileManager.default.contentsOfDirectory(at: completedDir, includingPropertiesForKeys: [.creationDateKey])
            
            for file in files {
                if let creationDate = try file.resourceValues(forKeys: [.creationDateKey]).creationDate,
                   creationDate < cutoffDate {
                    try FileManager.default.removeItem(at: file)
                    print("🗑️ Cleaned old completed recording: \(file.lastPathComponent)")
                }
            }
        } catch {
            print("⚠️ Failed to clean completed uploads: \(error)")
        }
    }
}

// MARK: - Supporting Models
struct RecordingMetadata: Codable {
    let recordingId: String
    let appointmentId: String
    let petId: String
    let visitId: String?
    let originalFilename: String
    let createdAt: Date
    let fileSize: Int64
    var integrityHash: String = ""
}

struct PendingUpload: Codable {
    let recordingId: String
    let metadata: RecordingMetadata
    var status: UploadStatus
    var retryCount: Int
    var nextRetryAt: Date?
    var completedAt: Date?
    var lastError: String?
    let secureFileURL: URL
    
    enum CodingKeys: String, CodingKey {
        case recordingId, metadata, status, retryCount, nextRetryAt, completedAt, lastError
        case secureFileURLPath = "secureFileURL"
    }
    
    init(recordingId: String, metadata: RecordingMetadata, status: UploadStatus, retryCount: Int, secureFileURL: URL) {
        self.recordingId = recordingId
        self.metadata = metadata
        self.status = status
        self.retryCount = retryCount
        self.secureFileURL = secureFileURL
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        recordingId = try container.decode(String.self, forKey: .recordingId)
        metadata = try container.decode(RecordingMetadata.self, forKey: .metadata)
        status = try container.decode(UploadStatus.self, forKey: .status)
        retryCount = try container.decode(Int.self, forKey: .retryCount)
        nextRetryAt = try container.decodeIfPresent(Date.self, forKey: .nextRetryAt)
        completedAt = try container.decodeIfPresent(Date.self, forKey: .completedAt)
        lastError = try container.decodeIfPresent(String.self, forKey: .lastError)
        
        let path = try container.decode(String.self, forKey: .secureFileURLPath)
        secureFileURL = URL(fileURLWithPath: path)
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(recordingId, forKey: .recordingId)
        try container.encode(metadata, forKey: .metadata)
        try container.encode(status, forKey: .status)
        try container.encode(retryCount, forKey: .retryCount)
        try container.encodeIfPresent(nextRetryAt, forKey: .nextRetryAt)
        try container.encodeIfPresent(completedAt, forKey: .completedAt)
        try container.encodeIfPresent(lastError, forKey: .lastError)
        try container.encode(secureFileURL.path, forKey: .secureFileURLPath)
    }
}

enum UploadStatus: String, Codable {
    case pending = "pending"
    case uploading = "uploading"
    case retrying = "retrying"
    case completed = "completed"
    case failed = "failed"
}

enum MedicalRecordingError: Error, LocalizedError {
    case fileCorrupted(String)
    case uploadFailed(String)
    case integrityCheckFailed
    
    var errorDescription: String? {
        switch self {
        case .fileCorrupted(let message):
            return "Medical recording corrupted: \(message)"
        case .uploadFailed(let message):
            return "Upload failed: \(message)"
        case .integrityCheckFailed:
            return "File integrity check failed"
        }
    }
}
