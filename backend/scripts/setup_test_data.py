#!/usr/bin/env python3
"""
Setup test data for curl integration tests
Creates the jwade admin user in the test database
"""

import asyncio
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from database_pg import Base
from models_pg.user import User, UserRole
from auth.jwt_auth_pg import get_password_hash

# Test database URL
TEST_DB_URL = "postgresql+asyncpg://justinzollars@localhost:5432/helppet_test"

async def setup_test_data():
    """Create test admin user for curl integration tests"""
    
    # Create engine and session
    engine = create_async_engine(TEST_DB_URL, echo=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    
    try:
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create test admin user
        async with SessionLocal() as session:
            # Check if user already exists
            from sqlalchemy import select
            result = await session.execute(select(User).where(User.username == "jwade"))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print("✅ Test user 'jwade' already exists")
                return
            
            # Create admin user
            hashed_password = get_password_hash("rep8iv")
            admin_user = User(
                username="jwade",
                email="jwade@test.com",
                full_name="Test Admin",
                password_hash=hashed_password,
                role=UserRole.ADMIN,
                is_active=True
            )
            
            session.add(admin_user)
            await session.commit()
            print("✅ Created test admin user: jwade / rep8iv")
            
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        return False
    finally:
        await engine.dispose()
    
    return True

if __name__ == "__main__":
    asyncio.run(setup_test_data())
