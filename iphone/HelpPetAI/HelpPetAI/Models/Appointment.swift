//
//  Appointment.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

// MARK: - 2. Models/Appointment.swift

import Foundation

struct Appointment: Codable, Identifiable, Equatable {
    let id: String
    let practiceId: String
    let petOwnerId: String
    let assignedVetUserId: String?
    let appointmentDate: Date
    let durationMinutes: Int
    let appointmentType: String
    let status: AppointmentStatus
    let title: String
    let description: String?
    let notes: String?
    let pets: [PetSummary]
    let createdAt: Date
    let updatedAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id
        case practiceId = "practice_id"
        case petOwnerId = "pet_owner_id"
        case assignedVetUserId = "assigned_vet_user_id"
        case appointmentDate = "appointment_date"
        case durationMinutes = "duration_minutes"
        case appointmentType = "appointment_type"
        case status, title, description, notes, pets
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

enum AppointmentStatus: String, Codable, CaseIterable {
    case scheduled = "scheduled"
    case confirmed = "confirmed"
    case inProgress = "in_progress"
    case completed = "completed"
    case complete = "complete"  // API sends "complete" instead of "completed"
    case cancelled = "cancelled"
    
    var displayName: String {
        switch self {
        case .scheduled: return "Scheduled"
        case .confirmed: return "Confirmed"
        case .inProgress: return "In Progress"
        case .completed, .complete: return "Completed"
        case .cancelled: return "Cancelled"
        }
    }
    
    var color: String {
        switch self {
        case .scheduled: return "gray"
        case .confirmed: return "gray"
        case .inProgress: return "blue"
        case .completed, .complete: return "green"
        case .cancelled: return "red"
        }
    }
}

struct DashboardResponse: Codable {
    let appointmentsToday: [Appointment]
    let nextAppointment: Appointment?
    let currentAppointment: Appointment?
    let completedCount: Int
    let remainingCount: Int
    
    enum CodingKeys: String, CodingKey {
        case appointmentsToday = "appointments_today"
        case nextAppointment = "next_appointment"
        case currentAppointment = "current_appointment"
        case completedCount = "completed_count"
        case remainingCount = "remaining_count"
    }
}

struct Practice: Codable, Identifiable {
    let id: String
    let name: String
    let address: String?
}

struct CreateAppointmentRequest: Codable {
    let practiceId: String
    let petOwnerId: String
    let assignedVetUserId: String?
    let petIds: [String]
    let appointmentDate: Date
    let durationMinutes: Int
    let appointmentType: String
    let title: String
    let description: String?
    let notes: String?
    
    enum CodingKeys: String, CodingKey {
        case practiceId = "practice_id"
        case petOwnerId = "pet_owner_id"
        case assignedVetUserId = "assigned_vet_user_id"
        case petIds = "pet_ids"
        case appointmentDate = "appointment_date"
        case durationMinutes = "duration_minutes"
        case appointmentType = "appointment_type"
        case title, description, notes
    }
}
