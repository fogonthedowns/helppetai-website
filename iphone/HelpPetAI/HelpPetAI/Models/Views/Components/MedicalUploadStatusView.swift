//
//  MedicalUploadStatusView.swift
//  HelpPetAI
//
//  Medical recording upload queue status component
//

import SwiftUI

struct MedicalUploadStatusView: View {
    @ObservedObject private var medicalManager = MedicalRecordingManager.shared
    @State private var showDetails = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            if !medicalManager.uploadQueue.isEmpty {
                HStack {
                    Image(systemName: "shield.checkerboard")
                        .foregroundColor(.green)
                    
                    Text("Secure Medical Uploads")
                        .font(.headline)
                    
                    Spacer()
                    
                    Button(showDetails ? "Hide" : "Show") {
                        showDetails.toggle()
                    }
                    .font(.caption)
                    .foregroundColor(.blue)
                }
                
                // Summary
                HStack(spacing: 16) {
                    uploadStatusBadge("Pending", count: medicalManager.uploadQueue.filter { $0.status == .pending }.count, color: .gray)
                    uploadStatusBadge("Uploading", count: medicalManager.uploadQueue.filter { $0.status == .uploading }.count, color: .blue)
                    uploadStatusBadge("Retrying", count: medicalManager.uploadQueue.filter { $0.status == .retrying }.count, color: .yellow)
                    uploadStatusBadge("Failed", count: medicalManager.uploadQueue.filter { $0.status == .failed }.count, color: .red)
                }
                
                if showDetails {
                    Divider()
                    
                    ForEach(medicalManager.uploadQueue, id: \.recordingId) { upload in
                        uploadDetailRow(upload)
                    }
                    
                    // Action buttons
                    HStack {
                        Button("Retry Failed") {
                            Task {
                                await medicalManager.retryFailedUploads()
                            }
                        }
                        .disabled(!medicalManager.uploadQueue.contains { $0.status == .failed })
                        
                        Spacer()
                        
                        Button("Clean Completed") {
                            medicalManager.cleanCompletedUploads()
                        }
                    }
                    .font(.caption)
                    .padding(.top, 8)
                }
            } else {
                HStack {
                    Image(systemName: "checkmark.shield")
                        .foregroundColor(.green)
                    
                    Text("All medical recordings secured")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
        .padding(.horizontal)
    }
    
    private func uploadStatusBadge(_ title: String, count: Int, color: Color) -> some View {
        VStack(spacing: 2) {
            Text("\(count)")
                .font(.headline)
                .fontWeight(.bold)
                .foregroundColor(color)
            
            Text(title)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .frame(minWidth: 50)
    }
    
    private func uploadDetailRow(_ upload: PendingUpload) -> some View {
        HStack {
            Circle()
                .fill(statusColor(upload.status))
                .frame(width: 8, height: 8)
            
            VStack(alignment: .leading, spacing: 2) {
                Text("Pet: \(upload.metadata.petId.prefix(8))...")
                    .font(.caption)
                    .fontWeight(.medium)
                
                Text("Size: \(ByteCountFormatter.string(fromByteCount: upload.metadata.fileSize, countStyle: .file))")
                    .font(.caption2)
                    .foregroundColor(.secondary)
                
                if let error = upload.lastError {
                    Text("Error: \(error)")
                        .font(.caption2)
                        .foregroundColor(.red)
                        .lineLimit(1)
                }
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 2) {
                Text(upload.status.rawValue.capitalized)
                    .font(.caption)
                    .foregroundColor(statusColor(upload.status))
                
                if upload.retryCount > 0 {
                    Text("Retry \(upload.retryCount)")
                        .font(.caption2)
                        .foregroundColor(.orange)
                }
                
                if let nextRetry = upload.nextRetryAt {
                    let timeRemaining = max(0, nextRetry.timeIntervalSinceNow)
                    if timeRemaining > 0 {
                        Text("Next: \(Int(timeRemaining))s")
                            .font(.caption2)
                            .foregroundColor(.blue)
                    }
                }
            }
        }
        .padding(.vertical, 4)
    }
    
    private func statusColor(_ status: UploadStatus) -> Color {
        switch status {
        case .pending: return .gray
        case .uploading: return .blue
        case .retrying: return .yellow
        case .completed: return .green
        case .failed: return .red
        }
    }
}

#Preview {
    MedicalUploadStatusView()
}