# HelpPet AI Backend Makefile

# Variables
IMAGE_NAME = helppet-backend
IMAGE_TAG = latest
CONTAINER_NAME = helppet-backend-container
PORT = 8000

# Default target
.PHONY: help
help:
	@echo "HelpPet AI Backend - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Run development server with auto-reload"
	@echo "  make run-test       - Run server with test DB (local)"
	@echo "  make install        - Install dependencies"
	@echo "  make test           - Run unit tests + conflict test + curl integration tests"
	@echo "  make test-conflict  - Run conflict detection test only"
	@echo ""
	@echo "Docker:"
	@echo "  make build          - Build Docker image"
	@echo "  make run            - Run container with .env (development)"
	@echo "  make run-prod       - Run container with .env.production"
	@echo "  make stop           - Stop running container"
	@echo "  make clean          - Remove container and image"
	@echo "  make logs           - Show container logs"
	@echo "  make env-check      - Check environment file setup"
	@echo ""
	@echo "Database:"
	@echo "  make migrate             - Run database migrations (local)"
	@echo "  make migrate-create      - Create new migration"
	@echo "  make migrate-production  - Run migrations in production via API"
	@echo ""
	@echo "Production:"
	@echo "  make build-prod     - Build production Docker image"
	@echo "  make push-image     - Push image to ECR"
	@echo "  make update-service - Build, push, and update ECS service"
	@echo "  make deploy         - Complete deployment (build + push + update)"

# Development
.PHONY: dev
dev:
	uvicorn src.main_pg:app --host 0.0.0.0 --port $(PORT) --reload

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: test
test:
	@echo "🧪 Running unit tests..."
	pytest || true
	@echo "🧪 Running conflict detection integration test..."
	pytest tests/test_conflict_detection_integration.py -v || true
	@echo "🧪 Running curl integration tests..."
	bash scripts/run_curls.sh

test-conflict:
	@echo "🎯 Running conflict detection test specifically..."
	pytest tests/test_conflict_detection_integration.py -v -s

.PHONY: run-test
run-test:
	@echo "🚀 Starting server with TEST database configuration"
	POSTGRESQL_URL=postgresql+asyncpg://justinzollars@localhost:5432/helppet_test \
	POSTGRESQL_SYNC_URL=postgresql+psycopg2://justinzollars@localhost:5432/helppet_test \
	uvicorn src.main_pg:app --host 0.0.0.0 --port $(PORT) --reload

.PHONY: test-timezone
test-timezone:
	@echo "🧪 Running timezone-specific tests..."
	python run_timezone_tests.py

.PHONY: test-all
test-all:
	@echo "🧪 Running all tests (including legacy)..."
	pytest

# Docker Commands
.PHONY: build
build:
	@echo "Building Docker image: $(IMAGE_NAME):$(IMAGE_TAG)"
	docker buildx build --platform linux/amd64 -t $(IMAGE_NAME):$(IMAGE_TAG) .

.PHONY: build-prod
build-prod:
	@echo "Building production Docker image: $(IMAGE_NAME):prod"
	docker buildx build --platform linux/amd64 -t $(IMAGE_NAME):prod .
	@echo "Production image built successfully!"
	@echo "To tag for deployment:"
	@echo "  docker tag $(IMAGE_NAME):prod your-registry/$(IMAGE_NAME):prod"

.PHONY: run
run:
	@if [ ! -f .env ]; then \
		echo "❌ Error: .env file not found!"; \
		echo "💡 Copy from template: cp env.template .env"; \
		exit 1; \
	fi
	@echo "Running development container: $(CONTAINER_NAME)"
	@echo "Using .env file for local development"
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(PORT):$(PORT) \
		--env-file .env \
		-e POSTGRESQL_URL=postgresql+asyncpg://justinzollars@host.docker.internal:5432/helppet_dev \
		-e POSTGRESQL_SYNC_URL=postgresql+psycopg2://justinzollars@host.docker.internal:5432/helppet_dev \
		$(IMAGE_NAME):$(IMAGE_TAG)
	@echo "✅ Container started at http://localhost:$(PORT)"
	@echo "📄 API docs: http://localhost:$(PORT)/docs"

.PHONY: run-prod
run-prod:
	@if [ ! -f .env.production ]; then \
		echo "❌ Error: .env.production file not found!"; \
		echo "💡 Create it with RDS settings for production"; \
		exit 1; \
	fi
	@echo "Running production container: $(CONTAINER_NAME)-prod"
	@echo "Using .env.production file with RDS settings"
	docker run -d \
		--name $(CONTAINER_NAME)-prod \
		-p $(PORT):$(PORT) \
		--env-file .env.production \
		$(IMAGE_NAME):prod
	@echo "✅ Production container started at http://localhost:$(PORT)"

.PHONY: stop
stop:
	@echo "Stopping all containers..."
	-docker stop $(CONTAINER_NAME)
	-docker rm $(CONTAINER_NAME)
	-docker stop $(CONTAINER_NAME)-prod
	-docker rm $(CONTAINER_NAME)-prod
	@echo "✅ All containers stopped"

.PHONY: clean
clean: stop
	@echo "Cleaning up Docker resources"
	-docker rmi $(IMAGE_NAME):$(IMAGE_TAG)
	-docker rmi $(IMAGE_NAME):prod

.PHONY: logs
logs:
	docker logs -f $(CONTAINER_NAME)

.PHONY: shell
shell:
	docker exec -it $(CONTAINER_NAME) /bin/bash

# Database Commands
.PHONY: migrate
migrate:
	POSTGRESQL_URL=postgresql+asyncpg://justinzollars@localhost:5432/helppet_dev \
	POSTGRESQL_SYNC_URL=postgresql+psycopg2://justinzollars@localhost:5432/helppet_dev \
	alembic upgrade head

.PHONY: migrate-create
migrate-create:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

.PHONY: migrate-production
migrate-production:
	@echo "🚀 Running database migration in production..."
	@echo "📡 Calling migration endpoint: https://api.helppet.ai/api/v1/auth/admin/migrate"
	@curl -X POST "https://api.helppet.ai/api/v1/auth/admin/migrate" \
		-H "Content-Type: application/json" \
		-d '{"password": "HelpPetSeed2024!"}' \
		-w "\n\n📊 Response Status: %{http_code}\n⏱️  Total Time: %{time_total}s\n" \
		-s --fail-with-body || (echo "❌ Migration failed!" && exit 1)
	@echo "✅ Migration completed successfully!"

.PHONY: reset-production-db
reset-production-db:
	@echo "⚠️  DANGER: This will DELETE ALL DATA in production database!"
	@echo "🗑️  Calling database reset endpoint: https://api.helppet.ai/api/v1/auth/admin/reset-database"
	@read -p "Type 'DELETE' to confirm: " confirm; \
	if [ "$$confirm" = "DELETE" ]; then \
		curl -X POST "https://api.helppet.ai/api/v1/auth/admin/reset-database" \
			-H "Content-Type: application/json" \
			-d '{"password": "HelpPetSeed2024!"}' \
			-w "\n\n📊 Response Status: %{http_code}\n⏱️  Total Time: %{time_total}s\n" \
			-s --fail-with-body || (echo "❌ Database reset failed!" && exit 1); \
		echo "✅ Database reset completed successfully!"; \
	else \
		echo "❌ Database reset cancelled."; \
	fi

# Deployment Preparation
.PHONY: deploy-prep
deploy-prep: build-prod
	@echo "Deployment preparation checklist:"
	@echo "✓ Docker image built: $(IMAGE_NAME):prod"
	@echo ""
	@echo "Next steps for Fargate deployment:"
	@echo "1. Push image to ECR:"
	@echo "   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_URI"
	@echo "   docker tag $(IMAGE_NAME):prod YOUR_ECR_URI/$(IMAGE_NAME):prod"
	@echo "   docker push YOUR_ECR_URI/$(IMAGE_NAME):prod"
	@echo ""
	@echo "2. Set environment variables in Fargate task definition:"
	@echo "   - RDS_HOSTNAME, RDS_USERNAME, RDS_PASSWORD"
	@echo "   - OPENAI_API_KEY, PINECONE_API_KEY"
	@echo "   - JWT_SECRET_KEY, RETELL_API_KEY"
	@echo ""
	@echo "3. Configure CORS_ORIGINS=https://helppet.ai"

# Health check
.PHONY: health
health:
	curl -f http://localhost:$(PORT)/api/v1/health || echo "Health check failed"

# Environment check
.PHONY: env-check
env-check:
	@echo "🔍 Environment Configuration Check:"
	@echo ""
	@if [ -f .env ]; then \
		echo "✅ .env found (development)"; \
		echo "   Database: $$(grep POSTGRESQL_URL .env | cut -d'=' -f2-)"; \
		echo "   CORS: $$(grep CORS_ORIGINS .env | cut -d'=' -f2-)"; \
	else \
		echo "❌ .env missing (development)"; \
	fi
	@echo ""
	@if [ -f .env.production ]; then \
		echo "✅ .env.production found (production)"; \
		if grep -q "RDS_HOSTNAME" .env.production; then \
			echo "   Database: RDS configured"; \
		else \
			echo "   Database: Local PostgreSQL"; \
		fi; \
	else \
		echo "❌ .env.production missing (production)"; \
	fi
	@echo ""
	@if [ -f env.template ]; then \
		echo "✅ env.template available for reference"; \
	fi

# Quick development setup
.PHONY: setup
setup: install
	@echo "Development setup complete!"
	@echo "Create .env file with your configuration"
	@echo "Run 'make env-check' to verify configuration"
	@echo "Run 'make dev' to start development server"

# ─── DEPLOYMENT ───────────────────────────────────────────────────────────────
# Variables for deployment
AWS_ACCOUNT_ID = 724843234496
REGION = us-west-1
STACK_NAME = helppet-api-prod
CLUSTER_NAME = helppet-prod
SERVICE_NAME = helppet-api-prod
CONTAINER_IMAGE = $(AWS_ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com/helppet-api:latest
TASK_CPU = 512
TASK_MEMORY = 1024
CONTAINER_PORT = 8000

# Get RDS connection details from CloudFormation
RDS_HOSTNAME := $(shell aws cloudformation describe-stacks --stack-name $(STACK_NAME) --region $(REGION) --query "Stacks[0].Outputs[?OutputKey=='DatabaseEndpoint'].OutputValue" --output text)
RDS_PORT := $(shell aws cloudformation describe-stacks --stack-name $(STACK_NAME) --region $(REGION) --query "Stacks[0].Outputs[?OutputKey=='DatabasePort'].OutputValue" --output text)
EXEC_ROLE_ARN := $(shell aws cloudformation describe-stacks --stack-name $(STACK_NAME) --region $(REGION) --query "Stacks[0].Outputs[?OutputKey=='TaskExecutionRoleArn'].OutputValue" --output text)
TASK_ROLE_ARN := arn:aws:iam::724843234496:role/helppet-api-prod-TaskRole-09am3AGqERAX
SECRETS_ARN := $(shell aws secretsmanager describe-secret --secret-id helppet-prod/database-password --region $(REGION) --query 'ARN' --output text)

# JWT secret - should be set as environment variable or retrieved from AWS Secrets Manager
JWT_SECRET ?= $(shell echo "$$JWT_SECRET_KEY")

# Retell AI API Key - retrieved from .env.production file (required for deployment)
RETELL_API_KEY := $(shell grep '^RETELL_API_KEY=' .env.production 2>/dev/null | cut -d'=' -f2- | tr -d '"')

# Push image to ECR
.PHONY: push-image
push-image:
	@echo "🔐 Logging in to ECR..."
	aws ecr get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com
	@echo "📤 Tagging and pushing to ECR..."
	docker tag $(IMAGE_NAME):prod $(CONTAINER_IMAGE)
	docker push $(CONTAINER_IMAGE)

# Update ECS service with new task definition
.PHONY: update-service
update-service: build-prod push-image
	@echo "🔍 Checking required environment variables..."
	@if [ -z "$(RETELL_API_KEY)" ]; then \
		echo "❌ ERROR: RETELL_API_KEY environment variable is required but not set!"; \
		echo "💡 Run: export RETELL_API_KEY=your_api_key"; \
		exit 1; \
	fi
	@echo "✅ RETELL_API_KEY is set"
	@echo "▶ Cluster:       $(CLUSTER_NAME)"
	@echo "▶ Service:       $(SERVICE_NAME)" 
	@echo "▶ RDS Host:      $(RDS_HOSTNAME)"
	@echo "▶ Exec Role:     $(EXEC_ROLE_ARN)"
	@echo "▶ Retell API:    $(shell echo "$(RETELL_API_KEY)" | cut -c1-10)..."
	@echo ""
	@echo "⟳ Registering new task-definition with RDS connection..."
	$(eval TASK_DEF_ARN := $(shell \
	  aws ecs register-task-definition \
	    --family $(SERVICE_NAME) \
	    --network-mode awsvpc \
	    --requires-compatibilities FARGATE \
	    --execution-role-arn "$(EXEC_ROLE_ARN)" \
	    --task-role-arn "$(TASK_ROLE_ARN)" \
	    --cpu $(TASK_CPU) --memory $(TASK_MEMORY) \
	    --container-definitions '[{"name":"helppet-api","image":"$(CONTAINER_IMAGE)","essential":true,"portMappings":[{"containerPort":$(CONTAINER_PORT)}],"environment":[{"name":"ENVIRONMENT","value":"production"},{"name":"DEBUG","value":"false"},{"name":"LOG_LEVEL","value":"INFO"},{"name":"APP_NAME","value":"HelpPetAI API"},{"name":"RDS_HOSTNAME","value":"$(RDS_HOSTNAME)"},{"name":"RDS_PORT","value":"$(RDS_PORT)"},{"name":"RDS_DB_NAME","value":"postgres"},{"name":"RDS_USERNAME","value":"helppetadmin"},{"name":"RDS_SSL_MODE","value":"require"},{"name":"CORS_ORIGINS","value":"https://helppet.ai,https://www.helppet.ai"},{"name":"AWS_REGION","value":"us-west-1"},{"name":"S3_BUCKET_NAME","value":"helppetai-visit-recordings"},{"name":"S3_REGION","value":"us-west-1"},{"name":"RETELL_API_KEY","value":"$(RETELL_API_KEY)"}],"secrets":[{"name":"RDS_PASSWORD","valueFrom":"$(SECRETS_ARN)"}],"logConfiguration":{"logDriver":"awslogs","options":{"awslogs-group":"/ecs/prod/helppet-api","awslogs-region":"$(REGION)","awslogs-stream-prefix":"helppet-api"}}}]' \
	    --query 'taskDefinition.taskDefinitionArn' \
	    --output text))
	@echo "✅ New task-definition: $(TASK_DEF_ARN)"
	@echo ""
	@echo "⟳ Updating ECS service to use latest task..."
	aws ecs update-service \
	  --cluster $(CLUSTER_NAME) \
	  --service $(SERVICE_NAME) \
	  --task-definition "$(TASK_DEF_ARN)" \
	  --force-new-deployment \
	  --region $(REGION)
	@echo "✅ Service update completed!"

# Quick deploy - build, push, and update service
.PHONY: deploy
deploy: update-service
	@echo "🎉 Deployment complete!"
	@echo "🌐 API available at: https://api.helppet.ai"
