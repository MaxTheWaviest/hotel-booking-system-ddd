#!/bin/bash

# scripts/setup.sh
set -e

echo "Setting up Hotel Booking System..."

# Create project structure
echo "Creating project structure..."
mkdir -p src/{domain,application,infrastructure,api}
mkdir -p tests/{domain,application,infrastructure,api}

# Create virtual environment using uv
echo "Creating virtual environment..."
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies directly (without editable install)
echo "Installing dependencies..."
uv pip install \
    "fastapi>=0.104.0" \
    "uvicorn[standard]>=0.24.0" \
    "sqlalchemy>=2.0.0" \
    "pydantic>=2.0.0" \
    "python-multipart>=0.0.6" \
    "email-validator>=2.0.0" \
    "httpx>=0.24.0" \
    "pytest>=7.4.0" \
    "pytest-cov>=4.1.0" \
    "pytest-asyncio>=0.21.0" \
    "ruff>=0.1.0"

# Create simple pyproject.toml (without the problematic editable install)
echo "Creating pyproject.toml..."
cat > pyproject.toml << 'EOF'
[project]
name = "hotel-booking-system"
version = "0.1.0"
description = "Domain-Driven Design Hotel Booking System"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "python-multipart>=0.0.6",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.1.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=70"

[tool.ruff]
line-length = 88
target-version = "py313"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "S", "B", "A", "COM", "C4", "DTZ", "EM", "ISC", "G", "INP", "PIE", "T20", "PYI", "PT", "Q", "RSE", "RET", "SLF", "SIM", "TID", "TCH", "ARG", "PTH", "ERA", "PD", "PGH", "PL", "TRY", "NPY", "RUF"]
ignore = ["S101", "S311"]
EOF

# Create __init__.py files
echo "Creating __init__.py files..."
touch src/__init__.py
touch src/domain/__init__.py
touch src/application/__init__.py
touch src/infrastructure/__init__.py
touch src/api/__init__.py

touch tests/__init__.py
touch tests/domain/__init__.py
touch tests/application/__init__.py
touch tests/infrastructure/__init__.py
touch tests/api/__init__.py

# Add src to Python path for development
echo "Setting up Python path..."
echo "export PYTHONPATH=\"\${PYTHONPATH}:\$(pwd)/src\"" >> .venv/bin/activate

echo ""
echo "✅ Project structure created successfully!"
echo "📁 Virtual environment created at .venv/"
echo "🔧 Dependencies installed"
echo "🐍 Python path configured"
echo ""
echo "Next steps:"
echo "1. Run 'source .venv/bin/activate' to activate the environment"
echo "2. Create your domain model files"
echo "3. Run './scripts/test.sh' to run tests"
echo "4. Run './scripts/run.sh' to start the server"
