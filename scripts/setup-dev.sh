#!/bin/bash
# Setup development environment for OmniAudit

set -e

echo "Setting up OmniAudit development environment..."

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install package in development mode
echo "Installing OmniAudit in development mode..."
pip install -e ".[dev]"

# Install test dependencies
echo "Installing test dependencies..."
pip install pytest pytest-cov

# Run tests
echo "Running tests..."
pytest tests/unit/ -v

echo "✅ Development environment setup complete!"
echo "To activate: source venv/bin/activate"
echo "To run tests: pytest tests/unit/ -v"
