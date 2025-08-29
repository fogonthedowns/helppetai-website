# FastAPI Application

A modern, production-ready FastAPI application built with best practices, type safety, and comprehensive documentation.

## 🚀 Features

- **FastAPI Framework**: Modern, fast web framework for building APIs with Python 3.8+
- **Type Safety**: Full type hints throughout the codebase using Pydantic models
- **Automatic Documentation**: Interactive API documentation with Swagger UI and ReDoc
- **CORS Support**: Configurable Cross-Origin Resource Sharing
- **Error Handling**: Comprehensive exception handling with structured error responses
- **Health Checks**: Built-in health, readiness, and liveness endpoints
- **Configuration Management**: Environment-based configuration using Pydantic Settings
- **Logging**: Structured logging with request tracking
- **Modular Architecture**: Clean separation of concerns with organized code structure

## 📋 Requirements

- Python 3.8 or higher
- pip (Python package installer)

## 🛠️ Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Quick Start

### Running the Application

1. **Start the development server:**
   ```bash
   uvicorn main:app --reload
   ```
   
   Or run directly from the src module:
   ```bash
   uvicorn src.main:app --reload
   ```

2. **Access the application:**
   - **API Base URL**: http://localhost:8000
   - **Interactive API Docs (Swagger UI)**: http://localhost:8000/docs
   - **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
   - **Health Check**: http://localhost:8000/health

### Production Deployment

For production deployment:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📖 API Documentation

### Health Endpoints

- `GET /health` - Application health status
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check
- `GET /version` - Application version

### API Endpoints

All main API endpoints are prefixed with `/api/v1`:

- `GET /api/v1/items` - Retrieve all items (with filtering and pagination)
- `GET /api/v1/items/{item_id}` - Get specific item by ID
- `POST /api/v1/items` - Create new item
- `PUT /api/v1/items/{item_id}` - Update existing item
- `DELETE /api/v1/items/{item_id}` - Delete item

### Example API Usage

**Create a new item:**
```bash
curl -X POST "http://localhost:8000/api/v1/items" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Example Item",
       "description": "This is an example item",
       "category": "example",
       "tags": ["demo", "test"],
       "is_active": true
     }'
```

**Get all items:**
```bash
curl "http://localhost:8000/api/v1/items"
```

**Get items with filtering:**
```bash
curl "http://localhost:8000/api/v1/items?category=example&is_active=true&limit=10"
```

## ⚙️ Configuration

The application uses environment variables for configuration. Create a `.env` file in the root directory:

```env
# App Configuration
APP_NAME=FastAPI Application
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=development

# Server Configuration
HOST=0.0.0.0
PORT=8000

# API Configuration
API_V1_PREFIX=/api/v1
DOCS_URL=/docs
REDOC_URL=/redoc

# Security Configuration
CORS_ORIGINS=*
CORS_METHODS=*
CORS_HEADERS=*

# Logging
LOG_LEVEL=INFO

# Database (optional)
# DATABASE_URL=sqlite:///app.db
```

## 🏗️ Project Structure

```
backend/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── pyproject.toml         # Project configuration
├── .gitignore            # Git ignore patterns
├── README.md             # This file
└── src/                  # Source code directory
    ├── __init__.py      # Package initialization
    ├── main.py          # FastAPI application instance
    ├── config.py        # Configuration settings
    ├── models/          # Pydantic models
    │   ├── __init__.py
    │   └── base.py      # Base models and schemas
    └── routes/          # API endpoints
        ├── __init__.py
        ├── health.py    # Health check endpoints
        └── api.py       # Main API endpoints
```

## 🧪 Testing

To run tests (if test dependencies are installed):

```bash
# Install development dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run tests with coverage
pytest --cov=src
```

## 🔧 Development

### Code Quality Tools

Install development dependencies:
```bash
pip install black isort flake8 mypy
```

Format code:
```bash
black src/
isort src/
```

Lint code:
```bash
flake8 src/
mypy src/
```

### Adding New Endpoints

1. Create your Pydantic models in `src/models/base.py`
2. Add your route handlers in `src/routes/api.py` or create a new route file
3. Register new route modules in `src/routes/__init__.py`

### Environment Variables

All configuration is handled through the `src/config.py` file using Pydantic Settings. Add new configuration options by extending the `Settings` class.

## 🐳 Docker Support

Create a `Dockerfile` for containerization:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support and questions:
- Check the [API documentation](http://localhost:8000/docs) when running locally
- Review the code structure and comments
- Open an issue for bugs or feature requests

---

**Happy coding! 🎉**
