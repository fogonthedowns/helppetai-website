## Startup Backend
cd backend
source .venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload


## start frontend
cd frontend
npm run dev


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


# Deploy:

source deployment-config.sh && AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text) && ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/helppet-api" && docker buildx build --platform linux/amd64 -t helppet-api:latest . && docker tag helppet-api:latest ${ECR_URI}:latest && docker push ${ECR_URI}:latest

# New Task def
aws ecs register-task-definition --cli-input-json file://new-task-def.json --region us-west-1 --query 'taskDefinition.revision'

# Deploy to ECS
aws ecs update-service --cluster helppet-prod --service helppet-api-prod --task-definition helppet-api-prod:4 --region us-west-1 --query 'service.taskDefinition'

