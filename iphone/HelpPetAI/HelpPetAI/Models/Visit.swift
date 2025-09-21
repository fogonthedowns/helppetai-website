//
//  Visit.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

import Foundation

// MARK: - Visit Models

struct Visit: Codable, Identifiable {
    let id: String
    let petId: String
    let appointmentId: String?
    let visitDate: Date
    let visitType: String
    let status: VisitStatus
    let chiefComplaint: String?
    let diagnosis: String?
    let treatmentPlan: String?
    let notes: String?
    let followUpRequired: Bool
    let followUpDate: Date?
    let visitTranscripts: [VisitTranscript]?
    let createdBy: String
    let createdAt: Date
    let updatedAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id
        case petId = "pet_id"
        case appointmentId = "appointment_id"
        case visitDate = "visit_date"
        case visitType = "visit_type"
        case status
        case chiefComplaint = "chief_complaint"
        case diagnosis
        case treatmentPlan = "treatment_plan"
        case notes
        case followUpRequired = "follow_up_required"
        case followUpDate = "follow_up_date"
        case visitTranscripts = "visit_transcripts"
        case createdBy = "created_by"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

enum VisitStatus: String, Codable, CaseIterable {
    case scheduled = "scheduled"
    case inProgress = "in_progress"
    case completed = "completed"
    case cancelled = "cancelled"
    
    var displayName: String {
        switch self {
        case .scheduled: return "Scheduled"
        case .inProgress: return "In Progress"
        case .completed: return "Completed"
        case .cancelled: return "Cancelled"
        }
    }
    
    var color: String {
        switch self {
        case .scheduled: return "gray"
        case .inProgress: return "blue"
        case .completed: return "green"
        case .cancelled: return "red"
        }
    }
}

// MARK: - Visit Request/Response Models

struct CreateVisitRequest: Codable {
    let petId: String
    let appointmentId: String?
    let visitType: String
    let chiefComplaint: String?
    let notes: String?
    
    enum CodingKeys: String, CodingKey {
        case petId = "pet_id"
        case appointmentId = "appointment_id"
        case visitType = "visit_type"
        case chiefComplaint = "chief_complaint"
        case notes
    }
}

struct UpdateVisitRequest: Codable {
    let status: VisitStatus?
    let diagnosis: String?
    let treatmentPlan: String?
    let notes: String?
    let followUpRequired: Bool?
    let followUpDate: Date?
    
    enum CodingKeys: String, CodingKey {
        case status
        case diagnosis
        case treatmentPlan = "treatment_plan"
        case notes
        case followUpRequired = "follow_up_required"
        case followUpDate = "follow_up_date"
    }
}

struct VisitsResponse: Codable {
    let visits: [Visit]
    let total: Int
    let hasMore: Bool
    
    enum CodingKeys: String, CodingKey {
        case visits
        case total
        case hasMore = "has_more"
    }
}

// MARK: - Visit Summary for Lists

struct VisitSummary: Codable, Identifiable {
    let id: String
    let petId: String
    let petName: String
    let appointmentId: String?
    let visitDate: Date
    let visitType: String
    let status: VisitStatus
    let recordingsCount: Int
    
    enum CodingKeys: String, CodingKey {
        case id
        case petId = "pet_id"
        case petName = "pet_name"
        case appointmentId = "appointment_id"
        case visitDate = "visit_date"
        case visitType = "visit_type"
        case status
        case recordingsCount = "recordings_count"
    }
}
