//
//  DetailRow.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

// MARK: - 20. Views/Components/DetailRow.swift
import SwiftUI

struct DetailRow: View {
    let title: String
    let content: String
    
    init(title: String, content: String) {
        self.title = title
        self.content = content
    }
    
    init(title: String, content: Date, formatter: DateFormatter) {
        self.title = title
        self.content = formatter.string(from: content)
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(.primary)
            
            Text(content)
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
}
