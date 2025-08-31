"""
Vet Dashboard REST API endpoints
Based on spec in docs/0011_my_appointments_dashboard.md
"""

from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, status, Path, Depends
from uuid import UUID
from pydantic import BaseModel

from ..auth.jwt_auth import get_current_user, User

router = APIRouter()


# Pydantic models for dashboard responses
class DashboardStats(BaseModel):
    appointments_today: int
    pending_transcripts: int
    completed_visits: int


class DashboardAlert(BaseModel):
    id: str
    type: str  # 'follow_up', 'overdue', 'urgent'
    message: str
    pet_id: Optional[str] = None
    appointment_id: Optional[str] = None
    created_at: str


class PetSummary(BaseModel):
    id: str
    name: str
    species: str
    breed: Optional[str] = None


class AppointmentSummary(BaseModel):
    id: str
    practice_id: str
    pet_owner_id: str
    assigned_vet_user_id: Optional[str] = None
    created_by_user_id: str
    appointment_date: datetime
    duration_minutes: int
    appointment_type: str
    status: str
    title: str
    description: Optional[str] = None
    notes: Optional[str] = None
    pets: List[PetSummary]
    created_at: datetime
    updated_at: datetime


class MedicalRecordSummary(BaseModel):
    id: str
    pet_id: str
    title: str
    description: Optional[str] = None
    record_type: str
    visit_date: str
    veterinarian_name: Optional[str] = None
    follow_up_required: bool
    created_at: str


class VisitTranscriptSummary(BaseModel):
    uuid: str
    pet_id: str
    visit_date: int
    summary: Optional[str] = None
    state: str
    created_at: str


class VetDashboardResponse(BaseModel):
    today_appointments: List[AppointmentSummary]
    pending_visits: List[VisitTranscriptSummary]
    recent_medical_records: List[MedicalRecordSummary]
    alerts: List[DashboardAlert]
    stats: DashboardStats


class TodayWorkSummaryResponse(BaseModel):
    appointments_today: List[AppointmentSummary]
    next_appointment: Optional[AppointmentSummary] = None
    current_appointment: Optional[AppointmentSummary] = None
    completed_count: int
    remaining_count: int


def require_vet_access(current_user: User = Depends(get_current_user)) -> User:
    """Require VET or VET_STAFF role for dashboard access."""
    if current_user.role not in ["VET", "VET_STAFF"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Veterinary staff only."
        )
    return current_user


@router.get(
    "/vet/{vet_user_uuid}",
    response_model=VetDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Vet Dashboard",
    description="Get complete vet work dashboard with appointments, pending visits, and recent activity"
)
async def get_vet_dashboard(
    vet_user_uuid: str = Path(..., description="Veterinarian user UUID"),
    current_user: User = Depends(require_vet_access)
) -> VetDashboardResponse:
    """
    Get vet's complete work dashboard.
    Returns today's appointments, pending visits, recent medical records, alerts, and stats.
    """
    try:
        vet_uuid = UUID(vet_user_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vet user UUID format")
    
    # Verify user can access this dashboard (admin or self)
    if current_user.role != "ADMIN" and str(current_user.id) != vet_user_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Can only view your own dashboard."
        )
    
    # Mock data for now - in real implementation, this would query the database
    today = date.today()
    
    # Mock appointments
    mock_appointments = [
        AppointmentSummary(
            id="apt-1",
            practice_id="practice-1",
            pet_owner_id="owner-1",
            assigned_vet_user_id=vet_user_uuid,
            created_by_user_id=vet_user_uuid,
            appointment_date=datetime.combine(today, datetime.min.time().replace(hour=9)),
            duration_minutes=30,
            appointment_type="checkup",
            status="completed",
            title="Annual Checkup - Fluffy",
            pets=[PetSummary(id="pet-1", name="Fluffy", species="Dog", breed="Golden Retriever")],
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        AppointmentSummary(
            id="apt-2",
            practice_id="practice-1",
            pet_owner_id="owner-2",
            assigned_vet_user_id=vet_user_uuid,
            created_by_user_id=vet_user_uuid,
            appointment_date=datetime.combine(today, datetime.min.time().replace(hour=11)),
            duration_minutes=45,
            appointment_type="emergency",
            status="scheduled",
            title="Emergency Visit - Max",
            pets=[PetSummary(id="pet-2", name="Max", species="Cat", breed="Persian")],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    # Mock pending visits
    mock_pending_visits = [
        VisitTranscriptSummary(
            uuid="visit-1",
            pet_id="pet-1",
            visit_date=int(datetime.now().timestamp()),
            summary="Routine checkup completed, all vitals normal",
            state="processed",
            created_at=datetime.now().isoformat()
        )
    ]
    
    # Mock recent medical records
    mock_medical_records = [
        MedicalRecordSummary(
            id="record-1",
            pet_id="pet-1",
            title="Annual Vaccination",
            description="Administered DHPP and Rabies vaccines",
            record_type="vaccination",
            visit_date=today.isoformat(),
            veterinarian_name="Dr. Smith",
            follow_up_required=True,
            created_at=datetime.now().isoformat()
        )
    ]
    
    # Mock alerts
    mock_alerts = [
        DashboardAlert(
            id="alert-1",
            type="follow_up",
            message="Follow-up required for Fluffy's vaccination in 2 weeks",
            pet_id="pet-1",
            created_at=datetime.now().isoformat()
        )
    ]
    
    # Mock stats
    stats = DashboardStats(
        appointments_today=len(mock_appointments),
        pending_transcripts=len(mock_pending_visits),
        completed_visits=len([apt for apt in mock_appointments if apt.status == "completed"])
    )
    
    return VetDashboardResponse(
        today_appointments=mock_appointments,
        pending_visits=mock_pending_visits,
        recent_medical_records=mock_medical_records,
        alerts=mock_alerts,
        stats=stats
    )


@router.get(
    "/vet/{vet_user_uuid}/today",
    response_model=TodayWorkSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Today's Work Summary",
    description="Get vet's today work summary with next/current appointments"
)
async def get_vet_today_summary(
    vet_user_uuid: str = Path(..., description="Veterinarian user UUID"),
    current_user: User = Depends(require_vet_access)
) -> TodayWorkSummaryResponse:
    """
    Get vet's today work summary.
    Returns today's appointments with next/current appointment highlighting.
    """
    try:
        vet_uuid = UUID(vet_user_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vet user UUID format")
    
    # Verify user can access this dashboard (admin or self)
    if current_user.role != "ADMIN" and str(current_user.id) != vet_user_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Can only view your own dashboard."
        )
    
    # Mock data for now - same as above but focused on today's work
    today = date.today()
    now = datetime.now()
    
    mock_appointments = [
        AppointmentSummary(
            id="apt-1",
            practice_id="practice-1",
            pet_owner_id="owner-1",
            assigned_vet_user_id=vet_user_uuid,
            created_by_user_id=vet_user_uuid,
            appointment_date=datetime.combine(today, datetime.min.time().replace(hour=9)),
            duration_minutes=30,
            appointment_type="checkup",
            status="completed",
            title="Annual Checkup - Fluffy",
            pets=[PetSummary(id="pet-1", name="Fluffy", species="Dog", breed="Golden Retriever")],
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        AppointmentSummary(
            id="apt-2",
            practice_id="practice-1",
            pet_owner_id="owner-2",
            assigned_vet_user_id=vet_user_uuid,
            created_by_user_id=vet_user_uuid,
            appointment_date=datetime.combine(today, datetime.min.time().replace(hour=14)),
            duration_minutes=45,
            appointment_type="emergency",
            status="scheduled",
            title="Emergency Visit - Max",
            pets=[PetSummary(id="pet-2", name="Max", species="Cat", breed="Persian")],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    # Determine next appointment (next scheduled appointment after now)
    next_appointment = None
    current_appointment = None
    
    for apt in mock_appointments:
        if apt.status in ["scheduled", "confirmed"]:
            if apt.appointment_date > now:
                if next_appointment is None or apt.appointment_date < next_appointment.appointment_date:
                    next_appointment = apt
            elif (apt.appointment_date <= now and 
                  apt.appointment_date + datetime.timedelta(minutes=apt.duration_minutes) > now):
                current_appointment = apt
    
    completed_count = len([apt for apt in mock_appointments if apt.status == "completed"])
    remaining_count = len(mock_appointments) - completed_count
    
    return TodayWorkSummaryResponse(
        appointments_today=mock_appointments,
        next_appointment=next_appointment,
        current_appointment=current_appointment,
        completed_count=completed_count,
        remaining_count=remaining_count
    )


@router.get(
    "/visits/vet/{vet_user_uuid}/pending",
    response_model=List[VisitTranscriptSummary],
    status_code=status.HTTP_200_OK,
    summary="Get Pending Visit Transcripts",
    description="Get vet's pending visit transcripts to review"
)
async def get_vet_pending_visits(
    vet_user_uuid: str = Path(..., description="Veterinarian user UUID"),
    current_user: User = Depends(require_vet_access)
) -> List[VisitTranscriptSummary]:
    """
    Get vet's pending visit transcripts.
    Returns visit transcripts that need review/approval.
    """
    try:
        vet_uuid = UUID(vet_user_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vet user UUID format")
    
    # Verify user can access this data (admin or self)
    if current_user.role != "ADMIN" and str(current_user.id) != vet_user_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Can only view your own pending visits."
        )
    
    # Mock pending visits
    mock_pending_visits = [
        VisitTranscriptSummary(
            uuid="visit-1",
            pet_id="pet-1",
            visit_date=int(datetime.now().timestamp()),
            summary="Routine checkup completed, all vitals normal. Needs final review.",
            state="processed",
            created_at=datetime.now().isoformat()
        ),
        VisitTranscriptSummary(
            uuid="visit-2",
            pet_id="pet-2",
            visit_date=int((datetime.now() - datetime.timedelta(days=1)).timestamp()),
            summary="Emergency visit for digestive issues. Treatment administered.",
            state="new",
            created_at=(datetime.now() - datetime.timedelta(days=1)).isoformat()
        )
    ]
    
    return mock_pending_visits
