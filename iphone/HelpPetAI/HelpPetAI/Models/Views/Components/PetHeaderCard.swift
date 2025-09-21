//
//  PetHeaderCard.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//
// MARK: - Views/Components/PetHeaderCard.swift
import SwiftUI

struct PetHeaderCard: View {
    let pet: Pet
    
    var body: some View {
        VStack(spacing: 16) {
            // Pet Avatar and Basic Info
            HStack(spacing: 16) {
                Image(systemName: pet.species == "dog" ? "pawprint.circle.fill" : "cat.circle.fill")
                    .font(.system(size: 60))
                    .foregroundColor(.blue)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(pet.name)
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    Text("\(pet.species.capitalized) • \(pet.breed ?? "Mixed")")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    if let dateOfBirth = pet.dateOfBirth {
                        Text("Born: \(dateOfBirth, formatter: dateFormatter)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
            }
            
            // Pet Details Grid
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 16) {
                if let weight = pet.weight {
                    DetailItem(title: "Weight", value: String(format: "%.1f lbs", weight))
                }
                
                DetailItem(title: "Status", value: pet.isActive ? "Active" : "Inactive")
                
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.1), radius: 4, x: 0, y: 2)
    }
    
    private var dateFormatter: DateFormatter {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return formatter
    }
}
