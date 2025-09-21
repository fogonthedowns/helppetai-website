//
//  APIError.swift
//  HelpPetAI

//
//  TL;DR: Centralized error type for all API/network failures.
//
//  Features:
//  - Strongly typed cases for common API issues (URL, request, decoding, etc.)
//  - Maps HTTP status codes → semantic errors (401 → unauthorized, 403 → forbidden, etc.)
//  - Human-readable error messages via `LocalizedError`
//  - Supports server error codes (`.serverError(Int)`) with details
//  - Provides consistent error handling across services & UI
//
//  Usage: Throw or return `APIError` from network calls,
//          then display `error.localizedDescription` to the user.

// MARK: - 7. Services/APIError.swift
import Foundation

enum APIError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case invalidRequest
    case unauthorized
    case forbidden
    case notFound
    case validationError
    case serverError(Int)
    case decodingError
    case networkError
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .invalidRequest:
            return "Invalid request parameters"
        case .unauthorized:
            return "Session expired. Please log in again."
        case .forbidden:
            return "Access denied. You don't have permission to perform this action."
        case .notFound:
            return "The requested resource was not found."
        case .validationError:
            return "Invalid data provided. Please check your input."
        case .serverError(let code):
            return "Server error (\(code)). Please try again later."
        case .decodingError:
            return "Failed to process server response"
        case .networkError:
            return "Network error. Please check your internet connection."
        }
    }
    
    // Helper to create APIError from HTTP status code
    static func from(statusCode: Int) -> APIError {
        switch statusCode {
        case 400:
            return .validationError
        case 401:
            return .unauthorized
        case 403:
            return .forbidden
        case 404:
            return .notFound
        case 422:
            return .validationError
        default:
            return .serverError(statusCode)
        }
    }
}
