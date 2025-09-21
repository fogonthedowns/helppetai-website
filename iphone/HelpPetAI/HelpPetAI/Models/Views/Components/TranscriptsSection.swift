//
//  TranscriptsSection.swift
//  HelpPetAI
//
//  Created by Claude on 9/9/25.
//

// MARK: - Views/Components/TranscriptsSection.swift
import SwiftUI

struct TranscriptsSection: View {
    let transcripts: [VisitTranscriptListItem]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Office Visits")
                    .font(.headline)
                
                Spacer()
                
                Text("\(transcripts.count) total")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            if transcripts.isEmpty {
                Text("No transcripts found")
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding()
            } else {
                LazyVStack(spacing: 12) {
                    ForEach(transcripts) { transcript in
                        TranscriptCard(transcript: transcript)
                    }
                }
            }
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color(.separator), lineWidth: 0.5)
        )
    }
}
