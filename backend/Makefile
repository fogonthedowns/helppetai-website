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
	@echo "  make install        - Install dependencies"
	@echo "  make test           - Run tests"
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
	@echo "   - JWT_SECRET_KEY"
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
TASK_CPU = 256
TASK_MEMORY = 512
CONTAINER_PORT = 8000

# Get RDS connection details from CloudFormation
RDS_HOSTNAME := $(shell aws cloudformation describe-stacks --stack-name $(STACK_NAME) --region $(REGION) --query "Stacks[0].Outputs[?OutputKey=='DatabaseEndpoint'].OutputValue" --output text)
RDS_PORT := $(shell aws cloudformation describe-stacks --stack-name $(STACK_NAME) --region $(REGION) --query "Stacks[0].Outputs[?OutputKey=='DatabasePort'].OutputValue" --output text)
EXEC_ROLE_ARN := $(shell aws cloudformation describe-stacks --stack-name $(STACK_NAME) --region $(REGION) --query "Stacks[0].Outputs[?OutputKey=='TaskExecutionRoleArn'].OutputValue" --output text)

# JWT secret - should be set as environment variable or retrieved from AWS Secrets Manager
JWT_SECRET ?= $(shell echo "$$JWT_SECRET_KEY")

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
	@echo "▶ Cluster:       $(CLUSTER_NAME)"
	@echo "▶ Service:       $(SERVICE_NAME)" 
	@echo "▶ RDS Host:      $(RDS_HOSTNAME)"
	@echo "▶ Exec Role:     $(EXEC_ROLE_ARN)"
	@echo ""
	@echo "⟳ Registering new task-definition with RDS connection..."
	$(eval TASK_DEF_ARN := $(shell \
	  aws ecs register-task-definition \
	    --family $(SERVICE_NAME) \
	    --network-mode awsvpc \
	    --requires-compatibilities FARGATE \
	    --execution-role-arn "$(EXEC_ROLE_ARN)" \
	    --cpu $(TASK_CPU) --memory $(TASK_MEMORY) \
	    --container-definitions '[{"name":"helppet-api","image":"$(CONTAINER_IMAGE)","essential":true,"portMappings":[{"containerPort":$(CONTAINER_PORT)}],"environment":[{"name":"ENVIRONMENT","value":"production"},{"name":"DEBUG","value":"false"},{"name":"LOG_LEVEL","value":"INFO"},{"name":"APP_NAME","value":"HelpPetAI API"},{"name":"RDS_HOSTNAME","value":"$(RDS_HOSTNAME)"},{"name":"RDS_PORT","value":"$(RDS_PORT)"},{"name":"RDS_DB_NAME","value":"postgres"},{"name":"RDS_USERNAME","value":"helppetadmin"},{"name":"RDS_PASSWORD","value":"$(JWT_SECRET)DB"},{"name":"JWT_SECRET_KEY","value":"$(JWT_SECRET)"},{"name":"CORS_ORIGINS","value":"https://helppet.ai,https://www.helppet.ai"},{"name":"AWS_REGION","value":"us-west-1"},{"name":"S3_BUCKET_NAME","value":"helppetai-visit-recordings"}],"logConfiguration":{"logDriver":"awslogs","options":{"awslogs-group":"/ecs/prod/helppet-api","awslogs-region":"$(REGION)","awslogs-stream-prefix":"helppet-api"}}}]' \
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
