#!/bin/bash

# Kencot Bot V2.0 Setup Script
# Run this script to set up the project quickly

echo "=========================================="
echo "🤖 KENCOT BOT V2.0 - SETUP SCRIPT"
echo "=========================================="
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "⚠️  Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created - Please edit it with your API keys!"
    echo "⚠️  Important: Add your GEMINI_API_KEY in .env"
else
    echo "⚠️  .env file already exists"
fi
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data
echo "✅ Directories created"
echo ""

# Check MongoDB
echo "🗄️  Checking MongoDB..."
if command -v mongod &> /dev/null; then
    echo "✅ MongoDB is installed"
    echo "   Make sure MongoDB is running: sudo systemctl start mongodb"
else
    echo "⚠️  MongoDB not found. Please install MongoDB first:"
    echo "   Ubuntu/Debian: sudo apt install mongodb"
    echo "   MacOS: brew install mongodb-community"
fi
echo ""

# Test import
echo "🧪 Testing imports..."
python3 -c "import pymongo; import openai; from sentence_transformers import SentenceTransformer; print('✅ All core imports successful!')"
echo ""

echo "=========================================="
echo "✅ SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Start MongoDB: sudo systemctl start mongodb"
echo "3. Run bot in CLI mode: python -m src.main --cli"
echo ""
echo "For more info, check README.md"
echo ""