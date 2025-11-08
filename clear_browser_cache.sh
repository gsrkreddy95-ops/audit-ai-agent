#!/bin/bash

# Clear Browser Cache and Force Re-authentication
echo "🧹 Clearing browser cache and profiles..."

# Remove SharePoint browser profile
if [ -d ~/.audit-agent-browser ]; then
    rm -rf ~/.audit-agent-browser
    echo "✅ Cleared SharePoint browser profile"
else
    echo "ℹ️  No SharePoint browser profile found"
fi

# Remove AWS browser profile
if [ -d ~/.audit-agent-aws-browser ]; then
    rm -rf ~/.audit-agent-aws-browser
    echo "✅ Cleared AWS browser profile"
else
    echo "ℹ️  No AWS browser profile found"
fi

echo ""
echo "🎉 Cache cleared! Next agent run will prompt for fresh authentication."
echo ""
echo "📋 Next steps:"
echo "1. Start the agent: cd /Users/krishna/Documents/audit-ai-agent && ./QUICK_START.sh"
echo "2. Complete authentication when prompted"
echo "3. Your session will be saved for future runs"

