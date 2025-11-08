#!/bin/bash

# Complete Intelligent Agent Setup Script
# Installs all dependencies for SharePoint learning and file analysis

echo "════════════════════════════════════════════════════════════════"
echo "🧠 Intelligent AI Agent - Complete Setup"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $python_version detected"
echo ""

# Install core dependencies
echo "📦 Installing core dependencies..."
pip3 install --quiet --upgrade pip
pip3 install --quiet -r requirements.txt
echo "✅ Core dependencies installed"
echo ""

# Install file analysis dependencies
echo "📄 Installing file analysis dependencies..."
pip3 install --quiet pytesseract==0.3.10
pip3 install --quiet Pillow==10.1.0
pip3 install --quiet pandas==2.1.4
pip3 install --quiet openpyxl==3.1.2
pip3 install --quiet python-docx==1.1.0
pip3 install --quiet PyPDF2==3.0.1
echo "✅ File analysis dependencies installed"
echo ""

# Check for tesseract OCR binary
echo "🔍 Checking for tesseract OCR..."
if command -v tesseract &> /dev/null; then
    tesseract_version=$(tesseract --version 2>&1 | head -n 1)
    echo "✅ Tesseract installed: $tesseract_version"
else
    echo "⚠️  Tesseract not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install tesseract
            echo "✅ Tesseract installed via Homebrew"
        else
            echo "❌ Homebrew not found. Please install Homebrew first:"
            echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            echo "   Then run: brew install tesseract"
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr
        echo "✅ Tesseract installed via apt"
    else
        echo "⚠️  Please install tesseract manually for your OS"
    fi
fi
echo ""

# Verify installations
echo "✓ Verifying installations..."
echo ""

# Python packages
python3 -c "import pytesseract" 2>/dev/null && echo "✅ pytesseract" || echo "❌ pytesseract"
python3 -c "from PIL import Image" 2>/dev/null && echo "✅ Pillow" || echo "❌ Pillow"
python3 -c "import pandas" 2>/dev/null && echo "✅ pandas" || echo "❌ pandas"
python3 -c "import openpyxl" 2>/dev/null && echo "✅ openpyxl" || echo "❌ openpyxl"
python3 -c "from docx import Document" 2>/dev/null && echo "✅ python-docx" || echo "❌ python-docx"
python3 -c "import PyPDF2" 2>/dev/null && echo "✅ PyPDF2" || echo "❌ PyPDF2"
python3 -c "from rich.console import Console" 2>/dev/null && echo "✅ rich" || echo "❌ rich"
python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null && echo "✅ playwright" || echo "❌ playwright"

echo ""

# Install playwright browsers if needed
echo "🌐 Setting up Playwright browsers..."
if python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
    python3 -m playwright install chromium
    echo "✅ Playwright Chromium browser installed"
else
    echo "⚠️  Playwright not found, skipping browser install"
fi
echo ""

# Create directories
echo "📁 Creating evidence directories..."
mkdir -p ~/Documents/audit-evidence/FY2025
mkdir -p ~/Documents/audit-evidence/_learning_cache
echo "✅ Directories created"
echo ""

# Environment check
echo "🔍 Checking environment variables..."
if [ -z "$LLM_PROVIDER" ]; then
    echo "⚠️  LLM_PROVIDER not set (required for Claude analysis)"
    echo "   Run: export LLM_PROVIDER=bedrock"
else
    echo "✅ LLM_PROVIDER=$LLM_PROVIDER"
fi

if [ -z "$AWS_BEDROCK_REGION" ] && [ "$LLM_PROVIDER" == "bedrock" ]; then
    echo "⚠️  AWS_BEDROCK_REGION not set (required for Bedrock)"
    echo "   Run: export AWS_BEDROCK_REGION=us-east-1"
else
    echo "✅ AWS_BEDROCK_REGION=${AWS_BEDROCK_REGION:-not needed}"
fi

if [ -z "$SHAREPOINT_SITE_URL" ]; then
    echo "⚠️  SHAREPOINT_SITE_URL not set (required for uploads)"
    echo "   Run: export SHAREPOINT_SITE_URL=https://yourcompany.sharepoint.com/sites/audit"
else
    echo "✅ SHAREPOINT_SITE_URL set"
fi
echo ""

# Test run
echo "🧪 Running quick test..."
python3 -c "
from evidence_manager.llm_evidence_analyzer import LLMEvidenceAnalyzer
from evidence_manager.sharepoint_evidence_learner import SharePointEvidenceLearner
print('✅ All modules importable')
" 2>/dev/null && echo "✅ Module imports successful" || echo "⚠️  Some modules failed to import (may need LLM config)"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ Setup Complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📚 Next Steps:"
echo "   1. Configure environment variables (see above)"
echo "   2. Run: python3 chat_interface.py"
echo "   3. Try: 'Learn from [SharePoint URL]'"
echo ""
echo "📖 Documentation:"
echo "   • COMPLETE_INTELLIGENT_AGENT_GUIDE.md - User guide"
echo "   • IMPLEMENTATION_COMPLETE_FINAL.md - Technical details"
echo ""
echo "🚀 Ready to use!"
