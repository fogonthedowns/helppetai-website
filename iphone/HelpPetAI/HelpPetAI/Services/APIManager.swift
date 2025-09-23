//
//  APIManager.swift
//  HelpPetAI
//
//  TL;DR: Centralized REST API client for all network operations.
//
//  Features:
//  - Handles authentication (login, logout, token management)
//  - Attaches Bearer tokens + device info headers to all requests
//  - Provides strongly typed API calls for:
//      * User management
//      * Dashboard data
//      * Appointments & status updates
//      * Pets & medical records
//      * Visits (create, update, transcripts)
//      * Audio upload & playback
//  - Consistent JSON decoding with flexible date parsing
//  - Error handling with `APIError` (invalid URL, decoding, server, etc.)
//  - Auto-logout on 401 Unauthorized
//  - `ObservableObject` with `@Published currentUser` for SwiftUI
//  - Unified logging of requests and responses for debugging
//
//  Usage: Access via `APIManager.shared` (singleton).
//
//
//  APIManager.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

import Foundation

class APIManager: ObservableObject {
    static let shared = APIManager()
    
    private let baseURL = "https://api.helppet.ai"
    private let session = URLSession.shared
    private let decoder: JSONDecoder
    
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    
    private init() {
        decoder = JSONDecoder()
        
        // Configure flexible date decoding to handle various API date formats
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateString = try container.decode(String.self)
            
            // Try different date formats
            let formatters = [
                // ISO8601 with Z
                { () -> DateFormatter in
                    let formatter = DateFormatter()
                    formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss'Z'"
                    formatter.timeZone = TimeZone(abbreviation: "UTC")
                    return formatter
                }(),
                // ISO8601 with milliseconds
                { () -> DateFormatter in
                    let formatter = DateFormatter()
                    formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'"
                    formatter.timeZone = TimeZone(abbreviation: "UTC")
                    return formatter
                }(),
                // ISO8601 with microseconds and timezone offset
                { () -> DateFormatter in
                    let formatter = DateFormatter()
                    formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSXXXXX"
                    return formatter
                }(),
                // Standard ISO8601
                { () -> DateFormatter in
                    let formatter = DateFormatter()
                    formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ssZ"
                    return formatter
                }(),
                // Date-only format (for birth dates)
                { () -> DateFormatter in
                    let formatter = DateFormatter()
                    formatter.dateFormat = "yyyy-MM-dd"
                    formatter.timeZone = TimeZone(abbreviation: "UTC")
                    return formatter
                }()
            ]
            
            for formatter in formatters {
                if let date = formatter.date(from: dateString) {
                    return date
                }
            }
            
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode date string \(dateString)")
        }
        
        // Check if we have a stored token
        if KeychainManager.shared.getAccessToken() != nil {
            isAuthenticated = true
        }
    }
    
    private var authHeaders: [String: String] {
        guard let token = KeychainManager.shared.getAccessToken() else { return [:] }
        return [
            "Authorization": "Bearer \(token)",
            "Content-Type": "application/json"
        ]
    }
    
    // MARK: - Retry Logic
    private func performRequestWithRetry<T>(
        maxRetries: Int = 3,
        operation: @escaping () async throws -> T
    ) async throws -> T {
        var lastError: Error?
        
        for attempt in 0..<maxRetries {
            do {
                return try await operation()
            } catch let error as APIError {
                lastError = error
                
                // Don't retry 4xx errors (except 401 which is handled separately)
                if case .serverError(let code) = error, code >= 400 && code < 500 {
                    throw error
                }
                
                // Don't retry on last attempt
                if attempt == maxRetries - 1 {
                    break
                }
                
                // Exponential backoff: 1s, 2s, 4s
                let delay = pow(2.0, Double(attempt))
                try await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                
            } catch {
                lastError = error
                throw error // Don't retry non-API errors
            }
        }
        
        throw lastError ?? APIError.networkError
    }
    
    // MARK: - Authentication
    func login(username: String, password: String) async throws -> LoginResponse {
        let url = URL(string: "\(baseURL)/api/v1/auth/token")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        
        let body = "username=\(username)&password=\(password)"
        request.httpBody = body.data(using: .utf8)
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        if httpResponse.statusCode == 401 {
            throw APIError.unauthorized
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        // Debug: Print the raw response
        if let responseString = String(data: data, encoding: .utf8) {
            print("Login API Response: \(responseString)")
        }
        
        do {
            let loginResponse = try decoder.decode(LoginResponse.self, from: data)
            
            // Store token securely
            KeychainManager.shared.saveAccessToken(loginResponse.accessToken)
            
            await MainActor.run {
                self.isAuthenticated = true
            }
            
            return loginResponse
        } catch {
            print("Decoding error: \(error)")
            if let decodingError = error as? DecodingError {
                print("Detailed decoding error: \(decodingError)")
            }
            throw APIError.decodingError
        }
    }
    

    func getCurrentUser() async throws -> User {
        let url = URL(string: "\(baseURL)/api/v1/auth/me")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        if httpResponse.statusCode == 401 {
            // Token is invalid/expired - trigger logout
            await MainActor.run {
                self.logout()
            }
            throw APIError.unauthorized
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        // Debug: Print the raw response to see what we're getting
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 getCurrentUser API Response: \(responseString)")
        }
        
        do {
            let user = try decoder.decode(User.self, from: data)
            
            await MainActor.run {
                self.currentUser = user
            }
            
            return user
        } catch {
            print("❌ Failed to decode user: \(error)")
            if let decodingError = error as? DecodingError {
                print("❌ Detailed decoding error: \(decodingError)")
            }
            
            // If we can't decode the user, the token is likely invalid
            await MainActor.run {
                self.logout()
            }
            
            throw APIError.decodingError
        }
    }
    
    func logout() {
        KeychainManager.shared.deleteAccessToken()
        
        DispatchQueue.main.async {
            self.isAuthenticated = false
            self.currentUser = nil
        }
    }
    
    // MARK: - Dashboard
    func getTodaySchedule(vetId: String, date: String? = nil) async throws -> DashboardResponse {
        var urlString = "\(baseURL)/api/v1/dashboard/vet/\(vetId)/today"
        
        // Use provided date or today's date
        let actualDate = date ?? {
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd"
            formatter.timeZone = TimeZone.current
            return formatter.string(from: Date())
        }()
        
        urlString += "?date=\(actualDate)"
        
        let url = URL(string: urlString)!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        print("Dashboard API Request URL: \(url)")
        print("Dashboard API Headers: \(authHeaders)")
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        print("Dashboard API Response Status: \(httpResponse.statusCode)")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("Dashboard API Response: \(responseString)")
        }
        
        guard httpResponse.statusCode == 200 else {
            if httpResponse.statusCode == 401 {
                // Token expired - trigger logout
                await MainActor.run {
                    self.logout()
                }
                throw APIError.unauthorized
            }
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(DashboardResponse.self, from: data)
    }
    
    // MARK: - Appointments
    func updateAppointmentStatus(appointmentId: String, status: AppointmentStatus) async throws {
        let url = URL(string: "\(baseURL)/api/v1/appointments/\(appointmentId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let body = ["status": status.rawValue]
        request.httpBody = try JSONEncoder().encode(body)
        
        let (_, _) = try await session.data(for: request)
    }
    
    func updateAppointmentDateTime(appointmentId: String, newDate: Date) async throws -> Appointment {
        let url = URL(string: "\(baseURL)/api/v1/appointments/\(appointmentId)")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "PUT"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .custom { date, encoder in
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss'Z'"
            formatter.timeZone = TimeZone(abbreviation: "UTC")
            let dateString = formatter.string(from: date)
            print("🔍 Encoding updated appointment date: \(date) (local) as \(dateString) (UTC)")
            var container = encoder.singleValueContainer()
            try container.encode(dateString)
        }
        
        let body = ["appointment_date": newDate]
        urlRequest.httpBody = try encoder.encode(body)
        
        print("🔍 UPDATE APPOINTMENT DATE REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(urlRequest.httpMethod ?? "nil")")
        print("🔍 Headers: \(urlRequest.allHTTPHeaderFields ?? [:])")
        
        if let requestBody = urlRequest.httpBody,
           let requestString = String(data: requestBody, encoding: .utf8) {
            print("🔍 Request Body: \(requestString)")
        }
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ UPDATE APPOINTMENT: Invalid response type")
            throw APIError.invalidResponse
        }
        
        print("🔍 UPDATE APPOINTMENT RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
        }
        
        guard httpResponse.statusCode == 200 else {
            if httpResponse.statusCode == 401 {
                await MainActor.run {
                    self.logout()
                }
                throw APIError.unauthorized
            }
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(Appointment.self, from: data)
    }
    
    func updateAppointment(appointmentId: String, request: UpdateAppointmentRequest) async throws -> Appointment {
        let url = URL(string: "\(baseURL)/api/v1/appointments/\(appointmentId)")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "PUT"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .custom { date, encoder in
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss'Z'"
            formatter.timeZone = TimeZone(abbreviation: "UTC")
            let dateString = formatter.string(from: date)
            print("🔍 Encoding appointment date: \(date) (local) as \(dateString) (UTC)")
            var container = encoder.singleValueContainer()
            try container.encode(dateString)
        }
        
        urlRequest.httpBody = try encoder.encode(request)
        
        print("🔍 UPDATE APPOINTMENT REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(urlRequest.httpMethod ?? "nil")")
        print("🔍 Headers: \(urlRequest.allHTTPHeaderFields ?? [:])")
        
        if let requestBody = urlRequest.httpBody,
           let requestString = String(data: requestBody, encoding: .utf8) {
            print("🔍 Request Body: \(requestString)")
        }
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ UPDATE APPOINTMENT: Invalid response type")
            throw APIError.invalidResponse
        }
        
        print("🔍 UPDATE APPOINTMENT RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
        }
        
        guard httpResponse.statusCode == 200 else {
            if httpResponse.statusCode == 401 {
                await MainActor.run {
                    self.logout()
                }
                throw APIError.unauthorized
            }
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(Appointment.self, from: data)
    }
    
    func getAppointmentDetails(appointmentId: String) async throws -> Appointment {
        let url = URL(string: "\(baseURL)/api/v1/appointments/\(appointmentId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        if httpResponse.statusCode == 401 {
            throw APIError.unauthorized
        }
        
        if httpResponse.statusCode == 404 {
            throw APIError.notFound
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(Appointment.self, from: data)
    }
    
    // MARK: - Pet Owners
    func getPetOwners() async throws -> [PetOwnerResponse] {
        let url = URL(string: "\(baseURL)/api/v1/pet_owners/")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.from(statusCode: httpResponse.statusCode)
        }
        
        return try decoder.decode([PetOwnerResponse].self, from: data)
    }
    
    func getPetOwnersDetailed() async throws -> [PetOwnerDetails] {
        let url = URL(string: "\(baseURL)/api/v1/pet_owners/")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.from(statusCode: httpResponse.statusCode)
        }
        
        return try decoder.decode([PetOwnerDetails].self, from: data)
    }
    
    func createPetOwner(_ request: CreatePetOwnerRequest) async throws -> PetOwnerDetails {
        let url = URL(string: "\(baseURL)/api/v1/pet_owners/")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        urlRequest.httpBody = try encoder.encode(request)
        
        print("🔍 CREATE PET OWNER REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(urlRequest.httpMethod ?? "nil")")
        print("🔍 Headers: \(urlRequest.allHTTPHeaderFields ?? [:])")
        print("🔍 Content-Length: \(urlRequest.httpBody?.count ?? 0) bytes")
        
        // Check if we have auth token
        if let token = KeychainManager.shared.getAccessToken() {
            print("🔍 Auth Token (first 20 chars): \(String(token.prefix(20)))...")
        } else {
            print("❌ NO AUTH TOKEN FOUND!")
        }
        
        if let requestBody = urlRequest.httpBody,
           let requestString = String(data: requestBody, encoding: .utf8) {
            print("🔍 Request Body: \(requestString)")
            
            // Parse and validate JSON structure
            do {
                if let json = try JSONSerialization.jsonObject(with: requestBody) as? [String: Any] {
                    print("🔍 Parsed JSON Keys: \(Array(json.keys).sorted())")
                    print("🔍 full_name: \(json["full_name"] ?? "nil")")
                    print("🔍 email: \(json["email"] ?? "nil")")
                }
            } catch {
                print("🔍 JSON parsing error: \(error)")
            }
        }
        
        print("🔍 REQUEST TIMESTAMP: \(ISO8601DateFormatter().string(from: Date()))")
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ CREATE PET OWNER: Invalid response type")
            throw APIError.invalidResponse
        }
        
        print("🔍 CREATE PET OWNER RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        print("🔍 Response Headers: \(httpResponse.allHeaderFields)")
        print("🔍 Response Content-Length: \(data.count) bytes")
        print("🔍 RESPONSE TIMESTAMP: \(ISO8601DateFormatter().string(from: Date()))")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
            
            // Try to parse error response
            if httpResponse.statusCode >= 400 {
                do {
                    if let errorJson = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        print("🔍 Error JSON Keys: \(Array(errorJson.keys).sorted())")
                        print("🔍 Error Detail: \(errorJson["detail"] ?? "No detail provided")")
                        if let errors = errorJson["errors"] as? [[String: Any]] {
                            print("🔍 Validation Errors: \(errors)")
                        }
                    }
                } catch {
                    print("🔍 Error response is not valid JSON: \(error)")
                }
            }
        } else {
            print("🔍 Response Body: Unable to decode as UTF-8, \(data.count) bytes")
        }
        
        guard httpResponse.statusCode == 201 || httpResponse.statusCode == 200 else {
            print("❌ CREATE PET OWNER FAILED: Status \(httpResponse.statusCode)")
            throw APIError.from(statusCode: httpResponse.statusCode)
        }
        
        return try decoder.decode(PetOwnerDetails.self, from: data)
    }
    
    func updatePetOwner(petOwnerId: String, request: UpdatePetOwnerRequest) async throws -> PetOwnerDetails {
        let url = URL(string: "\(baseURL)/api/v1/pet_owners/\(petOwnerId)")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "PUT"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        urlRequest.httpBody = try encoder.encode(request)
        
        print("🔍 UPDATE PET OWNER REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(urlRequest.httpMethod ?? "nil")")
        print("🔍 Headers: \(urlRequest.allHTTPHeaderFields ?? [:])")
        print("🔍 Content-Length: \(urlRequest.httpBody?.count ?? 0) bytes")
        
        if let requestBody = urlRequest.httpBody,
           let requestString = String(data: requestBody, encoding: .utf8) {
            print("🔍 Request Body: \(requestString)")
        }
        
        print("🔍 REQUEST TIMESTAMP: \(ISO8601DateFormatter().string(from: Date()))")
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ UPDATE PET OWNER: Invalid response type")
            throw APIError.invalidResponse
        }
        
        print("🔍 UPDATE PET OWNER RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        print("🔍 Response Headers: \(httpResponse.allHeaderFields)")
        print("🔍 Response Content-Length: \(data.count) bytes")
        print("🔍 RESPONSE TIMESTAMP: \(ISO8601DateFormatter().string(from: Date()))")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
            
            // Try to parse error response
            if httpResponse.statusCode >= 400 {
                do {
                    if let errorJson = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        print("🔍 Error JSON Keys: \(Array(errorJson.keys).sorted())")
                        print("🔍 Error Detail: \(errorJson["detail"] ?? "No detail provided")")
                        if let errors = errorJson["errors"] as? [[String: Any]] {
                            print("🔍 Validation Errors: \(errors)")
                        }
                    }
                } catch {
                    print("🔍 Error response is not valid JSON: \(error)")
                }
            }
        } else {
            print("🔍 Response Body: Unable to decode as UTF-8, \(data.count) bytes")
        }
        
        guard httpResponse.statusCode == 200 else {
            print("❌ UPDATE PET OWNER FAILED: Status \(httpResponse.statusCode)")
            throw APIError.from(statusCode: httpResponse.statusCode)
        }
        
        return try decoder.decode(PetOwnerDetails.self, from: data)
    }
    
    func getPetsByOwner(ownerId: String) async throws -> [Pet] {
        let url = URL(string: "\(baseURL)/api/v1/pets/owner/\(ownerId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.from(statusCode: httpResponse.statusCode)
        }
        
        return try decoder.decode([Pet].self, from: data)
    }
    
    // MARK: - Practices
    func getPractices() async throws -> [Practice] {
        let url = URL(string: "\(baseURL)/api/v1/practices/")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.from(statusCode: httpResponse.statusCode)
        }
        
        return try decoder.decode([Practice].self, from: data)
    }
    
    // MARK: - Appointments
    func createAppointment(_ request: CreateAppointmentRequest) async throws -> Appointment {
        let url = URL(string: "\(baseURL)/api/v1/appointments")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .custom { date, encoder in
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss'Z'"
            formatter.timeZone = TimeZone(abbreviation: "UTC")
            let dateString = formatter.string(from: date)
            print("🔍 Encoding appointment date: \(date) (local) as \(dateString) (UTC)")
            var container = encoder.singleValueContainer()
            try container.encode(dateString)
        }
        urlRequest.httpBody = try encoder.encode(request)
        
        // 🔍 DETAILED REQUEST LOGGING
        print("🔍 CREATE APPOINTMENT REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(urlRequest.httpMethod ?? "nil")")
        print("🔍 Headers: \(urlRequest.allHTTPHeaderFields ?? [:])")
        
        if let requestBody = urlRequest.httpBody,
           let requestString = String(data: requestBody, encoding: .utf8) {
            print("🔍 Request Body: \(requestString)")
        }
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ CREATE APPOINTMENT: Invalid response type")
            throw APIError.invalidResponse
        }
        
        // 🔍 DETAILED RESPONSE LOGGING
        print("🔍 CREATE APPOINTMENT RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        print("🔍 Response Headers: \(httpResponse.allHeaderFields)")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
        }
        
        guard httpResponse.statusCode == 201 || httpResponse.statusCode == 200 else {
            print("❌ CREATE APPOINTMENT FAILED: Status \(httpResponse.statusCode)")
            throw APIError.from(statusCode: httpResponse.statusCode)
        }
        
        return try decoder.decode(Appointment.self, from: data)
    }

    // MARK: - Pets
    func getPetDetails(petId: String) async throws -> Pet {
        let url = URL(string: "\(baseURL)/api/v1/pets/\(petId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let (data, response) = try await session.data(for: request)
        
        // Debug: Print the raw response to see the actual structure
        if let responseString = String(data: data, encoding: .utf8) {
            print("Pet API Response: \(responseString)")
        }
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.from(statusCode: httpResponse.statusCode)
        }
        
        return try decoder.decode(Pet.self, from: data)
    }
    
    func createPet(_ request: CreatePetRequest) async throws -> Pet {
        let url = URL(string: "\(baseURL)/api/v1/pets/")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .custom { date, encoder in
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd"
            formatter.timeZone = TimeZone(abbreviation: "UTC")
            let dateString = formatter.string(from: date)
            var container = encoder.singleValueContainer()
            try container.encode(dateString)
        }
        urlRequest.httpBody = try encoder.encode(request)
        
        print("🔍 CREATE PET REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(urlRequest.httpMethod ?? "nil")")
        print("🔍 Headers: \(urlRequest.allHTTPHeaderFields ?? [:])")
        print("🔍 Content-Length: \(urlRequest.httpBody?.count ?? 0) bytes")
        
        // Check if we have auth token
        if let token = KeychainManager.shared.getAccessToken() {
            print("🔍 Auth Token (first 20 chars): \(String(token.prefix(20)))...")
        } else {
            print("❌ NO AUTH TOKEN FOUND!")
        }
        
        if let requestBody = urlRequest.httpBody,
           let requestString = String(data: requestBody, encoding: .utf8) {
            print("🔍 Request Body: \(requestString)")
            
            // Parse and validate JSON structure
            do {
                if let json = try JSONSerialization.jsonObject(with: requestBody) as? [String: Any] {
                    print("🔍 Parsed JSON Keys: \(Array(json.keys).sorted())")
                    print("🔍 owner_id: \(json["owner_id"] ?? "nil")")
                    print("🔍 name: \(json["name"] ?? "nil")")
                }
            } catch {
                print("🔍 JSON parsing error: \(error)")
            }
        }
        
        print("🔍 REQUEST TIMESTAMP: \(ISO8601DateFormatter().string(from: Date()))")
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ CREATE PET: Invalid response type")
            throw APIError.invalidResponse
        }
        
        print("🔍 CREATE PET RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        print("🔍 Response Headers: \(httpResponse.allHeaderFields)")
        print("🔍 Response Content-Length: \(data.count) bytes")
        print("🔍 RESPONSE TIMESTAMP: \(ISO8601DateFormatter().string(from: Date()))")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
            
            // Try to parse error response
            if httpResponse.statusCode >= 400 {
                do {
                    if let errorJson = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        print("🔍 Error JSON Keys: \(Array(errorJson.keys).sorted())")
                        print("🔍 Error Detail: \(errorJson["detail"] ?? "No detail provided")")
                        if let errors = errorJson["errors"] as? [[String: Any]] {
                            print("🔍 Validation Errors: \(errors)")
                        }
                    }
                } catch {
                    print("🔍 Error response is not valid JSON: \(error)")
                }
            }
        } else {
            print("🔍 Response Body: Unable to decode as UTF-8, \(data.count) bytes")
        }
        
        guard httpResponse.statusCode == 201 || httpResponse.statusCode == 200 else {
            print("❌ CREATE PET FAILED: Status \(httpResponse.statusCode)")
            throw APIError.from(statusCode: httpResponse.statusCode)
        }
        
        return try decoder.decode(Pet.self, from: data)
    }
    
    func updatePet(petId: String, request: UpdatePetRequest) async throws -> Pet {
        let url = URL(string: "\(baseURL)/api/v1/pets/\(petId)")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "PUT"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .custom { date, encoder in
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd"
            formatter.timeZone = TimeZone(abbreviation: "UTC")
            let dateString = formatter.string(from: date)
            var container = encoder.singleValueContainer()
            try container.encode(dateString)
        }
        urlRequest.httpBody = try encoder.encode(request)
        
        print("🔍 UPDATE PET REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(urlRequest.httpMethod ?? "nil")")
        print("🔍 Headers: \(urlRequest.allHTTPHeaderFields ?? [:])")
        print("🔍 Content-Length: \(urlRequest.httpBody?.count ?? 0) bytes")
        
        if let requestBody = urlRequest.httpBody,
           let requestString = String(data: requestBody, encoding: .utf8) {
            print("🔍 Request Body: \(requestString)")
        }
        
        print("🔍 REQUEST TIMESTAMP: \(ISO8601DateFormatter().string(from: Date()))")
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ UPDATE PET: Invalid response type")
            throw APIError.invalidResponse
        }
        
        print("🔍 UPDATE PET RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        print("🔍 Response Headers: \(httpResponse.allHeaderFields)")
        print("🔍 Response Content-Length: \(data.count) bytes")
        print("🔍 RESPONSE TIMESTAMP: \(ISO8601DateFormatter().string(from: Date()))")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
            
            // Try to parse error response
            if httpResponse.statusCode >= 400 {
                do {
                    if let errorJson = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        print("🔍 Error JSON Keys: \(Array(errorJson.keys).sorted())")
                        print("🔍 Error Detail: \(errorJson["detail"] ?? "No detail provided")")
                        if let errors = errorJson["errors"] as? [[String: Any]] {
                            print("🔍 Validation Errors: \(errors)")
                        }
                    }
                } catch {
                    print("🔍 Error response is not valid JSON: \(error)")
                }
            }
        } else {
            print("🔍 Response Body: Unable to decode as UTF-8, \(data.count) bytes")
        }
        
        guard httpResponse.statusCode == 200 else {
            print("❌ UPDATE PET FAILED: Status \(httpResponse.statusCode)")
            throw APIError.from(statusCode: httpResponse.statusCode)
        }
        
        return try decoder.decode(Pet.self, from: data)
    }
    
    // MARK: - Medical Records
    func getMedicalRecords(petId: String) async throws -> MedicalRecordsResponse {
        let url = URL(string: "\(baseURL)/api/v1/medical-records/pet/\(petId)?include_historical=true")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let (data, _) = try await session.data(for: request)
        return try decoder.decode(MedicalRecordsResponse.self, from: data)
    }
    
    func getCurrentMedicalRecords(petId: String) async throws -> MedicalRecordsResponse {
        let url = URL(string: "\(baseURL)/api/v1/medical-records/pet/\(petId)?latest_only=true")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let (data, _) = try await session.data(for: request)
        return try decoder.decode(MedicalRecordsResponse.self, from: data)
    }
    
    func createMedicalRecord(_ request: CreateMedicalRecordRequest) async throws -> MedicalRecord {
        let url = URL(string: "\(baseURL)/api/v1/medical-records/")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .custom { date, encoder in
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"
            formatter.timeZone = TimeZone(abbreviation: "UTC")
            let dateString = formatter.string(from: date)
            var container = encoder.singleValueContainer()
            try container.encode(dateString)
        }
        urlRequest.httpBody = try encoder.encode(request)
        
        print("🔍 CREATE MEDICAL RECORD REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(urlRequest.httpMethod ?? "nil")")
        print("🔍 Headers: \(urlRequest.allHTTPHeaderFields ?? [:])")
        print("🔍 Content-Length: \(urlRequest.httpBody?.count ?? 0) bytes")
        
        if let requestBody = urlRequest.httpBody,
           let requestString = String(data: requestBody, encoding: .utf8) {
            print("🔍 Request Body: \(requestString)")
        }
        
        print("🔍 REQUEST TIMESTAMP: \(ISO8601DateFormatter().string(from: Date()))")
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ CREATE MEDICAL RECORD: Invalid response type")
            throw APIError.invalidResponse
        }
        
        print("🔍 CREATE MEDICAL RECORD RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        print("🔍 Response Headers: \(httpResponse.allHeaderFields)")
        print("🔍 Response Content-Length: \(data.count) bytes")
        print("🔍 RESPONSE TIMESTAMP: \(ISO8601DateFormatter().string(from: Date()))")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
            
            // Try to parse error response
            if httpResponse.statusCode >= 400 {
                do {
                    if let errorJson = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        print("🔍 Error JSON Keys: \(Array(errorJson.keys).sorted())")
                        print("🔍 Error Detail: \(errorJson["detail"] ?? "No detail provided")")
                        if let errors = errorJson["errors"] as? [[String: Any]] {
                            print("🔍 Validation Errors: \(errors)")
                        }
                    }
                } catch {
                    print("🔍 Error response is not valid JSON: \(error)")
                }
            }
        } else {
            print("🔍 Response Body: Unable to decode as UTF-8, \(data.count) bytes")
        }
        
        guard httpResponse.statusCode == 201 || httpResponse.statusCode == 200 else {
            print("❌ CREATE MEDICAL RECORD FAILED: Status \(httpResponse.statusCode)")
            throw APIError.from(statusCode: httpResponse.statusCode)
        }
        
        return try decoder.decode(MedicalRecord.self, from: data)
    }
    
    func updateMedicalRecord(recordId: String, request: UpdateMedicalRecordRequest) async throws -> MedicalRecord {
        let url = URL(string: "\(baseURL)/api/v1/medical-records/\(recordId)")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "PUT"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .custom { date, encoder in
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"
            formatter.timeZone = TimeZone(abbreviation: "UTC")
            let dateString = formatter.string(from: date)
            var container = encoder.singleValueContainer()
            try container.encode(dateString)
        }
        urlRequest.httpBody = try encoder.encode(request)
        
        print("🔄 UPDATE MEDICAL RECORD REQUEST:")
        print("🔄 URL: \(url.absoluteString)")
        print("🔄 Method: \(urlRequest.httpMethod ?? "nil")")
        print("🔄 Headers: \(urlRequest.allHTTPHeaderFields ?? [:])")
        
        if let requestBody = urlRequest.httpBody,
           let requestString = String(data: requestBody, encoding: .utf8) {
            print("🔄 Request Body: \(requestString)")
        }
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ UPDATE MEDICAL RECORD: Invalid response type")
            throw APIError.invalidResponse
        }
        
        print("🔄 UPDATE MEDICAL RECORD RESPONSE:")
        print("🔄 Status Code: \(httpResponse.statusCode)")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔄 Response Body: \(responseString)")
        }
        
        guard httpResponse.statusCode == 200 else {
            print("❌ UPDATE MEDICAL RECORD FAILED: Status \(httpResponse.statusCode)")
            throw APIError.from(statusCode: httpResponse.statusCode)
        }
        
        return try decoder.decode(MedicalRecord.self, from: data)
    }
    
    // MARK: - Visits
    func getVisits(
        petId: String? = nil,
        appointmentId: String? = nil,
        limit: Int = 50,
        offset: Int = 0
    ) async throws -> VisitsResponse {
        var components = URLComponents(string: "\(baseURL)/api/v1/visits/")!
        var queryItems: [URLQueryItem] = []
        
        if let petId = petId {
            queryItems.append(URLQueryItem(name: "pet_id", value: petId))
        }
        if let appointmentId = appointmentId {
            queryItems.append(URLQueryItem(name: "appointment_id", value: appointmentId))
        }
        queryItems.append(URLQueryItem(name: "limit", value: String(limit)))
        queryItems.append(URLQueryItem(name: "offset", value: String(offset)))
        
        components.queryItems = queryItems
        
        guard let url = components.url else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(VisitsResponse.self, from: data)
    }
    
    func getVisitDetails(visitId: String) async throws -> Visit {
        let url = URL(string: "\(baseURL)/api/v1/visits/\(visitId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        if httpResponse.statusCode == 404 {
            throw APIError.notFound
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(Visit.self, from: data)
    }
    
    func createVisit(_ request: CreateVisitRequest) async throws -> Visit {
        let url = URL(string: "\(baseURL)/api/v1/visits/")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        urlRequest.httpBody = try JSONEncoder().encode(request)
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 201 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(Visit.self, from: data)
    }
    
    func updateVisit(visitId: String, request: UpdateVisitRequest) async throws -> Visit {
        let url = URL(string: "\(baseURL)/api/v1/visits/\(visitId)")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "PUT"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        urlRequest.httpBody = try JSONEncoder().encode(request)
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(Visit.self, from: data)
    }
}

// MARK: - Recording Upload Methods (S3 Architecture)
extension APIManager {
    
    // MARK: - Initiate Audio Upload (v2.0)
    func initiateAudioUpload(_ request: AudioUploadRequest) async throws -> AudioUploadResponse {
        // Validate the request before sending
        try request.validate()
        
        // Validate that the pet belongs to the appointment (appointment context is now required)
        try await validatePetInAppointment(petId: request.petId, appointmentId: request.appointmentId)
        
        let url = URL(string: "\(baseURL)/api/v1/visit-transcripts/audio/upload/initiate")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        urlRequest.httpBody = try JSONEncoder().encode(request)
        
        // 🔍 DETAILED REQUEST LOGGING FOR BACKEND DEBUGGING
        print("🔍 UPLOAD INITIATE REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(urlRequest.httpMethod ?? "nil")")
        print("🔍 Headers: \(urlRequest.allHTTPHeaderFields ?? [:])")
        print("🔍 Content-Length: \(urlRequest.httpBody?.count ?? 0) bytes")
        
        if let requestBody = urlRequest.httpBody,
           let requestString = String(data: requestBody, encoding: .utf8) {
            print("🔍 Request Body (JSON): \(requestString)")
            
            // Parse and validate JSON structure for backend team
            do {
                if let json = try JSONSerialization.jsonObject(with: requestBody) as? [String: Any] {
                    print("🔍 Parsed JSON Keys: \(Array(json.keys).sorted())")
                    print("🔍 pet_id type: \(type(of: json["pet_id"]))")
                    print("🔍 appointment_id type: \(type(of: json["appointment_id"]))")
                    print("🔍 content_type: \(json["content_type"] ?? "nil")")
                    print("🔍 filename: \(json["filename"] ?? "nil")")
                }
            } catch {
                print("🔍 JSON parsing error: \(error)")
            }
        }
        
        print("🎵 Initiating audio upload for pet \(request.petId), appointment: \(request.appointmentId)")
        print("🔍 REQUEST TIMESTAMP: \(ISO8601DateFormatter().string(from: Date()))")
        
        let (data, urlResponse) = try await session.data(for: urlRequest)
        
        guard let httpResponse = urlResponse as? HTTPURLResponse else {
            print("❌ UPLOAD INITIATE: Invalid response type")
            throw APIError.invalidResponse
        }
        
        // 🔍 DETAILED RESPONSE LOGGING FOR BACKEND DEBUGGING
        print("🔍 UPLOAD INITIATE RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        print("🔍 Response Headers: \(httpResponse.allHeaderFields)")
        print("🔍 Response Content-Length: \(data.count) bytes")
        print("🔍 RESPONSE TIMESTAMP: \(ISO8601DateFormatter().string(from: Date()))")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
            
            // Try to parse error response for backend debugging
            if httpResponse.statusCode >= 400 {
                do {
                    if let errorJson = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        print("🔍 Error JSON Keys: \(Array(errorJson.keys).sorted())")
                        print("🔍 Error Detail: \(errorJson["detail"] ?? "No detail provided")")
                        if let errors = errorJson["errors"] as? [[String: Any]] {
                            print("🔍 Validation Errors: \(errors)")
                        }
                    }
                } catch {
                    print("🔍 Error response is not valid JSON: \(error)")
                }
            }
        } else {
            print("🔍 Response Body: Unable to decode as UTF-8, \(data.count) bytes")
        }
        
        // Log detailed error information for backend team
        if httpResponse.statusCode != 200 && httpResponse.statusCode != 201 {
            print("❌ UPLOAD INITIATE FAILED: Status \(httpResponse.statusCode)")
            print("❌ This is a BACKEND ERROR - iOS request is properly formatted")
            print("❌ Backend team should check:")
            print("   - Database connection issues")
            print("   - S3 configuration problems") 
            print("   - Appointment/Pet validation logic")
            print("   - Server logs for this timestamp: \(ISO8601DateFormatter().string(from: Date()))")
            
            if let responseString = String(data: data, encoding: .utf8) {
                print("❌ Error Response: \(responseString)")
            }
        }
        
        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        let response = try decoder.decode(AudioUploadResponse.self, from: data)
        print("✅ Audio upload initiated successfully: \(response.visitId)")
        
        return response
    }
    
    // MARK: - Validate Pet in Appointment
    private func validatePetInAppointment(petId: String, appointmentId: String) async throws {
        // Get appointment details to check if pet is associated
        let appointment = try await getAppointmentDetails(appointmentId: appointmentId)
        
        // Check if the pet is in the appointment's pet list
        let petExists = appointment.pets.contains { pet in
            pet.id == petId
        }
        
        if !petExists {
            print("❌ Pet \(petId) is not associated with appointment \(appointmentId)")
            throw AudioError.petNotInAppointment
        }
        
        print("✅ Pet \(petId) is valid for appointment \(appointmentId)")
    }
    
    // MARK: - Complete Audio Upload (v2.0)
    func completeAudioUpload(visitId: String, request: AudioUploadCompleteRequest) async throws -> VisitTranscript {
        let url = URL(string: "\(baseURL)/api/v1/visit-transcripts/audio/upload/complete/\(visitId)")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        urlRequest.httpBody = try encoder.encode(request)
        
        // Log the full request
        print("🔄 Complete Upload Request:")
        print("🔄 URL: \(url)")
        print("🔄 Method: \(urlRequest.httpMethod ?? "unknown")")
        print("🔄 Headers: \(authHeaders)")
        if let bodyData = urlRequest.httpBody, let bodyString = String(data: bodyData, encoding: .utf8) {
            print("🔄 Request Body: \(bodyString)")
        }
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ Complete Upload: Invalid response type")
            throw APIError.invalidResponse
        }
        
        // Log the full response
        print("🔄 Complete Upload Response:")
        print("🔄 Status Code: \(httpResponse.statusCode)")
        print("🔄 Response Headers: \(httpResponse.allHeaderFields)")
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔄 Response Body: \(responseString)")
        }
        
        if httpResponse.statusCode == 401 {
            throw APIError.unauthorized
        }
        
        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
            print("❌ Complete Upload failed with status: \(httpResponse.statusCode)")
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        let visitTranscript = try decoder.decode(VisitTranscript.self, from: data)
        print("✅ Complete Upload successful - Visit ID: \(visitTranscript.uuid)")
        
        return visitTranscript
    }
    
    // MARK: - Get Audio Playback URL (v2.0)
    func getAudioPlaybackUrl(visitId: String) async throws -> AudioPlaybackResponse {
        let url = URL(string: "\(baseURL)/api/v1/visit-transcripts/audio/playback/\(visitId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        if httpResponse.statusCode == 401 {
            throw APIError.unauthorized
        }
        
        if httpResponse.statusCode == 404 {
            throw APIError.notFound
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(AudioPlaybackResponse.self, from: data)
    }
    
    // MARK: - Get Visit Transcripts (v2.0) - FIXED to use correct endpoint
    func getVisitTranscripts(
        petId: String? = nil,
        appointmentId: String? = nil,
        limit: Int = 50,
        offset: Int = 0
    ) async throws -> [VisitTranscript] {
        // Use the correct endpoint that React frontend uses: /api/v1/visit-transcripts/pet/{pet_id}
        guard let petId = petId else {
            throw APIError.invalidRequest
        }
        let url = URL(string: "\(baseURL)/api/v1/visit-transcripts/pet/\(petId)")!
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        // 🔍 DETAILED REQUEST LOGGING
        print("🔍 GET VISIT TRANSCRIPTS REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(request.httpMethod ?? "nil")")
        print("🔍 Headers: \(request.allHTTPHeaderFields ?? [:])")
        print("🔍 Pet ID: \(petId)")
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ GET VISIT TRANSCRIPTS: Invalid response type")
            throw APIError.invalidResponse
        }
        
        // 🔍 DETAILED RESPONSE LOGGING
        print("🔍 GET VISIT TRANSCRIPTS RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
        }
        
        if httpResponse.statusCode == 401 {
            print("❌ GET VISIT TRANSCRIPTS: Unauthorized (401)")
            throw APIError.unauthorized
        }
        
        guard httpResponse.statusCode == 200 else {
            print("❌ GET VISIT TRANSCRIPTS FAILED: Status \(httpResponse.statusCode)")
            if let errorString = String(data: data, encoding: .utf8) {
                print("❌ Error Response: \(errorString)")
            }
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        // Decode visit transcripts array (now using correct endpoint!)
        let visitTranscripts = try decoder.decode([VisitTranscript].self, from: data)
        print("✅ GET VISIT TRANSCRIPTS SUCCESS: Got \(visitTranscripts.count) transcripts")
        
        return visitTranscripts
    }
    
    // MARK: - Get Visit Transcripts by Appointment (v2.0)
    func getVisitTranscriptsByAppointment(appointmentId: String) async throws -> [VisitTranscriptResponse] {
        let url = URL(string: "\(baseURL)/api/v1/visit-transcripts/appointments/\(appointmentId)/visits")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        // 🔍 DETAILED REQUEST LOGGING
        print("🔍 GET VISIT TRANSCRIPTS BY APPOINTMENT REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(request.httpMethod ?? "nil")")
        print("🔍 Headers: \(request.allHTTPHeaderFields ?? [:])")
        print("🔍 Appointment ID: \(appointmentId)")
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ GET VISIT TRANSCRIPTS BY APPOINTMENT: Invalid response type")
            throw APIError.invalidResponse
        }
        
        // 🔍 DETAILED RESPONSE LOGGING
        print("🔍 GET VISIT TRANSCRIPTS BY APPOINTMENT RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
        }
        
        if httpResponse.statusCode == 401 {
            print("❌ GET VISIT TRANSCRIPTS BY APPOINTMENT: Unauthorized (401)")
            throw APIError.unauthorized
        }
        
        if httpResponse.statusCode == 404 {
            print("❌ GET VISIT TRANSCRIPTS BY APPOINTMENT: Not Found (404)")
            throw APIError.notFound
        }
        
        guard httpResponse.statusCode == 200 else {
            print("❌ GET VISIT TRANSCRIPTS BY APPOINTMENT FAILED: Status \(httpResponse.statusCode)")
            if let errorString = String(data: data, encoding: .utf8) {
                print("❌ Error Response: \(errorString)")
            }
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        // Decode visit transcripts array
        let visitTranscripts = try decoder.decode([VisitTranscriptResponse].self, from: data)
        print("✅ GET VISIT TRANSCRIPTS BY APPOINTMENT SUCCESS: Got \(visitTranscripts.count) transcripts for appointment \(appointmentId)")
        
        return visitTranscripts
    }
    
    // MARK: - Pet Transcript List (for Medical Records)
    func getPetTranscriptList(petId: String) async throws -> [VisitTranscriptListItem] {
        let url = URL(string: "\(baseURL)/api/v1/visit-transcripts/pet/\(petId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        if httpResponse.statusCode == 401 {
            throw APIError.unauthorized
        }
        
        if httpResponse.statusCode == 404 {
            throw APIError.notFound
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode([VisitTranscriptListItem].self, from: data)
    }
    
    // MARK: - Transcript Detail (for detailed view)
    func getTranscriptDetail(visitId: String) async throws -> VisitTranscriptDetailResponse {
        let url = URL(string: "\(baseURL)/api/v1/visit-transcripts/\(visitId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        if httpResponse.statusCode == 401 {
            throw APIError.unauthorized
        }
        
        if httpResponse.statusCode == 404 {
            throw APIError.notFound
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(VisitTranscriptDetailResponse.self, from: data)
    }
    
    // MARK: - Vet Availability
    func createVetAvailability(_ request: CreateVetAvailabilityRequest) async throws -> VetAvailability {
        let url = URL(string: "\(baseURL)/api/v1/scheduling/vet-availability")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        urlRequest.httpBody = try encoder.encode(request)
        
        print("🔍 CREATE VET AVAILABILITY REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(urlRequest.httpMethod ?? "nil")")
        print("🔍 Headers: \(urlRequest.allHTTPHeaderFields ?? [:])")
        
        if let requestBody = urlRequest.httpBody,
           let requestString = String(data: requestBody, encoding: .utf8) {
            print("🔍 Request Body: \(requestString)")
        }
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ CREATE VET AVAILABILITY: Invalid response type")
            throw APIError.invalidResponse
        }
        
        print("🔍 CREATE VET AVAILABILITY RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
        }
        
        guard httpResponse.statusCode == 201 || httpResponse.statusCode == 200 else {
            if httpResponse.statusCode == 401 {
                await MainActor.run {
                    self.logout()
                }
                throw APIError.unauthorized
            }
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(VetAvailability.self, from: data)
    }
    
    func updateVetAvailability(availabilityId: String, request: UpdateVetAvailabilityRequest) async throws -> VetAvailability {
        let url = URL(string: "\(baseURL)/api/v1/scheduling/vet-availability/\(availabilityId)")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "PUT"
        authHeaders.forEach { urlRequest.setValue($1, forHTTPHeaderField: $0) }
        
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        urlRequest.httpBody = try encoder.encode(request)
        
        print("🔍 UPDATE VET AVAILABILITY REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(urlRequest.httpMethod ?? "nil")")
        print("🔍 Headers: \(urlRequest.allHTTPHeaderFields ?? [:])")
        
        if let requestBody = urlRequest.httpBody,
           let requestString = String(data: requestBody, encoding: .utf8) {
            print("🔍 Request Body: \(requestString)")
        }
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ UPDATE VET AVAILABILITY: Invalid response type")
            throw APIError.invalidResponse
        }
        
        print("🔍 UPDATE VET AVAILABILITY RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
        }
        
        guard httpResponse.statusCode == 200 else {
            if httpResponse.statusCode == 401 {
                await MainActor.run {
                    self.logout()
                }
                throw APIError.unauthorized
            }
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(VetAvailability.self, from: data)
    }
    
    func getVetAvailability(vetUserId: String, date: String) async throws -> [VetAvailability] {
        // Get the device's current timezone
        let deviceTimezone = TimeZone.current.identifier
        let url = URL(string: "\(baseURL)/api/v1/scheduling/vet-availability/\(vetUserId)?date=\(date)&timezone=\(deviceTimezone)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        print("🔍 GET VET AVAILABILITY REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(request.httpMethod ?? "nil")")
        print("🔍 Headers: \(request.allHTTPHeaderFields ?? [:])")
        print("🌍 Device Timezone: \(deviceTimezone)")
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ GET VET AVAILABILITY: Invalid response type")
            throw APIError.invalidResponse
        }
        
        print("🔍 GET VET AVAILABILITY RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
        }
        
        guard httpResponse.statusCode == 200 else {
            if httpResponse.statusCode == 401 {
                await MainActor.run {
                    self.logout()
                }
                throw APIError.unauthorized
            }
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode([VetAvailability].self, from: data)
    }
    
    func deleteVetAvailability(availabilityId: String) async throws {
        let url = URL(string: "\(baseURL)/api/v1/scheduling/vet-availability/\(availabilityId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        print("🔍 DELETE VET AVAILABILITY REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(request.httpMethod ?? "nil")")
        print("🔍 Headers: \(request.allHTTPHeaderFields ?? [:])")
        
        let (_, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ DELETE VET AVAILABILITY: Invalid response type")
            throw APIError.invalidResponse
        }
        
        print("🔍 DELETE VET AVAILABILITY RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        
        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 204 else {
            if httpResponse.statusCode == 401 {
                await MainActor.run {
                    self.logout()
                }
                throw APIError.unauthorized
            }
            throw APIError.serverError(httpResponse.statusCode)
        }
    }
    
    // MARK: - Call Analysis
    func getPracticeCalls(practiceId: String, limit: Int = 20, offset: Int = 0) async throws -> CallListResponse {
        let url = URL(string: "\(baseURL)/api/v1/call-analysis/practice/\(practiceId)/calls?limit=\(limit)&offset=\(offset)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        print("🔍 GET PRACTICE CALLS REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Practice ID: \(practiceId)")
        print("🔍 Limit: \(limit), Offset: \(offset)")
        print("🔍 Method: \(request.httpMethod ?? "nil")")
        print("🔍 Headers: \(request.allHTTPHeaderFields ?? [:])")
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ GET PRACTICE CALLS: Invalid response type")
            throw APIError.invalidResponse
        }
        
        print("🔍 GET PRACTICE CALLS RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
        }
        
        guard httpResponse.statusCode == 200 else {
            if httpResponse.statusCode == 401 {
                await MainActor.run {
                    self.logout()
                }
                throw APIError.unauthorized
            }
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(CallListResponse.self, from: data)
    }
    
    func getCallDetail(practiceId: String, callId: String) async throws -> CallDetailResponse {
        let url = URL(string: "\(baseURL)/api/v1/call-analysis/practice/\(practiceId)/calls/\(callId)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        authHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        
        print("🔍 GET CALL DETAIL REQUEST:")
        print("🔍 URL: \(url.absoluteString)")
        print("🔍 Method: \(request.httpMethod ?? "nil")")
        print("🔍 Headers: \(request.allHTTPHeaderFields ?? [:])")
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ GET CALL DETAIL: Invalid response type")
            throw APIError.invalidResponse
        }
        
        print("🔍 GET CALL DETAIL RESPONSE:")
        print("🔍 Status Code: \(httpResponse.statusCode)")
        
        if let responseString = String(data: data, encoding: .utf8) {
            print("🔍 Response Body: \(responseString)")
        }
        
        guard httpResponse.statusCode == 200 else {
            if httpResponse.statusCode == 401 {
                await MainActor.run {
                    self.logout()
                }
                throw APIError.unauthorized
            }
            throw APIError.serverError(httpResponse.statusCode)
        }
        
        return try decoder.decode(CallDetailResponse.self, from: data)
    }

    // MARK: - Legacy v1.0 methods removed
    // These methods have been replaced with v2.0 visit-transcript based methods:
    // - getRecordingDetails() -> Use getVisitTranscripts()
    // - getRecordingDownloadUrl() -> Use getAudioPlaybackUrl()
    // - deleteRecording() -> Visit transcripts are managed by the backend
}

// MARK: - v2.0 Visit Transcript Models
// Visit transcript models are defined in Models/AudioModels.swift

// Note: Response models are defined in their respective model files:
// - LoginResponse: Models/User.swift
// - DashboardResponse: Models/Appointment.swift  
// - MedicalRecordsResponse: Models/MedicalRecord.swift
// - VisitTranscript, AudioUploadResponse, etc.: Models/AudioModels.swift

// MARK: - APIError Extension
// Note: APIError cases are now defined in APIError.swift
