//
//  CurrentAppointmentCard.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

// MARK: - 11. Views/Components/CurrentAppointmentCard.swift
import SwiftUI

struct CurrentAppointmentCard: View {
    let appointment: Appointment
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Current Visit")
                    .font(.headline)
                    .foregroundColor(.orange)
                
                Spacer()
                
                Text(appointment.appointmentDate, style: .time)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            Text(appointment.title)
                .font(.title3)
                .fontWeight(.semibold)
            
            if let firstPet = appointment.pets.first {
                HStack {
                    Image(systemName: firstPet.species == "dog" ? "pawprint.fill" : "cat.fill")
                        .foregroundColor(.orange)
                    
                    Text("\(firstPet.name) (\(firstPet.breed ?? firstPet.species.capitalized))")
                        .font(.subheadline)
                }
            }
            
            if let description = appointment.description {
                Text(description)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color.orange.opacity(0.1))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.orange.opacity(0.3), lineWidth: 1)
        )
    }
}
