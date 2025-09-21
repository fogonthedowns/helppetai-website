//
//  AudioModels.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

import Foundation

// MARK: - Audio Error Types
enum AudioError: Error, LocalizedError {
    case permissionDenied
    case recordingFailed
    case playbackFailed
    case fileNotFound
    case s3UploadFailed
    case uploadInitializationFailed
    case uploadInProgress
    case validationFailed(String)
    case petNotInAppointment
    
    var errorDescription: String? {
        switch self {
        case .permissionDenied:
            return "Microphone permission is required to record audio"
        case .recordingFailed:
            return "Failed to start or complete recording"
        case .playbackFailed:
            return "Failed to play audio file"
        case .fileNotFound:
            return "Audio file not found"
        case .s3UploadFailed:
            return "Failed to upload recording to server"
        case .uploadInitializationFailed:
            return "The recording service is temporarily unavailable. Please try again in a few moments, or contact support if this persists."
        case .uploadInProgress:
            return "Upload already in progress. Please wait."
        case .validationFailed(let message):
            return "Validation error: \(message)"
        case .petNotInAppointment:
            return "The selected pet is not associated with this appointment"
        }
    }
}

// MARK: - Audio Upload Request Models (v2.0)
struct AudioUploadRequest: Codable {
    let petId: String
    let filename: String
    let contentType: String
    let estimatedDurationSeconds: Double?
    let appointmentId: String  // Required - appointment context is mandatory
    
    enum CodingKeys: String, CodingKey {
        case petId = "pet_id"
        case filename
        case contentType = "content_type"
        case estimatedDurationSeconds = "estimated_duration_seconds"
        case appointmentId = "appointment_id"
    }
    
    // MARK: - Validation
    func validate() throws {
        // Ensure both petId and appointmentId are always provided
        if petId.isEmpty {
            throw AudioError.validationFailed("Pet ID is required for all recordings")
        }
        
        if appointmentId.isEmpty {
            throw AudioError.validationFailed("Appointment ID is required for all recordings")
        }
        
        // Validate filename
        if filename.isEmpty {
            throw AudioError.validationFailed("Filename cannot be empty")
        }
        
        // Validate content type
        if contentType != "audio/m4a" {
            throw AudioError.validationFailed("Content type must be audio/m4a")
        }
        
        // Validate duration if provided
        if let duration = estimatedDurationSeconds, duration <= 0 || duration > 3600 {
            throw AudioError.validationFailed("Duration must be between 0 and 3600 seconds")
        }
    }
}

struct AudioUploadResponse: Codable {
    let visitId: String
    let uploadUrl: String
    let uploadFields: [String: String]
    let s3Key: String
    let bucket: String
    let expiresIn: Int
    
    enum CodingKeys: String, CodingKey {
        case visitId = "visit_id"
        case uploadUrl = "upload_url"
        case uploadFields = "upload_fields"
        case s3Key = "s3_key"
        case bucket
        case expiresIn = "expires_in"
    }
}

struct AudioUploadCompleteRequest: Codable {
    let fileSizeBytes: Int?
    let durationSeconds: Double?
    let deviceMetadata: [String: String]?
    
    enum CodingKeys: String, CodingKey {
        case fileSizeBytes = "file_size_bytes"
        case durationSeconds = "duration_seconds"
        case deviceMetadata = "device_metadata"
    }
}

// MARK: - Visit Transcript Model (v2.0)
struct VisitTranscript: Codable, Identifiable {
    let uuid: String  // This is the visit ID
    let petId: String
    let visitDate: Date
    let fullText: String?
    let audioTranscriptUrl: String?
    let state: VisitState
    let metadata: [String: AnyCodable]?  // Contains S3 info and file details
    
    var id: String { uuid }  // For Identifiable protocol
    
    enum CodingKeys: String, CodingKey {
        case uuid
        case petId = "pet_id"
        case visitDate = "visit_date"
        case fullText = "full_text"
        case audioTranscriptUrl = "audio_transcript_url"
        case state
        case metadata
    }
    
    // Custom init to handle Unix timestamp decoding
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        uuid = try container.decode(String.self, forKey: .uuid)
        petId = try container.decode(String.self, forKey: .petId)
        fullText = try container.decodeIfPresent(String.self, forKey: .fullText)
        audioTranscriptUrl = try container.decodeIfPresent(String.self, forKey: .audioTranscriptUrl)
        state = try container.decode(VisitState.self, forKey: .state)
        metadata = try container.decodeIfPresent([String: AnyCodable].self, forKey: .metadata)
        
        // Handle visit_date as Unix timestamp (number)
        let visitDateTimestamp = try container.decode(TimeInterval.self, forKey: .visitDate)
        visitDate = Date(timeIntervalSince1970: visitDateTimestamp)
    }
}

enum VisitState: String, Codable, CaseIterable {
    case new = "new"
    case processing = "processing"
    case processed = "processed"
    case failed = "failed"
    
    var displayName: String {
        switch self {
        case .new: return "New"
        case .processing: return "Processing"
        case .processed: return "Processed"
        case .failed: return "Failed"
        }
    }
    
    var color: String {
        switch self {
        case .new: return "blue"
        case .processing: return "orange"
        case .processed: return "green"
        case .failed: return "red"
        }
    }
}

// MARK: - Audio Playback Response (v2.0)
struct AudioPlaybackResponse: Codable {
    let presignedUrl: String
    let expiresIn: Int
    let visitId: String
    let filename: String?
    
    enum CodingKeys: String, CodingKey {
        case presignedUrl = "presigned_url"
        case expiresIn = "expires_in"
        case visitId = "visit_id"
        case filename
    }
}

// MARK: - Audio Upload Result (v2.0)
struct AudioUploadResult {
    let visitId: String
    let audioUrl: String?
}

// MARK: - Visit Transcript List Item (for pet transcript list)
struct VisitTranscriptListItem: Codable, Identifiable {
    let uuid: String
    let visitDate: Int  // Unix timestamp
    let state: VisitState
    let hasAudio: Bool
    let summary: String?
    let createdAt: String
    let createdBy: String
    let chiefComplaint: String?
    
    var id: String { uuid }  // For Identifiable protocol
    
    enum CodingKeys: String, CodingKey {
        case uuid
        case visitDate = "visit_date"
        case state
        case hasAudio = "has_audio"
        case summary
        case createdAt = "created_at"
        case createdBy = "created_by"
        case chiefComplaint = "chief_complaint"
    }
    
    // Computed property to convert Unix timestamp to Date
    var visitDateAsDate: Date {
        return Date(timeIntervalSince1970: TimeInterval(visitDate))
    }
}

// MARK: - Visit Transcript Detail Response (for individual transcript)
struct VisitTranscriptDetailResponse: Codable, Identifiable {
    let uuid: String
    let petId: String
    let visitDate: Int  // Unix timestamp
    let fullText: String
    let audioTranscriptUrl: String?
    let metadata: [String: AnyCodable]
    let summary: String?
    let state: VisitState
    let createdAt: String
    let updatedAt: String
    let createdBy: String?
    let chiefComplaint: String?
    let hasAudio: Bool?
    
    var id: String { uuid }  // For Identifiable protocol
    
    enum CodingKeys: String, CodingKey {
        case uuid
        case petId = "pet_id"
        case visitDate = "visit_date"
        case fullText = "full_text"
        case audioTranscriptUrl = "audio_transcript_url"
        case metadata
        case summary
        case state
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case createdBy = "created_by"
        case chiefComplaint = "chief_complaint"
        case hasAudio = "has_audio"
    }
    
    // Computed property to convert Unix timestamp to Date
    var visitDateAsDate: Date {
        return Date(timeIntervalSince1970: TimeInterval(visitDate))
    }
    
    // Computed property to get filtered metadata (excluding specified fields)
    var filteredMetadata: [String: AnyCodable] {
        let excludedKeys = [
            "appointment_id", "content_type", "device_metadata", "duration_seconds", 
            "estimated_duration", "extraction_cost", "extraction_date", "extraction_info", 
            "extraction_model", "file_size_bytes", "filename", "metadata_last_updated", 
            "s3_bucket", "s3_key", "transcript_length", "transcription_completed_at", 
            "transcription_source", "transcription_job_name", "upload_completed_at", 
            "upload_initiated_at", "uploaded_by", "transcript_full_data"
        ]
        
        return metadata.filter { key, _ in
            !excludedKeys.contains(key)
        }
    }
}

// MARK: - Visit Transcript Response Model (for new endpoint)
struct VisitTranscriptResponse: Codable, Identifiable {
    let uuid: String
    let petId: String
    let visitDate: Int  // Unix timestamp
    let fullText: String
    let audioTranscriptUrl: String?
    let metadata: [String: AnyCodable]
    let summary: String?
    let state: VisitState
    let createdAt: String
    let updatedAt: String
    let createdBy: String?
    
    var id: String { uuid }  // For Identifiable protocol
    
    enum CodingKeys: String, CodingKey {
        case uuid
        case petId = "pet_id"
        case visitDate = "visit_date"
        case fullText = "full_text"
        case audioTranscriptUrl = "audio_transcript_url"
        case metadata
        case summary
        case state
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case createdBy = "created_by"
    }
    
    // Computed property to convert Unix timestamp to Date
    var visitDateAsDate: Date {
        return Date(timeIntervalSince1970: TimeInterval(visitDate))
    }
}

// MARK: - Helper for JSON metadata
struct AnyCodable: Codable {
    let value: Any
    
    init<T>(_ value: T) {
        self.value = value
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        
        // Handle null values first
        if container.decodeNil() {
            value = NSNull()
        } else if let intValue = try? container.decode(Int.self) {
            value = intValue
        } else if let doubleValue = try? container.decode(Double.self) {
            value = doubleValue
        } else if let stringValue = try? container.decode(String.self) {
            value = stringValue
        } else if let boolValue = try? container.decode(Bool.self) {
            value = boolValue
        } else if let arrayValue = try? container.decode([AnyCodable].self) {
            value = arrayValue.map { $0.value }
        } else if let dictionaryValue = try? container.decode([String: AnyCodable].self) {
            value = dictionaryValue.mapValues { $0.value }
        } else {
            throw DecodingError.typeMismatch(AnyCodable.self, DecodingError.Context(codingPath: decoder.codingPath, debugDescription: "Unsupported type"))
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        
        if value is NSNull {
            try container.encodeNil()
        } else if let intValue = value as? Int {
            try container.encode(intValue)
        } else if let doubleValue = value as? Double {
            try container.encode(doubleValue)
        } else if let stringValue = value as? String {
            try container.encode(stringValue)
        } else if let boolValue = value as? Bool {
            try container.encode(boolValue)
        } else if let arrayValue = value as? [Any] {
            try container.encode(arrayValue.map { AnyCodable($0) })
        } else if let dictionaryValue = value as? [String: Any] {
            try container.encode(dictionaryValue.mapValues { AnyCodable($0) })
        } else {
            throw EncodingError.invalidValue(value, EncodingError.Context(codingPath: encoder.codingPath, debugDescription: "Unsupported type"))
        }
    }
}
