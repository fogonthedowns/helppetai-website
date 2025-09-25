"""
Push Notification Service for HelpPet AI

Handles sending push notifications to iOS devices when appointments are booked.
Uses Apple Push Notification service (APNs) for iOS notifications.
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID
import os

# For APNs (Apple Push Notifications)
try:
    from aioapns import APNs, NotificationRequest, PushType
    APNS_AVAILABLE = True
except ImportError:
    APNS_AVAILABLE = False
    logging.warning("aioapns not installed. Push notifications will be disabled.")

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models_pg.user import User
from ..models_pg.pet_owner import PetOwner
from ..models_pg.appointment import Appointment
from ..models_pg.practice import VeterinaryPractice

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for sending push notifications to mobile devices"""
    
    def __init__(self):
        self.apns_client = None
        self.apns_bundle_id = None
        self._initialize_apns()
    
    def _initialize_apns(self):
        """Initialize Apple Push Notification service"""
        if not APNS_AVAILABLE:
            logger.warning("APNs not available - push notifications disabled")
            return
        
        # APNs configuration from environment variables
        apns_key_path = os.getenv("APNS_KEY_PATH")
        apns_key_id = os.getenv("APNS_KEY_ID")
        apns_team_id = os.getenv("APNS_TEAM_ID")
        apns_bundle_id = os.getenv("APNS_BUNDLE_ID", "ai.helppet.HelpPetAI")
        apns_use_sandbox = os.getenv("APNS_USE_SANDBOX", "true").lower() == "true"
        
        if not all([apns_key_path, apns_key_id, apns_team_id]):
            logger.warning("APNs credentials not configured. Set APNS_KEY_PATH, APNS_KEY_ID, APNS_TEAM_ID")
            return
        
        try:
            # Read the APNs key file content
            with open(apns_key_path, 'r') as key_file:
                apns_key_content = key_file.read()
            
            # aioapns APNs client initialization - correct parameters
            self.apns_client = APNs(
                key=apns_key_content,
                key_id=apns_key_id,
                team_id=apns_team_id,
                topic=apns_bundle_id,  # Use topic instead of bundle_id
                use_sandbox=apns_use_sandbox
            )
            # Store bundle_id separately for use in notifications
            self.apns_bundle_id = apns_bundle_id
            logger.info(f"✅ APNs initialized - Topic: {apns_bundle_id}, Sandbox: {apns_use_sandbox}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize APNs: {e}")
            self.apns_client = None
    
    async def send_appointment_booked_notification(
        self,
        appointment: Appointment,
        pet_owner: PetOwner,
        practice: VeterinaryPractice,
        db_session: AsyncSession
    ) -> bool:
        """
        Send push notification to vet staff when an appointment is successfully booked via voice
        
        Args:
            appointment: The booked appointment
            pet_owner: The pet owner who booked
            practice: The veterinary practice
            db_session: Database session for queries
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        try:
            # Get device tokens for vet staff at this practice
            device_tokens = await self._get_device_tokens_for_practice_staff(practice.id, db_session)
            
            if not device_tokens:
                logger.info(f"No device tokens found for practice staff at {practice.name}")
                return False
            
            # Format appointment time for display
            appointment_time = appointment.appointment_date.strftime("%A, %B %d at %I:%M %p")
            
            # Create notification payload for vet staff
            notification_payload = {
                "aps": {
                    "alert": {
                        "title": "New Voice Appointment! 📞",
                        "body": f"{pet_owner.full_name} booked an appointment for {appointment_time}"
                    },
                    "badge": 0,  # Let iOS app manage badge count
                    "sound": "default",
                    "category": "VOICE_APPOINTMENT_BOOKED"
                },
                "appointment_id": str(appointment.id),
                "practice_id": str(appointment.practice_id),
                "appointment_date": appointment.appointment_date.isoformat(),
                "practice_name": practice.name,
                "pet_owner_name": pet_owner.full_name,
                "pet_owner_phone": pet_owner.phone,
                "notification_type": "voice_appointment_booked"
            }
            
            # Send to all registered devices
            success_count = 0
            for device_token in device_tokens:
                if await self._send_notification_to_device(device_token, notification_payload):
                    success_count += 1
            
            if success_count > 0:
                logger.info(f"✅ Sent voice appointment notification to {success_count}/{len(device_tokens)} vet staff devices at {practice.name}")
            else:
                logger.warning(f"❌ Failed to send voice appointment notification to any of {len(device_tokens)} vet staff devices at {practice.name}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to send appointment notification: {e}")
            return False
    
    async def _get_device_tokens_for_practice_staff(self, practice_id: UUID, db_session: AsyncSession) -> List[str]:
        """
        Get all registered device tokens for vet staff at a practice
        """
        try:
            from ..models_pg.device_token import DeviceToken
            from ..models_pg.user import User, UserRole
            
            # Get device tokens for active vet staff and admins at this practice
            result = await db_session.execute(
                select(DeviceToken.device_token).join(User).where(
                    User.practice_id == practice_id,
                    User.role.in_([UserRole.VET_STAFF, UserRole.ADMIN]),
                    User.is_active == True,
                    DeviceToken.is_active == True,
                    DeviceToken.device_type == "ios"  # Only iOS for now
                )
            )
            tokens = [row[0] for row in result.all()]
            logger.info(f"Found {len(tokens)} active device tokens for practice staff at practice {practice_id}")
            return tokens
            
        except Exception as e:
            logger.error(f"Failed to get device tokens for practice staff {practice_id}: {e}")
            return []
    
    async def _send_notification_to_device(self, device_token: str, payload: Dict[str, Any]) -> bool:
        """
        Send notification to a specific device token
        
        Args:
            device_token: APNs device token
            payload: Notification payload
            
        Returns:
            bool: True if sent successfully
        """
        if not self.apns_client:
            logger.warning("APNs client not initialized - cannot send notification")
            return False
        
        try:
            request = NotificationRequest(
                device_token=device_token,
                message=payload,
                push_type=PushType.ALERT
            )
            
            await self.apns_client.send_notification(request)
            logger.debug(f"✅ Notification sent to device {device_token[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send notification to device {device_token[:8]}...: {e}")
            return False
    
    async def send_appointment_reminder_notification(
        self,
        appointment: Appointment,
        pet_owner: PetOwner,
        practice: VeterinaryPractice,
        db_session: AsyncSession,
        hours_before: int = 24
    ) -> bool:
        """
        Send appointment reminder notification
        
        Args:
            appointment: The appointment to remind about
            pet_owner: The pet owner
            practice: The veterinary practice
            db_session: Database session
            hours_before: How many hours before the appointment
            
        Returns:
            bool: True if notification sent successfully
        """
        try:
            device_tokens = await self._get_device_tokens_for_pet_owner(pet_owner.id, db_session)
            
            if not device_tokens:
                return False
            
            appointment_time = appointment.appointment_date.strftime("%A, %B %d at %I:%M %p")
            
            notification_payload = {
                "aps": {
                    "alert": {
                        "title": f"Appointment Reminder 📅",
                        "body": f"Don't forget! Your appointment at {practice.name} is tomorrow at {appointment_time}"
                    },
                    "badge": 0,  # Let iOS app manage badge count
                    "sound": "default",
                    "category": "APPOINTMENT_REMINDER"
                },
                "appointment_id": str(appointment.id),
                "practice_id": str(appointment.practice_id),
                "appointment_date": appointment.appointment_date.isoformat(),
                "practice_name": practice.name,
                "notification_type": "appointment_reminder",
                "hours_before": hours_before
            }
            
            success_count = 0
            for device_token in device_tokens:
                if await self._send_notification_to_device(device_token, notification_payload):
                    success_count += 1
            
            logger.info(f"✅ Sent reminder notification to {success_count}/{len(device_tokens)} devices")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to send reminder notification: {e}")
            return False


# Global instance
_push_service = None

def get_push_notification_service() -> PushNotificationService:
    """Get or create the push notification service instance"""
    global _push_service
    if _push_service is None:
        _push_service = PushNotificationService()
    return _push_service
