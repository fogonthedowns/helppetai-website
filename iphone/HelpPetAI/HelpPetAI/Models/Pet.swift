//
//  Pet.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

import Foundation

struct Pet: Codable, Identifiable, Hashable, Equatable {
    let id: String
    let name: String
    let species: String
    let breed: String?
    let color: String?
    let gender: String?
    let weight: Double?
    let dateOfBirth: Date?
    let microchipId: String?
    let spayedNeutered: Bool?
    let allergies: String?
    let medications: String?
    let medicalNotes: String?
    let emergencyContact: String?
    let emergencyPhone: String?
    let ownerId: String
    let isActive: Bool
    let createdAt: Date
    let updatedAt: Date
    let ageYears: Int?
    let displayName: String?
    let owner: PetOwner?
    
    enum CodingKeys: String, CodingKey {
        case id, name, species, breed, color, gender, weight, owner
        case dateOfBirth = "date_of_birth"
        case microchipId = "microchip_id"
        case spayedNeutered = "spayed_neutered"
        case allergies, medications
        case medicalNotes = "medical_notes"
        case emergencyContact = "emergency_contact"
        case emergencyPhone = "emergency_phone"
        case ownerId = "owner_id"
        case isActive = "is_active"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case ageYears = "age_years"
        case displayName = "display_name"
    }
    
    // MARK: - Hashable and Equatable conformance
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
    
    static func == (lhs: Pet, rhs: Pet) -> Bool {
        // Compare all properties that can change to ensure SwiftUI detects updates
        return lhs.id == rhs.id &&
               lhs.name == rhs.name &&
               lhs.species == rhs.species &&
               lhs.breed == rhs.breed &&
               lhs.color == rhs.color &&
               lhs.gender == rhs.gender &&
               lhs.weight == rhs.weight &&
               lhs.dateOfBirth == rhs.dateOfBirth &&
               lhs.microchipId == rhs.microchipId &&
               lhs.spayedNeutered == rhs.spayedNeutered &&
               lhs.allergies == rhs.allergies &&
               lhs.medications == rhs.medications &&
               lhs.medicalNotes == rhs.medicalNotes &&
               lhs.emergencyContact == rhs.emergencyContact &&
               lhs.emergencyPhone == rhs.emergencyPhone &&
               lhs.updatedAt == rhs.updatedAt
    }
}

struct PetSummary: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let species: String
    let breed: String?
}

struct PetOwner: Codable, Identifiable {
    let id: String
    let userId: String?
    let fullName: String
    let email: String
    let phone: String?
    
    enum CodingKeys: String, CodingKey {
        case id, email, phone
        case userId = "user_id"
        case fullName = "full_name"
    }
}

struct PetOwnerResponse: Codable {
    let uuid: String
    let fullName: String
    let email: String
    let phone: String?
    
    enum CodingKeys: String, CodingKey {
        case uuid, email, phone
        case fullName = "full_name"
    }
}

struct PetOwnerDetails: Codable, Identifiable, Hashable {
    let uuid: String
    let userId: String?
    let fullName: String
    let email: String
    let phone: String?
    let secondaryPhone: String?
    let address: String?
    let emergencyContact: String?
    let preferredCommunication: String?
    let notificationsEnabled: Bool
    let createdAt: Date
    let updatedAt: Date
    
    var id: String { uuid }
    
    enum CodingKeys: String, CodingKey {
        case uuid, email, phone, address
        case userId = "user_id"
        case fullName = "full_name"
        case secondaryPhone = "secondary_phone"
        case emergencyContact = "emergency_contact"
        case preferredCommunication = "preferred_communication"
        case notificationsEnabled = "notifications_enabled"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(uuid)
    }
}

struct PetOwnerWithPets: Identifiable, Hashable, Equatable {
    let uuid: String
    let fullName: String
    let email: String
    let phone: String?
    let pets: [Pet]
    
    var id: String { uuid }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(uuid)
    }
    
    static func == (lhs: PetOwnerWithPets, rhs: PetOwnerWithPets) -> Bool {
        lhs.uuid == rhs.uuid
    }
}

struct UpdatePetOwnerRequest: Codable {
    let userId: String?
    let fullName: String
    let email: String
    let phone: String
    let emergencyContact: String
    let secondaryPhone: String
    let address: String
    let preferredCommunication: String
    let notificationsEnabled: Bool
    
    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case fullName = "full_name"
        case email, phone
        case emergencyContact = "emergency_contact"
        case secondaryPhone = "secondary_phone"
        case address
        case preferredCommunication = "preferred_communication"
        case notificationsEnabled = "notifications_enabled"
    }
}

struct UpdatePetRequest: Codable {
    let name: String
    let species: String
    let breed: String?
    let color: String?
    let gender: String?
    let weight: Double?
    let dateOfBirth: Date?
    let microchipId: String?
    let spayedNeutered: Bool?
    let allergies: String?
    let medications: String?
    let medicalNotes: String?
    let emergencyContact: String?
    let emergencyPhone: String?
    
    enum CodingKeys: String, CodingKey {
        case name, species, breed, color, gender, weight
        case dateOfBirth = "date_of_birth"
        case microchipId = "microchip_id"
        case spayedNeutered = "spayed_neutered"
        case allergies, medications
        case medicalNotes = "medical_notes"
        case emergencyContact = "emergency_contact"
        case emergencyPhone = "emergency_phone"
    }
}
