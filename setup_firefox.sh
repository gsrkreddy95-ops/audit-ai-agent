#!/bin/bash

# Firefox Browser Setup Script
# Fixes Chrome update prompt issue

echo "🦊 Setting up Firefox for Audit Agent..."
echo ""

# Navigate to agent directory
cd /Users/krishna/Documents/audit-ai-agent || { echo "Error: Could not find audit-ai-agent directory"; exit 1; }

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate || { echo "Error: Could not activate venv"; exit 1; }

# Install Firefox for Playwright
echo ""
echo "🔽 Installing Firefox browser..."
echo "(This will download ~70MB, please wait...)"
playwright install firefox

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Firefox installed successfully!"
else
    echo ""
    echo "❌ Firefox installation failed"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  No .env file found. Creating from template..."
    cp config/env.template .env
    echo "✅ Created .env file. Please configure it before running the agent."
fi

# Update .env with Firefox browser setting (if not already set)
if ! grep -q "SHAREPOINT_BROWSER" .env; then
    echo ""
    echo "📝 Adding Firefox browser configuration to .env..."
    echo "" >> .env
    echo "# Browser Configuration (Firefox avoids Chrome update prompts)" >> .env
    echo "SHAREPOINT_BROWSER=firefox" >> .env
    echo "AWS_SCREENSHOT_BROWSER=firefox" >> .env
    echo "✅ Browser configuration added to .env"
else
    echo ""
    echo "ℹ️  Browser configuration already exists in .env"
fi

# Optional: Clear old browser profiles
echo ""
read -p "🗑️  Clear old browser profiles? (recommended if switching from Chromium) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Clearing old browser profiles..."
    rm -rf ~/.audit-agent-browser/
    rm -rf ~/.audit-agent-aws-browser/
    echo "✅ Old profiles cleared"
fi

# Success message
echo ""
echo "🎉 Firefox setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Make sure your .env file is configured"
echo "2. Start the agent: ./QUICK_START.sh"
echo "3. Look for: '🦊 Using Firefox browser'"
echo ""
echo "✅ No more Chrome update prompts!"

