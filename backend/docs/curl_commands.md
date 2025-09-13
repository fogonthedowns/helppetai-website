curl -X GET "https://api.helppet.ai/api/v1/scheduling/vet-availability/e1e3991b-4efa-464b-9bae-f94c74d0a20f?date=2025-09-13" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqd2FkZSIsImV4cCI6MTc1NzgyODg4MH0.PRxj4ZFjn4KnWHK1qg0ox8g3rMOTKYc4d7Pzx-g6ZKk" \
  -H "Content-Type: application/json"

  curl -X GET "https://api.helppet.ai/api/v1/scheduling/vet-availability/e1e3991b-4efa-464b-9bae-f94c74d0a20f?date=2025-09-13" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqd2FkZSIsImV4cCI6MTc1NzgyODg4MH0.PRxj4ZFjn4KnWHK1qg0ox8g3rMOTKYc4d7Pzx-g6ZKk" \
  -H "Content-Type: application/json"

  [{"date":"2025-09-13","start_time":"09:00:00","end_time":"17:00:00","availability_type":"AVAILABLE","notes":null,"is_active":true,"id":"fd7f1d31-36df-4f9d-9c6c-04259958714e","vet_user_id":"e1e3991b-4efa-464b-9bae-f94c74d0a20f","practice_id":"934c57e7-4f9c-4d28-aa0f-3cb881e3c225","created_at":"2025-09-13T22:06:50.933662Z","updated_at":"2025-09-13T22:06:50.933662Z"}]%


curl -X POST "https://api.helppet.ai/api/v1/scheduling/vet-availability" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqd2FkZSIsImV4cCI6MTc1NzgyODg4MH0.PRxj4ZFjn4KnWHK1qg0ox8g3rMOTKYc4d7Pzx-g6ZKk" \
  -H "Content-Type: application/json" \
  -d '{
    "vet_user_id": "e1e3991b-4efa-464b-9bae-f94c74d0a20f",
    "practice_id": "934c57e7-4f9c-4d28-aa0f-3cb881e3c225",
    "date": "2025-09-13",
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "availability_type": "AVAILABLE"
  }'
