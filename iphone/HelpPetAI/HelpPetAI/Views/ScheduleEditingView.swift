//
//  ScheduleEditingView.swift
//  HelpPetAI
//
//  Restored professional schedule editor: overlays vet availability on the shared CalendarView
//  Uses Unix scheduling APIs under the hood without changing appointment screens.
//

import SwiftUI

struct ScheduleEditingView: View {
    let onToggleSidebar: (() -> Void)?
    @ObservedObject private var apiManager = APIManager.shared
    @State private var vetAvailabilities: [VetAvailability] = []
    @State private var appointments: [Appointment] = []
    @State private var selectedDate: Date = Calendar.current.startOfDay(for: Date())
    @State private var isLoading = true
    @State private var errorMessage = ""
    @State private var showError = false
    @State private var showNewAvailability = false
    @State private var newAvailabilityTime: Date? = nil
    @State private var editingAvailability: VetAvailability? = nil
    @State private var loadingTask: Task<Void, Never>? = nil
    // Date Picker Sheet
    @State private var showDatePickerSheet = false
    @State private var tempSelectedDate = Date()

    private var dateFormatter: DateFormatter {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        f.timeZone = TimeZone.current
        return f
    }

    private var displayDateFormatter: DateFormatter {
        let f = DateFormatter()
        f.dateFormat = "EEE, MMM d"
        f.timeZone = TimeZone.current
        return f
    }

    private var formattedSelectedDate: String {
        dateFormatter.string(from: selectedDate)
    }

    private var isToday: Bool { Calendar.current.isDate(selectedDate, inSameDayAs: Date()) }

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                dateNavigationHeader
                    .padding(.top, -8)

                ZStack {
                    if isLoading && vetAvailabilities.isEmpty {
                        loadingView
                    } else {
                        calendarContent
                    }
                }
                .refreshable { await refreshData() }
            }
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    if let onToggleSidebar = onToggleSidebar {
                        Button(action: { onToggleSidebar() }) {
                            Image(systemName: "line.3.horizontal").font(.title3).foregroundColor(.blue)
                        }
                    }
                }
                ToolbarItem(placement: .principal) {
                    Text("Edit Schedule").font(.headline).fontWeight(.medium)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showNewAvailability = true }) {
                        Image(systemName: "plus").font(.title3).foregroundColor(.blue)
                    }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .alert("Error", isPresented: $showError) { Button("OK") {} } message: { Text(errorMessage) }
            .sheet(isPresented: $showNewAvailability) {
                CreateAvailabilityUnixView(
                    vetId: apiManager.currentUser?.id ?? "",
                    selectedDate: selectedDate
                ) {
                    Task { await loadData() }
                }
            }
            .sheet(item: $editingAvailability) { availability in
                EditAvailabilityUnixView(availability: availability) {
                    Task { await loadData() }
                }
            }
        }
        .onAppear {
            if apiManager.currentUser != nil { loadSafely() } else { Task { await waitForUserAndLoad() } }
        }
        .onChange(of: selectedDate) { _, _ in loadSafely() }
        .onDisappear { loadingTask?.cancel() }
        .onChange(of: apiManager.currentUser) { oldUser, newUser in if oldUser == nil && newUser != nil { loadSafely() } }
        .sheet(isPresented: $showDatePickerSheet) {
            NavigationView {
                VStack {
                    DatePicker("Select Date", selection: $tempSelectedDate, displayedComponents: .date)
                        .datePickerStyle(.graphical)
                        .labelsHidden()
                        .padding()
                    Spacer()
                }
                .navigationTitle("Select Date")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .navigationBarLeading) { Button("Cancel") { showDatePickerSheet = false } }
                    ToolbarItem(placement: .navigationBarTrailing) { Button("Done") { showDatePickerSheet = false; selectedDate = tempSelectedDate } }
                }
            }
        }
    }

    private var dateNavigationHeader: some View {
        HStack {
            Button(action: { navigate(byDays: -1) }) { Image(systemName: "chevron.left").font(.title2).foregroundColor(.primary) }
            Spacer()
            VStack(spacing: 2) {
                VStack(spacing: 4) {
                    Text(isToday ? "Today" : displayDateFormatter.string(from: selectedDate)).font(.headline).fontWeight(.medium)
                    Rectangle().fill(Color.orange).frame(height: 2).frame(width: 40)
                }
                if !isToday {
                    Text("Tap to return to today").font(.caption2).foregroundColor(.secondary).onTapGesture { selectedDate = Date() }
                }
            }
            .onTapGesture { tempSelectedDate = selectedDate; showDatePickerSheet = true }
            Spacer()
            Button(action: { navigate(byDays: 1) }) { Image(systemName: "chevron.right").font(.title2).foregroundColor(.primary) }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 4)
        .background(Color(.systemGray6))
        .overlay(Rectangle().frame(height: 0.5).foregroundColor(Color(.separator)), alignment: .bottom)
    }

    private var loadingView: some View {
        VStack(spacing: 16) { ProgressView().scaleEffect(1.2); Text("Loading schedule...").foregroundColor(.secondary) }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var calendarContent: some View {
        CalendarView(
            appointments: [],
            selectedDate: selectedDate,
            onAppointmentTap: { _ in },
            onLongPress: { time in newAvailabilityTime = time; showNewAvailability = true },
            onAppointmentMoved: { _, _ in },
            isScheduleEditingMode: .constant(true),
            vetAvailabilities: vetAvailabilities,
            onAvailabilityTap: { availability in editingAvailability = availability },
            onAvailabilityLongPress: { time in newAvailabilityTime = time; showNewAvailability = true },
            onAvailabilityMoved: { availability, newTime in Task { await updateAvailabilityTime(availability: availability, newTime: newTime) } }
        )
        .onAppear { print("📅 UI: Showing schedule calendar with \(vetAvailabilities.count) availabilities") }
    }

    private func navigate(byDays delta: Int) { withAnimation(.easeInOut(duration: 0.3)) { selectedDate = Calendar.current.date(byAdding: .day, value: delta, to: selectedDate) ?? selectedDate }; loadSafely() }

    private func loadSafely() {
        loadingTask?.cancel()
        loadingTask = Task { try? await Task.sleep(nanoseconds: 100_000_000); if !Task.isCancelled { await loadData() } }
    }

    private func waitForUserAndLoad() async {
        for _ in 0..<50 { if Task.isCancelled { return }; if apiManager.currentUser != nil { await loadData(); return }; try? await Task.sleep(nanoseconds: 100_000_000) }
        await MainActor.run { self.errorMessage = "Failed to load user information. Please try again."; self.showError = true; self.isLoading = false }
    }

    private func refreshData() async { await loadData() }

    private func loadData() async {
        guard let user = apiManager.currentUser else { await MainActor.run { self.errorMessage = "User not authenticated"; self.showError = true; self.isLoading = false }; return }
        await MainActor.run { self.isLoading = true; self.errorMessage = "" }
        do {
            let a = try await apiManager.getVetAvailabilityUnix(vetId: user.id, date: selectedDate)
            await MainActor.run {
                self.vetAvailabilities = a
                self.isLoading = false
            }
        } catch {
            await MainActor.run { self.errorMessage = "Failed to load schedule: \(error.localizedDescription)"; self.showError = true; self.isLoading = false }
        }
    }

    private func updateAvailabilityTime(availability: VetAvailability, newTime: Date) async {
        let duration = availability.localEndTime.timeIntervalSince(availability.localStartTime)
        let newEnd = newTime.addingTimeInterval(duration)
        let request = VetAvailabilityUpdateRequest(
            startAt: newTime,
            endAt: newEnd,
            availabilityType: availability.availabilityType,
            notes: availability.notes,
            isActive: true
        )
        do {
            _ = try await apiManager.updateVetAvailabilityUnix(id: availability.id, request: request)
            await loadData()
        } catch {
            await MainActor.run { self.errorMessage = "Failed to update availability: \(error.localizedDescription)"; self.showError = true }
        }
    }
}



// MARK: - Create Availability Sheet (Unix API)

struct CreateAvailabilityUnixView: View {
    @Environment(\ .dismiss) private var dismiss
    @StateObject private var apiManager = APIManager.shared
    
    let vetId: String
    let selectedDate: Date
    let onCreated: () -> Void
    
    @State private var startTime = Date()
    @State private var endTime = Date()
    @State private var availabilityType = AvailabilityType.available
    @State private var notes = ""
    @State private var isCreating = false
    @State private var errorMessage: String?
    
    var body: some View {
        NavigationView {
            Form {
                Section("Time") {
                    DatePicker("Start Time", selection: $startTime, displayedComponents: .hourAndMinute)
                    DatePicker("End Time", selection: $endTime, displayedComponents: .hourAndMinute)
                }
                
                Section("Type") {
                    Picker("Availability Type", selection: $availabilityType) {
                        ForEach(AvailabilityType.allCases, id: \.self) { type in
                            HStack {
                                Image(systemName: type.systemIcon)
                                    .foregroundColor(type.color)
                                Text(type.displayName)
                            }
                            .tag(type)
                        }
                    }
                }
                
                Section("Notes") {
                    TextField("Optional notes", text: $notes, axis: .vertical)
                        .lineLimit(3...6)
                }
                
                if let errorMessage = errorMessage {
                    Section { Text(errorMessage).foregroundColor(.red) }
                }
            }
            .navigationTitle("Add Availability")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") { Task { await createAvailability() } }
                        .disabled(isCreating || endTime <= startTime)
                }
            }
        }
        .onAppear {
            let calendar = Calendar.current
            startTime = calendar.date(bySettingHour: 9, minute: 0, second: 0, of: selectedDate) ?? selectedDate
            endTime = calendar.date(bySettingHour: 17, minute: 0, second: 0, of: selectedDate) ?? selectedDate
        }
    }
    
    private func createAvailability() async {
        isCreating = true
        errorMessage = nil
        
        guard endTime > startTime else {
            errorMessage = "End time must be after start time"
            isCreating = false
            return
        }
        
        do {
            guard let practiceId = apiManager.currentUser?.practiceId, !practiceId.isEmpty else {
                errorMessage = "Missing practice. Please ensure your user is linked to a practice."
                isCreating = false
                return
            }
            
            let request = VetAvailabilityCreateRequest(
                vetUserId: vetId,
                practiceId: practiceId,
                startAt: startTime,
                endAt: endTime,
                availabilityType: availabilityType,
                notes: notes.isEmpty ? nil : notes
            )
            
            _ = try await apiManager.createVetAvailabilityUnix(request)
            onCreated()
            dismiss()
        } catch {
            errorMessage = "Failed to create availability: \(error.localizedDescription)"
        }
        
        isCreating = false
    }
}


// MARK: - Edit Availability Sheet (Unix API)

struct EditAvailabilityUnixView: View {
    @Environment(\ .dismiss) private var dismiss
    
    let availability: VetAvailability
    let onUpdated: () -> Void
    
    @State private var startTime: Date
    @State private var endTime: Date
    @State private var availabilityType: AvailabilityType
    @State private var notes: String
    @State private var isUpdating = false
    @State private var errorMessage: String?
    
    init(availability: VetAvailability, onUpdated: @escaping () -> Void) {
        self.availability = availability
        self.onUpdated = onUpdated
        _startTime = State(initialValue: availability.localStartTime)
        _endTime = State(initialValue: availability.localEndTime)
        _availabilityType = State(initialValue: availability.availabilityType)
        _notes = State(initialValue: availability.notes ?? "")
    }
    
    var body: some View {
        NavigationView {
            Form {
                Section("Time") {
                    DatePicker("Start Time", selection: $startTime, displayedComponents: .hourAndMinute)
                    DatePicker("End Time", selection: $endTime, displayedComponents: .hourAndMinute)
                }
                
                Section("Type") {
                    Picker("Availability Type", selection: $availabilityType) {
                        ForEach(AvailabilityType.allCases, id: \.self) { type in
                            HStack {
                                Image(systemName: type.systemIcon)
                                    .foregroundColor(type.color)
                                Text(type.displayName)
                            }
                            .tag(type)
                        }
                    }
                }
                
                Section("Notes") {
                    TextField("Optional notes", text: $notes, axis: .vertical)
                        .lineLimit(3...6)
                }
                
                if let errorMessage = errorMessage {
                    Section { Text(errorMessage).foregroundColor(.red) }
                }
            }
            .navigationTitle("Edit Availability")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") { Task { await updateAvailability() } }
                        .disabled(isUpdating || endTime <= startTime)
                }
            }
        }
    }
    
    private func updateAvailability() async {
        isUpdating = true
        errorMessage = nil
        
        guard endTime > startTime else {
            errorMessage = "End time must be after start time"
            isUpdating = false
            return
        }
        
        do {
            let request = VetAvailabilityUpdateRequest(
                startAt: startTime,
                endAt: endTime,
                availabilityType: availabilityType,
                notes: notes.isEmpty ? nil : notes,
                isActive: true
            )
            
            _ = try await APIManager.shared.updateVetAvailabilityUnix(id: availability.id, request: request)
            onUpdated()
            dismiss()
        } catch {
            errorMessage = "Failed to update availability: \(error.localizedDescription)"
        }
        
        isUpdating = false
    }
}

