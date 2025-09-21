//
//  FrontDeskView.swift
//  HelpPetAI
//
//  Created by Assistant on 9/20/25.
//

import SwiftUI
import AVFoundation

struct FrontDeskView: View {
    let onToggleSidebar: (() -> Void)?
    @ObservedObject private var apiManager = APIManager.shared
    
    @State private var calls: [CallSummary] = []
    @State private var isLoading = false
    @State private var isLoadingMore = false
    @State private var errorMessage = ""
    @State private var showError = false
    @State private var selectedCall: CallDetail?
    @State private var showCallDetail = false
    @State private var loadingTask: Task<Void, Never>? = nil
    
    // Pagination state
    @State private var currentOffset = 0
    @State private var hasMore = true
    private let pageSize = 20
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                if isLoading && calls.isEmpty {
                    loadingView
                } else if calls.isEmpty && !isLoading {
                    emptyStateView
                } else {
                    callsListView
                }
            }
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    if let onToggleSidebar = onToggleSidebar {
                        Button(action: {
                            onToggleSidebar()
                        }) {
                            Image(systemName: "line.3.horizontal")
                                .font(.title3)
                                .foregroundColor(.blue)
                        }
                    }
                }
                
                ToolbarItem(placement: .principal) {
                    Text("Front Desk")
                        .font(.headline)
                        .fontWeight(.medium)
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        Task {
                            await refreshCalls()
                        }
                    }) {
                        Image(systemName: "arrow.clockwise")
                            .font(.title3)
                            .foregroundColor(.blue)
                    }
                    .disabled(isLoading)
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .alert("Error", isPresented: $showError) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
            .sheet(isPresented: $showCallDetail) {
                if let selectedCall = selectedCall {
                    CallDetailSheet(call: selectedCall) {
                        print("🔥 CallDetailSheet onDismiss called")
                        self.selectedCall = nil
                    }
                    .onAppear {
                        print("🔥 Sheet is being presented - selectedCall: \(selectedCall.callId ?? "nil")")
                    }
                } else {
                    Text("Error: No call selected")
                        .onAppear {
                            print("🔥 ERROR: Sheet presented but selectedCall is nil!")
                        }
                }
            }
        }
        .onAppear {
            print("🔍 FrontDeskView appeared - calls count: \(calls.count), isLoading: \(isLoading)")
            loadCallsSafely()
        }
        .onChange(of: apiManager.currentUser) { oldUser, newUser in
            // When user gets loaded, load calls
            if oldUser == nil && newUser != nil {
                print("🔍 User loaded, now loading calls")
                loadCallsSafely()
            }
        }
        .onDisappear {
            loadingTask?.cancel()
        }
        .refreshable {
            await refreshCalls()
        }
    }
    
    // MARK: - View Components
    
    private var loadingView: some View {
        VStack(spacing: 20) {
            ProgressView()
                .scaleEffect(1.2)
            Text("Loading calls...")
                .font(.body)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "phone.badge.waveform")
                .font(.system(size: 48))
                .foregroundColor(.secondary)
            
            Text("No Calls Found")
                .font(.headline)
                .foregroundColor(.primary)
            
            Text("Call analysis data will appear here when calls are made to your practice.")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            Button("Refresh") {
                Task {
                    await refreshCalls()
                }
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    private var callsListView: some View {
        List {
            ForEach(calls) { call in
                CallRowView(call: call) {
                    print("🔥 FrontDeskView: CallRowView onTap triggered for call: \(call.callId ?? "no-id")")
                    print("🔥 Current selectedCall: \(selectedCall?.callId ?? "nil")")
                    print("🔥 Current showCallDetail: \(showCallDetail)")
                    
                    // Open sheet immediately with call summary data
                    let callDetail = CallDetail(
                        callId: call.callId,
                        recordingUrl: call.recordingUrl,
                        startTimestamp: call.startTimestamp,
                        endTimestamp: call.endTimestamp,
                        callAnalysis: call.callAnalysis,
                        durationMs: nil, // Will be loaded
                        agentId: nil, // Will be loaded
                        fromNumber: call.fromNumber,
                        toNumber: call.toNumber,
                        callStatus: nil, // Will be loaded
                        disconnectReason: nil // Will be loaded
                    )
                    
                    print("🔥 Setting selectedCall to: \(callDetail.callId ?? "no-id")")
                    selectedCall = callDetail
                    print("🔥 Setting showCallDetail to true")
                    showCallDetail = true
                    print("🔥 After setting - selectedCall: \(selectedCall?.callId ?? "nil"), showCallDetail: \(showCallDetail)")
                    
                    // Load additional details in background
                    Task {
                        await loadCallDetail(callId: call.callId ?? "")
                    }
                }
            }
            
            // Load more row
            if hasMore {
                HStack {
                    Spacer()
                    if isLoadingMore {
                        ProgressView()
                            .scaleEffect(0.8)
                        Text("Loading more...")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    } else {
                        Button("Load More") {
                            Task {
                                await loadCalls(refresh: false)
                            }
                        }
                        .font(.caption)
                        .foregroundColor(.blue)
                    }
                    Spacer()
                }
                .padding(.vertical, 8)
            }
        }
        .listStyle(.plain)
    }
    
    // MARK: - Data Loading Methods
    
    private func refreshCalls() async {
        await loadCalls(refresh: true)
    }
    
    private func loadCallsSafely() {
        // Cancel any existing loading task to prevent race conditions
        loadingTask?.cancel()
        
        loadingTask = Task {
            // Small delay to ensure UI is ready
            try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
            
            if !Task.isCancelled {
                await MainActor.run {
                    self.isLoading = true
                    self.errorMessage = ""
                }
                
                if apiManager.currentUser != nil {
                    await loadCalls(refresh: true)
                } else {
                    await waitForUserAndLoad()
                }
            }
        }
    }
    
    private func waitForUserAndLoad() async {
        print("🔍 Waiting for user to be loaded...")
        
        // Wait up to 5 seconds for user to be loaded
        for attempt in 0..<50 {
            if Task.isCancelled {
                print("🔍 Wait for user task was cancelled")
                return
            }
            
            if apiManager.currentUser != nil {
                print("🔍 User found after \(attempt * 100)ms, loading calls")
                await loadCalls(refresh: true)
                return
            }
            
            try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
        }
        
        print("❌ Timeout waiting for user to be loaded")
        await MainActor.run {
            self.errorMessage = "Failed to load user information. Please try again."
            self.showError = true
            self.isLoading = false
        }
    }
    
    private func loadCalls(refresh: Bool = false) async {
        print("🔍 loadCalls called - refresh: \(refresh)")
        print("🔍 currentUser: \(apiManager.currentUser?.fullName ?? "nil")")
        print("🔍 practiceId: \(apiManager.currentUser?.practiceId ?? "nil")")
        
        guard let currentUser = apiManager.currentUser,
              let practiceId = currentUser.practiceId else {
            print("❌ No current user or practice ID found")
            await MainActor.run {
                self.errorMessage = "No practice ID found for current user"
                self.showError = true
                self.isLoading = false
            }
            return
        }
        
        if refresh {
            await MainActor.run {
                self.currentOffset = 0
                self.hasMore = true
                self.isLoading = true
                self.calls = []
                self.errorMessage = ""
            }
        } else {
            await MainActor.run {
                self.isLoadingMore = true
            }
        }
        
        do {
            let response = try await apiManager.getPracticeCalls(
                practiceId: practiceId,
                limit: pageSize,
                offset: currentOffset
            )
            
            await MainActor.run {
                if refresh {
                    self.calls = response.calls
                } else {
                    self.calls.append(contentsOf: response.calls)
                }
                
                // Sort calls by start time (most recent first)
                self.calls.sort { call1, call2 in
                    guard let timestamp1 = call1.startTimestamp, let timestamp2 = call2.startTimestamp else {
                        return false
                    }
                    return timestamp1 > timestamp2
                }
                
                self.currentOffset += response.pagination.count
                self.hasMore = response.pagination.hasMore ?? false
                self.isLoading = false
                self.isLoadingMore = false
                
                print("✅ Loaded \(response.calls.count) calls, total: \(self.calls.count)")
            }
            
        } catch {
            print("❌ Failed to load calls: \(error)")
            await MainActor.run {
                self.errorMessage = "Failed to load calls: \(error.localizedDescription)"
                self.showError = true
                self.isLoading = false
                self.isLoadingMore = false
            }
        }
    }
    
    private func loadCallDetail(callId: String) async {
        guard let currentUser = apiManager.currentUser,
              let practiceId = currentUser.practiceId else {
            await MainActor.run {
                self.errorMessage = "No practice ID found for current user"
                self.showError = true
            }
            return
        }
        
        do {
            let response = try await apiManager.getCallDetail(
                practiceId: practiceId,
                callId: callId
            )
            
            await MainActor.run {
                // Update the existing selectedCall with additional details
                if let currentCall = self.selectedCall, currentCall.callId == response.call.callId {
                    let updatedCall = CallDetail(
                        callId: response.call.callId,
                        recordingUrl: response.call.recordingUrl,
                        startTimestamp: response.call.startTimestamp,
                        endTimestamp: response.call.endTimestamp,
                        callAnalysis: response.call.callAnalysis,
                        durationMs: response.call.durationMs,
                        agentId: response.call.agentId,
                        fromNumber: response.call.fromNumber,
                        toNumber: response.call.toNumber,
                        callStatus: response.call.callStatus,
                        disconnectReason: response.call.disconnectReason
                    )
                    self.selectedCall = updatedCall
                } else {
                    // Fallback if no existing call
                    self.selectedCall = response.call
                    self.showCallDetail = true
                }
            }
            
        } catch {
            print("❌ Failed to load call detail: \(error)")
            await MainActor.run {
                self.errorMessage = "Failed to load call details: \(error.localizedDescription)"
                self.showError = true
            }
        }
    }
}

// MARK: - Call Row View

struct CallRowView: View {
    let call: CallSummary
    let onTap: () -> Void
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(call.fromNumber ?? "Unknown Number")
                    .font(.body)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                
                HStack(spacing: 4) {
                    Text(formatLocalTime())
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text("•")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text(calculateDuration())
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
            
            // Just the sentiment badge
            if let sentiment = call.callAnalysis?.userSentiment {
                Text(sentiment.capitalized)
                    .font(.body)
                    .fontWeight(.medium)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(colorFromString(call.callAnalysis?.sentimentColor ?? "gray").opacity(0.2))
                    )
                    .foregroundColor(colorFromString(call.callAnalysis?.sentimentColor ?? "gray"))
            }
        }
        .padding(.vertical, 8)
        .contentShape(Rectangle())
        .onTapGesture {
            print("🔥 CallRowView onTapGesture triggered for call: \(call.callId ?? "no-id")")
            onTap()
        }
    }
    
    private func formatLocalTime() -> String {
        guard let startTimestamp = call.startTimestamp else {
            return "No timestamp"
        }
        
        // Parse the ISO8601 timestamp
        let isoFormatter = ISO8601DateFormatter()
        isoFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        
        guard let startDate = isoFormatter.date(from: startTimestamp) else {
            return "Invalid timestamp"
        }
        
        // Format to local time
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        formatter.dateStyle = .short
        formatter.timeZone = TimeZone.current
        return formatter.string(from: startDate)
    }
    
    private func calculateDuration() -> String {
        guard let startTimestamp = call.startTimestamp,
              let endTimestamp = call.endTimestamp else {
            return "Unknown duration"
        }
        
        // Parse both timestamps
        let isoFormatter = ISO8601DateFormatter()
        isoFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        
        guard let startDate = isoFormatter.date(from: startTimestamp),
              let endDate = isoFormatter.date(from: endTimestamp) else {
            return "Invalid timestamps"
        }
        
        // Calculate duration
        let duration = endDate.timeIntervalSince(startDate)
        let totalSeconds = Int(duration)
        let minutes = totalSeconds / 60
        let seconds = totalSeconds % 60
        
        return "\(minutes):\(String(format: "%02d", seconds))"
    }
    
    private func colorFromString(_ colorString: String) -> Color {
        switch colorString.lowercased() {
        case "green": return .green
        case "red": return .red
        case "orange": return .orange
        case "yellow": return .yellow
        case "blue": return .blue
        default: return .gray
        }
    }
}

// MARK: - Call Detail Sheet

struct CallDetailSheet: View {
    @Environment(\.dismiss) private var dismiss
    let call: CallDetail
    let onDismiss: () -> Void
    @State private var audioPlayer: AVPlayer?
    @State private var isPlaying = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    // Call header info
                    callHeaderSection
                    
                    // Call analysis
                    if let analysis = call.callAnalysis {
                        callAnalysisSection(analysis)
                    }
                    
                    // Technical details
                    technicalDetailsSection
                }
                .padding()
            }
            .navigationTitle("Call Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        onDismiss()
                        dismiss()
                    }
                }
            }
        }
    }
    
    private var callHeaderSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Call Information")
                        .font(.headline)
                        .fontWeight(.semibold)
                    
                    if let startDate = call.startDate {
                        Text(formatFullDate(startDate))
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                Text(call.formattedDuration)
                    .font(.title2)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
            }
            
            if let fromNumber = call.fromNumber {
                HStack {
                    Image(systemName: "phone")
                    Text("From: \(fromNumber)")
                        .font(.body)
                }
                .foregroundColor(.secondary)
            }
            
            if let toNumber = call.toNumber {
                HStack {
                    Image(systemName: "phone.badge.plus")
                    Text("To: \(toNumber)")
                        .font(.body)
                }
                .foregroundColor(.secondary)
            }
            
            if let status = call.callStatus {
                HStack {
                    Image(systemName: "info.circle")
                    Text("Status: \(status.capitalized)")
                        .font(.body)
                }
                .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemGray6))
        )
    }
    
    private func callAnalysisSection(_ analysis: CallAnalysisData) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Call Analysis")
                .font(.headline)
                .fontWeight(.semibold)
            
            // Success and sentiment
            HStack {
                HStack(spacing: 4) {
                    Image(systemName: analysis.successIcon)
                        .foregroundColor(colorFromString(analysis.successColor))
                    Text(analysis.callSuccessful == true ? "Successful" : "Unsuccessful")
                        .font(.body)
                        .fontWeight(.medium)
                }
                
                Spacer()
                
                if let sentiment = analysis.userSentiment {
                    Text(sentiment.capitalized)
                        .font(.body)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(
                            RoundedRectangle(cornerRadius: 6)
                                .fill(colorFromString(analysis.sentimentColor).opacity(0.2))
                        )
                        .foregroundColor(colorFromString(analysis.sentimentColor))
                }
            }
            
            // Summary
            if let summary = analysis.callSummary {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Summary")
                        .font(.subheadline)
                        .fontWeight(.semibold)
                    Text(summary)
                        .font(.body)
                        .foregroundColor(.primary)
                }
            }
            
            // Custom analysis data
            if let appointmentType = analysis.appointmentType {
                DetailRow(title: "Appointment Type", content: appointmentType.capitalized)
            }
            
            if let urgency = analysis.urgencyLevel {
                DetailRow(title: "Urgency Level", content: urgency.capitalized)
            }
            
            if let pet = analysis.petMentioned {
                DetailRow(title: "Pet Mentioned", content: pet)
            }
            
            if let symptoms = analysis.symptomsMentioned, !symptoms.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Symptoms Mentioned")
                        .font(.subheadline)
                        .fontWeight(.semibold)
                    Text(symptoms.joined(separator: ", "))
                        .font(.body)
                        .foregroundColor(.primary)
                }
            }
            
            if let scheduled = analysis.appointmentScheduled {
                DetailRow(title: "Appointment Scheduled", content: scheduled ? "Yes" : "No")
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemGray6))
        )
    }
    
    private var technicalDetailsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Technical Details")
                .font(.headline)
                .fontWeight(.semibold)
            
            if let callId = call.callId {
                DetailRow(title: "Call ID", content: callId)
            }
            
            if let agentId = call.agentId {
                DetailRow(title: "Agent ID", content: agentId)
            }
            
            if let disconnectReason = call.disconnectReason {
                DetailRow(title: "Disconnect Reason", content: disconnectReason.capitalized)
            }
            
            if let recordingUrl = call.recordingUrl {
                HStack {
                    Text("Recording")
                        .font(.subheadline)
                        .fontWeight(.semibold)
                    Spacer()
                    Button(isPlaying ? "Stop" : "Play") {
                        if isPlaying {
                            stopRecording()
                        } else {
                            playRecording(url: recordingUrl)
                        }
                    }
                    .buttonStyle(.bordered)
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemGray6))
        )
    }
    
    private func formatFullDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .full
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
    
    private func colorFromString(_ colorString: String) -> Color {
        switch colorString.lowercased() {
        case "green": return .green
        case "red": return .red
        case "orange": return .orange
        case "yellow": return .yellow
        case "blue": return .blue
        default: return .gray
        }
    }
    
    private func playRecording(url: String) {
        guard let recordingURL = URL(string: url) else {
            print("❌ Invalid recording URL: \(url)")
            return
        }
        
        // Configure audio session to play even when silent switch is on
        do {
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.playback, mode: .default, options: [])
            try audioSession.setActive(true)
            print("🎵 Audio session configured for playback")
        } catch {
            print("❌ Failed to configure audio session: \(error)")
        }
        
        print("🎵 Playing recording: \(url)")
        audioPlayer = AVPlayer(url: recordingURL)
        audioPlayer?.play()
        isPlaying = true
        
        // Add notification to detect when playback ends
        NotificationCenter.default.addObserver(
            forName: .AVPlayerItemDidPlayToEndTime,
            object: audioPlayer?.currentItem,
            queue: .main
        ) { _ in
            self.isPlaying = false
            // Reset audio session when playback ends
            do {
                try AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
            } catch {
                print("❌ Failed to deactivate audio session: \(error)")
            }
        }
    }
    
    private func stopRecording() {
        print("🛑 Stopping recording")
        audioPlayer?.pause()
        audioPlayer = nil
        isPlaying = false
        
        // Reset audio session when manually stopped
        do {
            try AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
            print("🎵 Audio session deactivated")
        } catch {
            print("❌ Failed to deactivate audio session: \(error)")
        }
    }
}

#Preview {
    FrontDeskView(onToggleSidebar: nil)
}
