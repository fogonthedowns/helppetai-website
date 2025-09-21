import SwiftUI

struct PetOwnerRow: View {
    let petOwner: PetOwnerDetails
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                // Avatar circle
                ZStack {
                    Circle()
                        .fill(Color.blue)
                        .frame(width: 40, height: 40)
                    
                    Text(String(petOwner.fullName.prefix(1)))
                        .font(.headline)
                        .fontWeight(.medium)
                        .foregroundColor(.white)
                }
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(petOwner.fullName)
                        .font(.headline)
                        .fontWeight(.medium)
                    
                    Text(petOwner.email)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color(.separator), lineWidth: 0.5)
        )
        .shadow(color: Color.black.opacity(0.1), radius: 2, x: 0, y: 1)
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

#Preview {
    let sampleOwner = PetOwnerDetails(
        uuid: "1",
        userId: nil,
        fullName: "Justin Zollars",
        email: "justin@jz.io",
        phone: "4157549214",
        secondaryPhone: nil,
        address: nil,
        emergencyContact: nil,
        preferredCommunication: "email",
        notificationsEnabled: true,
        createdAt: Date(),
        updatedAt: Date()
    )
    
    PetOwnerRow(petOwner: sampleOwner)
        .padding()
}