"""
Script to initialize test users in RDS PostgreSQL database
"""

import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

async def init_test_users():
    """Initialize test users in RDS PostgreSQL"""
    
    # RDS Database connection
    DATABASE_URL = "postgresql+asyncpg://helppetadmin:dkxrBrYfY2Yy7R4I+knv0Z0kcMdaQZPHoSToOxuGy3g=DB@helppet-prod-postgres.c9206kio0fa8.us-west-1.rds.amazonaws.com:5432/postgres"
    
    print("🌱 Connecting to RDS PostgreSQL database...")
    engine = create_async_engine(DATABASE_URL)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session_maker() as session:
            # Test users to create (using correct PostgreSQL enum values)
            test_users = [
                {
                    "username": "admin",
                    "password": "mlpzaq106",
                    "email": "admin@helppet.ai",
                    "full_name": "System Administrator",
                    "role": "ADMIN"
                },
                {
                    "username": "vet1",
                    "password": "mlpzaq106",
                    "email": "vet1@helppet.ai",
                    "full_name": "Dr. Sarah Johnson",
                    "role": "VET_STAFF"
                },
                {
                    "username": "vet2",
                    "password": "mlpzaq106",
                    "email": "vet2@helppet.ai",
                    "full_name": "Dr. Michael Chen",
                    "role": "VET_STAFF"
                },
                {
                    "username": "tech1",
                    "password": "mlpzaq106",
                    "email": "tech1@helppet.ai",
                    "full_name": "Lisa Rodriguez",
                    "role": "VET_STAFF"
                },
                {
                    "username": "justin",
                    "password": "mlpzaq106",
                    "email": "justin@helppet.ai",
                    "full_name": "Justin Zollars",
                    "role": "ADMIN"
                }
            ]
            
            created_count = 0
            
            for user_data in test_users:
                # Check if user already exists
                result = await session.execute(
                    text("SELECT id FROM users WHERE username = :username"),
                    {"username": user_data["username"]}
                )
                existing_user = result.fetchone()
                
                if existing_user:
                    print(f"  ↳ User {user_data['username']} already exists, skipping...")
                    continue
                
                # Create new user
                user_id = str(uuid4())
                hashed_password = get_password_hash(user_data["password"])
                now = datetime.utcnow()
                
                await session.execute(
                    text("""
                        INSERT INTO users (id, username, password_hash, email, full_name, role, is_active, created_at, updated_at)
                        VALUES (:id, :username, :password_hash, :email, :full_name, :role, :is_active, :created_at, :updated_at)
                    """),
                    {
                        "id": user_id,
                        "username": user_data["username"],
                        "password_hash": hashed_password,
                        "email": user_data["email"],
                        "full_name": user_data["full_name"],
                        "role": user_data["role"],
                        "is_active": True,
                        "created_at": now,
                        "updated_at": now
                    }
                )
                
                print(f"  ✅ Created user: {user_data['username']} ({user_data['full_name']}) - {user_data['role']}")
                created_count += 1
            
            await session.commit()
            
            print(f"\n🎉 RDS initialization complete! Created {created_count} new users.")
            print("\n🔑 Production test credentials:")
            for user_data in test_users:
                print(f"  • Username: {user_data['username']}, Password: {user_data['password']}")
            print(f"\n🌐 You can now login at https://helppet.ai")
            
    except Exception as e:
        print(f"❌ Error initializing users: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_test_users())
