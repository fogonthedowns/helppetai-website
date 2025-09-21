import SwiftUI

struct PetOwnerCard: View {
    let petOwner: PetOwnerDetails
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header with avatar and name
            HStack(spacing: 12) {
                // Avatar circle
                ZStack {
                    Circle()
                        .fill(Color.blue)
                        .frame(width: 50, height: 50)
                    
                    Text(String(petOwner.fullName.prefix(1)))
                        .font(.title2)
                        .fontWeight(.medium)
                        .foregroundColor(.white)
                }
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(petOwner.fullName)
                        .font(.headline)
                        .fontWeight(.medium)
                    
                    Text(petOwner.email)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }
                
                Spacer()
            }
            
            // Contact information
            VStack(alignment: .leading, spacing: 8) {
                if let phone = petOwner.phone, !phone.isEmpty {
                    ContactRow(icon: "phone.fill", text: formatPhoneNumber(phone), color: .green)
                }
                
                if let secondaryPhone = petOwner.secondaryPhone, !secondaryPhone.isEmpty {
                    ContactRow(icon: "phone.badge.plus", text: formatPhoneNumber(secondaryPhone), color: .orange)
                }
                
                if let address = petOwner.address, !address.isEmpty {
                    ContactRow(icon: "location.fill", text: address, color: .blue)
                }
                
                if let emergencyContact = petOwner.emergencyContact, !emergencyContact.isEmpty {
                    ContactRow(icon: "exclamationmark.triangle.fill", text: "Emergency: \(formatPhoneNumber(emergencyContact))", color: .red)
                }
            }
            
            // Communication preferences
            HStack {
                if let preferredComm = petOwner.preferredCommunication {
                    Label(preferredComm.capitalized, systemImage: preferredComm == "email" ? "envelope.fill" : "message.fill")
                        .font(.caption2)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color(.systemGray5))
                        .foregroundColor(.secondary)
                        .clipShape(Capsule())
                }
                
                if petOwner.notificationsEnabled {
                    Label("Notifications", systemImage: "bell.fill")
                        .font(.caption2)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.green.opacity(0.2))
                        .foregroundColor(.green)
                        .clipShape(Capsule())
                }
                
                Spacer()
            }
        }
        .padding(16)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
    }
    
    private func formatPhoneNumber(_ phone: String) -> String {
        // Simple phone number formatting
        let digits = phone.components(separatedBy: CharacterSet.decimalDigits.inverted).joined()
        
        if digits.count == 10 {
            return String(format: "(%@) %@-%@",
                         String(digits.prefix(3)),
                         String(digits.dropFirst(3).prefix(3)),
                         String(digits.suffix(4)))
        }
        
        return phone // Return original if not standard format
    }
}

struct ContactRow: View {
    let icon: String
    let text: String
    let color: Color
    
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.caption)
                .foregroundColor(color)
                .frame(width: 16)
            
            Text(text)
                .font(.caption)
                .foregroundColor(.primary)
                .lineLimit(2)
                .multilineTextAlignment(.leading)
            
            Spacer()
        }
    }
}

#Preview {
    let sampleOwner = PetOwnerDetails(
        uuid: "1",
        userId: nil,
        fullName: "Justin Zollars",
        email: "justin@jz.io",
        phone: "4157549214",
        secondaryPhone: "4192831624",
        address: "1248 Military West Benicia CA, 94510",
        emergencyContact: "4192831624",
        preferredCommunication: "email",
        notificationsEnabled: true,
        createdAt: Date(),
        updatedAt: Date()
    )
    
    PetOwnerCard(petOwner: sampleOwner)
        .padding()
}