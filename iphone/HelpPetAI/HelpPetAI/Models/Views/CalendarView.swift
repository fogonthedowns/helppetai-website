//
//  CalendarView.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/12/25.
//

import SwiftUI

struct CalendarView: View {
    let appointments: [Appointment]
    let selectedDate: Date
    let onAppointmentTap: (Appointment) -> Void
    let onLongPress: (Date) -> Void
    let onAppointmentMoved: (Appointment, Date) -> Void
    
    // Schedule editing mode
    @Binding var isScheduleEditingMode: Bool
    let vetAvailabilities: [VetAvailability]
    let onAvailabilityTap: (VetAvailability) -> Void
    let onAvailabilityLongPress: (Date) -> Void
    let onAvailabilityMoved: (VetAvailability, Date) -> Void
    // New: optionally overlay availability blocks on top of appointments
    let showAvailabilityOverlay: Bool = false
    
    @State private var optimisticAppointments: [Appointment] = []
    @State private var optimisticAvailabilities: [VetAvailability] = []
    
    @State private var scrollOffset: CGFloat = 0
    @State private var showingNewAppointmentTime: Date?
    @State private var showingNewAvailabilityTime: Date?
    @State private var longPressLocation: CGPoint = .zero
    @State private var draggedAppointment: Appointment? = nil
    @State private var draggedAvailability: VetAvailability? = nil
    @State private var dragOffset: CGSize = .zero
    @State private var isDragging: Bool = false
    @State private var dragTimeoutTask: Task<Void, Never>? = nil
    @State private var scrollViewProxy: ScrollViewProxy? = nil
    @State private var isScrolling: Bool = false
    @State private var scrollEndTask: Task<Void, Never>? = nil
    @State private var tappedAppointment: Appointment? = nil
    @State private var tappedAvailability: VetAvailability? = nil
    @State private var tapTransitionOffset: CGFloat = 0
    @Environment(\.colorScheme) private var colorScheme
    
    // Calendar configuration
    private let hourHeight: CGFloat = 60
    private let startHour = 0
    private let endHour = 24
    private let timeColumnWidth: CGFloat = 60
    
    private var totalHours: Int {
        endHour - startHour
    }
    
    private var totalHeight: CGFloat {
        CGFloat(totalHours) * hourHeight
    }
    
    private var currentAppointments: [Appointment] {
        optimisticAppointments.isEmpty ? appointments : optimisticAppointments
    }
    
    private var currentAvailabilities: [VetAvailability] {
        optimisticAvailabilities.isEmpty ? vetAvailabilities : optimisticAvailabilities
    }
    
    var body: some View {
        GeometryReader { geometry in
            ScrollViewReader { proxy in
                ScrollView(.vertical, showsIndicators: true) {
                    ZStack(alignment: .topLeading) {
                        // Background grid
                        calendarGrid(width: geometry.size.width)
                        
                        // Time labels
                        timeLabels
                        
                        // Appointment blocks (always show; appointment screen passes default behavior)
                        appointmentBlocks(width: geometry.size.width)
                        
                        // Availability blocks (in editing mode OR when overlay is enabled)
                        if isScheduleEditingMode || showAvailabilityOverlay {
                            availabilityBlocks(width: geometry.size.width)
                        }
                        
                        // Current time indicator line
                        currentTimeLine(width: geometry.size.width)
                        
                        // New appointment preview (yellow box)
                        if let newTime = showingNewAppointmentTime {
                            newAppointmentPreview(for: newTime, width: geometry.size.width)
                        }
                        
                        // New availability preview (green box)
                        if let newTime = showingNewAvailabilityTime {
                            newAvailabilityPreview(for: newTime, width: geometry.size.width)
                        }
                        
                        // Phantom appointment at original position
                        if let draggedAppointment = draggedAppointment, isDragging {
                            phantomAppointment(for: draggedAppointment, width: geometry.size.width)
                                .allowsHitTesting(false)
                        }
                        
                        // Phantom availability at original position
                        if let draggedAvailability = draggedAvailability, isDragging {
                            phantomAvailability(for: draggedAvailability, width: geometry.size.width)
                                .allowsHitTesting(false)
                        }

                        // Drag preview
                        if let draggedAppointment = draggedAppointment, isDragging {
                            dragTimePreview(for: draggedAppointment, width: geometry.size.width)
                                .allowsHitTesting(false)
                        }
                        
                        // Availability drag preview
                        if let draggedAvailability = draggedAvailability, isDragging {
                            availabilityDragTimePreview(for: draggedAvailability, width: geometry.size.width)
                                .allowsHitTesting(false)
                        }
                        
                        // Cancel button when dragging
                        if isDragging && (draggedAppointment != nil || draggedAvailability != nil) {
                            VStack {
                                HStack {
                                    Spacer()
                                    Button(action: {
                                        print("📅 Cancel button tapped")
                                        resetDragState()
                                    }) {
                                        Text("Cancel")
                                            .font(.system(size: 14, weight: .medium))
                                            .foregroundColor(.white)
                                            .padding(.horizontal, 16)
                                            .padding(.vertical, 8)
                                            .background(Color.red)
                                            .cornerRadius(20)
                                    }
                                    .padding(.trailing, 20)
                                    .padding(.top, 20)
                                }
                                Spacer()
                            }
                            .zIndex(1000)
                        }
                    }
                    .frame(height: totalHeight)
                    .background(Color(.systemBackground))
                }
                .onScrollGeometryChange(for: CGFloat.self) { geometry in
                    geometry.contentOffset.y
                } action: { oldOffset, newOffset in
                    handleScrollChange(newOffset: newOffset)
                }
                // CRITICAL: Disable scrolling when dragging to prevent conflicts
                .scrollDisabled(isDragging)
                .coordinateSpace(name: "calendar")
                .onAppear {
                    scrollViewProxy = proxy
                    // scrollToCurrentTime()
                    optimisticAppointments = appointments
                    optimisticAvailabilities = vetAvailabilities
                }
                .onChange(of: appointments) { _, newAppointments in
                    if !isDragging {
                        optimisticAppointments = newAppointments
                    }
                }
                .onChange(of: vetAvailabilities) { _, newAvailabilities in
                    if !isDragging {
                        optimisticAvailabilities = newAvailabilities
                    }
                }
                .gesture(
                    LongPressGesture(minimumDuration: 0.5)
                        .sequenced(before: DragGesture(minimumDistance: 0))
                        .onEnded { value in
                            switch value {
                            case .second(true, let drag):
                                if let location = drag?.location {
                                    if !isLocationOnAppointment(location) && !isLocationOnAvailability(location) && !isDragging {
                                        print("📅 Background long press at: \(location)")
                                        handleLongPress(at: location, in: geometry)
                                    }
                                }
                            default:
                                break
                            }
                        }
                )
                .onTapGesture {
                    if isDragging {
                        print("📅 Background tap - cancelling drag")
                        resetDragState()
                    }
                }
            }
        }
    }
    
    // MARK: - State Management
    
    private func resetDragState() {
        print("📅 Resetting drag state")
        
        dragTimeoutTask?.cancel()
        dragTimeoutTask = nil
        
        withAnimation(.easeInOut(duration: 0.2)) {
            draggedAppointment = nil
            draggedAvailability = nil
            dragOffset = .zero
            isDragging = false
        }
    }
    
    private func handleScrollChange(newOffset: CGFloat) {
        // Cancel any existing scroll end task
        scrollEndTask?.cancel()
        
        // Mark as scrolling
        if !isScrolling {
            isScrolling = true
            print("📅 Scrolling started")
        }
        
        // Set a new task to detect when scrolling ends
        scrollEndTask = Task {
            try? await Task.sleep(nanoseconds: 150_000_000) // 150ms delay
            if !Task.isCancelled {
                await MainActor.run {
                    isScrolling = false
                    print("📅 Scrolling ended")
                }
            }
        }
    }
    
    // MARK: - Calendar Grid
    
    private func calendarGrid(width: CGFloat) -> some View {
        VStack(spacing: 0) {
            ForEach(startHour..<endHour, id: \.self) { hour in
                HStack(spacing: 0) {
                    Rectangle()
                        .fill(Color.clear)
                        .frame(width: timeColumnWidth)
                    
                    Rectangle()
                        .stroke(Color(.separator), lineWidth: 0.5)
                        .frame(height: hourHeight)
                }
                .id("hour_\(hour)")
            }
        }
    }
    
    // MARK: - Time Labels
    
    private var timeLabels: some View {
        VStack(spacing: 0) {
            ForEach(startHour..<endHour, id: \.self) { hour in
                HStack {
                    VStack {
                        Text(formatHour(hour))
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .frame(width: timeColumnWidth - 8, alignment: .trailing)
                        Spacer()
                    }
                    .frame(height: hourHeight)
                    
                    Spacer()
                }
            }
        }
    }
    
    // MARK: - Appointment Blocks
    
    private func appointmentBlocks(width: CGFloat) -> some View {
        let appointmentWidth = width - timeColumnWidth - 10 // Only left padding, extend to right edge
        
        let visibleAppointments = currentAppointments.filter { appointment in
            var calendar = Calendar.current
            calendar.timeZone = TimeZone.current
            let hour = calendar.component(.hour, from: appointment.appointmentDate)
            let isToday = calendar.isDate(appointment.appointmentDate, inSameDayAs: selectedDate)
            let inTimeRange = hour >= startHour && hour < endHour
            
            return isToday && inTimeRange
        }
        
        return ForEach(visibleAppointments) { appointment in
            appointmentBlock(
                appointment: appointment,
                width: appointmentWidth
            )
        }
    }
    
    // MARK: - Availability Blocks
    
    private func availabilityBlocks(width: CGFloat) -> some View {
        let availabilityWidth = width - timeColumnWidth - 10
        
        let visibleAvailabilities = currentAvailabilities.filter { availability in
            var calendar = Calendar.current
            calendar.timeZone = TimeZone.current
            let hour = calendar.component(.hour, from: availability.localStartTime)
            
            // Compare using computed localDate derived from startAt
            let isCorrectDate = calendar.isDate(availability.localDate, inSameDayAs: selectedDate)
            let inTimeRange = hour >= startHour && hour < endHour
            
            // Debug logging for availability filtering
            if isCorrectDate {
                let debugFormatter = DateFormatter()
                debugFormatter.dateFormat = "yyyy-MM-dd HH:mm"
                debugFormatter.timeZone = TimeZone.current
                print("🔍 Calendar Filter - Including availability:")
                print("🔍 Date: \(debugFormatter.string(from: availability.localDate))")
                print("🔍 Start: \(debugFormatter.string(from: availability.localStartTime))")
                print("🔍 Selected: \(debugFormatter.string(from: selectedDate))")
                print("🔍 Hour: \(hour), InRange: \(inTimeRange)")
            }
            
            return isCorrectDate && inTimeRange
        }
        
        return ForEach(visibleAvailabilities) { availability in
            availabilityBlock(
                availability: availability,
                width: availabilityWidth
            )
        }
    }
    
    private func appointmentBlock(appointment: Appointment, width: CGFloat) -> some View {
        let startTime = appointment.appointmentDate
        let startOffset = timeToOffset(startTime)
        let height = CGFloat(appointment.durationMinutes) * (hourHeight / 60)
        let isDragged = draggedAppointment?.id == appointment.id
        let isTapped = tappedAppointment?.id == appointment.id
        
        return appointmentContent(
            appointment: appointment,
            width: width,
            height: height
        )
        .offset(x: timeColumnWidth + 4, // Minimal left padding
                y: startOffset + (isDragged ? dragOffset.height : 0))
        .zIndex(isDragged ? 1 : 0)
        .opacity(isDragged ? 0.8 : 1.0)
        .simultaneousGesture(
            TapGesture()
                .onEnded { _ in
                    if !isDragging && !isScrolling {
                        print("📅 Tapping appointment: \(appointment.title)")
                        onAppointmentTap(appointment)
                    } else if isScrolling {
                        print("📅 Tap ignored - still scrolling")
                    }
                }
        )
        .simultaneousGesture(
            LongPressGesture(minimumDuration: 0.3)
                .onEnded { _ in
                    if !isDragging && !isScrolling {
                        print("📅 Long press on appointment: \(appointment.title)")
                        withAnimation(.easeInOut(duration: 0.2)) {
                            draggedAppointment = appointment
                            isDragging = true
                        }
                        
                        // Set timeout for drag operation
                        dragTimeoutTask = Task {
                            try? await Task.sleep(nanoseconds: 10_000_000_000)
                            if !Task.isCancelled {
                                await MainActor.run {
                                    resetDragState()
                                }
                            }
                        }
                    } else if isScrolling {
                        print("📅 Long press ignored - still scrolling")
                    }
                }
        )
        .simultaneousGesture(
            DragGesture(minimumDistance: 5, coordinateSpace: .named("calendar"))
                .onChanged { drag in
                    // Only process if this appointment is being dragged
                    guard isDragging, draggedAppointment?.id == appointment.id else { return }
                    
                    let snapped = snapToGrid(drag.translation.height)
                    
                    
                    dragOffset = CGSize(width: 0, height: snapped)
                }
                .onEnded { drag in
                    guard isDragging, draggedAppointment?.id == appointment.id else {
                        resetDragState()
                        return
                    }
                    
                    let newOffset = startOffset + dragOffset.height
                    let newTime = offsetToTime(newOffset)
                    
                    print("📅 Moving appointment to: \(formatTime(newTime))")
                    
                    // Optimistic update: immediately update the appointment in the local state
                    let updatedAppointment = Appointment(
                        id: appointment.id,
                        practiceId: appointment.practiceId,
                        petOwnerId: appointment.petOwnerId,
                        assignedVetUserId: appointment.assignedVetUserId,
                        appointmentDate: newTime,
                        durationMinutes: appointment.durationMinutes,
                        appointmentType: appointment.appointmentType,
                        status: appointment.status,
                        title: appointment.title,
                        description: appointment.description,
                        notes: appointment.notes,
                        pets: appointment.pets,
                        createdAt: appointment.createdAt,
                        updatedAt: appointment.updatedAt
                    )
                    
                    var updatedAppointments = currentAppointments
                    if let index = updatedAppointments.firstIndex(where: { $0.id == appointment.id }) {
                        updatedAppointments[index] = updatedAppointment
                        optimisticAppointments = updatedAppointments
                    }
                    
                    resetDragState()
                    
                    // Call the callback to update the backend (without refreshing the view)
                    onAppointmentMoved(appointment, newTime)
                }
        )
    }
    
    private func availabilityBlock(availability: VetAvailability, width: CGFloat) -> some View {
        let startTime = availability.localStartTime
        let startOffset = timeToOffset(startTime)
        let endTime = availability.localEndTime
        let duration = endTime.timeIntervalSince(startTime)
        let height = CGFloat(duration / 3600) * hourHeight // Convert seconds to hours
        let isDragged = draggedAvailability?.id == availability.id
        let isTapped = tappedAvailability?.id == availability.id
        
        return availabilityContent(
            availability: availability,
            width: width,
            height: height
        )
        .offset(x: timeColumnWidth + 4,
                y: startOffset + (isDragged ? dragOffset.height : 0))
        .zIndex(isDragged ? 1 : 0)
        .opacity(isDragged ? 0.8 : 1.0)
        .simultaneousGesture(
            TapGesture()
                .onEnded { _ in
                    if !isDragging && !isScrolling {
                        print("📅 Tapping availability: \(availability.availabilityType.rawValue)")
                        onAvailabilityTap(availability)
                    } else if isScrolling {
                        print("📅 Tap ignored - still scrolling")
                    }
                }
        )
        .simultaneousGesture(
            LongPressGesture(minimumDuration: 0.3)
                .onEnded { _ in
                    if !isDragging && !isScrolling {
                        print("📅 Long press on availability: \(availability.availabilityType.rawValue)")
                        withAnimation(.easeInOut(duration: 0.2)) {
                            draggedAvailability = availability
                            isDragging = true
                        }
                        
                        // Set timeout for drag operation
                        dragTimeoutTask = Task {
                            try? await Task.sleep(nanoseconds: 10_000_000_000)
                            if !Task.isCancelled {
                                await MainActor.run {
                                    resetDragState()
                                }
                            }
                        }
                    } else if isScrolling {
                        print("📅 Long press ignored - still scrolling")
                    }
                }
        )
        .simultaneousGesture(
            DragGesture(minimumDistance: 5, coordinateSpace: .named("calendar"))
                .onChanged { drag in
                    // Only process if this availability is being dragged
                    guard isDragging, draggedAvailability?.id == availability.id else { return }
                    
                    let snapped = snapToGrid(drag.translation.height)
                    
                    
                    dragOffset = CGSize(width: 0, height: snapped)
                }
                .onEnded { drag in
                    guard isDragging, draggedAvailability?.id == availability.id else {
                        resetDragState()
                        return
                    }
                    
                    let newOffset = startOffset + dragOffset.height
                    let newTime = offsetToTime(newOffset)
                    
                    print("📅 Moving availability to: \(formatTime(newTime))")
                    
                    // Optimistic update: immediately update the availability in the local state
                    let updatedAvailability = VetAvailability(
                        id: availability.id,
                        vetUserId: availability.vetUserId,
                        practiceId: availability.practiceId,
                        startAt: newTime,
                        endAt: newTime.addingTimeInterval(duration),
                        availabilityType: availability.availabilityType,
                        notes: availability.notes,
                        isActive: availability.isActive,
                        createdAt: availability.createdAt,
                        updatedAt: availability.updatedAt
                    )
                    
                    var updatedAvailabilities = currentAvailabilities
                    if let index = updatedAvailabilities.firstIndex(where: { $0.id == availability.id }) {
                        updatedAvailabilities[index] = updatedAvailability
                        optimisticAvailabilities = updatedAvailabilities
                    }
                    
                    resetDragState()
                    
                    // Call the callback to update the backend (without refreshing the view)
                    onAvailabilityMoved(availability, newTime)
                }
        )
    }
    
    // MARK: - New Appointment Preview
    
    private func newAppointmentPreview(for time: Date, width: CGFloat) -> some View {
        let offset = timeToOffset(time)
        let appointmentWidth = min(width - timeColumnWidth - 16, 280) // Match appointment sizing
        let defaultHeight: CGFloat = 60
        
        return VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("New Appointment")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.black)
                Spacer()
            }
            
            HStack {
                Text(formatTime(time))
                    .font(.system(size: 10))
                    .foregroundColor(.black.opacity(0.7))
                Spacer()
            }
            
            Spacer()
        }
        .padding(8)
        .frame(width: appointmentWidth, height: defaultHeight, alignment: .topLeading)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(Color.yellow.opacity(0.8))
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.yellow, lineWidth: 2)
                )
        )
        .shadow(color: .black.opacity(0.2), radius: 4, x: 0, y: 2)
        .offset(x: timeColumnWidth + 8, y: offset) // Match appointment positioning
        .animation(.easeInOut(duration: 0.2), value: showingNewAppointmentTime)
        .allowsHitTesting(false)
    }
    
    private func newAvailabilityPreview(for time: Date, width: CGFloat) -> some View {
        let offset = timeToOffset(time)
        let availabilityWidth = min(width - timeColumnWidth - 16, 280)
        let defaultHeight: CGFloat = 60
        
        return VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("New Availability")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.black)
                Spacer()
            }
            
            HStack {
                Text(formatTime(time))
                    .font(.system(size: 10))
                    .foregroundColor(.black.opacity(0.7))
                Spacer()
            }
            
            Spacer()
        }
        .padding(8)
        .frame(width: availabilityWidth, height: defaultHeight, alignment: .topLeading)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(Color.green.opacity(0.8))
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.green, lineWidth: 2)
                )
        )
        .shadow(color: .black.opacity(0.2), radius: 4, x: 0, y: 2)
        .offset(x: timeColumnWidth + 8, y: offset)
        .animation(.easeInOut(duration: 0.2), value: showingNewAvailabilityTime)
        .allowsHitTesting(false)
    }
    
    // MARK: - Current Time Line
    
    private func currentTimeLine(width: CGFloat) -> some View {
        let now = Date()
        var calendar = Calendar.current
        calendar.timeZone = TimeZone.current
        
        // Only show the line if we're viewing today
        guard calendar.isDate(selectedDate, inSameDayAs: now) else {
            return AnyView(EmptyView())
        }
        
        let currentTimeOffset = timeToOffset(now)
        
        // Custom colors for light and dark modes
        let lineColor: Color = {
            switch colorScheme {
            case .light:
                return Color(red: 1.0, green: 0.7, blue: 0.7) // Pastel red for light mode
            case .dark:
                return Color(red: 0.95, green: 0.95, blue: 0.95) // Off-white for dark mode
            @unknown default:
                return Color.primary.opacity(0.4)
            }
        }()
        
        return AnyView(
            Rectangle()
                .fill(lineColor)
                .frame(height: 2)
                .frame(width: width)
                .offset(y: currentTimeOffset)
                .zIndex(10) // Above appointment blocks but below drag previews
        )
    }
    
    // MARK: - Helper Methods
    
    private func formatHour(_ hour: Int) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "h a"
        let date = Calendar.current.date(bySettingHour: hour, minute: 0, second: 0, of: Date()) ?? Date()
        return formatter.string(from: date)
    }
    
    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "h:mm a"
        formatter.timeZone = TimeZone.current
        return formatter.string(from: date)
    }
    
    private func timeToOffset(_ date: Date) -> CGFloat {
        var calendar = Calendar.current
        calendar.timeZone = TimeZone.current
        let hour = calendar.component(.hour, from: date)
        let minute = calendar.component(.minute, from: date)
        
        let hoursSinceStart = hour - startHour
        let minuteOffset = CGFloat(minute) / 60.0
        return CGFloat(hoursSinceStart) * hourHeight + (minuteOffset * hourHeight)
    }
    
    private func offsetToTime(_ offset: CGFloat) -> Date {
        let totalMinutes = (offset / hourHeight) * 60
        let hours = Int(totalMinutes / 60) + startHour
        let minutes = Int(totalMinutes.truncatingRemainder(dividingBy: 60))
        
        // Round to nearest 15 minutes
        let roundedMinutes = (minutes / 15) * 15
        
        let calendar = Calendar.current
        return calendar.date(bySettingHour: hours, minute: roundedMinutes, second: 0, of: selectedDate) ?? selectedDate
    }
    
    private func scrollToCurrentTime() {
        let now = Date()
        var calendar = Calendar.current
        calendar.timeZone = TimeZone.current
        
        // Only auto-scroll to current time if viewing today
        guard calendar.isDate(selectedDate, inSameDayAs: now) else {
            return // Don't auto-scroll for yesterday or tomorrow
        }
        
        let scrollToHour = calendar.component(.hour, from: now)
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            withAnimation(.easeInOut(duration: 0.5)) {
                scrollViewProxy?.scrollTo("hour_\(scrollToHour)", anchor: .center)
            }
        }
    }
    
    private func isLocationOnAppointment(_ location: CGPoint) -> Bool {
        for appointment in currentAppointments {
            let appointmentOffset = timeToOffset(appointment.appointmentDate)
            let appointmentHeight = CGFloat(appointment.durationMinutes) * (hourHeight / 60)
            let appointmentX = timeColumnWidth + 16
            let appointmentWidth = 300.0
            
            if location.x >= appointmentX &&
               location.x <= appointmentX + appointmentWidth &&
               location.y >= appointmentOffset &&
               location.y <= appointmentOffset + appointmentHeight {
                return true
            }
        }
        return false
    }
    
    private func isLocationOnAvailability(_ location: CGPoint) -> Bool {
        for availability in currentAvailabilities {
            let availabilityOffset = timeToOffset(availability.localStartTime)
            let endTime = availability.localEndTime
            let duration = endTime.timeIntervalSince(availability.localStartTime)
            let availabilityHeight = CGFloat(duration / 3600) * hourHeight
            let availabilityX = timeColumnWidth + 16
            let availabilityWidth = 300.0
            
            if location.x >= availabilityX &&
               location.x <= availabilityX + availabilityWidth &&
               location.y >= availabilityOffset &&
               location.y <= availabilityOffset + availabilityHeight {
                return true
            }
        }
        return false
    }
    
    private func handleLongPress(at location: CGPoint, in geometry: GeometryProxy) {
        let adjustedY = location.y
        let time = offsetToTime(adjustedY)
        
        print("📅 Long press at time: \(formatTime(time))")
        
        if isScheduleEditingMode {
            withAnimation(.easeInOut(duration: 0.2)) {
                showingNewAvailabilityTime = time
            }
            
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                withAnimation(.easeInOut(duration: 0.2)) {
                    showingNewAvailabilityTime = nil
                }
                onAvailabilityLongPress(time)
            }
        } else {
            withAnimation(.easeInOut(duration: 0.2)) {
                showingNewAppointmentTime = time
            }
            
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                withAnimation(.easeInOut(duration: 0.2)) {
                    showingNewAppointmentTime = nil
                }
                onLongPress(time)
            }
        }
    }
    
    // MARK: - Appointment Content Helper
    
    private func appointmentContent(appointment: Appointment, width: CGFloat, height: CGFloat, isPhantom: Bool = false) -> some View {
        let isDragged = draggedAppointment?.id == appointment.id
        let googleBlue = Color(red: 0.26, green: 0.52, blue: 0.96)

        // Dynamic background color
        let backgroundColor: Color = {
            if isPhantom {
                // Phantom appointments use muted colors
                switch colorScheme {
                case .light:
                    return Color.gray.opacity(0.3)
                case .dark:
                    return Color.gray.opacity(0.4)
                @unknown default:
                    return Color.gray.opacity(0.3)
                }
            } else {
                switch colorScheme {
                case .light:
                    return Color(red: 0.9, green: 0.95, blue: 1.0) // light blue
                case .dark:
                    return Color(red: 0.89, green: 0.76, blue: 0.27) // mustard yellow (#E3C23C)
                @unknown default:
                    return Color.gray.opacity(0.3)
                }
            }
        }()

        // Text color: force black on mustard yellow for contrast
        let textColor: Color = {
            if isPhantom {
                return Color.secondary
            } else {
                switch colorScheme {
                case .dark:
                    return .black
                default:
                    return .primary
                }
            }
        }()

        return HStack {
            Text(appointment.title)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(textColor)
                .lineLimit(1)
                .minimumScaleFactor(0.8)

            Spacer()

            HStack(spacing: 4) {
                Circle()
                    .fill(isPhantom ? Color.gray.opacity(0.5) : googleBlue)
                    .frame(width: 6, height: 6)

                Image(systemName: "chevron.right")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(textColor.opacity(0.6))
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .frame(width: width, height: height, alignment: .topLeading)
        .background(backgroundColor)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(isPhantom ? Color.gray.opacity(0.3) : (isDragged ? googleBlue : googleBlue.opacity(0.3)),
                        lineWidth: isPhantom ? 1 : (isDragged ? 2 : 1))
        )
        .shadow(color: isPhantom ? Color.clear : googleBlue.opacity(isDragged ? 0.4 : 0.2),
                radius: isPhantom ? 0 : (isDragged ? 8 : 4),
                x: 0,
                y: isPhantom ? 0 : (isDragged ? 4 : 2))
        .scaleEffect(isPhantom ? 1.0 : (isDragged ? 1.05 : 1.0))
        .animation(.easeInOut(duration: 0.2), value: isDragged)
    }
    
    // MARK: - Availability Content Helper
    
    private func availabilityContent(availability: VetAvailability, width: CGFloat, height: CGFloat, isPhantom: Bool = false) -> some View {
        let isDragged = draggedAvailability?.id == availability.id
        
        // Dynamic background color based on availability type with light/dark mode support
        let backgroundColor: Color = {
            if isPhantom {
                // Phantom availabilities use muted colors
                switch colorScheme {
                case .light:
                    return Color.gray.opacity(0.2)
                case .dark:
                    return Color.gray.opacity(0.3)
                @unknown default:
                    return Color.gray.opacity(0.2)
                }
            } else {
                // More translucent colors that adapt to light/dark mode
                switch colorScheme {
                case .light:
                    return availability.availabilityType.color.opacity(0.3)
                case .dark:
                    return availability.availabilityType.color.opacity(0.4)
                @unknown default:
                    return availability.availabilityType.color.opacity(0.3)
                }
            }
        }()
        
        // Text color: ensure visibility in both light and dark modes
        let textColor: Color = {
            if isPhantom {
                return Color.secondary
            } else {
                switch colorScheme {
                case .light:
                    return Color.primary
                case .dark:
                    return Color.primary
                @unknown default:
                    return Color.primary
                }
            }
        }()
        
        return HStack {
            Image(systemName: availability.availabilityType.systemIcon)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(textColor)
            
            Text(availability.availabilityType.displayName)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(textColor)
                .lineLimit(1)
                .minimumScaleFactor(0.8)
            
            Spacer()
            
            HStack(spacing: 4) {
                Circle()
                    .fill(isPhantom ? Color.gray.opacity(0.5) : availability.availabilityType.color)
                    .frame(width: 6, height: 6)
                
                Image(systemName: "chevron.right")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(textColor.opacity(0.6))
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .frame(width: width, height: height, alignment: .topLeading)
        .background(backgroundColor)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(
                    isPhantom ? Color.gray.opacity(0.3) : 
                    (isDragged ? availability.availabilityType.color : availability.availabilityType.color.opacity(0.6)),
                    lineWidth: isPhantom ? 1 : (isDragged ? 2 : 1.5)
                )
        )
        .shadow(
            color: isPhantom ? Color.clear : 
            (colorScheme == .light ? 
             availability.availabilityType.color.opacity(isDragged ? 0.3 : 0.15) :
             Color.black.opacity(isDragged ? 0.4 : 0.2)),
            radius: isPhantom ? 0 : (isDragged ? 6 : 3),
            x: 0,
            y: isPhantom ? 0 : (isDragged ? 3 : 1.5)
        )
        .scaleEffect(isPhantom ? 1.0 : (isDragged ? 1.05 : 1.0))
        .animation(.easeInOut(duration: 0.2), value: isDragged)
    }

    
    // MARK: - Drag and Drop Helpers
    
    private func snapToGrid(_ offset: CGFloat) -> CGFloat {
        let minuteHeight = hourHeight / 60
        let fifteenMinuteHeight = minuteHeight * 15
        let snappedOffset = round(offset / fifteenMinuteHeight) * fifteenMinuteHeight
        return snappedOffset
    }
    
    private func shouldTriggerHapticFeedback(oldOffset: CGFloat, newOffset: CGFloat) -> Bool {
        let minuteHeight = hourHeight / 60
        let thirtyMinuteHeight = minuteHeight * 30
        
        let oldThirtyMinuteSlot = Int(oldOffset / thirtyMinuteHeight)
        let newThirtyMinuteSlot = Int(newOffset / thirtyMinuteHeight)
        
        return oldThirtyMinuteSlot != newThirtyMinuteSlot
    }
    
    private func phantomAppointment(for appointment: Appointment, width: CGFloat) -> some View {
        let startOffset = timeToOffset(appointment.appointmentDate)
        let height = CGFloat(appointment.durationMinutes) * (hourHeight / 60)
        let appointmentWidth = width - timeColumnWidth - 10

        return appointmentContent(
            appointment: appointment,
            width: appointmentWidth,
            height: height,
            isPhantom: true
        )
        .offset(x: timeColumnWidth + 4, y: startOffset)
        .opacity(0.3)
        .zIndex(-1) // Behind other appointments but above background
    }

    private func dragTimePreview(for appointment: Appointment, width: CGFloat) -> some View {
        let originalOffset = timeToOffset(appointment.appointmentDate)
        let newOffset = originalOffset + dragOffset.height
        let newTime = offsetToTime(newOffset)

        return VStack(spacing: 4) {
            Text("Moving to:")
                .font(.caption2)
                .foregroundColor(.blue)

            Text(formatTime(newTime))
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(.blue)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(Color.blue.opacity(0.1))
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.blue, lineWidth: 1)
                )
        )
        .offset(x: timeColumnWidth + width - 80, y: newOffset - 20)
        .zIndex(1000)
    }
    
    private func phantomAvailability(for availability: VetAvailability, width: CGFloat) -> some View {
        let startOffset = timeToOffset(availability.localStartTime)
        let endTime = availability.localEndTime
        let duration = endTime.timeIntervalSince(availability.localStartTime)
        let height = CGFloat(duration / 3600) * hourHeight
        let availabilityWidth = width - timeColumnWidth - 10

        return availabilityContent(
            availability: availability,
            width: availabilityWidth,
            height: height,
            isPhantom: true
        )
        .offset(x: timeColumnWidth + 4, y: startOffset)
        .opacity(0.3)
        .zIndex(-1) // Behind other availabilities but above background
    }

    private func availabilityDragTimePreview(for availability: VetAvailability, width: CGFloat) -> some View {
        let originalOffset = timeToOffset(availability.localStartTime)
        let newOffset = originalOffset + dragOffset.height
        let newTime = offsetToTime(newOffset)

        return VStack(spacing: 4) {
            Text("Moving to:")
                .font(.caption2)
                .foregroundColor(.blue)

            Text(formatTime(newTime))
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(.blue)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(Color.blue.opacity(0.1))
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.blue, lineWidth: 1)
                )
        )
        .offset(x: timeColumnWidth + width - 80, y: newOffset - 20)
        .zIndex(1000)
    }
}

// MARK: - Preview

struct CalendarView_Previews: PreviewProvider {
    static var previews: some View {
        let sampleAppointments = [
            Appointment(
                id: "1",
                practiceId: "practice1",
                petOwnerId: "owner1",
                assignedVetUserId: "vet1",
                appointmentDate: Calendar.current.date(bySettingHour: 9, minute: 0, second: 0, of: Date()) ?? Date(),
                durationMinutes: 30,
                appointmentType: "checkup",
                status: .scheduled,
                title: "Fluffy Checkup",
                description: "Regular checkup",
                notes: nil,
                pets: [PetSummary(id: "pet1", name: "Fluffy", species: "Dog", breed: "Golden Retriever")],
                createdAt: Date(),
                updatedAt: Date()
            ),
            Appointment(
                id: "2",
                practiceId: "practice1",
                petOwnerId: "owner2",
                assignedVetUserId: "vet1",
                appointmentDate: Calendar.current.date(bySettingHour: 14, minute: 30, second: 0, of: Date()) ?? Date(),
                durationMinutes: 45,
                appointmentType: "surgery",
                status: .scheduled,
                title: "Max Surgery",
                description: "Dental surgery",
                notes: nil,
                pets: [PetSummary(id: "pet2", name: "Max", species: "Cat", breed: "Persian")],
                createdAt: Date(),
                updatedAt: Date()
            )
        ]
        
        CalendarView(
            appointments: sampleAppointments,
            selectedDate: Date(),
            onAppointmentTap: { _ in },
            onLongPress: { _ in },
            onAppointmentMoved: { _, _ in },
            isScheduleEditingMode: Binding.constant(false),
            vetAvailabilities: [],
            onAvailabilityTap: { _ in },
            onAvailabilityLongPress: { _ in },
            onAvailabilityMoved: { _, _ in }
        )
    }
}
