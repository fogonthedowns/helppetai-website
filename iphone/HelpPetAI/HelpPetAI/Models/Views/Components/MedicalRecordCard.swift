//
//  MedicalRecordCard.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

// MARK: - Views/Components/MedicalRecordCard.swift
import SwiftUI

struct MedicalRecordCard: View {
    let record: MedicalRecord
    
    var body: some View {
        HStack(spacing: 12) {
            // Medical record icon
            Image(systemName: "doc.text.fill")
                .font(.title2)
                .foregroundColor(.blue)
                .frame(width: 30)
            
            Spacer()
            
            // Only show the date
            Text(record.visitDate, formatter: dateFormatter)
                .font(.headline)
                .fontWeight(.medium)
            
            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundColor(.secondary)
    }
    .padding()
    .background(Color(.systemBackground))
    .cornerRadius(8)
    .overlay(
        RoundedRectangle(cornerRadius: 8)
            .stroke(Color(.separator), lineWidth: 0.5)
    )
    }
    
    private var dateFormatter: DateFormatter {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return formatter
    }
}
