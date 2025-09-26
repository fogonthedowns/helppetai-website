"""
Test configuration and fixtures for HelpPetAI backend tests
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from src.models_pg.user import User, UserRole
from src.models_pg.practice import VeterinaryPractice
from src.models_pg.pet_owner import PetOwner
from src.models_pg.pet import Pet
from src.auth.jwt_auth_pg import get_password_hash


@pytest.fixture
def test_db_session():
    """Mock database session for testing"""
    session = AsyncMock()
    
    # Storage for test data added via session.add()
    session._test_data = []
    
    # Mock the execute method to handle different query types
    def mock_execute(query):
        from src.models_pg.scheduling_unix import VetAvailability
        from src.models_pg.appointment import Appointment
        
        result_mock = MagicMock()
        scalars_mock = MagicMock()
        
        # Convert query to string to understand what's being requested
        query_str = str(query)
        
        if "vet_availability_unix" in query_str or "VetAvailability" in query_str:
            # Return availability records
            availability_records = [item for item in session._test_data if isinstance(item, VetAvailability)]
            scalars_mock.all.return_value = availability_records
            scalars_mock.first.return_value = availability_records[0] if availability_records else None
            
            # For the specific case where we're looking for vet_user_id (availability lookup)
            if "vet_user_id" in query_str and availability_records:
                # Return the vet IDs from available records
                vet_ids = [(record.vet_user_id,) for record in availability_records]
                result_mock.all.return_value = vet_ids
                return result_mock
                
        elif "appointments" in query_str or "Appointment" in query_str:
            # Return appointment records (for conflict checking)
            appointment_records = [item for item in session._test_data if isinstance(item, Appointment)]
            scalars_mock.all.return_value = appointment_records
            scalars_mock.first.return_value = appointment_records[0] if appointment_records else None
        else:
            # Default empty result
            scalars_mock.all.return_value = []
            scalars_mock.first.return_value = None
        
        result_mock.scalars.return_value = scalars_mock
        return result_mock
    
    session.execute.side_effect = mock_execute
    
    # Mock add to store test data
    def mock_add(item):
        session._test_data.append(item)
    
    session.add.side_effect = mock_add
    
    # Mock other operations
    session.commit.return_value = None
    session.rollback.return_value = None
    
    return session


@pytest.fixture
def test_data():
    """Test data fixture with sample entities"""
    practice_id = uuid.uuid4()
    vet_user_id = uuid.uuid4()
    pet_owner_id = uuid.uuid4()
    pet_id = uuid.uuid4()
    
    practice = VeterinaryPractice(
        id=practice_id,
        name="Test Practice",
        phone="555-0123",
        email="test@practice.com",
        address_line1="123 Test St",
        license_number="TEST-001",
        timezone="US/Pacific"
    )
    
    vet_user = User(
        id=vet_user_id,
        username="vet1",
        password_hash=get_password_hash("password"),
        email="vet1@test.com",
        full_name="Test Vet",
        role=UserRole.VET_STAFF,
        practice_id=practice_id,
        is_active=True
    )
    
    pet_owner = PetOwner(
        id=pet_owner_id,
        full_name="Pet Owner",
        email="owner@test.com",
        phone="555-1234",
        address="456 Oak St"
    )
    
    pet = Pet(
        id=pet_id,
        owner_id=pet_owner_id,
        name="Test Pet",
        species="dog",
        breed="mutt",
        gender="male"
    )
    
    return {
        "practice": practice,
        "vet_user": vet_user,
        "pet_owner": pet_owner,
        "pet": pet
    }
