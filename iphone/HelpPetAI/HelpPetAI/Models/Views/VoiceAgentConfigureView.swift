//
//  VoiceAgentConfigureView.swift
//  HelpPetAI
//
//  TL;DR: Settings view for managing voice agent configuration for the practice.
//
//  Features:
//  - Display current voice agent configuration
//  - Show agent metadata (agent ID, timezone, etc.)
//  - Allow setup of new voice agent if none exists
//  - Update voice agent settings
//
//  Usage: Navigate to from sidebar menu Configure button.
//

import SwiftUI

struct VoiceAgentConfigureView: View {
    @StateObject private var apiManager = APIManager.shared
    @State private var voiceAgent: VoiceAgentResponse?
    @State private var isLoading = true
    @State private var errorMessage: String?
    @State private var isCreatingAgent = false
    @State private var welcomeMessage = ""
    @State private var isUpdatingMessage = false
    @State private var showingMessageEditor = false
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            Group {
                if isLoading {
                    ProgressView("Loading voice agent configuration...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let error = errorMessage {
                    VStack(spacing: 20) {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.largeTitle)
                            .foregroundColor(.orange)
                        
                        Text("Error")
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Text(error)
                            .multilineTextAlignment(.center)
                            .foregroundColor(.secondary)
                        
                        Button("Retry") {
                            loadVoiceAgent()
                        }
                        .buttonStyle(.borderedProminent)
                    }
                    .padding()
                } else if let agent = voiceAgent {
                    // Voice agent exists - show configuration
                    voiceAgentConfiguredView(agent: agent)
                } else {
                    // No voice agent - show setup option
                    voiceAgentSetupView()
                }
            }
            .navigationTitle("Voice Agent")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .task {
            loadVoiceAgent()
        }
        .sheet(isPresented: $showingMessageEditor) {
            WelcomeMessageEditorView(
                currentMessage: welcomeMessage,
                isSaving: $isUpdatingMessage,
                onSave: { newMessage in
                    updateWelcomeMessage(newMessage)
                }
            )
        }
    }
    
    // MARK: - Voice Agent Configured View
    
    @ViewBuilder
    private func voiceAgentConfiguredView(agent: VoiceAgentResponse) -> some View {
        List {
            Section(header: Text("Voice Agent Information")) {
                VoiceAgentInfoRow(label: "Agent ID", value: agent.agentId)
                VoiceAgentInfoRow(label: "Status", value: agent.isActive ? "Active" : "Inactive")
                VoiceAgentInfoRow(label: "Timezone", value: agent.timezone)
                VoiceAgentInfoRow(label: "Last Updated", value: formatDate(agent.updatedAt))
            }
            
            Section(header: Text("Welcome Message")) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Current Message:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text(welcomeMessage.isEmpty ? "Loading..." : welcomeMessage)
                        .padding(12)
                        .background(Color(.systemGray6))
                        .cornerRadius(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .contentShape(Rectangle())
                        .onTapGesture {
                            showingMessageEditor = true
                        }
                    
                    Button(action: {
                        showingMessageEditor = true
                    }) {
                        HStack(spacing: 8) {
                            Image(systemName: isUpdatingMessage ? "clock" : "pencil")
                            Text(isUpdatingMessage ? "Updating..." : "Edit Welcome Message")
                            Spacer()
                            if isUpdatingMessage {
                                ProgressView()
                                    .scaleEffect(0.8)
                            }
                        }
                        .foregroundColor(isUpdatingMessage ? .orange : .blue)
                    }
                    .disabled(isUpdatingMessage)
                }
                .padding(.vertical, 4)
            }
            
            if !agent.metadata.isEmpty {
                Section(header: Text("Configuration Details")) {
                    ForEach(Array(agent.metadata.keys.sorted()), id: \.self) { key in
                        if let value = agent.metadata[key] {
                            VoiceAgentInfoRow(label: key.capitalized, value: "\(value)")
                        }
                    }
                }
            }
        }
    }
    
    // MARK: - Voice Agent Setup View
    
    @ViewBuilder
    private func voiceAgentSetupView() -> some View {
        VStack(spacing: 24) {
            Spacer()
            
            Image(systemName: "phone.badge.waveform")
                .font(.system(size: 60))
                .foregroundColor(.blue)
            
            VStack(spacing: 16) {
                Text("No Voice Agent Configured")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Text("Set up a voice agent to handle phone calls for your practice. The voice agent will help customers book appointments and answer common questions.")
                    .multilineTextAlignment(.center)
                    .foregroundColor(.secondary)
                    .padding(.horizontal)
            }
            
            Button(action: {
                createVoiceAgent()
            }) {
                HStack {
                    if isCreatingAgent {
                        ProgressView()
                            .scaleEffect(0.8)
                    } else {
                        Image(systemName: "plus.circle.fill")
                    }
                    Text(isCreatingAgent ? "Setting up..." : "Set Up Voice Agent")
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.blue)
                .foregroundColor(.white)
                .cornerRadius(12)
            }
            .disabled(isCreatingAgent)
            .padding(.horizontal)
            
            Spacer()
        }
    }
    
    // MARK: - Helper Methods
    
    private func loadVoiceAgent() {
        guard let practiceId = apiManager.currentUser?.practiceId else {
            errorMessage = "No practice associated with current user"
            isLoading = false
            return
        }
        
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let agent = try await apiManager.getVoiceAgent(practiceId: practiceId)
                await MainActor.run {
                    self.voiceAgent = agent
                    self.isLoading = false
                }
                
                // Load the actual current welcome message
                await loadWelcomeMessage(practiceId: practiceId)
            } catch {
                await MainActor.run {
                    if case APIError.notFound = error {
                        // No voice agent exists - this is expected
                        self.voiceAgent = nil
                    } else {
                        self.errorMessage = error.localizedDescription
                    }
                    self.isLoading = false
                }
            }
        }
    }
    
    private func createVoiceAgent() {
        guard let practiceId = apiManager.currentUser?.practiceId else {
            errorMessage = "No practice associated with current user"
            return
        }
        
        isCreatingAgent = true
        errorMessage = nil
        
        Task {
            do {
                let createRequest = VoiceAgentCreateRequest(
                    timezone: "US/Pacific", // Default timezone
                    metadata: [:]
                )
                
                let agent = try await apiManager.createVoiceAgent(
                    practiceId: practiceId,
                    request: createRequest
                )
                
                await MainActor.run {
                    self.voiceAgent = agent
                    self.isCreatingAgent = false
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isCreatingAgent = false
                }
            }
        }
    }
    
    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateStyle = .medium
            displayFormatter.timeStyle = .short
            return displayFormatter.string(from: date)
        }
        
        return dateString
    }
    
    private func loadWelcomeMessage(practiceId: String) async {
        do {
            let response = try await apiManager.getVoiceAgentNodeMessage(
                practiceId: practiceId,
                nodeName: "Welcome Node"
            )
            
            await MainActor.run {
                self.welcomeMessage = response.message
                print("✅ Loaded current welcome message: \(response.message.prefix(100))...")
            }
        } catch {
            await MainActor.run {
                // Set a fallback message if we can't load the current one
                self.welcomeMessage = "Unable to load current message"
                print("⚠️ Failed to load welcome message: \(error.localizedDescription)")
            }
        }
    }
    
    private func updateWelcomeMessage(_ newMessage: String) {
        guard let practiceId = apiManager.currentUser?.practiceId else {
            errorMessage = "No practice associated with current user"
            return
        }
        
        isUpdatingMessage = true
        errorMessage = nil
        
        Task {
            do {
                let response = try await apiManager.updateVoiceAgentNodeMessage(
                    practiceId: practiceId,
                    nodeName: "Welcome Node",
                    messageText: newMessage
                )
                
                await MainActor.run {
                    self.welcomeMessage = newMessage
                    self.isUpdatingMessage = false
                    self.showingMessageEditor = false
                    
                    print("✅ Welcome message updated successfully")
                    print("🔍 Response: \(response.message)")
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = "Failed to update welcome message: \(error.localizedDescription)"
                    self.isUpdatingMessage = false
                }
            }
        }
    }
}

// MARK: - Voice Agent Info Row Component

struct VoiceAgentInfoRow: View {
    let label: String
    let value: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
            Text(value)
                .fontWeight(.medium)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

// MARK: - Voice Agent Models

struct VoiceAgentResponse: Codable, Identifiable {
    let id: String
    let practiceId: String
    let agentId: String
    let timezone: String
    let metadata: [String: VoiceAgentAnyCodable]
    let isActive: Bool
    let createdAt: String
    let updatedAt: String
    
    enum CodingKeys: String, CodingKey {
        case id
        case practiceId = "practice_id"
        case agentId = "agent_id"
        case timezone
        case metadata
        case isActive = "is_active"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

struct VoiceAgentCreateRequest: Encodable {
    let timezone: String
    let metadata: [String: VoiceAgentAnyCodable]
}

struct VoiceAgentPersonalityRequest: Encodable {
    let personalityText: String
    
    enum CodingKeys: String, CodingKey {
        case personalityText = "personality_text"
    }
}

struct VoiceAgentPersonalityResponse: Codable {
    let success: Bool
    let message: String
    let agentId: String
    let conversationFlowId: String
    let currentVersion: Int
    let personalityTextLength: Int
    let note: String
    
    enum CodingKeys: String, CodingKey {
        case success
        case message
        case agentId = "agent_id"
        case conversationFlowId = "conversation_flow_id"
        case currentVersion = "current_version"
        case personalityTextLength = "personality_text_length"
        case note
    }
}

struct VoiceAgentNodeMessageResponse: Codable {
    let success: Bool
    let nodeName: String
    let message: String
    let agentId: String
    let conversationFlowId: String
    
    enum CodingKeys: String, CodingKey {
        case success
        case nodeName = "node_name"
        case message
        case agentId = "agent_id"
        case conversationFlowId = "conversation_flow_id"
    }
}

// MARK: - VoiceAgentAnyCodable Helper

struct VoiceAgentAnyCodable: Codable {
    let value: Any
    
    init(_ value: Any) {
        self.value = value
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        
        if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let array = try? container.decode([VoiceAgentAnyCodable].self) {
            value = array.map { $0.value }
        } else if let dictionary = try? container.decode([String: VoiceAgentAnyCodable].self) {
            value = dictionary.mapValues { $0.value }
        } else {
            value = NSNull()
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        
        switch value {
        case let bool as Bool:
            try container.encode(bool)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let string as String:
            try container.encode(string)
        case let array as [Any]:
            try container.encode(array.map(VoiceAgentAnyCodable.init))
        case let dictionary as [String: Any]:
            try container.encode(dictionary.mapValues(VoiceAgentAnyCodable.init))
        default:
            try container.encodeNil()
        }
    }
}

// MARK: - Welcome Message Editor

struct WelcomeMessageEditorView: View {
    @State private var messageText: String
    @Environment(\.dismiss) private var dismiss
    @Binding var isSaving: Bool
    let onSave: (String) -> Void
    
    init(currentMessage: String, isSaving: Binding<Bool>, onSave: @escaping (String) -> Void) {
        _messageText = State(initialValue: currentMessage)
        _isSaving = isSaving
        self.onSave = onSave
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Twitter-style header with HP avatar and info
                HStack(spacing: 12) {
                    // HP Avatar (blue circle)
                    ZStack {
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 50, height: 50)
                        
                        Text("HP")
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                    }
                    
                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 8) {
                            Text("Welcome Message")
                                .font(.headline)
                                .fontWeight(.bold)
                            
                            // Blue circle indicator
                            Circle()
                                .fill(Color.blue)
                                .frame(width: 8, height: 8)
                        }
                        
                        HStack(spacing: 4) {
                            Image(systemName: "globe")
                                .font(.caption)
                                .foregroundColor(.blue)
                            Text("Updates Voice Agent Immediately")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    Spacer()
                }
                .padding(.horizontal, 16)
                .padding(.top, 16)
                
                // Twitter-style text editor (no border, clean)
                TextEditor(text: $messageText)
                    .font(.body)
                    .padding(.horizontal, 16)
                    .padding(.top, 12)
                    .frame(minHeight: 200)
                    .background(Color.clear)
                    .scrollContentBackground(.hidden)
                
                Spacer()
            }
            .background(Color(.systemBackground))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .foregroundColor(.primary)
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        onSave(messageText)
                    }) {
                        HStack(spacing: 4) {
                            if isSaving {
                                ProgressView()
                                    .scaleEffect(0.8)
                                    .tint(.white)
                            }
                            Text(isSaving ? "Updating..." : "Update")
                        }
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(
                            RoundedRectangle(cornerRadius: 20)
                                .fill(messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSaving ? Color.blue.opacity(0.5) : Color.blue)
                        )
                    }
                    .disabled(messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSaving)
                }
            }
        }
    }
}

#Preview {
    VoiceAgentConfigureView()
}
