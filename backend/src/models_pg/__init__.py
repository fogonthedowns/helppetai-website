"""
PostgreSQL SQLAlchemy models for HelpPet MVP
"""

from .user import User
from .practice import VeterinaryPractice
from .pet_owner import PetOwner
from .pet_owner_practice_association import PetOwnerPracticeAssociation
from .pet import Pet
from .medical_record import MedicalRecord
from .visit import Visit
from .appointment import Appointment, AppointmentPet
from .contact_form import ContactForm
from .scheduling import (
    PracticeHours,
    VetAvailability,
    RecurringAvailability,
    AppointmentConflict,
    AvailabilityType,
    ConflictType,
    ConflictSeverity
)

__all__ = [
    "User",
    "VeterinaryPractice", 
    "PetOwner",
    "PetOwnerPracticeAssociation",
    "Pet",
    "MedicalRecord",
    "Visit",
    "Appointment",
    "AppointmentPet",
    "ContactForm",
    "PracticeHours",
    "VetAvailability",
    "RecurringAvailability",
    "AppointmentConflict",
    "AvailabilityType",
    "ConflictType",
    "ConflictSeverity"
]
