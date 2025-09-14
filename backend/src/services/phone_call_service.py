"""
Phone Call Service - Main Entry Point

This module provides a backward-compatible interface to the modular phone services.
The actual implementation has been broken down into specialized services in the phone/ directory.

For new code, prefer importing directly from the phone/ modules:
- from services.phone.user_service import UserService
- from services.phone.scheduling_service import SchedulingService
- from services.phone.appointment_service import AppointmentService
- from services.phone.retell_service import RetellAIService
- from services.phone.webhook_handler import handle_phone_webhook
"""

# Re-export all services for backward compatibility
from .phone.user_service import UserService
from .phone.scheduling_service import SchedulingService
from .phone.appointment_service import AppointmentService
from .phone.retell_service import RetellAIService, get_retell_service
from .phone.webhook_handler import (
    handle_phone_webhook,
    RetellWebhookRequest,
    FunctionCall,
    CallInfo,
    User,
    Appointment
)

# Export everything for backward compatibility
__all__ = [
    # Services
    'UserService',
    'SchedulingService', 
    'AppointmentService',
    'RetellAIService',
    
    # Functions
    'handle_phone_webhook',
    'get_retell_service',
    
    # Models
    'RetellWebhookRequest',
    'FunctionCall',
    'CallInfo',
    'User',
    'Appointment'
]
