//
//  VetAvailability.swift
//  HelpPetAI
//
//  CLEAN Unix Timestamp Implementation
//  Eliminates complex timezone conversion logic
//

import Foundation
import SwiftUI

// MARK: - Clean Unix Timestamp Vet Availability Models

enum AvailabilityType: String, Codable, CaseIterable {
    case available = "AVAILABLE"
    case surgeryBlock = "SURGERY_BLOCK"
    case unavailable = "UNAVAILABLE"
    case emergencyOnly = "EMERGENCY_ONLY"
    
    var displayName: String {
        switch self {
        case .available: return "Available"
        case .surgeryBlock: return "Surgery Block"
        case .unavailable: return "Unavailable"
        case .emergencyOnly: return "Emergency Only"
        }
    }
    
    var color: Color {
        switch self {
        case .available: return .green
        case .surgeryBlock: return .blue
        case .unavailable: return .red
        case .emergencyOnly: return .orange
        }
    }
    
    var systemIcon: String {
        switch self {
        case .available: return "checkmark.circle.fill"
        case .surgeryBlock: return "scissors"
        case .unavailable: return "xmark.circle.fill"
        case .emergencyOnly: return "exclamationmark.triangle.fill"
        }
    }
}

struct VetAvailability: Codable, Identifiable, Equatable {
    let id: String
    let vetUserId: String
    let practiceId: String
    let startAt: Date        // 🔑 CLEAN: Direct UTC timestamp
    let endAt: Date          // 🔑 CLEAN: Direct UTC timestamp
    let availabilityType: AvailabilityType
    let notes: String?
    let isActive: Bool
    let createdAt: Date
    let updatedAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id
        case vetUserId = "vet_user_id"
        case practiceId = "practice_id"
        case startAt = "start_at"
        case endAt = "end_at"
        case availabilityType = "availability_type"
        case notes
        case isActive = "is_active"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
    
    // 🔥 ELIMINATED: 150+ lines of complex timezone conversion logic
    // Unix timestamps decode directly from API - no conversion needed!
    
    // Equatable implementation
    static func == (lhs: VetAvailability, rhs: VetAvailability) -> Bool {
        return lhs.id == rhs.id
    }
    
    // MARK: - Computed Properties for Local Display
    
    /// Get the local date this availability represents
    var localDate: Date {
        Calendar.current.startOfDay(for: startAt)
    }
    
    /// Get local start time for display
    var localStartTime: Date {
        startAt  // SwiftUI automatically converts UTC to local for display
    }
    
    /// Get local end time for display
    var localEndTime: Date {
        endAt  // SwiftUI automatically converts UTC to local for display
    }
    
    /// Get time range string for display
    var timeRangeString: String {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return "\(formatter.string(from: localStartTime)) - \(formatter.string(from: localEndTime))"
    }
    
    /// Get duration in minutes
    var durationMinutes: Int {
        Int(endAt.timeIntervalSince(startAt) / 60)
    }
    
    /// Check if availability is on a specific local date
    func isOn(localDate: Date) -> Bool {
        Calendar.current.isDate(startAt, inSameDayAs: localDate)
    }
    
    /// Check if availability overlaps with a time range
    func overlaps(with startTime: Date, endTime: Date) -> Bool {
        return !(endTime <= startAt || startTime >= endAt)
    }
    
    // MARK: - Creation Helpers
    
    /// Create availability from local time components
    static func create(
        vetUserId: String,
        practiceId: String,
        localDate: Date,
        startTime: Date,
        endTime: Date,
        availabilityType: AvailabilityType = .available,
        notes: String? = nil
    ) -> VetAvailabilityCreateRequest {
        // Convert local times to UTC for API
        let calendar = Calendar.current
        let startComponents = calendar.dateComponents([.hour, .minute], from: startTime)
        let endComponents = calendar.dateComponents([.hour, .minute], from: endTime)
        
        let localStartDateTime = calendar.date(bySettingHour: startComponents.hour ?? 0,
                                             minute: startComponents.minute ?? 0,
                                             second: 0,
                                             of: localDate) ?? localDate
        
        let localEndDateTime = calendar.date(bySettingHour: endComponents.hour ?? 0,
                                           minute: endComponents.minute ?? 0,
                                           second: 0,
                                           of: localDate) ?? localDate
        
        return VetAvailabilityCreateRequest(
            vetUserId: vetUserId,
            practiceId: practiceId,
            startAt: localStartDateTime,
            endAt: localEndDateTime,
            availabilityType: availabilityType,
            notes: notes
        )
    }
}

// MARK: - API Request Models

struct VetAvailabilityCreateRequest: Codable {
    let vetUserId: String
    let practiceId: String
    let startAt: Date
    let endAt: Date
    let availabilityType: AvailabilityType
    let notes: String?
    
    enum CodingKeys: String, CodingKey {
        case vetUserId = "vet_user_id"
        case practiceId = "practice_id"
        case startAt = "start_at"
        case endAt = "end_at"
        case availabilityType = "availability_type"
        case notes
    }
}

struct VetAvailabilityUpdateRequest: Codable {
    let startAt: Date?
    let endAt: Date?
    let availabilityType: AvailabilityType?
    let notes: String?
    let isActive: Bool?
    
    enum CodingKeys: String, CodingKey {
        case startAt = "start_at"
        case endAt = "end_at"
        case availabilityType = "availability_type"
        case notes
        case isActive = "is_active"
    }
}

// MARK: - Response Models

struct VetAvailabilityListResponse: Codable {
    let availabilities: [VetAvailability]
    let totalCount: Int
    let page: Int
    let pageSize: Int
    
    enum CodingKeys: String, CodingKey {
        case availabilities = "data"
        case totalCount = "total_count"
        case page
        case pageSize = "page_size"
    }
}

struct VetAvailabilitySlotsResponse: Codable {
    let vetUserId: String
    let date: Date
    let practiceId: String
    let slots: [TimeSlot]
    let totalSlots: Int
    let availableSlots: Int
    
    enum CodingKeys: String, CodingKey {
        case vetUserId = "vet_user_id"
        case date
        case practiceId = "practice_id"
        case slots
        case totalSlots = "total_slots"
        case availableSlots = "available_slots"
    }
}

struct TimeSlot: Codable, Identifiable {
    let id = UUID()
    let startTime: Date
    let endTime: Date
    let available: Bool
    let availabilityType: AvailabilityType
    let conflictingAppointment: String?
    let notes: String?
    
    enum CodingKeys: String, CodingKey {
        case startTime = "start_time"
        case endTime = "end_time"
        case available
        case availabilityType = "availability_type"
        case conflictingAppointment = "conflicting_appointment"
        case notes
    }
    
    /// Get time range string for display
    var timeRangeString: String {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return "\(formatter.string(from: startTime)) - \(formatter.string(from: endTime))"
    }
}

// MARK: - Extensions for Calendar Integration

extension VetAvailability {
    /// Convert to calendar event for local display
    var calendarTitle: String {
        switch availabilityType {
        case .available:
            return "Available"
        case .surgeryBlock:
            return "Surgery Block"
        case .unavailable:
            return "Unavailable"
        case .emergencyOnly:
            return "Emergency Only"
        }
    }
    
    /// Get background color for calendar display
    var calendarColor: Color {
        availabilityType.color.opacity(0.3)
    }
    
    /// Get text color for calendar display
    var textColor: Color {
        availabilityType.color
    }
}
