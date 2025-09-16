"""
User Service for Phone Operations

Handles user lookup, creation, and management for phone calls.
"""

import logging
from datetime import datetime
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ...models_pg.pet_owner import PetOwner
from ...models_pg.pet import Pet
from ...models_pg.pet_owner_practice_association import PetOwnerPracticeAssociation, AssociationStatus, AssociationRequestType
from ...repositories_pg.pet_owner_repository import PetOwnerRepository
from ...repositories_pg.pet_repository import PetRepository
from ...repositories_pg.association_repository import AssociationRepository

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user-related operations (lookup, creation)"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.pet_owner_repo = PetOwnerRepository(db_session)
        self.pet_repo = PetRepository(db_session)
        self.association_repo = AssociationRepository(db_session)
    
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
    
    async def create_user(self, phone_number: str, email: str, address: str, owner_name: str, practice_uuid: str) -> Dict[str, Any]:
        """Create a new pet owner and associate them with a practice"""
        try:
            logger.info("Starting user creation process.")
            
            # Clean phone number and email
            clean_phone = self._clean_phone_number(phone_number)
            clean_email = email.lower().strip() if email else None
            logger.debug(f"Cleaned phone number: {clean_phone}, Cleaned email: {clean_email}")

            # Validate required fields
            if not owner_name or not owner_name.strip():
                logger.warning("Owner name is missing or empty.")
                return {
                    "success": False,
                    "message": "I need your full name to create your profile. Could you please provide that?"
                }

            # Validate practice_uuid
            try:
                practice_id = UUID(practice_uuid)
                logger.debug(f"Validated practice UUID: {practice_id}")
            except ValueError:
                logger.error("Invalid practice UUID provided.")
                return {
                    "success": False,
                    "message": "Invalid practice information provided."
                }

            # Check if phone or email already exists using repository methods
            if clean_phone:
                logger.info(f"Checking existing account by phone: {clean_phone}")
                existing_by_phone = await self.pet_owner_repo.get_by_phone(clean_phone)
                if existing_by_phone:
                    logger.info(f"Found existing account by phone: {existing_by_phone.id}")
                    # Check if they're already associated with this practice
                    existing_association = await self.association_repo.check_association_exists(
                        existing_by_phone.id, practice_id
                    )
                    if existing_association and existing_association.status == AssociationStatus.APPROVED:
                        logger.info("Existing association found and approved.")
                        return {
                            "success": False,
                            "message": "I found an existing account with that phone number. Let me look that up for you instead."
                        }

            if clean_email:
                logger.info(f"Checking existing account by email: {clean_email}")
                existing_by_email = await self.pet_owner_repo.get_by_email(clean_email)
                if existing_by_email:
                    logger.info(f"Found existing account by email: {existing_by_email.id}")
                    # Check if they're already associated with this practice
                    existing_association = await self.association_repo.check_association_exists(
                        existing_by_email.id, practice_id
                    )
                    if existing_association and existing_association.status == AssociationStatus.APPROVED:
                        logger.info("Existing association found and approved.")
                        return {
                            "success": False,
                            "message": "I found an existing account with that email address. Let me look that up for you instead."
                        }

            # Create pet owner using repository
            logger.info("Creating new pet owner.")
            pet_owner = PetOwner(
                full_name=owner_name.strip(),
                phone=clean_phone,
                email=clean_email,
                address=address.strip() if address else None,
                preferred_communication="phone"
            )

            created_owner = await self.pet_owner_repo.create(pet_owner)
            logger.info(f"Created new pet owner with ID: {created_owner.id}")

            # Create practice association - automatically approved for new clients
            logger.info("Creating practice association for new client.")
            association = PetOwnerPracticeAssociation(
                pet_owner_id=created_owner.id,
                practice_id=practice_id,
                request_type=AssociationRequestType.NEW_CLIENT,
                primary_contact=True,
                notes="Automatically approved for phone booking"
            )
            # Auto-approve the association (this sets status, approved_at, and approved_by_user_id)
            # Using None for approved_by_user_id since this is system auto-approval
            association.status = AssociationStatus.APPROVED
            association.approved_at = datetime.utcnow()

            try:
                await self.association_repo.create(association)
                logger.info("Practice association created and approved.")
            except Exception as assoc_error:
                logger.error(f"Failed to create practice association for pet owner {created_owner.id}: {str(assoc_error)}")
                # Note: Pet owner was created but association failed - this may need cleanup
                raise Exception(f"Created pet owner but failed to associate with practice: {str(assoc_error)}")

            return {
                "success": True,
                "user_id": str(created_owner.id),
                "message": f"Perfect! I've created a profile for {owner_name}. Now let's find an appointment time."
            }
        except Exception as e:
            logger.error(f"Error during user creation: {str(e)}")
            return {
                "success": False,
                "message": "I'm having trouble creating your profile. Let me try again."
            }
    
    async def create_pet(self, pet_owner_id: str, pet_name: str, species: str, breed: str = "", gender: str = "", weight: float = None, date_of_birth: str = "") -> Dict[str, Any]:
        """Create a new pet for a pet owner"""
        try:
            logger.info(f"Creating new pet: {pet_name} ({species}) for owner {pet_owner_id}")

            # Validate pet owner ID
            try:
                owner_uuid = UUID(pet_owner_id)
            except ValueError:
                logger.error(f"Invalid pet owner UUID: {pet_owner_id}")
                return {
                    "success": False,
                    "message": "I'm having trouble finding your profile. Let me try again."
                }

            # Validate required fields
            if not pet_name or not pet_name.strip():
                return {
                    "success": False,
                    "message": "I need your pet's name to add them to your profile."
                }

            if not species or not species.strip():
                return {
                    "success": False,
                    "message": "I need to know what type of pet this is (dog, cat, etc.)."
                }

            # Verify pet owner exists
            pet_owner = await self.pet_owner_repo.get_by_id(owner_uuid)
            if not pet_owner:
                logger.error(f"Pet owner not found: {pet_owner_id}")
                return {
                    "success": False,
                    "message": "I'm having trouble finding your profile. Let me try again."
                }

            # Parse date of birth if provided
            parsed_date = None
            if date_of_birth and date_of_birth.strip():
                try:
                    from datetime import datetime
                    parsed_date = datetime.strptime(date_of_birth.strip(), "%Y-%m-%d").date()
                except ValueError:
                    logger.warning(f"Invalid date format: {date_of_birth}")
                    # Continue without date rather than failing

            # Create pet using the Pet model
            pet = Pet(
                owner_id=owner_uuid,
                name=pet_name.strip(),
                species=species.strip().lower(),
                breed=breed.strip() if breed else None,
                gender=gender.strip() if gender else None,
                weight=weight if weight and weight > 0 else None,
                date_of_birth=parsed_date,
                is_active=True
            )

            # Save pet using repository
            created_pet = await self.pet_repo.create(pet)
            logger.info(f"Successfully created pet: {created_pet.id} - {created_pet.name}")

            return {
                "success": True,
                "pet_id": str(created_pet.id),
                "pet_name": created_pet.name,
                "pet_species": created_pet.species,
                "message": f"Perfect! I've added {created_pet.name} the {created_pet.species} to your profile."
            }

        except Exception as e:
            logger.error(f"Error creating pet: {str(e)}")
            return {
                "success": False,
                "message": "I'm having trouble adding your pet to the system. Let me try again."
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
