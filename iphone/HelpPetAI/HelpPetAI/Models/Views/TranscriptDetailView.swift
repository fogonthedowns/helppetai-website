//
//  TranscriptDetailView.swift
//  HelpPetAI
//
//  Created by Claude on 9/9/25.
//

// MARK: - Views/TranscriptDetailView.swift
import SwiftUI

struct TranscriptDetailView: View {
    let visitId: String
    
    @State private var transcript: VisitTranscriptDetailResponse?
    @State private var isLoading = true
    @State private var errorMessage = ""
    @State private var showError = false
    
    var body: some View {
        ScrollView {
            if isLoading {
                ProgressView("Loading transcript...")
                    .padding()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let transcript = transcript {
                VStack(spacing: 20) {
                    // Header Info
                    TranscriptHeaderCard(transcript: transcript)
                    
                    // Full Text Section
                    if !transcript.fullText.isEmpty {
                        FullTextSection(fullText: transcript.fullText)
                    }
                    
                    // Metadata Section
                    if !transcript.filteredMetadata.isEmpty {
                        MetadataSection(metadata: transcript.filteredMetadata)
                    }
                }
                .padding()
            }
        }
        .navigationTitle("Visit Details")
        .navigationBarTitleDisplayMode(.large)
        .onAppear {
            loadTranscriptDetail()
        }
        .alert("Error", isPresented: $showError) {
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
    }
    
    private func loadTranscriptDetail() {
        print("📄 Loading transcript details for ID: \(visitId)")
        isLoading = true
        
        Task {
            do {
                let result = try await APIManager.shared.getTranscriptDetail(visitId: visitId)
                print("📄 Transcript loaded successfully")
                
                await MainActor.run {
                    self.transcript = result
                    self.isLoading = false
                }
            } catch {
                print("📄 Error loading transcript: \(error)")
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.showError = true
                    self.isLoading = false
                }
            }
        }
    }
}

// MARK: - Header Card
struct TranscriptHeaderCard: View {
    let transcript: VisitTranscriptDetailResponse
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(transcript.visitDateAsDate, formatter: dateFormatter)
                        .font(.headline)
                        .fontWeight(.semibold)
                    
                    if let chiefComplaint = transcript.chiefComplaint, !chiefComplaint.isEmpty {
                        Text(chiefComplaint)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 4) {
                    HStack(spacing: 6) {
                        Circle()
                            .fill(statusColor)
                            .frame(width: 10, height: 10)
                        Text(transcript.state.displayName)
                            .font(.subheadline)
                            .fontWeight(.medium)
                    }
                    
                    if transcript.hasAudio == true {
                        HStack(spacing: 4) {
                            Image(systemName: "waveform")
                                .foregroundColor(.blue)
                            Text("Audio Available")
                                .font(.caption)
                                .foregroundColor(.blue)
                        }
                    }
                }
            }
            
            if let summary = transcript.summary, !summary.isEmpty {
                Divider()
                VStack(alignment: .leading, spacing: 4) {
                    Text("Summary")
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(.secondary)
                    Text(summary)
                        .font(.body)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.1), radius: 4, x: 0, y: 2)
    }
    
    private var statusColor: Color {
        switch transcript.state {
        case .new: return .blue
        case .processing: return .orange
        case .processed: return .green
        case .failed: return .red
        }
    }
    
    private var dateFormatter: DateFormatter {
        let formatter = DateFormatter()
        formatter.dateStyle = .full
        formatter.timeStyle = .short
        return formatter
    }
}

// MARK: - Full Text Section
struct FullTextSection: View {
    let fullText: String
    @State private var isExpanded = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Full Transcript")
                    .font(.headline)
                
                Spacer()
                
                Button(action: {
                    withAnimation(.easeInOut(duration: 0.3)) {
                        isExpanded.toggle()
                    }
                }) {
                    Text(isExpanded ? "Collapse" : "Expand")
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(.blue)
                }
            }
            
            Text(fullText)
                .font(.body)
                .lineLimit(isExpanded ? nil : 10)
                .multilineTextAlignment(.leading)
                .textSelection(.enabled)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.1), radius: 4, x: 0, y: 2)
    }
}

// MARK: - Metadata Section
struct MetadataSection: View {
    let metadata: [String: AnyCodable]
    
    private var categorizedMetadata: [(category: String, items: [(key: String, value: AnyCodable)])] {
        let sortedItems = metadata.sorted { $0.key < $1.key }
        
        // Group items by category for better organization
        var categories: [String: [(key: String, value: AnyCodable)]] = [:]
        
        for (key, value) in sortedItems {
            let category = categorizeKey(key)
            if categories[category] == nil {
                categories[category] = []
            }
            categories[category]?.append((key: key, value: value))
        }
        
        // Sort categories by priority
        let categoryOrder = ["Clinical", "Patient", "Treatment", "Assessment", "Other"]
        return categoryOrder.compactMap { category in
            if let items = categories[category], !items.isEmpty {
                return (category: category, items: items)
            }
            return nil
        } + categories.compactMap { (key, value) in
            if !categoryOrder.contains(key) {
                return (category: key, items: value)
            }
            return nil
        }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Healthcare Attributes")
                .font(.headline)
            
            ForEach(categorizedMetadata, id: \.category) { categoryData in
                VStack(alignment: .leading, spacing: 12) {
                    // Category Header
                    Text(categoryData.category)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(.blue)
                    
                    // Chips Layout
                    FlowLayout(spacing: 8) {
                        ForEach(categoryData.items, id: \.key) { item in
                            HealthcareAttributeChip(
                                title: formatKey(item.key),
                                value: formatValue(item.value.value)
                            )
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.1), radius: 4, x: 0, y: 2)
    }
    
    private func categorizeKey(_ key: String) -> String {
        let clinicalKeys = ["diagnosis", "symptoms", "condition", "clinical", "medical", "vital", "assessment", "exam", "physical"]
        let patientKeys = ["patient", "age", "weight", "breed", "species", "gender", "sex"]
        let treatmentKeys = ["treatment", "medication", "therapy", "prescription", "dose", "drug"]
        let assessmentKeys = ["severity", "priority", "urgency", "risk", "level", "grade", "score"]
        
        let lowercaseKey = key.lowercased()
        
        if clinicalKeys.contains(where: lowercaseKey.contains) {
            return "Clinical"
        } else if patientKeys.contains(where: lowercaseKey.contains) {
            return "Patient"
        } else if treatmentKeys.contains(where: lowercaseKey.contains) {
            return "Treatment"
        } else if assessmentKeys.contains(where: lowercaseKey.contains) {
            return "Assessment"
        } else {
            return "Other"
        }
    }
    
    private func formatKey(_ key: String) -> String {
        return key.replacingOccurrences(of: "_", with: " ")
                 .split(separator: " ")
                 .map { $0.capitalized }
                 .joined(separator: " ")
    }
    
    private func formatValue(_ value: Any) -> String {
        if let stringValue = value as? String {
            return stringValue
        } else if let numberValue = value as? NSNumber {
            return numberValue.stringValue
        } else if let boolValue = value as? Bool {
            return boolValue ? "Yes" : "No"
        } else if let arrayValue = value as? [Any] {
            return arrayValue.map { formatValue($0) }.joined(separator: ", ")
        } else {
            return String(describing: value)
        }
    }
}

// MARK: - Healthcare Attribute Chip
struct HealthcareAttributeChip: View {
    let title: String
    let value: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title)
                .font(.caption2)
                .fontWeight(.medium)
                .foregroundColor(.secondary)
                .lineLimit(1)
            
            Text(value)
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(.primary)
                .lineLimit(2)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(chipBackgroundColor)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(chipBorderColor, lineWidth: 1)
                )
        )
        .fixedSize(horizontal: false, vertical: true)
    }
    
    private var chipBackgroundColor: Color {
        // Color code by value type for medical context
        if value.lowercased().contains("normal") || value.lowercased().contains("stable") {
            return Color.green.opacity(0.1)
        } else if value.lowercased().contains("abnormal") || value.lowercased().contains("elevated") {
            return Color.orange.opacity(0.1)
        } else if value.lowercased().contains("critical") || value.lowercased().contains("severe") {
            return Color.red.opacity(0.1)
        } else {
            return Color(.systemGray6)
        }
    }
    
    private var chipBorderColor: Color {
        if value.lowercased().contains("normal") || value.lowercased().contains("stable") {
            return Color.green.opacity(0.3)
        } else if value.lowercased().contains("abnormal") || value.lowercased().contains("elevated") {
            return Color.orange.opacity(0.3)
        } else if value.lowercased().contains("critical") || value.lowercased().contains("severe") {
            return Color.red.opacity(0.3)
        } else {
            return Color(.systemGray4)
        }
    }
}

// MARK: - Flow Layout for Chips
struct FlowLayout: Layout {
    let spacing: CGFloat
    
    init(spacing: CGFloat = 8) {
        self.spacing = spacing
    }
    
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = FlowResult(
            in: proposal.replacingUnspecifiedDimensions(by: CGSize(width: 10, height: 10)).width,
            subviews: subviews,
            spacing: spacing
        )
        return result.size
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = FlowResult(
            in: bounds.width,
            subviews: subviews,
            spacing: spacing
        )
        for (index, subview) in subviews.enumerated() {
            subview.place(at: CGPoint(x: bounds.minX + result.frames[index].minX, y: bounds.minY + result.frames[index].minY), proposal: ProposedViewSize(result.frames[index].size))
        }
    }
}

struct FlowResult {
    let size: CGSize
    let frames: [CGRect]
    
    init(in maxWidth: CGFloat, subviews: LayoutSubviews, spacing: CGFloat) {
        var frames: [CGRect] = []
        var currentRowY: CGFloat = 0
        var currentRowX: CGFloat = 0
        var currentRowHeight: CGFloat = 0
        
        for subview in subviews {
            let subviewSize = subview.sizeThatFits(ProposedViewSize(width: nil, height: nil))
            
            if currentRowX + subviewSize.width > maxWidth && !frames.isEmpty {
                // Start new row
                currentRowY += currentRowHeight + spacing
                currentRowX = 0
                currentRowHeight = 0
            }
            
            frames.append(CGRect(x: currentRowX, y: currentRowY, width: subviewSize.width, height: subviewSize.height))
            
            currentRowX += subviewSize.width + spacing
            currentRowHeight = max(currentRowHeight, subviewSize.height)
        }
        
        self.frames = frames
        self.size = CGSize(width: maxWidth, height: currentRowY + currentRowHeight)
    }
}
