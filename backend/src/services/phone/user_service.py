"""
User Service for Phone Operations

Handles user lookup, creation, and management for phone calls.
"""

import logging
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ...models_pg.pet_owner import PetOwner
from ...models_pg.pet import Pet
from ...repositories_pg.pet_owner_repository import PetOwnerRepository
from ...repositories_pg.pet_repository import PetRepository

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user-related operations (lookup, creation)"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.pet_owner_repo = PetOwnerRepository(db_session)
        self.pet_repo = PetRepository(db_session)
    
    async def check_user(self, phone_number: str) -> Dict[str, Any]:
        """Check if user exists by phone number"""
        try:
            # Clean phone number (remove formatting)
            clean_phone = self._clean_phone_number(phone_number)
            
            # Look up pet owner by phone
            pet_owner = await self.pet_owner_repo.get_by_phone(clean_phone)
            logger.info(f"Pet owner: {clean_phone}")
          
            if pet_owner:
                logger.info(f"Pet owner found!!!!!!!!!!!!!!!!!!!!!!!: {pet_owner}")
                return await self._format_user_response(pet_owner, "phone")
            else:
                logger.info(f"Pet owner not found!!!!!!!!!!!!!!!!!!!!!!!")
                return {
                    "success": True,
                    "user_exists": False,
                    "message": "I don't see that phone number in our system. Could you provide your email address so I can check that way?"
                }
        except Exception as e:
            return {
                "success": False,
                "message": "I'm having trouble looking up your information. Let me try again."
            }
    
    async def check_user_by_email(self, email: str) -> Dict[str, Any]:
        """Check if user exists by email address"""
        try:
            # Clean email (convert to lowercase)
            clean_email = email.lower().strip()
            
            # Look up pet owner by email
            pet_owner = await self.pet_owner_repo.get_by_email(clean_email)
            
            if pet_owner:
                return await self._format_user_response(pet_owner, "email")
            else:
                return {
                    "success": True,
                    "user_exists": False,
                    "message": "I don't see that email in our system either. Let me get you set up as a new customer!"
                }
        except Exception as e:
            return {
                "success": False,
                "message": "I'm having trouble looking up your information. Let me try again."
            }
    
    async def _format_user_response(self, pet_owner: PetOwner, found_by: str) -> Dict[str, Any]:
        """Format user response with pet information"""
        try:
            # Get their pets
            pets = await self.pet_repo.get_by_owner_id(pet_owner.id)
            
            if pets:
                # Format pets list for response
                pets_list = []
                pet_names = []
                for pet in pets:
                    pets_list.append({
                        "id": str(pet.id),
                        "name": pet.name,
                        "species": pet.species
                    })
                    pet_names.append(pet.name)
                
                # Create greeting message based on number of pets
                if len(pets) == 1:
                    pet_message = f"I see you have {pets[0].name} the {pets[0].species} in our system."
                else:
                    pet_names_str = ", ".join(pet_names[:-1]) + f" and {pet_names[-1]}"
                    pet_message = f"I see you have {len(pets)} pets in our system: {pet_names_str}."
                
                # Create flattened pet fields for Retell AI compatibility
                flattened_pets = {}
                for i, pet in enumerate(pets_list):
                    flattened_pets[f"pet_{i+1}_id"] = pet["id"]
                    flattened_pets[f"pet_{i+1}_name"] = pet["name"]
                    flattened_pets[f"pet_{i+1}_species"] = pet["species"]
                
                # Build user response
                user_data = {
                    "id": str(pet_owner.id),
                    "phone_number": pet_owner.phone or "",
                    "email": pet_owner.email or "",
                    "address": pet_owner.address or "",
                    "owner_name": pet_owner.full_name,
                    "pet_count": len(pets),
                    # Flattened pet fields for Retell AI
                    **flattened_pets,
                    # Keep pets array for advanced integrations
                    "pets": pets_list
                }
                
                # Only add legacy pet_name/pet_type for single pet owners
                # For multiple pets, force explicit pet selection in booking
                if len(pets) == 1:
                    user_data["pet_name"] = pets[0].name
                    user_data["pet_type"] = pets[0].species
                
                return {
                    "success": True,
                    "user_exists": True,
                    "user": user_data,
                    "message": f"Welcome back {pet_owner.full_name}! I found you by your {found_by}. {pet_message}"
                }
            else:
                return {
                    "success": True,
                    "user_exists": True,
                    "user": {
                        "id": str(pet_owner.id),
                        "phone_number": pet_owner.phone or "",
                        "email": pet_owner.email or "",
                        "address": pet_owner.address or "",
                        "pet_name": "",
                        "pet_type": "",
                        "owner_name": pet_owner.full_name
                    },
                    "message": f"Welcome back {pet_owner.full_name}! I found you by your {found_by}. Let me help you schedule an appointment."
                }
        except Exception as e:
            return {
                "success": False,
                "message": "I found your information but I'm having trouble loading your details. Let me try again."
            }
    
    async def create_user(self, phone_number: str, email: str, address: str, pet_name: str, pet_type: str, owner_name: str) -> Dict[str, Any]:
        """Create a new user in your database"""
        try:
            # Clean phone number and email
            clean_phone = self._clean_phone_number(phone_number)
            clean_email = email.lower().strip() if email else None
            
            # Validate required fields
            if not owner_name or not owner_name.strip():
                return {
                    "success": False,
                    "message": "I need your full name to create your profile. Could you please provide that?"
                }
            
            # Check if phone or email already exists
            if clean_phone:
                existing_by_phone = await self.pet_owner_repo.get_by_phone(clean_phone)
                if existing_by_phone:
                    return {
                        "success": False,
                        "message": "I found an existing account with that phone number. Let me look that up for you instead."
                    }
            
            if clean_email:
                existing_by_email = await self.pet_owner_repo.get_by_email(clean_email)
                if existing_by_email:
                    return {
                        "success": False,
                        "message": "I found an existing account with that email address. Let me look that up for you instead."
                    }
            
            # Create pet owner
            pet_owner = PetOwner(
                full_name=owner_name.strip(),
                phone=clean_phone,
                email=clean_email,
                address=address.strip() if address else None,
                preferred_communication="phone"
            )
            
            self.db.add(pet_owner)
            await self.db.flush()  # Get the ID
            
            # Create pet if provided
            if pet_name and pet_type:
                pet = Pet(
                    name=pet_name.strip(),
                    species=pet_type.title(),
                    owner_id=pet_owner.id
                )
                self.db.add(pet)
            
            await self.db.commit()
            
            return {
                "success": True,
                "user_id": str(pet_owner.id),
                "message": f"Perfect! I've created a profile for {owner_name}{' and ' + pet_name if pet_name else ''}. Now let's find an appointment time."
            }
        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "message": "I'm having trouble creating your profile. Let me try again."
            }
    
    async def get_user_pets(self, pet_owner_id: str) -> Dict[str, Any]:
        """Get all pets for a pet owner - useful for appointment booking"""
        try:
            # Validate UUID
            try:
                owner_uuid = UUID(pet_owner_id)
            except ValueError:
                return {
                    "success": False,
                    "message": "I'm having trouble finding your profile. Let me try again."
                }
            
            # Get pet owner
            pet_owner = await self.pet_owner_repo.get_by_id(owner_uuid)
            if not pet_owner:
                return {
                    "success": False,
                    "message": "I'm having trouble finding your profile. Let me try again."
                }
            
            # Get their pets
            pets = await self.pet_repo.get_by_owner_id(owner_uuid)
            
            if pets:
                pets_list = []
                for pet in pets:
                    pets_list.append({
                        "id": str(pet.id),
                        "name": pet.name,
                        "species": pet.species
                    })
                
                # Create flattened pet fields for Retell AI compatibility
                flattened_pets = {}
                for i, pet in enumerate(pets_list):
                    flattened_pets[f"pet_{i+1}_id"] = pet["id"]
                    flattened_pets[f"pet_{i+1}_name"] = pet["name"]
                    flattened_pets[f"pet_{i+1}_species"] = pet["species"]
                
                if len(pets) == 1:
                    message = f"You have {pets[0].name} the {pets[0].species} in our system."
                else:
                    pet_names = [pet.name for pet in pets]
                    pet_names_str = ", ".join(pet_names[:-1]) + f" and {pet_names[-1]}"
                    message = f"You have {len(pets)} pets: {pet_names_str}. Which pet is this appointment for?"
                
                return {
                    "success": True,
                    "pet_count": len(pets),
                    # Flattened pet fields for Retell AI
                    **flattened_pets,
                    "message": message,
                    "owner_name": pet_owner.full_name,
                    # Keep pets array for advanced integrations
                    "pets": pets_list
                }
            else:
                return {
                    "success": False,
                    "message": "I don't see any pets in your profile. Let me help you add one first."
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting user pets: {str(e)}")
            return {
                "success": False,
                "message": "I'm having trouble loading your pet information. Let me try again."
            }
    
    def _clean_phone_number(self, phone_number: str) -> str:
        """Clean and format phone number"""
        # Remove all non-digit characters
        clean = ''.join(filter(str.isdigit, phone_number))
        
        # Add +1 if it's a 10-digit US number
        if len(clean) == 10:
            clean = '1' + clean
        
        # Format as +1XXXXXXXXXX
        if len(clean) == 11 and clean.startswith('1'):
            return '+' + clean
        
        return phone_number  # Return original if we can't parse it
