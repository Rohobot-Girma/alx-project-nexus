#!/bin/bash

# Setup script for Movie Recommendation Backend
# This script sets up the development environment

set -e

echo "🎬 Setting up Movie Recommendation Backend..."

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating environment configuration..."
    cp env.example .env
    echo "📝 Please edit .env file with your configuration"
else
    echo "✅ Environment file already exists"
fi

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Create superuser (optional)
echo "👤 Creating superuser..."
python manage.py createsuperuser --noinput --username admin --email admin@example.com || echo "Superuser already exists or creation failed"

# Collect static files
echo "📄 Collecting static files..."
python manage.py collectstatic --noinput

# Load initial data (optional)
echo "🎭 Syncing initial movie data..."
python manage.py sync_tmdb_data --pages 2 || echo "TMDB sync failed (check API key)"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Add your TMDb API key to .env"
echo "3. Run 'python manage.py runserver' to start the development server"
echo "4. Visit http://localhost:8000/api/docs/ for API documentation"
echo ""
echo "For production deployment, see README.md"
