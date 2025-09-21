import SwiftUI

struct EditPetOwnerView: View {
    let petOwner: PetOwnerDetails
    let onSave: (PetOwnerDetails) -> Void
    
    @StateObject private var apiManager = APIManager.shared
    @Environment(\.presentationMode) var presentationMode
    
    @State private var fullName: String
    @State private var email: String
    @State private var phone: String
    @State private var secondaryPhone: String
    @State private var address: String
    @State private var emergencyContact: String
    @State private var preferredCommunication: String
    @State private var notificationsEnabled: Bool
    
    @State private var isLoading = false
    @State private var showError = false
    @State private var errorMessage = ""
    
    init(petOwner: PetOwnerDetails, onSave: @escaping (PetOwnerDetails) -> Void) {
        self.petOwner = petOwner
        self.onSave = onSave
        
        // Initialize state variables with current values
        _fullName = State(initialValue: petOwner.fullName)
        _email = State(initialValue: petOwner.email)
        _phone = State(initialValue: petOwner.phone ?? "")
        _secondaryPhone = State(initialValue: petOwner.secondaryPhone ?? "")
        _address = State(initialValue: petOwner.address ?? "")
        _emergencyContact = State(initialValue: petOwner.emergencyContact ?? "")
        _preferredCommunication = State(initialValue: petOwner.preferredCommunication ?? "email")
        _notificationsEnabled = State(initialValue: petOwner.notificationsEnabled)
    }
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Basic Information")) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Full Name")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter full name", text: $fullName)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Email")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter email address", text: $email)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .keyboardType(.emailAddress)
                            .autocapitalization(.none)
                    }
                }
                
                Section(header: Text("Contact Information")) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Phone")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter phone number", text: $phone)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .keyboardType(.phonePad)
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Secondary Phone")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter secondary phone (optional)", text: $secondaryPhone)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .keyboardType(.phonePad)
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Emergency Contact")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter emergency contact (optional)", text: $emergencyContact)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .keyboardType(.phonePad)
                    }
                }
                
                Section(header: Text("Address")) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Address")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        TextField("Enter address (optional)", text: $address, axis: .vertical)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .lineLimit(2...4)
                    }
                }
                
                Section(header: Text("Preferences")) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Preferred Communication")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Picker("Preferred Communication", selection: $preferredCommunication) {
                            Text("Email").tag("email")
                            Text("Phone").tag("phone")
                            Text("SMS").tag("sms")
                        }
                        .pickerStyle(SegmentedPickerStyle())
                    }
                    
                    Toggle("Enable Notifications", isOn: $notificationsEnabled)
                }
            }
            .navigationTitle("Edit Pet Owner")
            .navigationBarTitleDisplayMode(.inline)
            .navigationBarItems(
                leading: Button("Cancel") {
                    presentationMode.wrappedValue.dismiss()
                },
                trailing: Button("Save") {
                    Task {
                        await savePetOwner()
                    }
                }
                .disabled(isLoading || fullName.isEmpty || email.isEmpty)
            )
            .alert("Error", isPresented: $showError) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
        }
    }
    
    @MainActor
    private func savePetOwner() async {
        isLoading = true
        
        let updateRequest = UpdatePetOwnerRequest(
            userId: petOwner.userId,
            fullName: fullName.trimmingCharacters(in: .whitespacesAndNewlines),
            email: email.trimmingCharacters(in: .whitespacesAndNewlines),
            phone: phone.isEmpty ? "" : phone.trimmingCharacters(in: .whitespacesAndNewlines),
            emergencyContact: emergencyContact.isEmpty ? "" : emergencyContact.trimmingCharacters(in: .whitespacesAndNewlines),
            secondaryPhone: secondaryPhone.isEmpty ? "" : secondaryPhone.trimmingCharacters(in: .whitespacesAndNewlines),
            address: address.isEmpty ? "" : address.trimmingCharacters(in: .whitespacesAndNewlines),
            preferredCommunication: preferredCommunication,
            notificationsEnabled: notificationsEnabled
        )
        
        do {
            let updatedPetOwner = try await apiManager.updatePetOwner(petOwnerId: petOwner.uuid, request: updateRequest)
            onSave(updatedPetOwner)
            presentationMode.wrappedValue.dismiss()
        } catch {
            errorMessage = "Failed to update pet owner: \(error.localizedDescription)"
            showError = true
            print("❌ Failed to update pet owner: \(error)")
        }
        
        isLoading = false
    }
}


#Preview {
    let sampleOwner = PetOwnerDetails(
        uuid: "1",
        userId: nil,
        fullName: "Hillary Park",
        email: "hills@email.com.pk",
        phone: "4157549214",
        secondaryPhone: "4192831624",
        address: "1248 Military West Benicia CA, 94510",
        emergencyContact: "4192831624",
        preferredCommunication: "email",
        notificationsEnabled: true,
        createdAt: Date(),
        updatedAt: Date()
    )
    
    EditPetOwnerView(petOwner: sampleOwner) { _ in }
}
