import SwiftUI

struct CreatePracticeView: View {
    @State private var practiceName = ""
    @State private var address = ""
    @State private var city = ""
    @State private var state = ""
    @State private var zipCode = ""
    @State private var phone = ""
    @State private var email = ""
    @State private var website = ""
    @State private var isLoading = false
    @State private var errorMessage = ""
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        ScrollView {
                VStack(spacing: 24) {
                    // Header
                    VStack(spacing: 16) {
                        Image(systemName: "building.2.crop.circle.badge.plus")
                            .font(.system(size: 60))
                            .foregroundColor(.green)
                        
                        Text("Create New Practice")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .foregroundColor(.primary)
                        
                        Text("Set up your veterinary practice profile")
                            .font(.body)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding(.top, 32)
                    
                    // Form Fields
                    VStack(spacing: 20) {
                        // Practice Name (Required)
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text("Practice Name")
                                    .font(.headline)
                                    .foregroundColor(.primary)
                                Text("*")
                                    .foregroundColor(.red)
                            }
                            
                            TextField("Enter practice name", text: $practiceName)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .textContentType(.organizationName)
                        }
                        
                        // Address Section
                        VStack(alignment: .leading, spacing: 16) {
                            Text("Address")
                                .font(.headline)
                                .foregroundColor(.primary)
                            
                            TextField("Street address", text: $address)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .textContentType(.streetAddressLine1)
                            
                            HStack(spacing: 12) {
                                TextField("City", text: $city)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    .textContentType(.addressCity)
                                
                                TextField("State", text: $state)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    .textContentType(.addressState)
                                    .frame(maxWidth: 100)
                                
                                TextField("ZIP", text: $zipCode)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    .textContentType(.postalCode)
                                    .keyboardType(.numberPad)
                                    .frame(maxWidth: 100)
                            }
                        }
                        
                        // Contact Information
                        VStack(alignment: .leading, spacing: 16) {
                            Text("Contact Information")
                                .font(.headline)
                                .foregroundColor(.primary)
                            
                            TextField("Phone number", text: $phone)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .textContentType(.telephoneNumber)
                                .keyboardType(.phonePad)
                            
                            TextField("Email address", text: $email)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .textContentType(.emailAddress)
                                .keyboardType(.emailAddress)
                                .autocapitalization(.none)
                            
                            TextField("Website (optional)", text: $website)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .textContentType(.URL)
                                .keyboardType(.URL)
                                .autocapitalization(.none)
                        }
                    }
                    .padding(.horizontal, 24)
                    
                    // Error Message
                    if !errorMessage.isEmpty {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                            .padding(.horizontal, 24)
                    }
                    
                    // Privacy Note
                    VStack(spacing: 8) {
                        HStack {
                            Image(systemName: "lock.shield")
                                .foregroundColor(.green)
                            Text("Private by Design")
                                .font(.headline)
                                .foregroundColor(.green)
                        }
                        
                        Text("Your practice information is private and secure. Only authorized staff members can access your practice data.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding(.horizontal, 24)
                    .padding(.vertical, 16)
                    .background(Color.green.opacity(0.1))
                    .cornerRadius(12)
                    .padding(.horizontal, 24)
                    
                    // Create Button
                    Button(action: createPractice) {
                        HStack {
                            if isLoading {
                                ProgressView()
                                    .scaleEffect(0.8)
                                    .foregroundColor(.white)
                            }
                            Text(isLoading ? "Creating Practice..." : "Create Practice")
                                .fontWeight(.semibold)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.green)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }
                    .disabled(isLoading || !isFormValid)
                    .opacity(isFormValid ? 1.0 : 0.6)
                    .padding(.horizontal, 24)
                    
                    // Required Fields Note
                    Text("* Required fields")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                        .padding(.bottom, 32)
                }
            }
            .navigationTitle("New Practice")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
    }
    
    private var isFormValid: Bool {
        !practiceName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }
    
    private func createPractice() {
        guard isFormValid else {
            errorMessage = "Practice name is required"
            return
        }
        
        isLoading = true
        errorMessage = ""
        
        Task {
            do {
                // Combine address fields into single address string
                let fullAddress = [address, "\(city) \(state) \(zipCode)"]
                    .filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
                    .joined(separator: ", ")
                
                let practiceData = CreatePracticeRequest(
                    name: practiceName.trimmingCharacters(in: .whitespacesAndNewlines),
                    address: fullAddress.isEmpty ? nil : fullAddress,
                    phone: phone.isEmpty ? nil : phone,
                    email: email.isEmpty ? nil : email,
                    website: website.isEmpty ? nil : website,
                    licenseNumber: nil, // Could add this field to UI later
                    specialties: [], // Could add this field to UI later
                    description: nil, // Could add this field to UI later
                    acceptsNewPatients: true // Default to true
                )
                
                let success = await APIManager.shared.createPractice(practiceData: practiceData)
                
                await MainActor.run {
                    isLoading = false
                    if success {
                        print("✅ Practice created successfully!")
                        // Note: User will automatically be redirected to dashboard
                        // via AuthenticatedContentView when currentUser.practiceId is updated
                        dismiss()
                    } else {
                        errorMessage = "Failed to create practice. Please try again."
                    }
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                    errorMessage = "Network error. Please check your connection."
                    print("❌ Create practice error: \(error)")
                }
            }
        }
    }
}

// MARK: - Create Practice Request Model
// Note: CreatePracticeRequest is defined in APIManager.swift

#Preview {
    CreatePracticeView()
}
