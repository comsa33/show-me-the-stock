# Stock Dashboard - Development & Deployment Commands

.PHONY: help install dev build test clean docker-build docker-dev docker-prod logs

# Default target
help:
	@echo "📈 Stock Dashboard - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install     - Install all dependencies"
	@echo "  make dev         - Start development servers"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linting"
	@echo "  make format      - Format code"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-dev  - Start development with Docker"
	@echo "  make docker-prod - Start production with Docker"
	@echo "  make docker-build- Build Docker images"
	@echo "  make logs        - View Docker logs"
	@echo "  make clean       - Clean up Docker resources"
	@echo ""
	@echo "Production:"
	@echo "  make build       - Build for production"
	@echo "  make deploy      - Deploy to production"

# Install dependencies
install:
	@echo "📦 Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Dependencies installed!"

# Development servers
dev:
	@echo "🚀 Starting development servers..."
	@echo "Backend will be available at http://localhost:8000"
	@echo "Frontend will be available at http://localhost:3000"
	@echo "API docs will be available at http://localhost:8000/docs"
	docker-compose up --build

# Build for production
build:
	@echo "🏗️ Building for production..."
	cd frontend && npm run build
	@echo "✅ Production build complete!"

# Run tests
test:
	@echo "🧪 Running backend tests..."
	cd backend && python -m pytest
	@echo "🧪 Running frontend tests..."
	cd frontend && npm test -- --watchAll=false
	@echo "✅ Tests complete!"

# Linting
lint:
	@echo "🔍 Linting backend code..."
	cd backend && flake8 app/
	@echo "🔍 Linting frontend code..."
	cd frontend && npm run lint
	@echo "✅ Linting complete!"

# Code formatting
format:
	@echo "💅 Formatting backend code..."
	cd backend && black app/ && isort app/
	@echo "💅 Formatting frontend code..."
	cd frontend && npm run format
	@echo "✅ Formatting complete!"

# Docker commands
docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose build
	@echo "✅ Docker images built!"

docker-dev:
	@echo "🐳 Starting development environment with Docker..."
	docker-compose up --build

docker-prod:
	@echo "🐳 Starting production environment with Docker..."
	docker-compose --profile production up --build -d

logs:
	@echo "📋 Showing Docker logs..."
	docker-compose logs -f

# Clean up
clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "🧹 Cleaning up build files..."
	cd frontend && rm -rf build/ node_modules/.cache
	cd backend && find . -type f -name "*.pyc" -delete
	cd backend && find . -type d -name "__pycache__" -delete
	@echo "✅ Cleanup complete!"

# Production deployment
deploy:
	@echo "🚀 Deploying to production..."
	@echo "⚠️  Make sure to set production environment variables!"
	docker-compose --profile production up --build -d
	@echo "✅ Deployment complete!"
	@echo "🌐 Application should be available at your configured domain"

# Health check
health:
	@echo "🔍 Checking application health..."
	curl -f http://localhost:8000/health || exit 1
	curl -f http://localhost:3000/health || exit 1
	@echo "✅ Application is healthy!"

# Database migrations (for future use)
migrate:
	@echo "🗄️ Running database migrations..."
	cd backend && alembic upgrade head
	@echo "✅ Migrations complete!"

# Generate API documentation
docs:
	@echo "📚 Generating API documentation..."
	cd backend && python -c "import app.main; print('API docs available at http://localhost:8000/docs')"
	@echo "✅ Documentation ready!"