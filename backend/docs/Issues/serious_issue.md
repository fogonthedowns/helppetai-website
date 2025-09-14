This call is UTC. the time should map to PST time/date to 7:30pm 15th:

curl -X GET "https://api.helppet.ai/api/v1/scheduling/vet-availability/e1e3991b-4efa-464b-9bae-f94c74d0a20f?date=2025-09-16&slots=true&slot_duration=60" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqd2FkZSIsImV4cCI6MTc1NzkwMTc5MX0.uQKpd1kyAXOmUHE9qqkKKTeNaCCCsqEPEqRNB-kS-2Q" \
  -H "Content-Type: application/json" | jq
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   469  100   469    0     0   3211      0 --:--:-- --:--:-- --:--:--  3212
{
  "vet_user_id": "e1e3991b-4efa-464b-9bae-f94c74d0a20f",
  "date": "2025-09-16",
  "practice_id": "934c57e7-4f9c-4d28-aa0f-3cb881e3c225",
  "slots": [
    {
      "start_time": "02:30:00",
      "end_time": "03:30:00",
      "available": true,
      "availability_type": "AVAILABLE",
      "conflicting_appointment": null,
      "notes": "Available"
    },
    {
      "start_time": "03:30:00",
      "end_time": "04:30:00",
      "available": true,
      "availability_type": "AVAILABLE",
      "conflicting_appointment": null,
      "notes": "Available"
    }
  ],
  "total_slots": 2,
  "available_slots": 2
}

This call is local and should, PST -> UTC and find those slots. It does not!

❯ curl -X POST "https://api.helppet.ai/api/v1/webhook/phone" \
  -H "Authorization: Bearer ..." \
  -H "Content-Type: application/json" \
  -d '{
    "function_call": {
      "name": "get_available_times",
      "arguments": {
        "date": "2025-09-15",
        "time_preference": "morning",
        "practice_id": "934c57e7-4f9c-4d28-aa0f-3cb881e3c225"
      }
    }
  }'
{"response":{"success":false,"message":"I'm sorry, we don't have any morning appointments available on Monday, September 15. Would you like to try a different day or time?"}}%