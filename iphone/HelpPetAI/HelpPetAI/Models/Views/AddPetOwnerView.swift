import SwiftUI

struct AddPetOwnerView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var apiManager = APIManager.shared
    
    let onComplete: () -> Void
    
    // Form state
    @State private var fullName = ""
    @State private var email = ""
    @State private var phone = ""
    @State private var secondaryPhone = ""
    @State private var address = ""
    @State private var emergencyContact = ""
    @State private var preferredCommunication = "email"
    @State private var notificationsEnabled = true
    
    // UI state
    @State private var isCreating = false
    @State private var showError = false
    @State private var errorMessage = ""
    
    private let communicationOptions = ["email", "phone", "sms"]
    
    var body: some View {
        NavigationView {
            Form {
                // Basic Information Section
                basicInfoSection
                
                // Contact Information Section
                contactInfoSection
                
                // Communication Preferences Section
                preferencesSection
                
                // Create Button Section
                createButtonSection
            }
            .navigationTitle("Add Pet Owner")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .disabled(isCreating)
                }
            }
            .alert("Error", isPresented: $showError) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
        }
    }
    
    // MARK: - View Sections
    
    private var basicInfoSection: some View {
        Section("Basic Information") {
            TextField("Full Name", text: $fullName)
                .autocapitalization(.words)
            
            TextField("Email Address", text: $email)
                .keyboardType(.emailAddress)
                .autocapitalization(.none)
                .autocorrectionDisabled()
        }
    }
    
    private var contactInfoSection: some View {
        Section("Contact Information") {
            TextField("Phone Number", text: $phone)
                .keyboardType(.phonePad)
            
            TextField("Secondary Phone (Optional)", text: $secondaryPhone)
                .keyboardType(.phonePad)
            
            TextField("Address (Optional)", text: $address, axis: .vertical)
                .lineLimit(2, reservesSpace: true)
                .autocapitalization(.words)
            
            TextField("Emergency Contact (Optional)", text: $emergencyContact)
                .autocapitalization(.words)
        }
    }
    
    private var preferencesSection: some View {
        Section("Communication Preferences") {
            Picker("Preferred Communication", selection: $preferredCommunication) {
                Text("Email").tag("email")
                Text("Phone").tag("phone")
                Text("SMS").tag("sms")
            }
            .pickerStyle(.menu)
            
            HStack {
                Text("Enable Notifications")
                Spacer()
                Toggle("", isOn: $notificationsEnabled)
                    .labelsHidden()
            }
        }
    }
    
    private var createButtonSection: some View {
        Section {
            Button(action: createPetOwner) {
                HStack {
                    if isCreating {
                        ProgressView()
                            .scaleEffect(0.8)
                            .padding(.trailing, 8)
                    }
                    Text(isCreating ? "Creating Pet Owner..." : "Create Pet Owner")
                }
                .frame(maxWidth: .infinity)
            }
            .disabled(fullName.isEmpty || email.isEmpty || isCreating)
            .buttonStyle(.borderedProminent)
        }
        .listRowInsets(EdgeInsets())
        .listRowBackground(Color.clear)
    }
    
    // MARK: - Actions
    
    private func createPetOwner() {
        Task {
            await performCreatePetOwner()
        }
    }
    
    @MainActor
    private func performCreatePetOwner() async {
        guard !fullName.isEmpty && !email.isEmpty else {
            errorMessage = "Full name and email are required"
            showError = true
            return
        }
        
        // Basic email validation
        if !email.contains("@") {
            errorMessage = "Please enter a valid email address"
            showError = true
            return
        }
        
        isCreating = true
        
        do {
            let request = CreatePetOwnerRequest(
                fullName: fullName,
                email: email,
                phone: phone.isEmpty ? nil : phone,
                secondaryPhone: secondaryPhone.isEmpty ? nil : secondaryPhone,
                address: address.isEmpty ? nil : address,
                emergencyContact: emergencyContact.isEmpty ? nil : emergencyContact,
                preferredCommunication: preferredCommunication,
                notificationsEnabled: notificationsEnabled
            )
            
            let _ = try await apiManager.createPetOwner(request)
            
            print("✅ Pet owner created successfully: \(fullName)")
            onComplete()
            dismiss()
            
        } catch {
            errorMessage = "Failed to create pet owner: \(error.localizedDescription)"
            showError = true
            print("❌ Failed to create pet owner: \(error)")
        }
        
        isCreating = false
    }
}

// MARK: - Create Pet Owner Request Model
struct CreatePetOwnerRequest: Codable {
    let fullName: String
    let email: String
    let phone: String?
    let secondaryPhone: String?
    let address: String?
    let emergencyContact: String?
    let preferredCommunication: String
    let notificationsEnabled: Bool
    
    enum CodingKeys: String, CodingKey {
        case email, phone, address
        case fullName = "full_name"
        case secondaryPhone = "secondary_phone"
        case emergencyContact = "emergency_contact"
        case preferredCommunication = "preferred_communication"
        case notificationsEnabled = "notifications_enabled"
    }
}

#Preview {
    AddPetOwnerView(onComplete: {})
}
