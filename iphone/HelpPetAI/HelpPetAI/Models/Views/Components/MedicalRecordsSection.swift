//
//  MedicalRecordsSection.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

// MARK: - 18. Views/Components/MedicalRecordsSection.swift
import SwiftUI

struct MedicalRecordsSection: View {
    let records: MedicalRecordsResponse
    let pet: Pet
    let onRecordUpdated: (() -> Void)?
    let showOnlyCurrent: Bool
    
    private var displayRecords: [MedicalRecord] {
        if showOnlyCurrent {
            return records.records.filter { $0.isCurrent }
        } else {
            return records.records
        }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Medical Record")
                    .font(.headline)
                    .fontWeight(.medium)
                
                Spacer()
                
                if !displayRecords.isEmpty {
                    if showOnlyCurrent {
                        Text("Current")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    } else {
                        Text("\(displayRecords.count) total")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 16)
            
            if displayRecords.isEmpty {
                Text("No medical records found")
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 40)
            } else {
                LazyVStack(spacing: 8) {
                    ForEach(displayRecords) { record in
                        NavigationLink(destination: MedicalRecordDetailView(
                            medicalRecord: record,
                            pet: pet,
                            onRecordUpdated: onRecordUpdated
                        )) {
                            MedicalRecordCard(record: record)
                        }
                        .buttonStyle(PlainButtonStyle())
                    }
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 16)
            }
        }
        .background(Color(.secondarySystemBackground))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color(.separator), lineWidth: 0.5)
        )
    }
}
