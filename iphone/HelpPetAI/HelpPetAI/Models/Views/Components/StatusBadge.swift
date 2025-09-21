//
//  StatusBadge.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

// MARK: - 13. Views/Components/StatusBadge.swift
import SwiftUI

struct StatusBadge: View {
    let status: AppointmentStatus
    
    var body: some View {
        Text(status.displayName)
            .font(.caption)
            .fontWeight(.medium)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(backgroundColorFor(status))
            .foregroundColor(textColorFor(status))
            .cornerRadius(6)
    }
    
    private func backgroundColorFor(_ status: AppointmentStatus) -> Color {
        switch status {
        case .scheduled: return .gray.opacity(0.2)
        case .confirmed: return .gray.opacity(0.2)
        case .inProgress: return .blue.opacity(0.2)
        case .completed: return .green.opacity(0.2)
        case .cancelled: return .red.opacity(0.2)
        case .complete: return .green.opacity(0.2)
        }
    }
    
    private func textColorFor(_ status: AppointmentStatus) -> Color {
        switch status {
        case .scheduled: return .gray
        case .confirmed: return .gray
        case .inProgress: return .blue
        case .completed: return .green
        case .cancelled: return .red
        case .complete: return .green
        }
    }
}
