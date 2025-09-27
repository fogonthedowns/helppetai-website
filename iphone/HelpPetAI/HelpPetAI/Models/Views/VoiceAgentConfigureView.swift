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
    @State private var showingPhoneConfig = false
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
        .listStyle(.insetGrouped)
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
        .sheet(isPresented: $showingPhoneConfig) {
            if let agent = voiceAgent,
               let practiceId = apiManager.currentUser?.practiceId {
                PhoneConfigurationView(
                    practiceId: practiceId,
                    agentId: agent.id,
                    onPhoneConfigured: {
                        // Refresh the voice agent data after phone configuration
                        Task {
                            await loadVoiceAgent()
                        }
                    }
                )
            }
        }
    }
    
    // MARK: - Voice Agent Configured View
    
    @ViewBuilder
    private func voiceAgentConfiguredView(agent: VoiceAgentResponse) -> some View {
        List {
            // Show pricing info if no phone number is configured
            if agent.phoneNumber == nil || agent.phoneNumber?.isEmpty == true {
                Section {
                    VStack(spacing: 16) {
                        // Header with checkmark and "Pay As You Go" in compact light blue rounded box
                        HStack {
                            HStack {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.blue)
                                    .font(.system(size: 14, weight: .medium))
                                Text("Pay As You Go")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(.blue)
                            }
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(Color.blue.opacity(0.1))
                            )
                            Spacer()
                        }
                        
                        // Upcoming Invoice row
                        HStack {
                            Text("Credits:")
                                .font(.system(size: 16))
                                .foregroundColor(.primary)
                            Spacer()
                            Text("$10.00 💰")
                                .font(.system(size: 16, weight: .medium))
                                .foregroundColor(.primary)
                            Image(systemName: "info.circle")
                                .foregroundColor(.secondary)
                                .font(.system(size: 14))
                        }
                        
                        // Concurrency Used row
                        HStack {
                            Text("Phone Numbers Used:")
                                .font(.system(size: 16))
                                .foregroundColor(.primary)
                            Spacer()
                            Text("0/1")
                                .font(.system(size: 16, weight: .medium))
                                .foregroundColor(.primary)
                            Image(systemName: "info.circle")
                                .foregroundColor(.secondary)
                                .font(.system(size: 14))
                        }
                    }
                    .padding(.all, 20)
                }
                .listRowBackground(
                    RoundedRectangle(cornerRadius: 16)
                        .fill(Color(.systemBackground))
                        .shadow(color: .black.opacity(0.08), radius: 8, x: 0, y: 2)
                )
                .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
            }
            
            Section(header: 
                HStack {
                    Text("Voice Agent")
                    Spacer()
                    // Status chip - green if active, gray if disabled
                    HStack(spacing: 4) {
                        Circle()
                            .fill(agent.isActive ? Color.green : Color.gray)
                            .frame(width: 8, height: 8)
                        Text(agent.isActive ? "Active" : "Inactive")
                            .font(.caption)
                            .foregroundColor(agent.isActive ? .green : .gray)
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(agent.isActive ? Color.green.opacity(0.1) : Color.gray.opacity(0.1))
                    )
                }
            ) {
                VoiceAgentInfoRow(
                    label: "Phone Number", 
                    value: formatPhoneNumber(agent.phoneNumber) ?? ""
                )
                
                // Show Configure Phone Number button if no phone number exists
                if agent.phoneNumber == nil || agent.phoneNumber?.isEmpty == true {
                    Button(action: {
                        showingPhoneConfig = true
                    }) {
                        HStack {
                            Text("Configure Phone Number")
                            Spacer()
                        }
                        .foregroundColor(.blue)
                        .padding(.vertical, 8)
                    }
                }
                
                VoiceAgentInfoRow(label: "Timezone", value: agent.timezone)
                VoiceAgentInfoRow(label: "Last Updated", value: formatDate(agent.updatedAt))
            }
            
            Section {
                Rectangle()
                    .fill(Color.secondary.opacity(0.3))
                    .frame(height: 0.5)
            }
            .listRowInsets(EdgeInsets())
            .listRowBackground(Color.clear)
            .listSectionSpacing(.compact)
            
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
                        HStack {
                            if isUpdatingMessage {
                                ProgressView()
                                    .scaleEffect(0.8)
                                    .tint(.white)
                                Text("Updating...")
                                    .foregroundColor(.white)
                            } else {
                                Text("Edit")
                                    .foregroundColor(.white)
                            }
                        }
                        .padding(.horizontal, 20)
                        .padding(.vertical, 10)
                        .background(
                            RoundedRectangle(cornerRadius: 20)
                                .fill(isUpdatingMessage ? Color.orange : Color.blue)
                        )
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
    
    private func formatPhoneNumber(_ phoneNumber: String?) -> String? {
        guard let phone = phoneNumber else { return nil }
        
        // Remove all non-digit characters
        let digits = phone.replacingOccurrences(of: "[^0-9]", with: "", options: .regularExpression)
        
        // Format as (123) 123-1234 for US numbers
        if digits.count == 10 {
            let areaCode = String(digits.prefix(3))
            let exchange = String(digits.dropFirst(3).prefix(3))
            let number = String(digits.suffix(4))
            return "(\(areaCode)) \(exchange)-\(number)"
        } else if digits.count == 11 && digits.hasPrefix("1") {
            // Handle +1 country code
            let withoutCountryCode = String(digits.dropFirst())
            let areaCode = String(withoutCountryCode.prefix(3))
            let exchange = String(withoutCountryCode.dropFirst(3).prefix(3))
            let number = String(withoutCountryCode.suffix(4))
            return "(\(areaCode)) \(exchange)-\(number)"
        } else {
            // Return original if not standard US format
            return phone
        }
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
    let phoneNumber: String?
    
    enum CodingKeys: String, CodingKey {
        case id
        case practiceId = "practice_id"
        case agentId = "agent_id"
        case timezone
        case metadata
        case isActive = "is_active"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case phoneNumber = "phone_number"
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

// MARK: - Phone Configuration View

struct PhoneConfigurationView: View {
    let practiceId: String
    let agentId: String
    let onPhoneConfigured: () -> Void
    
    @State private var selectedAreaCode = ""
    @State private var isTollFree = false
    @State private var nickname = ""
    @State private var isConfiguring = false
    @State private var errorMessage: String?
    @Environment(\.dismiss) private var dismiss
    @StateObject private var apiManager = APIManager.shared
    
    // Common US area codes
    private let areaCodes = [
        "212", "213", "214", "215", "216", "217", "218", "219",
        "224", "225", "228", "229", "231", "234", "239", "240",
        "248", "251", "252", "253", "254", "256", "260", "262",
        "267", "269", "270", "276", "281", "301", "302", "303",
        "304", "305", "307", "308", "309", "310", "312", "313",
        "314", "315", "316", "317", "318", "319", "320", "321",
        "323", "325", "330", "331", "334", "336", "337", "339",
        "347", "351", "352", "360", "361", "386", "401", "402",
        "404", "405", "406", "407", "408", "409", "410", "412",
        "413", "414", "415", "417", "419", "423", "424", "425",
        "430", "432", "434", "435", "440", "442", "443", "458",
        "469", "470", "475", "478", "479", "480", "484", "501",
        "502", "503", "504", "505", "507", "508", "509", "510",
        "512", "513", "515", "516", "517", "518", "520", "530",
        "540", "541", "551", "559", "561", "562", "563", "564",
        "567", "570", "571", "573", "574", "575", "580", "585",
        "586", "601", "602", "603", "605", "606", "607", "608",
        "609", "610", "612", "614", "615", "616", "617", "618",
        "619", "620", "623", "626", "628", "629", "630", "631",
        "636", "641", "646", "650", "651", "657", "660", "661",
        "662", "667", "678", "681", "682", "701", "702", "703",
        "704", "706", "707", "708", "712", "713", "714", "715",
        "716", "717", "718", "719", "720", "724", "725", "727",
        "731", "732", "734", "737", "740", "747", "754", "757",
        "760", "762", "763", "765", "770", "772", "773", "774",
        "775", "781", "785", "786", "801", "802", "803", "804",
        "805", "806", "808", "810", "812", "813", "814", "815",
        "816", "817", "818", "828", "830", "831", "832", "843",
        "845", "847", "848", "850", "856", "857", "858", "859",
        "860", "862", "863", "864", "865", "870", "872", "878",
        "901", "903", "904", "906", "907", "908", "909", "910",
        "912", "913", "914", "915", "916", "917", "918", "919",
        "920", "925", "928", "929", "931", "934", "936", "937",
        "940", "941", "947", "949", "951", "952", "954", "956",
        "959", "970", "971", "972", "973", "978", "979", "980",
        "984", "985", "989"
    ]
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Phone Number Configuration")) {
                    // Toll-free toggle
                    Toggle("Toll-Free Number", isOn: $isTollFree)
                        .onChange(of: isTollFree) { _ in
                            if isTollFree {
                                selectedAreaCode = "" // Clear area code for toll-free
                            }
                        }
                    
                    // Area code picker (only show if not toll-free)
                    if !isTollFree {
                        Picker("Area Code", selection: $selectedAreaCode) {
                            Text("Select Area Code").tag("")
                            ForEach(areaCodes, id: \.self) { code in
                                Text(code).tag(code)
                            }
                        }
                        .pickerStyle(MenuPickerStyle())
                    }
                    
                    // Nickname field
                    TextField("Nickname (optional)", text: $nickname)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                }
                
                Section(header: Text("Pricing Information")) {
                    VStack(alignment: .leading, spacing: 4) {
                        if isTollFree {
                            Text("Toll-Free: $12/month")
                                .font(.body)
                                .foregroundColor(.primary)
                        } else {
                            Text("Regular Line: $3/month")
                                .font(.body)
                                .foregroundColor(.primary)
                        }
                        
                        Text("Plus 20¢/minute for calls")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding(.vertical, 4)
                }
                
                if let errorMessage = errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .font(.caption)
                    }
                }
            }
            .navigationTitle("Configure Phone")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        Task {
                            await configurePhoneNumber()
                        }
                    }) {
                        if isConfiguring {
                            HStack {
                                ProgressView()
                                    .scaleEffect(0.8)
                                Text("Configuring...")
                            }
                        } else {
                            Text("Configure")
                        }
                    }
                    .disabled(isConfiguring || (!isTollFree && selectedAreaCode.isEmpty))
                }
            }
        }
    }
    
    private func configurePhoneNumber() async {
        isConfiguring = true
        errorMessage = nil
        
        do {
            let areaCode = isTollFree ? nil : Int(selectedAreaCode)
            let finalNickname = nickname.isEmpty ? nil : nickname
            
            let response = try await apiManager.registerPhoneNumber(
                practiceId: practiceId,
                agentId: agentId,
                areaCode: areaCode,
                tollFree: isTollFree,
                nickname: finalNickname
            )
            
            print("✅ Phone number configured successfully: \(response)")
            
            // Call the completion handler
            onPhoneConfigured()
            
            // Dismiss the sheet
            dismiss()
            
        } catch {
            print("❌ Failed to configure phone number: \(error)")
            errorMessage = "Failed to configure phone number. Please try again."
        }
        
        isConfiguring = false
    }
}

#Preview {
    VoiceAgentConfigureView()
}
