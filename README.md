## Startup Backend
cd backend
source .venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload


## start frontend
cd frontend
npm run dev


## verify mongodb
mongosh


curl -X POST "http://localhost:8000/api/v1/rag/query" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "How do I know if my cat has kidney disease?",
       "species": ["cat"],
       "audience": "pet-owner",
       "symptoms": ["kidney-disease", "chronic-kidney-disease"]
     }'


     curl -X POST "http://localhost:8000/api/v1/rag/query" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "Compare diarrhea treatment across species",
       "species": ["dog", "cat"],
       "medical_system": "digestive",
       "symptoms": ["diarrhea"],
       "audience": "expert"
     }'