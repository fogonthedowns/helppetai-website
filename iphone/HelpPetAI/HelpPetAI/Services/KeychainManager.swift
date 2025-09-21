//
//  KeychainManager.swift
//  HelpPetAI
//
//  TL;DR: Secure wrapper for storing, retrieving, and deleting the API access token.
//
//  Features:
//  - Stores access token in iOS Keychain with service + account scoping
//  - Prevents persistence leaks by deleting old token before saving new one
//  - Fetches access token safely, returning `nil` if not found or unreadable
//  - Deletes token cleanly when logging out
//  - Centralized singleton (`KeychainManager.shared`) for consistency
//
//  Usage:
//      KeychainManager.shared.saveAccessToken(token)
//      let token = KeychainManager.shared.getAccessToken()
//      KeychainManager.shared.deleteAccessToken()
//

// MARK: - 6. Services/KeychainManager.swift
import Foundation
import Security

class KeychainManager {
    static let shared = KeychainManager()
    
    private let service = "ai.helppet.HelpPetAI"
    private let accessTokenKey = "access_token"
    
    private init() {}
    
    func saveAccessToken(_ token: String) {
        let data = token.data(using: .utf8)!
        
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: accessTokenKey,
            kSecValueData as String: data
        ]
        
        // Delete existing item
        SecItemDelete(query as CFDictionary)
        
        // Add new item
        SecItemAdd(query as CFDictionary, nil)
    }
    
    func getAccessToken() -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: accessTokenKey,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess,
              let data = result as? Data,
              let token = String(data: data, encoding: .utf8) else {
            return nil
        }
        
        return token
    }
    
    func deleteAccessToken() {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: accessTokenKey
        ]
        
        SecItemDelete(query as CFDictionary)
    }
}
