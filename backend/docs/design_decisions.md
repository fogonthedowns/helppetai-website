New Models Added:
1. practice_hours (Hard Constraint)

Simple open/closed times per day of week
NULL times = closed that day
Hard blocks scheduling outside hours (unless emergency override)

2. vet_availability (Individual Vet Schedules)

Daily availability for each vet
Different availability types (available, surgery block, emergency only, unavailable)
Generated from recurring templates or set manually

3. recurring_availability (Templates)

Weekly patterns for vets (e.g., "Mon-Fri 9-5")
Used to generate vet_availability records
Effective date ranges for schedule changes

4. appointment_conflict (Soft Warnings)

Tracks scheduling conflicts but doesn't block
Different severity levels (warning vs error)
Can be resolved by staff

Key Features:
PostgreSQL-Specific:

Proper ENUM types
UUID primary keys with gen_random_uuid()
Timestamp with time zones
Proper constraints and indexes
Helper functions for common queries

MVP Philosophy:

Hard constraint: Practice hours (no 2 AM appointments)
Soft constraints: Everything else (human judgment)
Emergency override: Can bypass practice hours if needed

Ready for Expansion:

Schema designed to easily add capacity models later
Room management can be added without breaking changes
Staff scheduling ready to extend

This gives you a solid, production-ready foundation that prevents silly scheduling mistakes while preserving human judgment for life-and-death decisions!