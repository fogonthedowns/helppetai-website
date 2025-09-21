//
//  DashboardView.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

// MARK: - 9. Views/DashboardView.swift
import SwiftUI

// MARK: - Supporting Types

enum AppointmentSheetMode {
    case simple
    case withTime(Date)
}

// MARK: - Simple New Appointment View

struct SimpleNewAppointmentView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject private var apiManager = APIManager.shared
    
    let selectedDate: Date
    let onComplete: () -> Void
    
    @State private var appointmentType = "checkup"
    @State private var appointmentTime: Date
    @State private var duration = 30
    @State private var isCreating = false
    @State private var showError = false
    @State private var errorMessage = ""
    
    // Data for appointment creation
    @State private var petOwners: [PetOwnerWithPets] = []
    @State private var selectedOwnerId: String = ""
    @State private var selectedPets: Set<String> = []
    @State private var isLoadingData = false
    
    // Computed property for selected owner
    private var selectedOwner: PetOwnerWithPets? {
        petOwners.first { $0.uuid == selectedOwnerId }
    }
    
    init(selectedDate: Date, onComplete: @escaping () -> Void) {
        self.selectedDate = selectedDate
        self.onComplete = onComplete
        self._appointmentTime = State(initialValue: Calendar.current.date(bySettingHour: 9, minute: 0, second: 0, of: selectedDate) ?? selectedDate)
    }
    
    var body: some View {
        NavigationView {
            Form {
                if isLoadingData {
                    Section {
                        HStack {
                            ProgressView()
                            Text("Loading...")
                        }
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding()
                    }
                } else {
                    Section("Appointment Type") {
                        Picker("Type", selection: $appointmentType) {
                            Text("Checkup").tag("checkup")
                            Text("Emergency").tag("emergency")
                            Text("Surgery").tag("surgery")
                            Text("Consultation").tag("consultation")
                        }
                        .pickerStyle(.menu)
                    }
                    
                    Section("Date & Time") {
                        DatePicker("Date & Time", selection: $appointmentTime)
                            .datePickerStyle(.compact)
                        
                        Picker("Duration", selection: $duration) {
                            Text("15 min").tag(15)
                            Text("30 min").tag(30)
                            Text("45 min").tag(45)
                            Text("60 min").tag(60)
                            Text("90 min").tag(90)
                            Text("120 min").tag(120)
                        }
                        .pickerStyle(.segmented)
                    }
                    
                    petOwnerSection
                    
                    Section {
                        Button(action: createAppointment) {
                            HStack {
                                if isCreating {
                                    ProgressView()
                                        .scaleEffect(0.8)
                                }
                                Text(isCreating ? "Creating..." : "Create Appointment")
                                    .fontWeight(.medium)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 8)
                        }
                        .disabled(!isFormValid || isCreating)
                        .buttonStyle(.borderedProminent)
                    }
                }
            }
            .navigationTitle("New Appointment")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .alert("Error", isPresented: $showError) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
            .onAppear {
                loadInitialData()
            }
        }
    }
    
    // MARK: - View Sections
    
    private var petOwnerSection: some View {
        Section("Pet Owner & Pets") {
            if petOwners.isEmpty {
                Text("No pet owners found")
                    .foregroundColor(.secondary)
            } else {
                Picker("Pet Owner", selection: $selectedOwnerId) {
                    Text("Select Owner").tag("")
                    ForEach(petOwners) { owner in
                        Text(owner.fullName).tag(owner.uuid)
                    }
                }
                .pickerStyle(.menu)
                .onChange(of: selectedOwnerId) { _ in
                    selectedPets.removeAll()
                }
                
                if let owner = selectedOwner, !owner.pets.isEmpty {
                    ForEach(owner.pets) { pet in
                        Toggle(isOn: Binding(
                            get: { selectedPets.contains(pet.id) },
                            set: { isSelected in
                                if isSelected {
                                    selectedPets.insert(pet.id)
                                } else {
                                    selectedPets.remove(pet.id)
                                }
                            }
                        )) {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(pet.name)
                                    .font(.headline)
                                Text("\(pet.species) • \(pet.breed ?? "Unknown breed")")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        .toggleStyle(CheckboxToggleStyle())
                    }
                }
            }
        }
    }
    
    
    // MARK: - Computed Properties
    
    private var generatedTitle: String {
        guard let owner = selectedOwner else { return "" }
        
        let petNames = owner.pets
            .filter { selectedPets.contains($0.id) }
            .map { $0.name }
            .joined(separator: ", ")
        
        let typeDisplayName = appointmentType.replacingOccurrences(of: "_", with: " ").capitalized
        
        return "\(petNames) \(typeDisplayName)"
    }
    
    private var isFormValid: Bool {
        !selectedOwnerId.isEmpty &&
        !selectedPets.isEmpty &&
        apiManager.currentUser?.practiceId != nil
    }
    
    // MARK: - Data Loading
    
    private func loadInitialData() {
        isLoadingData = true
        
        Task {
            await loadPetOwners()
        }
    }
    
    private func loadPetOwners() async {
        do {
            let owners = try await apiManager.getPetOwners()
            
            // Load pets for each owner
            var ownersWithPets: [PetOwnerWithPets] = []
            for owner in owners {
                let pets = try await apiManager.getPetsByOwner(ownerId: owner.uuid)
                ownersWithPets.append(PetOwnerWithPets(
                    uuid: owner.uuid,
                    fullName: owner.fullName,
                    email: owner.email,
                    phone: owner.phone,
                    pets: pets
                ))
            }
            
            await MainActor.run {
                self.petOwners = ownersWithPets
                self.isLoadingData = false
            }
        } catch {
            await MainActor.run {
                showErrorMessage("Failed to load pet owners: \(error.localizedDescription)")
                self.isLoadingData = false
            }
        }
    }
    
    
    // MARK: - Actions
    
    private func createAppointment() {
        guard let owner = selectedOwner,
              let practiceId = apiManager.currentUser?.practiceId,
              !selectedPets.isEmpty else {
            return
        }
        
        isCreating = true
        
        Task {
            do {
                let formatter = DateFormatter()
                formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
                formatter.timeZone = TimeZone.current
                
                print("🔍 Creating appointment:")
                print("🔍   Date: \(formatter.string(from: appointmentTime))")
                print("🔍   Duration: \(duration) min")
                print("🔍   Title: \(generatedTitle)")
                print("🔍   Pets: \(Array(selectedPets))")
                
                let request = CreateAppointmentRequest(
                    practiceId: practiceId,
                    petOwnerId: owner.uuid,
                    assignedVetUserId: apiManager.currentUser?.id,
                    petIds: Array(selectedPets),
                    appointmentDate: appointmentTime,
                    durationMinutes: duration,
                    appointmentType: appointmentType,
                    title: generatedTitle,
                    description: nil,
                    notes: nil
                )
                
                let createdAppointment = try await apiManager.createAppointment(request)
                print("✅ Appointment created successfully: \(createdAppointment.id)")
                print("✅   Created at: \(formatter.string(from: createdAppointment.appointmentDate))")
                
                await MainActor.run {
                    print("✅ Calling onComplete() to refresh dashboard...")
                    onComplete()
                    dismiss()
                }
            } catch {
                print("❌ Failed to create appointment: \(error)")
                await MainActor.run {
                    showErrorMessage("Failed to create appointment: \(error.localizedDescription)")
                    isCreating = false
                }
            }
        }
    }
    
    private func showErrorMessage(_ message: String) {
        errorMessage = message
        showError = true
    }
}

struct DashboardView: View {
    let onToggleSidebar: (() -> Void)?
    @ObservedObject private var apiManager = APIManager.shared
    @State private var dashboardData: DashboardResponse?
    @State private var appointmentCompletionStatus: [String: AppointmentStatus] = [:] // appointmentId -> status
    @State private var isLoading = true
    @State private var errorMessage = ""
    @State private var showError = false
    @State private var hideCompleted = false // Show all appointments by default
    @State private var selectedDate = Date() // Current selected date for navigation
    @State private var showNewAppointment = false // Show new appointment sheet
    @State private var showCalendarView = true // Default to calendar view
    @State private var newAppointmentTime: Date? = nil // Time selected from calendar long press
    @State private var selectedAppointment: Appointment? = nil // For navigation to appointment details
    @State private var appointmentSheetMode: AppointmentSheetMode = .simple // Track which sheet to show
    @State private var completionStatusTask: Task<Void, Never>? = nil // Track completion status task for cancellation
    
    
    // MARK: - Date Navigation Properties
    private var dateFormatter: DateFormatter {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        formatter.timeZone = TimeZone.current
        return formatter
    }
    
    private var displayDateFormatter: DateFormatter {
        let formatter = DateFormatter()
        formatter.dateFormat = "EEE, MMM d" // e.g., "Mon, Sep 7"
        formatter.timeZone = TimeZone.current
        return formatter
    }
    
    private var formattedSelectedDate: String {
        let formatted = dateFormatter.string(from: selectedDate)
        print("📅 Formatted selected date: \(formatted) from \(selectedDate)")
        return formatted
    }
    
    private var isToday: Bool {
        Calendar.current.isDate(selectedDate, inSameDayAs: Date())
    }
    
    // MARK: - Computed Properties for Correct Completion Logic
    private var correctCompletedCount: Int {
        guard let dashboard = dashboardData else { return 0 }
        
        return dashboard.appointmentsToday.filter { appointment in
            appointmentCompletionStatus[appointment.id] == .completed
        }.count
    }
    
    
    private var filteredAppointments: [Appointment] {
        guard let dashboard = dashboardData else { return [] }
        
        if hideCompleted {
            return dashboard.appointmentsToday.filter { appointment in
                appointmentCompletionStatus[appointment.id] != .completed
            }
        } else {
            return dashboard.appointmentsToday
        }
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Date navigation header
                dateNavigationHeader
                    .padding(.top, -8)
                
                // Main content
                ZStack {
                    if isLoading {
                        loadingView
                    } else if let dashboard = dashboardData {
                        if showCalendarView {
                            calendarContent(dashboard)
                        } else {
                            dashboardContent(dashboard)
                        }
                    } else {
                        emptyStateView
                    }
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
                    Text("HelpPetAI")
                        .font(.headline)
                        .fontWeight(.medium)
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        appointmentSheetMode = .simple
                        showNewAppointment = true
                    }) {
                        Image(systemName: "plus")
                            .font(.title3)
                            .foregroundColor(.blue)
                    }
                }
            }
            .alert("Error", isPresented: $showError) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
            .sheet(isPresented: $showNewAppointment) {
                switch appointmentSheetMode {
                case .simple:
                    SimpleNewAppointmentView(selectedDate: selectedDate) {
                        Task {
                            await loadDashboard()
                        }
                    }
                case .withTime(let appointmentTime):
                    NewAppointmentView(selectedDate: selectedDate, selectedTime: appointmentTime) {
                        Task {
                            await loadDashboard()
                        }
                    }
                }
            }
            .background(
                Group {
                    if selectedAppointment != nil {
                        NavigationLink(
                            destination: VisitRecordingView(appointment: selectedAppointment!),
                            isActive: Binding(
                                get: { selectedAppointment != nil },
                                set: { if !$0 { selectedAppointment = nil } }
                            )
                        ) {
                            EmptyView()
                        }
                        .hidden()
                    }
                }
            )
            .onAppear {
                loadCurrentUser()
            }
            .onDisappear {
                resetErrorStates()
                completionStatusTask?.cancel() // Cancel any running completion status task
            }
        }
    }
    
    // MARK: - View Components
    
    private var dateNavigationHeader: some View {
        HStack {
            Button(action: {
                let previousDay = Calendar.current.date(byAdding: .day, value: -1, to: selectedDate) ?? selectedDate
                navigateToDate(previousDay)
            }) {
                Image(systemName: "chevron.left")
                    .font(.title2)
                    .foregroundColor(.primary)
            }
            
            Spacer()
            
            VStack(spacing: 2) {
                VStack(spacing: 4) {
                    Text(isToday ? "Today" : displayDateFormatter.string(from: selectedDate))
                        .font(.headline)
                        .fontWeight(.medium)
                    
                    // Blue underline like Twitter
                    Rectangle()
                        .fill(Color.blue)
                        .frame(height: 2)
                        .frame(width: 40)
                }
                
                if !isToday {
                    Text("Tap to return to today")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                        .onTapGesture {
                            navigateToDate(Date())
                        }
                }
            }
            
            Spacer()
            
            Button(action: {
                let nextDay = Calendar.current.date(byAdding: .day, value: 1, to: selectedDate) ?? selectedDate
                navigateToDate(nextDay)
            }) {
                Image(systemName: "chevron.right")
                    .font(.title2)
                    .foregroundColor(.primary)
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 4)
        .background(Color(.systemGray6))
        .overlay(
            Rectangle()
                .frame(height: 0.5)
                .foregroundColor(Color(.separator)),
            alignment: .bottom
        )
    }
    
    
    private var loadingView: some View {
        ProgressView("Loading schedule...")
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .onAppear { print("📱 UI: Showing loading state") }
    }
    
    private var emptyStateView: some View {
        Text("No data available")
            .foregroundColor(.secondary)
            .onAppear {
                print("📱 UI: Showing 'No data available' - dashboardData is nil, isLoading = \(isLoading)")
            }
    }
    
    
    private func dashboardContent(_ dashboard: DashboardResponse) -> some View {
        ScrollView {
            VStack(spacing: 16) {
                if let currentAppointment = dashboard.currentAppointment {
                    CurrentAppointmentCard(appointment: currentAppointment)
                        .padding(.horizontal)
                }
                
                appointmentsSection
            }
            .padding(.vertical, 12)
            .onAppear {
                print("📱 UI: Showing dashboard with \(dashboard.appointmentsToday.count) appointments")
            }
        }
    }
    
    private func calendarContent(_ dashboard: DashboardResponse) -> some View {
        CalendarView(
            appointments: dashboard.appointmentsToday,
            selectedDate: selectedDate,
            onAppointmentTap: { appointment in
                // Navigate to appointment detail or recording view
                print("📅 Tapped appointment: \(appointment.title)")
                selectedAppointment = appointment
            },
            onLongPress: { time in
                // Set the selected time and show new appointment modal
                appointmentSheetMode = .withTime(time)
                showNewAppointment = true
            },
            onAppointmentMoved: { appointment, newTime in
                // Handle appointment time change
                Task {
                    await updateAppointmentTime(appointment: appointment, newTime: newTime)
                }
            },
            isScheduleEditingMode: .constant(false),
            vetAvailabilities: [],
            onAvailabilityTap: { _ in },
            onAvailabilityLongPress: { _ in },
            onAvailabilityMoved: { _, _ in }
        )
        .onAppear {
            print("📅 UI: Showing calendar with \(dashboard.appointmentsToday.count) appointments")
        }
        .onDisappear {
            // Reset the appointment mode when leaving calendar view
            appointmentSheetMode = .simple
        }
    }
    
    
    private var appointmentsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            scheduleHeader
            
            if filteredAppointments.isEmpty && hideCompleted && correctCompletedCount > 0 {
                completionMessage
            } else if filteredAppointments.isEmpty {
                noAppointmentsMessage
            } else {
                appointmentsList
            }
        }
    }
    
    private var scheduleHeader: some View {
        HStack {
            Text("Today's Schedule")
                .font(.headline)
            
            Spacer()
        }
        .padding(.horizontal)
    }
    
    
    private var completionMessage: some View {
        VStack(spacing: 8) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 36))
                .foregroundColor(.green)
            
            Text("All appointments completed!")
                .font(.headline)
                .foregroundColor(.secondary)
            
            Text("\(correctCompletedCount) completed appointment\(correctCompletedCount == 1 ? "" : "s") hidden")
                .font(.caption)
                .foregroundColor(Color(UIColor.tertiaryLabel))
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 16)
    }
    
    private var noAppointmentsMessage: some View {
        VStack(spacing: 8) {
            Image(systemName: "beach.umbrella")
                .font(.system(size: 36))
                .foregroundColor(.blue)
            
            Text("No appointments scheduled")
                .font(.headline)
                .foregroundColor(.secondary)
            
            Text("Enjoy your day off!")
                .font(.caption)
                .foregroundColor(Color(UIColor.tertiaryLabel))
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 16)
    }
    
    private var appointmentsList: some View {
        LazyVStack(spacing: 12) {
            ForEach(filteredAppointments) { appointment in
                AppointmentCard(
                    appointment: appointment,
                    status: appointmentCompletionStatus[appointment.id] ?? .scheduled
                ) {
                    Task {
                        await loadDashboard()
                    }
                }
                .padding(.horizontal)
            }
        }
    }
    
    private func resetErrorStates() {
        showError = false
        errorMessage = ""
        isLoading = false
    }
    
    private func loadCurrentUser() {
        Task {
            do {
                let user = try await apiManager.getCurrentUser()
                print("✅ User loaded successfully: \(user.username) (ID: \(user.id))")
                // After loading user, load the dashboard
                await loadDashboard()
            } catch {
                print("❌ Failed to load user: \(error)")
                await MainActor.run {
                    // Check if this is an authentication error or decoding error (which often means bad auth)
                    if let apiError = error as? APIError {
                        switch apiError {
                        case .unauthorized, .decodingError:
                            // User is not authenticated or token is invalid, trigger logout
                            print("🔐 User not authenticated or invalid token, logging out...")
                            self.isLoading = false // Stop loading first
                            apiManager.logout()
                            return // Don't show error - just logout
                        default:
                            break
                        }
                    }
                    
                    // For DecodingError (like missing "id" field), also logout
                    if error is DecodingError {
                        print("🔐 Token likely invalid (decoding error), logging out...")
                        self.isLoading = false // Stop loading first
                        apiManager.logout()
                        return // Don't show error - just logout
                    }
                    
                    // Only show error for non-auth related issues
                    self.errorMessage = "Failed to load user: \(error.localizedDescription)"
                    self.showError = true
                    self.isLoading = false
                }
            }
        }
    }
    
    private func loadDashboard() async {
        guard let userId = apiManager.currentUser?.id else {
            await MainActor.run {
                self.errorMessage = "User not loaded"
                self.showError = true
                self.isLoading = false
            }
            return
        }
        
        await MainActor.run {
            self.isLoading = true
        }
        
        do {
            let data = try await apiManager.getTodaySchedule(vetId: userId, date: formattedSelectedDate)
            print("📱 Dashboard data received for \(formattedSelectedDate): \(data.appointmentsToday.count) appointments")
            
            // Debug: Log all appointment details
            for appointment in data.appointmentsToday {
                let formatter = DateFormatter()
                formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
                formatter.timeZone = TimeZone.current
                print("📅 Appointment: \(appointment.title)")
                print("📅   Date: \(formatter.string(from: appointment.appointmentDate))")
                print("📅   Duration: \(appointment.durationMinutes) min")
                print("📅   Status: \(appointment.status.rawValue)")
                print("📅   Pets: \(appointment.pets.map { $0.name }.joined(separator: ", "))")
            }
            
            // Check completion status for each appointment
            completionStatusTask?.cancel() // Cancel any existing task
            completionStatusTask = Task {
                await checkAppointmentCompletionStatus(appointments: data.appointmentsToday)
            }
            await completionStatusTask?.value
            
            await MainActor.run {
                self.dashboardData = data
                self.isLoading = false
                print("📱 UI updated: dashboardData set, isLoading = false")
                print("📊 Completed appointments count: \(self.correctCompletedCount)")
            }
            
        } catch {
            print("📱 Dashboard load error: \(error)")
            await MainActor.run {
                self.errorMessage = error.localizedDescription
                self.showError = true
                self.isLoading = false
                print("📱 UI updated with error: \(error.localizedDescription)")
            }
        }
    }
    
    // MARK: - Date Navigation Methods
    private func navigateToDate(_ date: Date) {
        withAnimation(.easeInOut(duration: 0.3)) {
            selectedDate = date
        }

        Task {
            await loadDashboard()
        }
    }
    
    // MARK: - Appointment Update Methods
    private func updateAppointmentTime(appointment: Appointment, newTime: Date) async {
        print("🔄 Updating appointment \(appointment.title) to new time: \(newTime)")
        
        do {
            let updatedAppointment = try await apiManager.updateAppointmentDateTime(
                appointmentId: appointment.id,
                newDate: newTime
            )
            
            print("✅ Appointment time updated successfully")
            print("✅   Old time: \(appointment.appointmentDate)")
            print("✅   New time: \(updatedAppointment.appointmentDate)")
            
            // No longer need to refresh the dashboard - CalendarView handles optimistic updates
            // The next natural refresh (like switching dates) will sync the latest data
            
        } catch {
            print("❌ Failed to update appointment time: \(error)")
            await MainActor.run {
                self.errorMessage = "Failed to update appointment time: \(error.localizedDescription)"
                self.showError = true
            }
            
            // On error, refresh to revert optimistic changes
            await loadDashboard()
        }
    }
    
    // MARK: - Appointment Completion Logic
    private func checkAppointmentCompletionStatus(appointments: [Appointment]) async {
        // Use TaskGroup for concurrent execution instead of serial for loop
        await withTaskGroup(of: (String, AppointmentStatus).self) { group in
            var completionStatus: [String: AppointmentStatus] = [:]
            
            // Add tasks for each appointment
            for appointment in appointments {
                group.addTask {
                    let status = await self.calculateAppointmentStatus(appointment: appointment)
                    return (appointment.id, status)
                }
            }
            
            // Collect results as they complete
            for await (appointmentId, status) in group {
                completionStatus[appointmentId] = status
                
                // Find the appointment for logging
                if let appointment = appointments.first(where: { $0.id == appointmentId }) {
                    print("📊 Appointment \(appointment.title) (\(appointment.id)): \(status.displayName)")
                    print("📊   - Pets: \(appointment.pets.map { $0.name }.joined(separator: ", "))")
                }
            }
            
            await MainActor.run {
                self.appointmentCompletionStatus = completionStatus
            }
        }
    }
    
    private func calculateAppointmentStatus(appointment: Appointment) async -> AppointmentStatus {
        do {
            // Check for cancellation before making API call
            try Task.checkCancellation()
            
            // Get visit transcripts for this appointment using the new endpoint
            let visitTranscripts = try await apiManager.getVisitTranscriptsByAppointment(appointmentId: appointment.id)
            
            // Get local upload queue to check for recordings that haven't been uploaded yet
            let localUploads = MedicalRecordingManager.shared.uploadQueue.filter { 
                $0.metadata.appointmentId == appointment.id 
            }
            
            var allPetsHaveRecordings = true
            var allRecordingsProcessed = true
            
            print("📊   - Checking \(appointment.pets.count) pets for appointment \(appointment.title)")
            
            // Check EVERY pet in the appointment - ALL must have recordings
            for pet in appointment.pets {
                // Check for cancellation during processing
                try Task.checkCancellation()
                
                // Check server-side recordings
                let serverTranscript = visitTranscripts.first { $0.petId == pet.id }
                let petHasServerRecording = serverTranscript != nil && serverTranscript?.state != .failed
                
                // Check local recordings in upload queue
                let localUpload = localUploads.first { $0.metadata.petId == pet.id }
                let petHasLocalRecording = localUpload != nil && localUpload?.status != .failed
                
                if !petHasServerRecording && !petHasLocalRecording {
                    print("📊   - ❌ Pet \(pet.name) (\(pet.id)): NO recording (server or local) -> MISSING")
                    allPetsHaveRecordings = false
                    // Don't continue - we need to check all pets for debugging
                } else {
                    print("📊   - ✅ Pet \(pet.name) (\(pet.id)): HAS recording")
                    
                    if petHasServerRecording {
                        let transcriptState = serverTranscript?.state.rawValue ?? "none"
                        print("📊     → Server recording state: \(transcriptState)")
                        
                        // Only fully processed server recordings count as complete
                        if serverTranscript?.state != .processed {
                            allRecordingsProcessed = false
                            print("📊     → Not fully processed yet")
                        } else {
                            print("📊     → Fully processed ✅")
                        }
                    } else if petHasLocalRecording {
                        let uploadStatus = localUpload?.status.rawValue ?? "none"
                        print("📊     → Local recording upload status: \(uploadStatus)")
                        
                        // Local recordings are never fully processed yet
                        allRecordingsProcessed = false
                        print("📊     → Local recordings not processed yet")
                    }
                }
            }
            
            // Final status determination
            if !allPetsHaveRecordings {
                print("📊   - 🔄 RESULT: SCHEDULED (not all pets have recordings)")
                return .scheduled
            } else if allRecordingsProcessed {
                print("📊   - ✅ RESULT: COMPLETED (all pets have processed recordings)")
                return .completed
            } else {
                print("📊   - 🔄 RESULT: IN PROGRESS (all pets have recordings but not all processed)")
                return .inProgress
            }
            
        } catch {
            print("📊   - ⚠️ Error checking server status: \(error)")
            print("📊   - Falling back to local-only check for \(appointment.pets.count) pets")
            
            // If we can't check server, still check local uploads for ALL pets
            let localUploads = MedicalRecordingManager.shared.uploadQueue.filter { 
                $0.metadata.appointmentId == appointment.id 
            }
            
            var allPetsHaveLocalRecordings = true
            
            for pet in appointment.pets {
                // Check for cancellation during fallback processing
                do {
                    try Task.checkCancellation()
                } catch {
                    // Task was cancelled, return current status
                    print("📊   - ⚠️ Task cancelled during fallback processing")
                    return .scheduled
                }
                
                let petHasLocalRecording = localUploads.contains { upload in
                    upload.metadata.petId == pet.id && upload.status != .failed
                }
                
                if !petHasLocalRecording {
                    print("📊   - ❌ Pet \(pet.name) (\(pet.id)): NO local recording")
                    allPetsHaveLocalRecordings = false
                } else {
                    print("📊   - ✅ Pet \(pet.name) (\(pet.id)): HAS local recording")
                }
            }
            
            if !allPetsHaveLocalRecordings {
                print("📊   - 🔄 RESULT: SCHEDULED (not all pets have local recordings)")
                return .scheduled
            } else {
                print("📊   - 🔄 RESULT: IN PROGRESS (all pets have local recordings)")
                return .inProgress
            }
        }
    }
}
