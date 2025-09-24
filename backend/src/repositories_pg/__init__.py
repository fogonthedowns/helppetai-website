"""
Repository layer for PostgreSQL database operations.

CLEAN UNIX TIMESTAMP REPOSITORIES:
- scheduling_repository_unix: Pure Unix timestamp implementations
- No old data dependencies, no migrations, no rot
"""

from .base_repository import BaseRepository
from .scheduling_repository_unix import VetAvailabilityUnixRepository
# AppointmentUnixRepository is deprecated - not used by any production systems

# Export clean Unix timestamp repositories
__all__ = [
    'BaseRepository',
    'VetAvailabilityUnixRepository',
    # 'AppointmentUnixRepository'  # DEPRECATED - not used by voice or iPhone systems
]