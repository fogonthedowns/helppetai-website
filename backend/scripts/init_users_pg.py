"""
Initialize test users in PostgreSQL database
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database_pg import database_pg
from models_pg.user import User, UserRole
from repositories_pg.user_repository import UserRepository
from auth.jwt_auth_pg import get_password_hash


async def init_test_users():
    """Initialize test users in PostgreSQL"""
    
    # Connect to database
    await database_pg.connect()
    
    try:
        # Get a session
        async for session in database_pg.get_session():
            user_repo = UserRepository(session)
            
            # Test users to create
            test_users = [
                {
                    "username": "admin",
                    "password": "admin123",
                    "email": "admin@helppet.com",
                    "full_name": "System Administrator",
                    "role": UserRole.ADMIN
                },
                {
                    "username": "vet1",
                    "password": "password123",
                    "email": "vet1@helppet.com",
                    "full_name": "Dr. Sarah Johnson",
                    "role": UserRole.VET_STAFF
                },
                {
                    "username": "vet2",
                    "password": "password123",
                    "email": "vet2@helppet.com",
                    "full_name": "Dr. Michael Chen",
                    "role": UserRole.VET_STAFF
                },
                {
                    "username": "tech1",
                    "password": "password123",
                    "email": "tech1@helppet.com",
                    "full_name": "Lisa Rodriguez",
                    "role": UserRole.VET_STAFF
                }
            ]
            
            created_count = 0
            
            for user_data in test_users:
                # Check if user already exists
                existing_user = await user_repo.get_by_username(user_data["username"])
                if existing_user:
                    print(f"User {user_data['username']} already exists, skipping...")
                    continue
                
                # Create new user
                hashed_password = get_password_hash(user_data["password"])
                new_user = User(
                    username=user_data["username"],
                    password_hash=hashed_password,
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    role=user_data["role"]
                )
                
                created_user = await user_repo.create(new_user)
                print(f"Created user: {created_user.username} ({created_user.full_name}) - {created_user.role}")
                created_count += 1
            
            print(f"\nInitialization complete! Created {created_count} new users.")
            print("\nTest credentials:")
            for user_data in test_users:
                print(f"  Username: {user_data['username']}, Password: {user_data['password']}")
            
            break  # Exit the async generator
            
    except Exception as e:
        print(f"Error initializing users: {e}")
        raise
    finally:
        await database_pg.disconnect()


if __name__ == "__main__":
    asyncio.run(init_test_users())
