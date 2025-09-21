//
//  CallAnalysis.swift
//  HelpPetAI
//
//  Created by Assistant on 9/20/25.
//

import Foundation

// MARK: - Call Analysis Models

struct CallListResponse: Codable {
    let practiceId: String
    let calls: [CallSummary]
    let pagination: PaginationInfo
    
    enum CodingKeys: String, CodingKey {
        case practiceId = "practice_id"
        case calls
        case call // Handle single call response
        case pagination
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        
        practiceId = try container.decode(String.self, forKey: .practiceId)
        
        // Try to decode as list first, then as single call
        if let callsList = try? container.decode([CallSummary].self, forKey: .calls) {
            calls = callsList
        } else if let singleCall = try? container.decode(CallDetail.self, forKey: .call) {
            // Convert CallDetail to CallSummary
            let summary = CallSummary(
                callId: singleCall.callId,
                recordingUrl: singleCall.recordingUrl,
                startTimestamp: singleCall.startTimestamp,
                endTimestamp: singleCall.endTimestamp,
                callAnalysis: singleCall.callAnalysis,
                fromNumber: singleCall.fromNumber,
                toNumber: singleCall.toNumber
            )
            calls = [summary]
        } else {
            calls = []
        }
        
        // Provide default pagination if not present
        if let paginationInfo = try? container.decode(PaginationInfo.self, forKey: .pagination) {
            pagination = paginationInfo
        } else {
            // Create default pagination for single call response
            pagination = PaginationInfo(
                limit: 1,
                offset: 0,
                count: calls.count,
                hasMore: false,
                totalCount: calls.count
            )
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(practiceId, forKey: .practiceId)
        try container.encode(calls, forKey: .calls)
        try container.encode(pagination, forKey: .pagination)
    }
}

struct CallDetailResponse: Codable {
    let practiceId: String
    let call: CallDetail
    
    enum CodingKeys: String, CodingKey {
        case practiceId = "practice_id"
        case call
    }
}

struct CallSummary: Codable, Identifiable {
    let callId: String?
    let recordingUrl: String?
    let startTimestamp: String?
    let endTimestamp: String?
    let callAnalysis: CallAnalysisData?
    let fromNumber: String?
    let toNumber: String?
    
    // Computed property for SwiftUI Identifiable
    var id: String {
        return callId ?? UUID().uuidString
    }
    
    // Computed properties for display
    var startDate: Date? {
        guard let startTimestamp = startTimestamp else { return nil }
        return ISO8601DateFormatter().date(from: startTimestamp)
    }
    
    var endDate: Date? {
        guard let endTimestamp = endTimestamp else { return nil }
        return ISO8601DateFormatter().date(from: endTimestamp)
    }
    
    var duration: TimeInterval? {
        guard let start = startDate, let end = endDate else { return nil }
        return end.timeIntervalSince(start)
    }
    
    var formattedDuration: String {
        guard let duration = duration else { return "Unknown" }
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        return "\(minutes):\(String(format: "%02d", seconds))"
    }
    
    enum CodingKeys: String, CodingKey {
        case callId = "call_id"
        case recordingUrl = "recording_url"
        case startTimestamp = "start_timestamp"
        case endTimestamp = "end_timestamp"
        case callAnalysis = "call_analysis"
        case fromNumber = "from_number"
        case toNumber = "to_number"
    }
}

struct CallDetail: Codable, Identifiable {
    let callId: String?
    let recordingUrl: String?
    let startTimestamp: String?
    let endTimestamp: String?
    let callAnalysis: CallAnalysisData?
    let durationMs: Int?
    let agentId: String?
    let fromNumber: String?
    let toNumber: String?
    let callStatus: String?
    let disconnectReason: String?
    
    // Computed property for SwiftUI Identifiable
    var id: String {
        return callId ?? UUID().uuidString
    }
    
    // Computed properties for display
    var startDate: Date? {
        guard let startTimestamp = startTimestamp else { return nil }
        return ISO8601DateFormatter().date(from: startTimestamp)
    }
    
    var endDate: Date? {
        guard let endTimestamp = endTimestamp else { return nil }
        return ISO8601DateFormatter().date(from: endTimestamp)
    }
    
    var formattedDuration: String {
        guard let durationMs = durationMs else { return "Unknown" }
        let totalSeconds = durationMs / 1000
        let minutes = totalSeconds / 60
        let seconds = totalSeconds % 60
        return "\(minutes):\(String(format: "%02d", seconds))"
    }
    
    enum CodingKeys: String, CodingKey {
        case callId = "call_id"
        case recordingUrl = "recording_url"
        case startTimestamp = "start_timestamp"
        case endTimestamp = "end_timestamp"
        case callAnalysis = "call_analysis"
        case durationMs = "duration_ms"
        case agentId = "agent_id"
        case fromNumber = "from_number"
        case toNumber = "to_number"
        case callStatus = "call_status"
        case disconnectReason = "disconnect_reason"
    }
}

struct CallAnalysisData: Codable {
    let callSuccessful: Bool?
    let callSummary: String?
    let userSentiment: String?
    let inVoicemail: Bool?
    let customAnalysisData: [String: CallAnalysisValue]?
    
    // Computed properties for easy access to custom data
    var appointmentType: String? {
        return customAnalysisData?["appointment_type"]?.stringValue
    }
    
    var urgencyLevel: String? {
        return customAnalysisData?["urgency_level"]?.stringValue
    }
    
    var followUpNeeded: Bool? {
        return customAnalysisData?["follow_up_needed"]?.boolValue
    }
    
    var petMentioned: String? {
        return customAnalysisData?["pet_mentioned"]?.stringValue
    }
    
    var symptomsMentioned: [String]? {
        return customAnalysisData?["symptoms_mentioned"]?.arrayValue
    }
    
    var appointmentScheduled: Bool? {
        return customAnalysisData?["appointment_scheduled"]?.boolValue
    }
    
    var appointmentDate: String? {
        return customAnalysisData?["appointment_date"]?.stringValue
    }
    
    enum CodingKeys: String, CodingKey {
        case callSuccessful = "call_successful"
        case callSummary = "call_summary"
        case userSentiment = "user_sentiment"
        case inVoicemail = "in_voicemail"
        case customAnalysisData = "custom_analysis_data"
    }
}

struct PaginationInfo: Codable {
    let limit: Int
    let offset: Int
    let count: Int
    let hasMore: Bool?
    let totalCount: Int?
    
    enum CodingKeys: String, CodingKey {
        case limit
        case offset
        case count
        case hasMore = "has_more"
        case totalCount = "total_count"
    }
}

// Helper for handling dynamic JSON values
enum CallAnalysisValue: Codable {
    case string(String)
    case int(Int)
    case double(Double)
    case bool(Bool)
    case array([String])
    case null
    
    var stringValue: String? {
        switch self {
        case .string(let value): return value
        default: return nil
        }
    }
    
    var intValue: Int? {
        switch self {
        case .int(let value): return value
        default: return nil
        }
    }
    
    var doubleValue: Double? {
        switch self {
        case .double(let value): return value
        default: return nil
        }
    }
    
    var boolValue: Bool? {
        switch self {
        case .bool(let value): return value
        default: return nil
        }
    }
    
    var arrayValue: [String]? {
        switch self {
        case .array(let value): return value
        default: return nil
        }
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        
        if container.decodeNil() {
            self = .null
        } else if let stringValue = try? container.decode(String.self) {
            self = .string(stringValue)
        } else if let intValue = try? container.decode(Int.self) {
            self = .int(intValue)
        } else if let doubleValue = try? container.decode(Double.self) {
            self = .double(doubleValue)
        } else if let boolValue = try? container.decode(Bool.self) {
            self = .bool(boolValue)
        } else if let arrayValue = try? container.decode([String].self) {
            self = .array(arrayValue)
        } else {
            throw DecodingError.typeMismatch(CallAnalysisValue.self, DecodingError.Context(codingPath: decoder.codingPath, debugDescription: "Unsupported type"))
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        
        switch self {
        case .string(let value):
            try container.encode(value)
        case .int(let value):
            try container.encode(value)
        case .double(let value):
            try container.encode(value)
        case .bool(let value):
            try container.encode(value)
        case .array(let value):
            try container.encode(value)
        case .null:
            try container.encodeNil()
        }
    }
}

// MARK: - Extensions for UI

extension CallAnalysisData {
    var sentimentColor: String {
        switch userSentiment?.lowercased() {
        case "positive": return "green"
        case "negative": return "red"
        case "urgent": return "orange"
        case "concerned": return "yellow"
        default: return "gray"
        }
    }
    
    var successIcon: String {
        return callSuccessful == true ? "checkmark.circle.fill" : "xmark.circle.fill"
    }
    
    var successColor: String {
        return callSuccessful == true ? "green" : "red"
    }
}
