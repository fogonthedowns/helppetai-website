//
//  TranscriptCard.swift
//  HelpPetAI
//
//  Created by Claude on 9/9/25.
//

// MARK: - Views/Components/TranscriptCard.swift
import SwiftUI

struct TranscriptCard: View {
    let transcript: VisitTranscriptListItem
    
    var body: some View {
        NavigationLink(destination: TranscriptDetailView(visitId: transcript.uuid)) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(transcript.visitDateAsDate, formatter: dateFormatter)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                    
                    if let chiefComplaint = transcript.chiefComplaint, !chiefComplaint.isEmpty {
                        Text(chiefComplaint)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .lineLimit(2)
                    } else {
                        Text("No chief complaint recorded")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .italic()
                    }
                }
                
                Spacer()
                
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
        .buttonStyle(PlainButtonStyle())
    }
    
    
    private var dateFormatter: DateFormatter {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter
    }
    
    private var timestampFormatter: DateFormatter {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMM d, yyyy"
        return formatter
    }
    
    private func formatCreatedDate(_ createdAt: String) -> String {
        // Parse ISO8601 date string and format it
        let isoFormatter = ISO8601DateFormatter()
        if let date = isoFormatter.date(from: createdAt) {
            return timestampFormatter.string(from: date)
        }
        
        // Fallback: try to parse with DateFormatter
        let fallbackFormatter = DateFormatter()
        fallbackFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'"
        if let date = fallbackFormatter.date(from: createdAt) {
            return timestampFormatter.string(from: date)
        }
        
        // If parsing fails, return original string
        return createdAt
    }
}