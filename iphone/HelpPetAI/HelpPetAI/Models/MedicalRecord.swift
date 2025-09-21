//
//  MedicalRecord.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

// MARK: - 4. Models/MedicalRecord.swift
import Foundation

struct MedicalRecord: Codable, Identifiable {
    let id: String
    let petId: String
    let recordType: String
    let title: String
    let description: String?
    let medicalData: MedicalData?
    let visitDate: Date
    let veterinarianName: String?
    let clinicName: String?
    let diagnosis: String?
    let treatment: String?
    let medications: String?
    let followUpRequired: Bool
    let followUpDate: Date?
    let weight: Double?
    let temperature: Double?
    let cost: Double?
    let version: Int
    let isCurrent: Bool
    let createdByUserId: String
    let createdAt: Date
    let updatedAt: Date
    let isFollowUpDue: Bool
    let daysSinceVisit: Int
    
    enum CodingKeys: String, CodingKey {
        case id, title, description, diagnosis, treatment, medications, weight, temperature, cost, version
        case petId = "pet_id"
        case recordType = "record_type"
        case medicalData = "medical_data"
        case visitDate = "visit_date"
        case veterinarianName = "veterinarian_name"
        case clinicName = "clinic_name"
        case followUpRequired = "follow_up_required"
        case followUpDate = "follow_up_date"
        case isCurrent = "is_current"
        case createdByUserId = "created_by_user_id"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case isFollowUpDue = "is_follow_up_due"
        case daysSinceVisit = "days_since_visit"
    }
}

struct MedicalData: Codable {
    let heartRate: String?
    let respiratoryRate: String?
    let bloodPressure: String?
    let bodyConditionScore: String?
    let dentalCondition: String?
    let skinCondition: String?
    let eyeCondition: String?
    let earCondition: String?
    
    enum CodingKeys: String, CodingKey {
        case heartRate = "heart_rate"
        case respiratoryRate = "respiratory_rate"
        case bloodPressure = "blood_pressure"
        case bodyConditionScore = "body_condition_score"
        case dentalCondition = "dental_condition"
        case skinCondition = "skin_condition"
        case eyeCondition = "eye_condition"
        case earCondition = "ear_condition"
    }
}

struct MedicalRecordsResponse: Codable {
    let records: [MedicalRecord]
    let total: Int
    let currentRecordsCount: Int
    let historicalRecordsCount: Int
    
    enum CodingKeys: String, CodingKey {
        case records, total
        case currentRecordsCount = "current_records_count"
        case historicalRecordsCount = "historical_records_count"
    }
}

struct CreateMedicalRecordRequest: Codable {
    let recordType: String
    let title: String
    let description: String?
    let medicalData: MedicalData?
    let visitDate: Date
    let veterinarianName: String?
    let clinicName: String?
    let diagnosis: String?
    let treatment: String?
    let medications: String?
    let followUpRequired: Bool
    let followUpDate: Date?
    let weight: Double?
    let temperature: Double?
    let cost: Double?
    let petId: String
    
    enum CodingKeys: String, CodingKey {
        case title, description, diagnosis, treatment, medications, weight, temperature, cost
        case recordType = "record_type"
        case medicalData = "medical_data"
        case visitDate = "visit_date"
        case veterinarianName = "veterinarian_name"
        case clinicName = "clinic_name"
        case followUpRequired = "follow_up_required"
        case followUpDate = "follow_up_date"
        case petId = "pet_id"
    }
}

struct UpdateMedicalRecordRequest: Codable {
    let recordType: String
    let title: String
    let description: String
    let medicalData: MedicalData
    let visitDate: Date
    let veterinarianName: String
    let clinicName: String
    let diagnosis: String
    let treatment: String
    let medications: String
    let followUpRequired: Bool
    let followUpDate: Date?
    let weight: Double?
    let temperature: Double?
    let cost: Double?
    
    enum CodingKeys: String, CodingKey {
        case title, description, diagnosis, treatment, medications, weight, temperature, cost
        case recordType = "record_type"
        case medicalData = "medical_data"
        case visitDate = "visit_date"
        case veterinarianName = "veterinarian_name"
        case clinicName = "clinic_name"
        case followUpRequired = "follow_up_required"
        case followUpDate = "follow_up_date"
    }
}
