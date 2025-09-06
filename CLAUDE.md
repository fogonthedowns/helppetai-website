# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HelpPet.ai is a full-stack application that streamlines veterinary visit documentation using iPhone recording and AI. The project consists of:
- **Frontend**: React + TypeScript application with Tailwind CSS
- **Backend**: FastAPI Python application with PostgreSQL database
- **Serverless**: AWS Lambda functions for additional processing

## Development Commands

### Frontend (React)
```bash
cd frontend
npm run dev        # Start development server
npm run build      # Build for production
npm run test       # Run tests
npm start          # Start production server
```

### Backend (FastAPI)
```bash
cd backend
source .venv/bin/activate    # Activate virtual environment
make dev                     # Start development server with auto-reload
make install                 # Install dependencies
make test                    # Run tests
make migrate                 # Run database migrations
make migrate-create          # Create new migration
uvicorn src.main_pg:app --host 0.0.0.0 --port 8000 --reload  # Alternative dev start
```

### Database Operations
```bash
cd backend
make migrate                 # Apply migrations locally
make migrate-production      # Apply migrations to production via API
alembic upgrade head         # Direct Alembic command
alembic revision --autogenerate -m "description"  # Create migration
```

### Docker & Deployment
```bash
cd backend
make build          # Build Docker image
make run            # Run with .env (development)
make run-prod       # Run with .env.production
make deploy         # Complete deployment to AWS ECS
make push-image     # Push to ECR
make update-service # Update ECS service
```

## Project Architecture

### Frontend Structure (`frontend/src/`)
- `components/` - Reusable React components
- `pages/` - Page-level components
- `hooks/` - Custom React hooks
- `contexts/` - React context providers
- `types/` - TypeScript type definitions
- `utils/` - Utility functions
- `config/` - Configuration files

### Backend Structure (`backend/src/`)
- `auth/` - Authentication and authorization logic
- `models_pg/` - SQLAlchemy database models (PostgreSQL)
- `repositories_pg/` - Data access layer
- `routes_pg/` - API endpoint definitions
- `schemas/` - Pydantic models for request/response validation
- `services/` - Business logic layer
- `config.py` - Application configuration
- `main_pg.py` - FastAPI application entry point
- `database_pg.py` - Database connection and session management

### Key Technologies
- **Frontend**: React 19, TypeScript, Tailwind CSS, React Router, Lucide Icons
- **Backend**: FastAPI, SQLAlchemy, Alembic, PostgreSQL, Pydantic
- **Infrastructure**: AWS ECS Fargate, RDS PostgreSQL, S3, ECR
- **Development**: Black (formatting), isort (imports), pytest (testing), MyPy (type checking)

## Configuration Files

### Frontend
- `package.json` - Dependencies and scripts
- `tsconfig.json` - TypeScript configuration
- `tailwind.config.js` - Tailwind CSS configuration

### Backend
- `pyproject.toml` - Python project configuration with Black, isort, pytest, MyPy settings
- `requirements.txt` - Python dependencies
- `alembic.ini` - Database migration configuration
- `.env` - Development environment variables
- `.env.production` - Production environment variables

## Testing

### Frontend
```bash
cd frontend
npm test                    # Run React tests with Jest
```

### Backend
```bash
cd backend
make test                   # Run pytest
pytest                     # Direct pytest command
pytest --cov=src           # Run with coverage
```

## API Testing
```bash
# Example RAG query
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I know if my cat has kidney disease?",
    "species": ["cat"],
    "audience": "pet-owner",
    "symptoms": ["kidney-disease", "chronic-kidney-disease"]
  }'
```

## Development Environment Setup

1. **Backend Setup**:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   make install
   cp env.template .env  # Configure environment variables
   make migrate
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   ```

3. **Start Development Servers**:
   ```bash
   # Terminal 1 - Backend
   cd backend && make dev
   
   # Terminal 2 - Frontend  
   cd frontend && npm run dev
   ```

## Production Deployment

The application deploys to AWS ECS Fargate with the following infrastructure:
- **API**: https://api.helppet.ai (ECS Fargate)
- **Frontend**: https://helppet.ai (S3 + CloudFront)
- **Database**: AWS RDS PostgreSQL
- **Storage**: S3 bucket for visit recordings

Use `make deploy` from the backend directory for automated deployment.