"""
User repository for HelpPet MVP - Enhanced user management with role-based operations
"""

from typing import List, Optional
from beanie import PydanticObjectId

from .base_repository import BaseRepository
from ..models.user import User, UserRole


class UserRepository(BaseRepository[User]):
    """Repository for User document operations"""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username
        
        Args:
            username: Username to search for
            
        Returns:
            User if found, None otherwise
        """
        return await User.find_one({"username": username})
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address
        
        Args:
            email: Email address to search for
            
        Returns:
            User if found, None otherwise
        """
        return await User.find_one({"email": email})
    
    async def get_users_by_role(
        self,
        role: UserRole,
        is_active: bool = True,
        limit: int = 100
    ) -> List[User]:
        """
        Get users by role
        
        Args:
            role: User role to filter by
            is_active: Whether to include only active users
            limit: Maximum number of users to return
            
        Returns:
            List of users with the specified role
        """
        filters = {"role": role}
        if is_active:
            filters["is_active"] = True
        
        return await User.find(filters).limit(limit).to_list()
    
    async def get_practice_staff(
        self,
        practice_id: str | PydanticObjectId,
        is_active: bool = True
    ) -> List[User]:
        """
        Get all staff members for a specific practice
        
        Args:
            practice_id: Practice ID to filter by
            is_active: Whether to include only active staff
            
        Returns:
            List of staff users for the practice
        """
        if isinstance(practice_id, str):
            practice_id = PydanticObjectId(practice_id)
        
        filters = {
            "practice_id": practice_id,
            "role": {"$in": [UserRole.VET_STAFF, UserRole.PRACTICE_ADMIN]}
        }
        if is_active:
            filters["is_active"] = True
        
        return await User.find(filters).to_list()
    
    async def get_practice_admins(
        self,
        practice_id: str | PydanticObjectId,
        is_active: bool = True
    ) -> List[User]:
        """
        Get practice administrators for a specific practice
        
        Args:
            practice_id: Practice ID to filter by
            is_active: Whether to include only active admins
            
        Returns:
            List of practice admin users
        """
        if isinstance(practice_id, str):
            practice_id = PydanticObjectId(practice_id)
        
        filters = {
            "practice_id": practice_id,
            "role": UserRole.PRACTICE_ADMIN
        }
        if is_active:
            filters["is_active"] = True
        
        return await User.find(filters).to_list()
    
    async def get_pet_owners(
        self,
        is_active: bool = True,
        limit: int = 100,
        skip: int = 0
    ) -> List[User]:
        """
        Get pet owners with pagination
        
        Args:
            is_active: Whether to include only active users
            limit: Maximum number of users to return
            skip: Number of users to skip
            
        Returns:
            List of pet owner users
        """
        filters = {"role": UserRole.PET_OWNER}
        if is_active:
            filters["is_active"] = True
        
        return await User.find(filters).skip(skip).limit(limit).to_list()
    
    async def username_exists(self, username: str, exclude_user_id: Optional[str] = None) -> bool:
        """
        Check if username already exists (for validation)
        
        Args:
            username: Username to check
            exclude_user_id: User ID to exclude from check (for updates)
            
        Returns:
            True if username exists, False otherwise
        """
        filters = {"username": username}
        if exclude_user_id:
            filters["_id"] = {"$ne": PydanticObjectId(exclude_user_id)}
        
        return await self.exists(**filters)
    
    async def email_exists(self, email: str, exclude_user_id: Optional[str] = None) -> bool:
        """
        Check if email already exists (for validation)
        
        Args:
            email: Email to check
            exclude_user_id: User ID to exclude from check (for updates)
            
        Returns:
            True if email exists, False otherwise
        """
        filters = {"email": email}
        if exclude_user_id:
            filters["_id"] = {"$ne": PydanticObjectId(exclude_user_id)}
        
        return await self.exists(**filters)
    
    async def search_users(
        self,
        search_term: str,
        role: Optional[UserRole] = None,
        limit: int = 50
    ) -> List[User]:
        """
        Search users by username, email, or full name
        
        Args:
            search_term: Term to search for
            role: Optional role filter
            limit: Maximum number of results
            
        Returns:
            List of matching users
        """
        # Create regex pattern for case-insensitive search
        pattern = {"$regex": search_term, "$options": "i"}
        
        filters = {
            "$or": [
                {"username": pattern},
                {"email": pattern},
                {"full_name": pattern}
            ]
        }
        
        if role:
            filters["role"] = role
        
        return await User.find(filters).limit(limit).to_list()
    
    async def deactivate_user(self, user_id: str | PydanticObjectId) -> bool:
        """
        Deactivate a user account
        
        Args:
            user_id: User ID to deactivate
            
        Returns:
            True if deactivated, False if not found
        """
        return await self.soft_delete(user_id)
    
    async def activate_user(self, user_id: str | PydanticObjectId) -> bool:
        """
        Activate a user account
        
        Args:
            user_id: User ID to activate
            
        Returns:
            True if activated, False if not found
        """
        update_result = await self.update(user_id, {"is_active": True})
        return update_result is not None
