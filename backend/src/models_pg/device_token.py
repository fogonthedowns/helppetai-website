"""
Device Token Model for Push Notifications

Stores device tokens for iOS devices to enable push notifications.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base


class DeviceToken(Base):
    """Model for storing device tokens for push notifications"""
    
    __tablename__ = "device_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # The user (vet staff) this device belongs to
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # APNs device token (for iOS)
    device_token = Column(String(200), nullable=False, unique=True)
    
    # Device information
    device_type = Column(String(20), nullable=False, default="ios")  # ios, android
    device_name = Column(String(100))  # "John's iPhone", "iPad Pro"
    app_version = Column(String(20))   # App version when token was registered
    
    # Token status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True))  # Last time notification was sent
    
    # Relationships
    user = relationship("User", back_populates="device_tokens")
    
    def __repr__(self):
        return f"<DeviceToken(id={self.id}, user_id={self.user_id}, device_type={self.device_type}, active={self.is_active})>"
