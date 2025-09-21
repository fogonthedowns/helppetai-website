// MARK: - 1. Models/User.swift
import Foundation

struct LoginResponse: Codable {
    let accessToken: String
    let tokenType: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
    }
}

struct User: Codable, Identifiable, Equatable {
    let id: String
    let username: String
    let email: String
    let fullName: String
    let role: UserRole
    let isActive: Bool
    let practiceId: String?
    
    enum CodingKeys: String, CodingKey {
        case id, username, email, role
        case fullName = "full_name"
        case isActive = "is_active"
        case practiceId = "practice_id"
    }
}

enum UserRole: String, Codable {
    case vetStaff = "VET_STAFF"
    case vet = "VET"
    case admin = "ADMIN"
    case petOwner = "PET_OWNER"
}




