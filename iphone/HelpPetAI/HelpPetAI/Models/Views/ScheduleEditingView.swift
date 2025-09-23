//
//  ScheduleEditingView.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/12/25.
//

import SwiftUI

struct ScheduleEditingView: View {
    let onToggleSidebar: (() -> Void)?
    @ObservedObject private var apiManager = APIManager.shared
    @State private var vetAvailabilities: [VetAvailability] = []
    @State private var selectedDate: Date = {
        let calendar = Calendar.current
        let now = Date()
        // Ensure we get today's date at midnight in local timezone
        return calendar.startOfDay(for: now)
    }()
    @State private var isLoading = true
    @State private var errorMessage = ""
    @State private var showError = false
    @State private var showNewAvailability = false
    @State private var newAvailabilityTime: Date? = nil
    @State private var editingAvailability: VetAvailability? = nil
    @State private var loadingTask: Task<Void, Never>? = nil
    
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
        print("📅 DEBUG formattedSelectedDate: \(formatted) from \(selectedDate)")
        print("📅 DEBUG timezone: \(TimeZone.current.identifier)")
        return formatted
    }
    
    private var isToday: Bool {
        Calendar.current.isDate(selectedDate, inSameDayAs: Date())
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Date navigation header
                dateNavigationHeader
                    .padding(.top, -8)
                
                // Main content
                ZStack {
                    if isLoading && vetAvailabilities.isEmpty {
                        loadingView
                    } else {
                        scheduleCalendarContent
                    }
                }
                .refreshable {
                    await refreshAvailabilities()
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
                    Text("Edit Schedule")
                        .font(.headline)
                        .fontWeight(.medium)
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        showNewAvailability = true
                    }) {
                        Image(systemName: "plus")
                            .font(.title3)
                            .foregroundColor(.blue)
                    }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .alert("Error", isPresented: $showError) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
            .sheet(isPresented: $showNewAvailability) {
                NewAvailabilityView(
                    selectedDate: selectedDate,
                    preselectedTime: newAvailabilityTime,
                    onComplete: {
                        Task {
                            await loadVetAvailabilities()
                        }
                    }
                )
            }
            .sheet(item: $editingAvailability) { availability in
                EditAvailabilityView(
                    availability: availability,
                    onComplete: {
                        Task {
                            await loadVetAvailabilities()
                        }
                    },
                    onDelete: {
                        Task {
                            await deleteAvailability(availability)
                        }
                    }
                )
                .onAppear {
                    print("📅 DEBUG: Edit sheet opened for availability: \(availability.id)")
                }
            }
        }
        .onAppear {
            // Wait for user to be loaded before loading availabilities
            if apiManager.currentUser != nil {
                loadAvailabilitiesSafely()
            } else {
                // User not loaded yet, wait and retry
                Task {
                    await waitForUserAndLoad()
                }
            }
        }
        .onChange(of: selectedDate) { _, _ in
            loadAvailabilitiesSafely()
        }
        .onDisappear {
            loadingTask?.cancel()
        }
        .onChange(of: apiManager.currentUser) { oldUser, newUser in
            // When user gets loaded, load availabilities
            if oldUser == nil && newUser != nil {
                print("📅 User loaded, now loading availabilities")
                loadAvailabilitiesSafely()
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
                    
                    // Orange underline for schedule editing
                    Rectangle()
                        .fill(Color.orange)
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
        VStack(spacing: 20) {
            if !errorMessage.isEmpty {
                // Error state
                VStack(spacing: 16) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 48))
                        .foregroundColor(.orange)
                    
                    Text("Failed to load schedule")
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    Text(errorMessage)
                        .font(.body)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                    
                    Button("Retry") {
                        loadAvailabilitiesSafely()
                    }
                    .buttonStyle(.borderedProminent)
                }
            } else {
                // Loading state
                VStack(spacing: 16) {
                    ProgressView()
                        .scaleEffect(1.2)
                    Text("Loading schedule...")
                        .font(.body)
                        .foregroundColor(.secondary)
                }
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    private var scheduleCalendarContent: some View {
        ZStack {
            CalendarView(
                appointments: [], // No appointments in schedule view
                selectedDate: selectedDate,
                onAppointmentTap: { _ in },
                onLongPress: { _ in },
                onAppointmentMoved: { _, _ in },
                isScheduleEditingMode: .constant(true), // Always in schedule editing mode
                vetAvailabilities: vetAvailabilities,
            onAvailabilityTap: { availability in
                print("📅 Tapped availability: \(availability.availabilityType.rawValue)")
                print("📅 DEBUG: Setting editingAvailability to: \(availability.id)")
                editingAvailability = availability
                print("📅 DEBUG: editingAvailability set: \(editingAvailability?.id ?? "nil")")
            },
                onAvailabilityLongPress: { time in
                    print("📅 Long pressed for availability at: \(time)")
                    newAvailabilityTime = time
                    showNewAvailability = true
                },
                onAvailabilityMoved: { availability, newTime in
                    print("📅 Moved availability to: \(newTime)")
                    Task {
                        await updateAvailabilityTime(availability: availability, newTime: newTime)
                    }
                }
            )
            .onAppear {
                print("📅 UI: Showing schedule calendar with \(vetAvailabilities.count) availabilities")
            }
            
            // Loading overlay when refreshing
            if isLoading && !vetAvailabilities.isEmpty {
                VStack {
                    HStack {
                        Spacer()
                        HStack(spacing: 8) {
                            ProgressView()
                                .scaleEffect(0.8)
                            Text("Refreshing...")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(
                            RoundedRectangle(cornerRadius: 16)
                                .fill(.ultraThinMaterial)
                        )
                        .padding(.trailing, 20)
                        .padding(.top, 20)
                    }
                    Spacer()
                }
            }
        }
    }
    
    // MARK: - Date Navigation Methods
    private func navigateToDate(_ date: Date) {
        withAnimation(.easeInOut(duration: 0.3)) {
            selectedDate = date
        }
        
        loadAvailabilitiesSafely()
    }
    
    private func loadAvailabilitiesSafely() {
        // Cancel any existing loading task to prevent race conditions
        loadingTask?.cancel()
        
        loadingTask = Task {
            // Small delay to ensure UI is ready
            try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 seconds
            
            if !Task.isCancelled {
                await loadVetAvailabilities()
            }
        }
    }
    
    private func waitForUserAndLoad() async {
        print("📅 Waiting for user to be loaded...")
        
        // Wait up to 5 seconds for user to be loaded
        for attempt in 0..<50 {
            if Task.isCancelled {
                print("📅 Wait for user task was cancelled")
                return
            }
            
            if apiManager.currentUser != nil {
                print("📅 User found after \(attempt * 100)ms, loading availabilities")
                await loadVetAvailabilities()
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
    
    private func refreshAvailabilities() async {
        print("🔄 Refreshing availabilities...")
        // Cancel any existing loading task
        loadingTask?.cancel()
        await loadVetAvailabilities()
    }
    
    private func deleteAvailability(_ availability: VetAvailability) async {
        print("🗑️ Deleting availability: \(availability.id)")
        
        do {
            try await apiManager.deleteVetAvailability(availabilityId: availability.id)
            
            await MainActor.run {
                // Remove from local state
                self.vetAvailabilities.removeAll { $0.id == availability.id }
                self.editingAvailability = nil
            }
            
            print("✅ Availability deleted successfully")
        } catch {
            print("❌ Failed to delete availability: \(error)")
            await MainActor.run {
                self.errorMessage = "Failed to delete availability: \(error.localizedDescription)"
                self.showError = true
            }
        }
    }
    
    // MARK: - Availability Management
    
    private func updateAvailabilityTime(availability: VetAvailability, newTime: Date) async {
        print("🔄 Updating availability to new time: \(newTime)")
        
        let calendar = Calendar.current
        let duration = availability.endTime.timeIntervalSince(availability.startTime)
        let newEndTime = newTime.addingTimeInterval(duration)
        
        let timeFormatter = DateFormatter()
        timeFormatter.dateFormat = "HH:mm:ss"
        timeFormatter.timeZone = TimeZone.current  // ✅ Use local timezone, let backend handle UTC conversion
        
        let request = UpdateVetAvailabilityRequest(
            startTime: timeFormatter.string(from: newTime),
            endTime: timeFormatter.string(from: newEndTime),
            availabilityType: availability.availabilityType,
            notes: nil,
            isActive: true
        )
        
        do {
            let updatedAvailability = try await apiManager.updateVetAvailability(
                availabilityId: availability.id,
                request: request
            )
            
            print("✅ Availability time updated successfully")
            
            // Update local state
            if let index = vetAvailabilities.firstIndex(where: { $0.id == availability.id }) {
                vetAvailabilities[index] = updatedAvailability
            }
            
        } catch {
            print("❌ Failed to update availability time: \(error)")
            await MainActor.run {
                self.errorMessage = "Failed to update availability time: \(error.localizedDescription)"
                self.showError = true
            }
        }
    }
    
    private func loadVetAvailabilities() async {
        // Double-check we haven't been cancelled
        guard !Task.isCancelled else {
            print("📅 Loading task was cancelled")
            return
        }
        
        guard let currentUser = apiManager.currentUser else {
            print("❌ No current user found for loading availabilities")
            await MainActor.run {
                self.errorMessage = "User not authenticated"
                self.showError = true
                self.isLoading = false
            }
            return
        }
        
        print("📅 Starting to load availabilities for user: \(currentUser.id), date: \(selectedDate)")
        
        await MainActor.run {
            self.isLoading = true
            self.errorMessage = ""
        }
        
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        dateFormatter.timeZone = TimeZone.current
        
        let formattedDate = dateFormatter.string(from: selectedDate)
        print("📅 DEBUG: selectedDate = \(selectedDate)")
        print("📅 DEBUG: formattedDate = \(formattedDate)")
        print("📅 DEBUG: Current timezone = \(TimeZone.current)")
        
        do {
            // Check again if we've been cancelled before making the API call
            guard !Task.isCancelled else {
                print("📅 Loading task was cancelled before API call")
                return
            }
            
            let availabilities = try await apiManager.getVetAvailability(
                vetUserId: currentUser.id,
                date: formattedDate
            )
            
            // Final check before updating UI
            guard !Task.isCancelled else {
                print("📅 Loading task was cancelled after API call")
                return
            }
            
            await MainActor.run {
                self.vetAvailabilities = availabilities
                self.isLoading = false
                print("✅ UI Updated: Loaded \(availabilities.count) availabilities for \(self.selectedDate)")
            }
            
        } catch {
            guard !Task.isCancelled else {
                print("📅 Loading task was cancelled during error handling")
                return
            }
            
            print("❌ Failed to load vet availabilities: \(error)")
            await MainActor.run {
                self.errorMessage = "Failed to load schedule: \(error.localizedDescription)"
                self.showError = true
                self.isLoading = false
            }
        }
    }
}

// MARK: - New Availability Sheet

struct NewAvailabilityView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject private var apiManager = APIManager.shared
    
    let selectedDate: Date
    let preselectedTime: Date?
    let onComplete: () -> Void
    
    @State private var startTime: Date
    @State private var endTime: Date
    @State private var availabilityType: AvailabilityType = .available
    @State private var isCreating = false
    @State private var showError = false
    @State private var errorMessage = ""
    
    init(selectedDate: Date, preselectedTime: Date? = nil, onComplete: @escaping () -> Void) {
        self.selectedDate = selectedDate
        self.preselectedTime = preselectedTime
        self.onComplete = onComplete
        
        let defaultTime = preselectedTime ?? Calendar.current.date(bySettingHour: 9, minute: 0, second: 0, of: selectedDate) ?? selectedDate
        let defaultEndTime = Calendar.current.date(byAdding: .hour, value: 1, to: defaultTime) ?? defaultTime
        
        self._startTime = State(initialValue: defaultTime)
        self._endTime = State(initialValue: defaultEndTime)
    }
    
    
    var body: some View {
        NavigationView {
            Form {
                Section("Time") {
                    DatePicker("Start Time", selection: $startTime, displayedComponents: .hourAndMinute)
                        .onChange(of: startTime) { oldValue, newValue in
                            // Auto-adjust end time to maintain at least 1 hour duration
                            let minimumEndTime = Calendar.current.date(byAdding: .hour, value: 1, to: newValue) ?? newValue
                            if endTime < minimumEndTime {
                                endTime = minimumEndTime
                            }
                        }
                    DatePicker("End Time", selection: $endTime, displayedComponents: .hourAndMinute)
                }
                
                Section("Availability Type") {
                    VStack(spacing: 12) {
                        ForEach(AvailabilityType.allCases, id: \.self) { type in
                            Button(action: {
                                availabilityType = type
                            }) {
                                HStack(spacing: 12) {
                                    Image(systemName: type.systemIcon)
                                        .font(.system(size: 16, weight: .medium))
                                        .foregroundColor(type.color)
                                        .frame(width: 24)
                                    
                                    Text(type.displayName)
                                        .font(.system(size: 16, weight: .medium))
                                        .foregroundColor(.primary)
                                    
                                    Spacer()
                                    
                                    if availabilityType == type {
                                        Image(systemName: "checkmark.circle.fill")
                                            .foregroundColor(.blue)
                                    } else {
                                        Image(systemName: "circle")
                                            .foregroundColor(.secondary)
                                    }
                                }
                                .padding(.vertical, 8)
                                .padding(.horizontal, 12)
                                .background(
                                    RoundedRectangle(cornerRadius: 8)
                                        .fill(availabilityType == type ? type.color.opacity(0.1) : Color.clear)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 8)
                                                .stroke(availabilityType == type ? type.color : Color.clear, lineWidth: 1)
                                        )
                                )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
                
                Section("Date") {
                    HStack {
                        Text("Date")
                        Spacer()
                        Text(selectedDate.formatted(date: .abbreviated, time: .omitted))
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("New Availability")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        Task {
                            await createAvailability()
                        }
                    }
                    .disabled(isCreating || endTime <= startTime)
                }
            }
            .alert("Error", isPresented: $showError) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
        }
    }
    
    private func createAvailability() async {
        guard let currentUser = apiManager.currentUser else {
            await MainActor.run {
                self.errorMessage = "No current user found"
                self.showError = true
            }
            return
        }
        
        await MainActor.run {
            self.isCreating = true
        }
        
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        dateFormatter.timeZone = TimeZone.current
        
        let timeFormatter = DateFormatter()
        timeFormatter.dateFormat = "HH:mm:ss"
        timeFormatter.timeZone = TimeZone.current  // ✅ Use local timezone, let backend handle UTC conversion
        
        let deviceTimezone = TimeZone.current.identifier
        print("🌍 Creating availability with device timezone: \(deviceTimezone)")
        print("📅 Local date: \(dateFormatter.string(from: selectedDate))")
        print("⏰ Local times: \(timeFormatter.string(from: startTime)) - \(timeFormatter.string(from: endTime))")
        
        let request = CreateVetAvailabilityRequest(
            vetUserId: currentUser.id,
            practiceId: currentUser.practiceId ?? "",
            date: dateFormatter.string(from: selectedDate),
            startTime: timeFormatter.string(from: startTime),
            endTime: timeFormatter.string(from: endTime),
            availabilityType: availabilityType,
            timezone: deviceTimezone
        )
        
        do {
            let _ = try await apiManager.createVetAvailability(request)
            
            await MainActor.run {
                self.isCreating = false
                self.onComplete()
                self.dismiss()
            }
            
            print("✅ Created availability successfully")
        } catch {
            print("❌ Failed to create availability: \(error)")
            await MainActor.run {
                self.isCreating = false
                self.errorMessage = "Failed to create availability: \(error.localizedDescription)"
                self.showError = true
            }
        }
    }
}

// MARK: - Edit Availability Sheet

struct EditAvailabilityView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject private var apiManager = APIManager.shared
    
    let availability: VetAvailability
    let onComplete: () -> Void
    let onDelete: () -> Void
    
    @State private var startTime: Date
    @State private var endTime: Date
    @State private var availabilityType: AvailabilityType
    @State private var notes: String
    @State private var isActive: Bool
    @State private var isUpdating = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var showDeleteConfirmation = false
    
    init(availability: VetAvailability, onComplete: @escaping () -> Void, onDelete: @escaping () -> Void) {
        self.availability = availability
        self.onComplete = onComplete
        self.onDelete = onDelete
        
        self._startTime = State(initialValue: availability.startTime)
        self._endTime = State(initialValue: availability.endTime)
        self._availabilityType = State(initialValue: availability.availabilityType)
        self._notes = State(initialValue: "") // We'll need to add this field to VetAvailability
        self._isActive = State(initialValue: true) // We'll need to add this field to VetAvailability
    }
    
    
    var body: some View {
        NavigationView {
            Form {
                Section("Time") {
                    DatePicker("Start Time", selection: $startTime, displayedComponents: .hourAndMinute)
                        .onChange(of: startTime) { oldValue, newValue in
                            // Auto-adjust end time to maintain at least 1 hour duration
                            let minimumEndTime = Calendar.current.date(byAdding: .hour, value: 1, to: newValue) ?? newValue
                            if endTime < minimumEndTime {
                                endTime = minimumEndTime
                            }
                        }
                    DatePicker("End Time", selection: $endTime, displayedComponents: .hourAndMinute)
                }
                
                Section("Availability Type") {
                    VStack(spacing: 12) {
                        ForEach(AvailabilityType.allCases, id: \.self) { type in
                            Button(action: {
                                availabilityType = type
                            }) {
                                HStack(spacing: 12) {
                                    Image(systemName: type.systemIcon)
                                        .font(.system(size: 16, weight: .medium))
                                        .foregroundColor(type.color)
                                        .frame(width: 24)
                                    
                                    Text(type.displayName)
                                        .font(.system(size: 16, weight: .medium))
                                        .foregroundColor(.primary)
                                    
                                    Spacer()
                                    
                                    if availabilityType == type {
                                        Image(systemName: "checkmark.circle.fill")
                                            .foregroundColor(.blue)
                                    } else {
                                        Image(systemName: "circle")
                                            .foregroundColor(.secondary)
                                    }
                                }
                                .padding(.vertical, 8)
                                .padding(.horizontal, 12)
                                .background(
                                    RoundedRectangle(cornerRadius: 8)
                                        .fill(availabilityType == type ? type.color.opacity(0.1) : Color.clear)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 8)
                                                .stroke(availabilityType == type ? type.color : Color.clear, lineWidth: 1)
                                        )
                                )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
                
                Section("Notes") {
                    TextField("Optional notes", text: $notes, axis: .vertical)
                        .lineLimit(3...6)
                }
                
                Section("Status") {
                    Toggle("Active", isOn: $isActive)
                }
                
                Section("Date") {
                    HStack {
                        Text("Date")
                        Spacer()
                        Text(availability.date.formatted(date: .abbreviated, time: .omitted))
                            .foregroundColor(.secondary)
                    }
                }
                
                Section {
                    Button("Delete Availability") {
                        showDeleteConfirmation = true
                    }
                    .foregroundColor(.red)
                    .frame(maxWidth: .infinity, alignment: .center)
                }
            }
            .navigationTitle("Edit Availability")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        Task {
                            await updateAvailability()
                        }
                    }
                    .disabled(isUpdating || endTime <= startTime)
                }
            }
            .alert("Delete Availability", isPresented: $showDeleteConfirmation) {
                Button("Cancel", role: .cancel) { }
                Button("Delete", role: .destructive) {
                    onDelete()
                    dismiss()
                }
            } message: {
                Text("Are you sure you want to delete this availability? This action cannot be undone.")
            }
            .alert("Error", isPresented: $showError) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
        }
    }
    
    private func updateAvailability() async {
        await MainActor.run {
            self.isUpdating = true
        }
        
        let timeFormatter = DateFormatter()
        timeFormatter.dateFormat = "HH:mm:ss"
        timeFormatter.timeZone = TimeZone.current  // ✅ Use local timezone, let backend handle UTC conversion
        
        let request = UpdateVetAvailabilityRequest(
            startTime: timeFormatter.string(from: startTime),
            endTime: timeFormatter.string(from: endTime),
            availabilityType: availabilityType,
            notes: notes.isEmpty ? nil : notes,
            isActive: isActive
        )
        
        do {
            let _ = try await apiManager.updateVetAvailability(
                availabilityId: availability.id,
                request: request
            )
            
            await MainActor.run {
                self.isUpdating = false
                self.onComplete()
                self.dismiss()
            }
            
            print("✅ Updated availability successfully")
        } catch {
            print("❌ Failed to update availability: \(error)")
            await MainActor.run {
                self.isUpdating = false
                self.errorMessage = "Failed to update availability: \(error.localizedDescription)"
                self.showError = true
            }
        }
    }
}
