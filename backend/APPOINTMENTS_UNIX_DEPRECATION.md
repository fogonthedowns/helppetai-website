# Unused Tables Deprecation Report

**Date:** September 24, 2025  
**Status:** DEPRECATED - Safe to remove

## Summary

Two tables are being dropped as they are either unused or replaced:

1. **`appointments_unix`** - Created but never used by production systems
2. **`vet_availability`** - Old table completely replaced by `vet_availability_unix`

## Investigation Results

### AppointmentUnix Table
| Component | Uses AppointmentUnix? | Uses Regular Appointments? | Status |
|-----------|----------------------|----------------------------|---------|
| **Voice System** | ❌ NO | ✅ YES (`AppointmentRepository`) | Safe |
| **iPhone/Frontend** | ❌ NO | ✅ YES (via `/api/v1/appointments`) | Safe |
| **HTTP Endpoints** | ❌ NO endpoints defined | ✅ YES (`/api/v1/appointments`) | Safe |
| **Database Tables** | 📝 Exists but unused | ✅ Used actively | Safe |

### VetAvailability Table
| Component | Uses Old vet_availability? | Uses vet_availability_unix? | Status |
|-----------|----------------------------|---------------------------|---------|
| **Voice System** | ❌ NO | ✅ YES (`UnixTimestampSchedulingService`) | Safe |
| **iPhone/Frontend** | ❌ NO (deprecated endpoints) | ✅ YES (via `/api/v1/scheduling-unix`) | Safe |
| **HTTP Endpoints** | ❌ Returns HTTP 418 "I'm a teapot" | ✅ YES (`/api/v1/scheduling-unix`) | Safe |
| **Database Tables** | 📝 Exists but deprecated | ✅ Used actively | Safe |

## Files Modified

### 1. Models (`src/models_pg/scheduling_unix.py`)
- ✅ Commented out `AppointmentUnix` class with deprecation notice
- ✅ Commented out migration helper functions  
- ✅ Commented out backward compatibility alias

### 2. Repositories (`src/repositories_pg/scheduling_repository_unix.py`)
- ✅ Commented out `AppointmentUnixRepository` class
- ✅ Updated imports to remove AppointmentUnix
- ✅ Modified `VetAvailabilityUnixRepository.get_available_slots()` to handle missing appointments

### 3. Services (`src/services/phone/scheduling_service_unix.py`)
- ✅ Updated imports to remove AppointmentUnix references
- ✅ Added deprecation comments

### 4. Routes (`src/routes_pg/scheduling_unix.py`)
- ✅ Updated imports to remove AppointmentUnix references  
- ✅ Added deprecation comments

### 5. Repository Exports (`src/repositories_pg/__init__.py`)
- ✅ Commented out `AppointmentUnixRepository` export
- ✅ Added deprecation notice

## Database Cleanup

Execute the Alembic migration to drop both unused tables:

```bash
# Your normal deployment process:
make deploy         # Deploy code changes
make migrate-production  # Run Alembic migration on production DB
```

The migration will drop:
- `appointments_unix` table (never used)
- `vet_availability` table (replaced by `vet_availability_unix`)

## Verification

- ✅ All tests pass after deprecation
- ✅ Voice system continues using regular `AppointmentRepository`
- ✅ iPhone/Frontend continues using `/api/v1/appointments`
- ✅ No production impact

## Key Finding

**The voice system uses regular `AppointmentRepository`** (line 28 in `appointment_service.py`):
```python
self.appointment_repo = AppointmentRepository(db_session)  # NOT AppointmentUnixRepository
```

This means appointment booking continues to use the regular `appointments` table with proper timezone handling via the existing infrastructure.

## Recommendation

✅ **SAFE TO PROCEED** with dropping the `appointments_unix` table and removing all AppointmentUnix code.
