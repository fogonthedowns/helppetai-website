#!/usr/bin/env python3
"""
Script to initialize test users in MongoDB.
Run this once after setting up the database.
"""

import asyncio
import sys
import os

# Add the backend src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import Database
from src.models.user import User
from src.auth.jwt_auth import get_password_hash


async def init_test_users():
    """Initialize test users in MongoDB."""
    print("🔗 Connecting to MongoDB...")
    await Database.connect_db()
    
    test_users = [
        {"username": "vet1", "password": "password123"},
        {"username": "vet2", "password": "password123"},
        {"username": "tech1", "password": "password123"},
        {"username": "admin", "password": "admin123"}
    ]
    
    print("👥 Creating test users...")
    created_users = []
    
    for user_data in test_users:
        # Check if user already exists
        existing_user = await User.find_one(User.username == user_data["username"])
        if not existing_user:
            # Create new user
            hashed_password = get_password_hash(user_data["password"])
            new_user = User(
                username=user_data["username"],
                hashed_password=hashed_password
            )
            await new_user.insert()
            created_users.append(user_data["username"])
            print(f"✅ Created user: {user_data['username']}")
        else:
            print(f"⚠️  User already exists: {user_data['username']}")
    
    if created_users:
        print(f"\n🎉 Successfully created {len(created_users)} test users: {', '.join(created_users)}")
    else:
        print("\n📝 All test users already exist")
    
    print("\n🔐 Test Credentials:")
    for user_data in test_users:
        print(f"   Username: {user_data['username']:<8} | Password: {user_data['password']}")
    
    print("\n🔌 Closing database connection...")
    await Database.close_db()
    print("✅ Done!")


if __name__ == "__main__":
    asyncio.run(init_test_users())
