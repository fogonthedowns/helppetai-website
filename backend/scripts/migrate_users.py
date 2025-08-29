#!/usr/bin/env python3
"""
Migration script to update existing User documents to the new HelpPet MVP schema
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime


async def migrate_users():
    """
    Migrate existing users to the new schema by adding missing fields
    """
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["ai_visit_summary"]
    users_collection = db["users"]
    
    print("🔄 Starting user migration...")
    
    # Find all users missing the new required fields
    users_to_migrate = await users_collection.find({
        "$or": [
            {"email": {"$exists": False}},
            {"role": {"$exists": False}},
            {"full_name": {"$exists": False}}
        ]
    }).to_list(length=None)
    
    print(f"📊 Found {len(users_to_migrate)} users to migrate")
    
    migrated_count = 0
    
    for user in users_to_migrate:
        update_data = {}
        user_id = user["_id"]
        username = user.get("username", "unknown")
        
        # Add missing email (generate from username)
        if "email" not in user or not user["email"]:
            update_data["email"] = f"{username}@example.com"
        
        # Add missing role (default to PetOwner)
        if "role" not in user or not user["role"]:
            update_data["role"] = "PetOwner"
        
        # Add missing full_name (use username as fallback)
        if "full_name" not in user or not user["full_name"]:
            update_data["full_name"] = username.replace("_", " ").title()
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        if update_data:
            await users_collection.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )
            migrated_count += 1
            print(f"✅ Migrated user: {username}")
    
    print(f"🎉 Migration complete! Migrated {migrated_count} users")
    
    # Close connection
    client.close()


async def verify_migration():
    """
    Verify that all users now have the required fields
    """
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["ai_visit_summary"]
    users_collection = db["users"]
    
    print("\n🔍 Verifying migration...")
    
    # Check for users still missing required fields
    incomplete_users = await users_collection.find({
        "$or": [
            {"email": {"$exists": False}},
            {"role": {"$exists": False}},
            {"full_name": {"$exists": False}}
        ]
    }).to_list(length=None)
    
    if incomplete_users:
        print(f"❌ {len(incomplete_users)} users still have missing fields:")
        for user in incomplete_users:
            print(f"   - {user.get('username', 'unknown')} (ID: {user['_id']})")
    else:
        print("✅ All users have the required fields!")
    
    # Show sample of migrated users
    sample_users = await users_collection.find({}).limit(3).to_list(length=3)
    print(f"\n📋 Sample users after migration:")
    for user in sample_users:
        print(f"   - {user.get('username')}: {user.get('email')} ({user.get('role')})")
    
    client.close()


if __name__ == "__main__":
    async def main():
        await migrate_users()
        await verify_migration()
    
    asyncio.run(main())
