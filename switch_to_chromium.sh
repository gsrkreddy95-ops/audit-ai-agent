#!/bin/bash
# Switch from Firefox to Chromium for better Cisco Duo compatibility

cd /Users/krishna/Documents/audit-ai-agent

echo "🔧 Switching to Chromium browser..."

# Update .env file
sed -i '' 's/SHAREPOINT_BROWSER=firefox/SHAREPOINT_BROWSER=chromium/g' .env
sed -i '' 's/AWS_SCREENSHOT_BROWSER=firefox/AWS_SCREENSHOT_BROWSER=chromium/g' .env

echo "✅ Browser switched to Chromium!"
echo ""
echo "📋 Updated settings:"
grep "BROWSER" .env
echo ""
echo "🧹 Clearing browser cache..."
./clear_browser_cache.sh

echo ""
echo "✅ Done! Restart the agent:"
echo "   ./QUICK_START.sh"

