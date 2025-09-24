-- Debug Queries for Appointment Conflict Bug
-- Run these to identify the exact practice ID mismatch issue

-- 1. Check which practice has the Oct 1 availability records
SELECT 
    practice_id,
    vet_user_id,
    start_at,
    end_at,
    'Oct 1 9AM PST = 16:00 UTC' as note
FROM vet_availability_unix 
WHERE start_at = '2025-10-01 16:00:00+00'
   OR (start_at <= '2025-10-01 16:00:00+00' AND end_at >= '2025-10-01 17:00:00+00');

-- 2. Check which practice has the conflicting appointment
SELECT 
    practice_id,
    assigned_vet_user_id,
    appointment_date,
    duration_minutes,
    'Conflicting appointment' as note
FROM appointments 
WHERE appointment_date = '2025-10-01 16:00:00+00';

-- 3. Check all Oct 1 availability records by practice
SELECT 
    practice_id,
    COUNT(*) as availability_count,
    MIN(start_at) as earliest_time,
    MAX(end_at) as latest_time
FROM vet_availability_unix 
WHERE start_at::date = '2025-10-01' 
   OR end_at::date = '2025-10-01'
   OR (start_at <= '2025-10-01 07:00:00+00' AND end_at >= '2025-10-02 07:00:00+00')
GROUP BY practice_id;

-- 4. Check which vets belong to which practice
SELECT DISTINCT
    u.id as vet_user_id,
    u.full_name as vet_name,
    u.practice_id,
    p.name as practice_name
FROM users u
JOIN veterinary_practices p ON u.practice_id = p.id
WHERE u.id IN (
    'e1e3991b-4efa-464b-9bae-f94c74d0a20f',
    '0529065a-992a-47e9-b021-9a6606d06e83'
);

-- 5. Cross-check: which practice should the appointment conflict check use?
SELECT 
    'AVAILABILITY' as source,
    practice_id,
    vet_user_id,
    start_at as time_utc,
    'Should find this practice for conflict check' as note
FROM vet_availability_unix 
WHERE vet_user_id = 'e1e3991b-4efa-464b-9bae-f94c74d0a20f'
  AND start_at = '2025-10-01 16:00:00+00'

UNION ALL

SELECT 
    'APPOINTMENT' as source,
    practice_id,
    assigned_vet_user_id as vet_user_id,
    appointment_date as time_utc,
    'Appointment exists here - should conflict!' as note
FROM appointments 
WHERE assigned_vet_user_id = 'e1e3991b-4efa-464b-9bae-f94c74d0a20f'
  AND appointment_date = '2025-10-01 16:00:00+00';

-- 6. Check practice associations for the specific vet
SELECT 
    'VET_AVAILABILITY' as table_name,
    practice_id,
    COUNT(*) as records
FROM vet_availability_unix 
WHERE vet_user_id = 'e1e3991b-4efa-464b-9bae-f94c74d0a20f'
GROUP BY practice_id

UNION ALL

SELECT 
    'APPOINTMENTS' as table_name,
    practice_id,
    COUNT(*) as records
FROM appointments 
WHERE assigned_vet_user_id = 'e1e3991b-4efa-464b-9bae-f94c74d0a20f'
GROUP BY practice_id

UNION ALL

SELECT 
    'USER_PROFILE' as table_name,
    practice_id,
    1 as records
FROM users 
WHERE id = 'e1e3991b-4efa-464b-9bae-f94c74d0a20f';

-- 7. SMOKING GUN QUERY: Check which practice has availability vs appointments on Oct 1
SELECT 
    'Amarillo (bd8b...)' as practice_name,
    'bd8b1b2d-6b65-450d-930d-e04abff21b01' as practice_id,
    COUNT(va.id) as availability_count_oct1,
    COUNT(a.id) as appointment_count_oct1,
    'API likely queries THIS practice but finds no availability' as note
FROM vet_availability_unix va
FULL OUTER JOIN appointments a ON va.practice_id = a.practice_id 
    AND DATE(va.start_at) = DATE(a.appointment_date)
WHERE va.practice_id = 'bd8b1b2d-6b65-450d-930d-e04abff21b01'
  AND (DATE(va.start_at) = '2025-10-01' OR DATE(a.appointment_date) = '2025-10-01')

UNION ALL

SELECT 
    'Benicia (934c...)' as practice_name,
    '934c57e7-4f9c-4d28-aa0f-3cb881e3c225' as practice_id,
    COUNT(va.id) as availability_count_oct1,
    COUNT(a.id) as appointment_count_oct1,
    'Has BOTH availability AND appointment - conflict should be detected' as note
FROM vet_availability_unix va
FULL OUTER JOIN appointments a ON va.practice_id = a.practice_id 
    AND DATE(va.start_at) = DATE(a.appointment_date)
WHERE va.practice_id = '934c57e7-4f9c-4d28-aa0f-3cb881e3c225'
  AND (DATE(va.start_at) = '2025-10-01' OR DATE(a.appointment_date) = '2025-10-01');

-- 8. Check if there are fallback mechanisms or multiple scheduling paths
SELECT 
    p.id as practice_id,
    p.name as practice_name,
    'Available on Oct 1?' as availability_check,
    CASE WHEN va.practice_id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_availability
FROM veterinary_practices p
LEFT JOIN (
    SELECT DISTINCT practice_id 
    FROM vet_availability_unix 
    WHERE DATE(start_at) = '2025-10-01'
) va ON p.id = va.practice_id
ORDER BY p.name;

-- 9. CRITICAL DEBUG: Check if there are any availability records for the exact practice and date range
SELECT 
    'EXACT MATCH QUERY' as test_type,
    COUNT(*) as record_count,
    MIN(start_at) as earliest_start,
    MAX(end_at) as latest_end
FROM vet_availability_unix 
WHERE practice_id = '934c57e7-4f9c-4d28-aa0f-3cb881e3c225'
  AND start_at < '2025-10-02 07:00:00+00'  -- Oct 2 00:00 PST -> 07:00 UTC  
  AND end_at > '2025-10-01 07:00:00+00'    -- Oct 1 00:00 PST -> 07:00 UTC
  AND is_active = true;

-- 10. Check for any data inconsistencies or timing issues
SELECT 
    'DATA CONSISTENCY CHECK' as check_type,
    va.id,
    va.practice_id,
    va.vet_user_id,
    va.start_at,
    va.end_at,
    va.is_active,
    va.created_at,
    va.updated_at,
    'Verify this matches what API should find' as note
FROM vet_availability_unix va
WHERE va.practice_id = '934c57e7-4f9c-4d28-aa0f-3cb881e3c225'
  AND va.vet_user_id = 'e1e3991b-4efa-464b-9bae-f94c74d0a20f'
  AND DATE(va.start_at) = '2025-10-01'
ORDER BY va.start_at;
