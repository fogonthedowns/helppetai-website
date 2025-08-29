.PHONY: help build run test deploy
.DEFAULT_GOAL := help

BUCKET_NAME := helppet.ai
DISTRIBUTION_ID := # Add your CloudFront distribution ID here after setup

help: ## Show available commands
	@echo "Available commands:"
	@echo "  help     Show this help message"
	@echo "  build    Build the application for production"
	@echo "  run      Start the development server"
	@echo "  test     Run the test suite"
	@echo "  deploy   Build and deploy to AWS S3 + CloudFront"

build: ## Build the application for production
	@echo "Building the application..."
	yarn build

run: ## Start the development server
	@echo "Starting development server..."
	yarn start

test: ## Run the test suite
	@echo "Running tests..."
	yarn test

deploy: build ## Build and deploy to AWS S3 + CloudFront
	@echo "🚀 Deploying helppet.ai to AWS..."
	
	@echo "📁 Setting up SPA routing structure..."
	@mkdir -p build/vets build/about
	@cp build/index.html build/vets/index.html
	@cp build/index.html build/about/index.html
	
	@echo "☁️  Syncing to S3..."
	aws s3 sync ./build s3://$(BUCKET_NAME) --delete
	
	@echo "⚡ Setting proper cache headers..."
	@aws s3 cp s3://$(BUCKET_NAME) s3://$(BUCKET_NAME) --recursive \
		--exclude "*" --include "*.html" \
		--metadata-directive REPLACE \
		--content-type "text/html" \
		--cache-control "no-cache"
	
	@aws s3 cp s3://$(BUCKET_NAME) s3://$(BUCKET_NAME) --recursive \
		--exclude "*" --include "*.css" \
		--metadata-directive REPLACE \
		--content-type "text/css" \
		--cache-control "public, max-age=31536000"
	
	@aws s3 cp s3://$(BUCKET_NAME) s3://$(BUCKET_NAME) --recursive \
		--exclude "*" --include "*.js" \
		--metadata-directive REPLACE \
		--content-type "application/javascript" \
		--cache-control "public, max-age=31536000"
	
	@aws s3 cp s3://$(BUCKET_NAME) s3://$(BUCKET_NAME) --recursive \
		--exclude "*" --include "*.json" \
		--metadata-directive REPLACE \
		--content-type "application/json" \
		--cache-control "public, max-age=31536000"
	
	@if [ -n "$(DISTRIBUTION_ID)" ]; then \
		echo "🔄 Invalidating CloudFront cache..."; \
		aws cloudfront create-invalidation \
			--distribution-id $(DISTRIBUTION_ID) \
			--paths "/*"; \
	else \
		echo "⚠️  DISTRIBUTION_ID not set - skipping cache invalidation"; \
		echo "   Add your distribution ID to the Makefile after setup"; \
	fi
	
	@echo "✅ Deployment complete!"
	@echo "🌐 Your site will be live at https://helppet.ai in a few minutes."