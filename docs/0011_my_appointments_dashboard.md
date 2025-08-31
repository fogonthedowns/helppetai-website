Vet Dashboard - Individual Work Queue Spec
Backend Requirements
Additional REST Endpoints

GET /api/v1/dashboard/vet/{vet_user_uuid} - Get vet's complete work dashboard (Today's appointments, pending visits, recent medical records)
GET /api/v1/appointments/vet/{vet_user_uuid} - Get vet's appointments (with date filters)
GET /api/v1/visits/vet/{vet_user_uuid}/pending - Get vet's pending visit transcripts to review
GET /api/v1/dashboard/vet/{vet_user_uuid}/today - Today's work summary

Dashboard Data Structure
json{
  "today_appointments": [...],
  "pending_visits": [...], 
  "recent_medical_records": [...],
  "alerts": [...], // follow-ups, overdue items
  "stats": {
    "appointments_today": 8,
    "pending_transcripts": 3,
    "completed_visits": 12
  }
}
Frontend Requirements
New Page: Vet Work Dashboard
Route: /dashboard/vet (auto-routes to logged-in vet's UUID)
Dashboard Components

Today's Schedule Card - Chronological list of today's appointments
Pending Work Card - Visit transcripts needing review/approval
Recent Activity Card - Last medical records created
Quick Actions - Start visit, create record, etc.
Work Queue Navigation - One-click to next appointment/task

Design Patterns

Card-based layout - Each work type in its own card
One-click workflow - Click appointment → go directly to pet detail
Status indicators - Next up, in progress, completed
Minimal navigation - Focus on current work item
Progress tracking - "3 of 8 appointments completed"

Key UX Features

Auto-refresh - Dashboard updates in real-time
Next up highlighting - Shows current/next appointment prominently
Quick pet access - Direct links to pet records from appointments
Work completion - Mark visits complete, update statuses
Mobile responsive - Works on tablets for clinic use

Acceptance Criteria

✅ Vet sees only their assigned work
✅ Today-focused view with chronological ordering
✅ One-click navigation to pet records
✅ Real-time status updates
✅ Pending work queue management
✅ Mobile-friendly design
✅ Quick action buttons for common tasks
✅ Progress indicators for daily workload

MVP Focus: Simple, focused work queue that gets vets through their day efficiently without complex scheduling features.RetryClaude can make mistakes. Please double-check responses.Research Sonnet 4