//
//  DetailedItem.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//


// MARK: - 17. Views/Components/DetailItem.swift
import SwiftUI

struct DetailItem: View {
    let title: String
    let value: String
    
    init(title: String, value: String) {
        self.title = title
        self.value = value
    }
    
    init(title: String, value: Date, formatter: DateFormatter) {
        self.title = title
        self.value = formatter.string(from: value)
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
                .fontWeight(.medium)
            
            Text(value)
                .font(.subheadline)
                .lineLimit(2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}
