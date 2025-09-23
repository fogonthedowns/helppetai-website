//
//  VetAvailability.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/12/25.
//

import Foundation

// MARK: - Vet Availability Models

enum AvailabilityType: String, Codable, CaseIterable {
    case available = "AVAILABLE"
    case unavailable = "UNAVAILABLE"
    case emergencyOnly = "EMERGENCY_ONLY"
    
    var displayName: String {
        switch self {
        case .available: return "Available"
        case .unavailable: return "Unavailable"
        case .emergencyOnly: return "Emergency Only"
        }
    }
    
    var color: Color {
        switch self {
        case .available: return Color.availabilityGreen
        case .unavailable: return Color.availabilityRed
        case .emergencyOnly: return Color.availabilityOrange
        }
    }
    
    var systemIcon: String {
        switch self {
        case .available: return "checkmark.circle.fill"
        case .unavailable: return "xmark.circle.fill"
        case .emergencyOnly: return "exclamationmark.triangle.fill"
        }
    }
}

struct VetAvailability: Codable, Identifiable, Equatable {
    let id: String
    let vetUserId: String
    let practiceId: String
    let date: Date
    let startTime: Date
    let endTime: Date
    let availabilityType: AvailabilityType
    let createdAt: Date
    let updatedAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id
        case vetUserId = "vet_user_id"
        case practiceId = "practice_id"
        case date
        case startTime = "start_time"
        case endTime = "end_time"
        case availabilityType = "availability_type"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        
        id = try container.decode(String.self, forKey: .id)
        vetUserId = try container.decode(String.self, forKey: .vetUserId)
        practiceId = try container.decode(String.self, forKey: .practiceId)
        availabilityType = try container.decode(AvailabilityType.self, forKey: .availabilityType)
        
        // Decode date string
        let dateString = try container.decode(String.self, forKey: .date)
        let startTimeString = try container.decode(String.self, forKey: .startTime)
        let endTimeString = try container.decode(String.self, forKey: .endTime)
        
        // Parse date (API sends UTC storage date, but we need to derive the original local date)
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        dateFormatter.timeZone = TimeZone(abbreviation: "UTC")  // Parse as UTC since that's how it's stored
        guard let parsedDate = dateFormatter.date(from: dateString) else {
            throw DecodingError.dataCorruptedError(forKey: .date, in: container, debugDescription: "Cannot decode date string \(dateString)")
        }
        // Note: parsedDate is the UTC storage date, we'll derive the local date after time conversion
        
        // Parse time strings (API sends in UTC, need to convert to local)
        let timeFormatter = DateFormatter()
        timeFormatter.dateFormat = "HH:mm:ss"
        timeFormatter.timeZone = TimeZone(abbreviation: "UTC")
        
        guard let startTimeComponents = timeFormatter.date(from: startTimeString) else {
            throw DecodingError.dataCorruptedError(forKey: .startTime, in: container, debugDescription: "Cannot decode start time string \(startTimeString)")
        }
        
        guard let endTimeComponents = timeFormatter.date(from: endTimeString) else {
            throw DecodingError.dataCorruptedError(forKey: .endTime, in: container, debugDescription: "Cannot decode end time string \(endTimeString)")
        }
        
        // Combine date with UTC time components and convert to local timezone
        let calendar = Calendar.current
        var utcCalendar = Calendar(identifier: .gregorian)
        utcCalendar.timeZone = TimeZone(abbreviation: "UTC")!
        
        let startTimeCalendarComponents = utcCalendar.dateComponents([.hour, .minute, .second], from: startTimeComponents)
        let endTimeCalendarComponents = utcCalendar.dateComponents([.hour, .minute, .second], from: endTimeComponents)
        
        // Create UTC datetime by combining date with UTC time components
        var utcDateComponents = utcCalendar.dateComponents([.year, .month, .day], from: parsedDate)
        utcDateComponents.hour = startTimeCalendarComponents.hour
        utcDateComponents.minute = startTimeCalendarComponents.minute
        utcDateComponents.second = startTimeCalendarComponents.second
        utcDateComponents.timeZone = TimeZone(abbreviation: "UTC")
        
        guard let utcStartTime = utcCalendar.date(from: utcDateComponents) else {
            throw DecodingError.dataCorruptedError(forKey: .startTime, in: container, debugDescription: "Cannot create UTC start time")
        }
        
        // CRITICAL FIX: Handle cross-day UTC times correctly
        // If end_time < start_time, it means the end time is on the next UTC day
        // Example: start=00:00, end=01:00 on same date = midnight to 1am same day ✅
        // Example: start=23:00, end=07:00 on same date = 11pm to 7am NEXT day ✅
        
        var endUtcDateComponents = utcDateComponents
        endUtcDateComponents.hour = endTimeCalendarComponents.hour
        endUtcDateComponents.minute = endTimeCalendarComponents.minute
        endUtcDateComponents.second = endTimeCalendarComponents.second
        
        // If end time is earlier in the day than start time, it's the next day
        if let endHour = endTimeCalendarComponents.hour,
           let startHour = startTimeCalendarComponents.hour,
           endHour < startHour {
            // End time is next day
            let nextDay = utcCalendar.date(byAdding: .day, value: 1, to: parsedDate) ?? parsedDate
            endUtcDateComponents = utcCalendar.dateComponents([.year, .month, .day], from: nextDay)
            endUtcDateComponents.hour = endTimeCalendarComponents.hour
            endUtcDateComponents.minute = endTimeCalendarComponents.minute
            endUtcDateComponents.second = endTimeCalendarComponents.second
            endUtcDateComponents.timeZone = TimeZone(abbreviation: "UTC")
        }
        
        guard let utcEndTime = utcCalendar.date(from: endUtcDateComponents) else {
            throw DecodingError.dataCorruptedError(forKey: .endTime, in: container, debugDescription: "Cannot create UTC end time")
        }
        
        // Convert UTC times to local timezone
        startTime = utcStartTime
        endTime = utcEndTime
        
        // CRITICAL FIX: Set the date to the LOCAL date (derived from converted start time)
        // This ensures calendar filtering works correctly
        let localCalendar = Calendar.current
        date = localCalendar.startOfDay(for: startTime)
        
        // Debug logging for timezone conversion
        let debugFormatter = DateFormatter()
        debugFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        debugFormatter.timeZone = TimeZone.current
        print("🔍 VetAvailability Decoding:")
        print("🔍 UTC Storage Date: \(dateString)")
        print("🔍 UTC Start: \(startTimeString)")
        print("🔍 UTC End: \(endTimeString)")
        print("🔍 Local Start: \(debugFormatter.string(from: startTime))")
        print("🔍 Local End: \(debugFormatter.string(from: endTime))")
        print("🔍 Derived Local Date: \(debugFormatter.string(from: date))")
        print("🔍 Same Day Check: Start=\(localCalendar.isDate(startTime, inSameDayAs: date)), End=\(localCalendar.isDate(endTime, inSameDayAs: date))")
        print("🔍 ---")
        
        // Decode created_at and updated_at using the existing APIManager date decoder logic
        let createdAtString = try container.decode(String.self, forKey: .createdAt)
        let updatedAtString = try container.decode(String.self, forKey: .updatedAt)
        
        let isoFormatter = DateFormatter()
        isoFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'"
        isoFormatter.timeZone = TimeZone(abbreviation: "UTC")
        
        // Try different ISO formats
        if let parsedCreatedAt = isoFormatter.date(from: createdAtString) {
            createdAt = parsedCreatedAt
        } else {
            isoFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss'Z'"
            if let parsedCreatedAt = isoFormatter.date(from: createdAtString) {
                createdAt = parsedCreatedAt
            } else {
                throw DecodingError.dataCorruptedError(forKey: .createdAt, in: container, debugDescription: "Cannot decode created_at string \(createdAtString)")
            }
        }
        
        if let parsedUpdatedAt = isoFormatter.date(from: updatedAtString) {
            updatedAt = parsedUpdatedAt
        } else {
            isoFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss'Z'"
            if let parsedUpdatedAt = isoFormatter.date(from: updatedAtString) {
                updatedAt = parsedUpdatedAt
            } else {
                throw DecodingError.dataCorruptedError(forKey: .updatedAt, in: container, debugDescription: "Cannot decode updated_at string \(updatedAtString)")
            }
        }
    }
    
    // Standard initializer for creating VetAvailability objects in code
    init(id: String, vetUserId: String, practiceId: String, date: Date, startTime: Date, endTime: Date, availabilityType: AvailabilityType, createdAt: Date, updatedAt: Date) {
        self.id = id
        self.vetUserId = vetUserId
        self.practiceId = practiceId
        self.date = date
        self.startTime = startTime
        self.endTime = endTime
        self.availabilityType = availabilityType
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
    
    // Custom encoder for API requests
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        
        try container.encode(id, forKey: .id)
        try container.encode(vetUserId, forKey: .vetUserId)
        try container.encode(practiceId, forKey: .practiceId)
        try container.encode(availabilityType, forKey: .availabilityType)
        
        // Encode date as string
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        dateFormatter.timeZone = TimeZone.current
        try container.encode(dateFormatter.string(from: date), forKey: .date)
        
        // Encode times as UTC strings (convert local to UTC)
        let timeFormatter = DateFormatter()
        timeFormatter.dateFormat = "HH:mm:ss"
        timeFormatter.timeZone = TimeZone(abbreviation: "UTC")
        try container.encode(timeFormatter.string(from: startTime), forKey: .startTime)
        try container.encode(timeFormatter.string(from: endTime), forKey: .endTime)
        
        // Encode timestamps as ISO strings
        let isoFormatter = DateFormatter()
        isoFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'"
        isoFormatter.timeZone = TimeZone(abbreviation: "UTC")
        try container.encode(isoFormatter.string(from: createdAt), forKey: .createdAt)
        try container.encode(isoFormatter.string(from: updatedAt), forKey: .updatedAt)
    }
}

struct CreateVetAvailabilityRequest: Codable {
    let vetUserId: String
    let practiceId: String
    let date: String
    let startTime: String
    let endTime: String
    let availabilityType: AvailabilityType
    let timezone: String
    
    enum CodingKeys: String, CodingKey {
        case vetUserId = "vet_user_id"
        case practiceId = "practice_id"
        case date
        case startTime = "start_time"
        case endTime = "end_time"
        case availabilityType = "availability_type"
        case timezone
    }
}

struct UpdateVetAvailabilityRequest: Codable {
    let startTime: String
    let endTime: String
    let availabilityType: AvailabilityType
    let notes: String?
    let isActive: Bool
    
    enum CodingKeys: String, CodingKey {
        case startTime = "start_time"
        case endTime = "end_time"
        case availabilityType = "availability_type"
        case notes
        case isActive = "is_active"
    }
}

// MARK: - SwiftUI Color Extension
import SwiftUI

extension Color {
    static let availabilityGreen = Color.green.opacity(0.7)
    static let availabilityRed = Color.red.opacity(0.7)
    static let availabilityOrange = Color.orange.opacity(0.7)
}
