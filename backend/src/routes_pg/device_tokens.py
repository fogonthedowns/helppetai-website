"""
Device Token Management API Routes

Endpoints for iOS app to register/manage push notification device tokens.
"""

import logging
from typing import Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from ..database_pg import get_db_session
from ..models_pg.device_token import DeviceToken
from ..models_pg.user import User
from ..auth.jwt_auth_pg import get_current_user
from ..utils.error_handling import log_endpoint_errors

logger = logging.getLogger(__name__)

router = APIRouter()


class DeviceTokenRegisterRequest(BaseModel):
    """Request to register a device token"""
    device_token: str = Field(..., description="APNs device token")
    device_name: str = Field(None, description="Device name (e.g., 'John's iPhone')")
    app_version: str = Field(None, description="App version")


class DeviceTokenResponse(BaseModel):
    """Device token response"""
    id: str
    device_token: str
    device_type: str
    device_name: str = None
    app_version: str = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


@router.post("/register", response_model=Dict[str, Any])
@log_endpoint_errors("register_device_token")
async def register_device_token(
    request: DeviceTokenRegisterRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Register a device token for push notifications
    
    This endpoint allows the iOS app to register a device token
    so the user can receive push notifications when appointments are booked via voice.
    """
    try:
        logger.info(f"Registering device token for user {current_user.id} ({current_user.full_name})")
        
        # Check if this device token already exists
        existing_token_result = await db.execute(
            select(DeviceToken).where(DeviceToken.device_token == request.device_token)
        )
        existing_token = existing_token_result.scalar_one_or_none()
        
        if existing_token:
            # Update existing token with new user if different
            if existing_token.user_id != current_user.id:
                logger.info(f"Device token already exists for different user, updating to user {current_user.id}")
                await db.execute(
                    update(DeviceToken)
                    .where(DeviceToken.id == existing_token.id)
                    .values(
                        user_id=current_user.id,
                        device_name=request.device_name or existing_token.device_name,
                        app_version=request.app_version or existing_token.app_version,
                        is_active=True,
                        updated_at=datetime.utcnow()
                    )
                )
            else:
                # Just update metadata for same user
                await db.execute(
                    update(DeviceToken)
                    .where(DeviceToken.id == existing_token.id)
                    .values(
                        device_name=request.device_name or existing_token.device_name,
                        app_version=request.app_version or existing_token.app_version,
                        is_active=True,
                        updated_at=datetime.utcnow()
                    )
                )
            
            await db.commit()
            
            return {
                "success": True,
                "message": "Device token updated successfully",
                "device_token_id": str(existing_token.id)
            }
        
        else:
            # Before creating new token, deactivate any existing tokens for this user
            # This prevents accumulating old/expired tokens and avoids BadDeviceToken errors
            deactivate_result = await db.execute(
                update(DeviceToken)
                .where(DeviceToken.user_id == current_user.id)
                .where(DeviceToken.is_active == True)
                .values(is_active=False, updated_at=datetime.utcnow())
            )
            
            deactivated_count = deactivate_result.rowcount
            if deactivated_count > 0:
                logger.info(f"🔄 Deactivated {deactivated_count} existing device token(s) for user {current_user.full_name}")
            
            # Create new device token
            new_token = DeviceToken(
                user_id=current_user.id,
                device_token=request.device_token,
                device_type="ios",
                device_name=request.device_name,
                app_version=request.app_version,
                is_active=True
            )
            
            db.add(new_token)
            await db.commit()
            await db.refresh(new_token)
            
            logger.info(f"✅ Registered new device token {new_token.id} for user {current_user.full_name}")
            
            return {
                "success": True,
                "message": "Device token registered successfully",
                "device_token_id": str(new_token.id)
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to register device token: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to register device token"
        )


@router.delete("/unregister")
@log_endpoint_errors("unregister_device_token")
async def unregister_device_token(
    device_token: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Unregister a device token (mark as inactive)
    
    This should be called when the user logs out or uninstalls the app.
    """
    try:
        logger.info(f"Unregistering device token for user {current_user.id}")
        
        # Find and deactivate the token
        result = await db.execute(
            update(DeviceToken)
            .where(
                DeviceToken.device_token == device_token,
                DeviceToken.user_id == current_user.id
            )
            .values(
                is_active=False,
                updated_at=datetime.utcnow()
            )
        )
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Device token not found"
            )
        
        await db.commit()
        
        logger.info(f"✅ Unregistered device token for user {current_user.full_name}")
        
        return {
            "success": True,
            "message": "Device token unregistered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to unregister device token: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to unregister device token"
        )


@router.get("/my-tokens", response_model=Dict[str, Any])
@log_endpoint_errors("get_my_device_tokens")
async def get_my_device_tokens(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get all device tokens for the current user
    """
    try:
        result = await db.execute(
            select(DeviceToken).where(
                DeviceToken.user_id == current_user.id,
                DeviceToken.is_active == True
            ).order_by(DeviceToken.created_at.desc())
        )
        
        tokens = result.scalars().all()
        
        token_data = []
        for token in tokens:
            token_data.append({
                "id": str(token.id),
                "device_token": token.device_token[:20] + "..." if len(token.device_token) > 20 else token.device_token,  # Truncate for security
                "device_type": token.device_type,
                "device_name": token.device_name,
                "app_version": token.app_version,
                "is_active": token.is_active,
                "created_at": token.created_at.isoformat(),
                "updated_at": token.updated_at.isoformat()
            })
        
        return {
            "success": True,
            "tokens": token_data,
            "count": len(token_data)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get device tokens: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve device tokens"
        )
