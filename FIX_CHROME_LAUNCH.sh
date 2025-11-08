#!/bin/bash

echo "🔧 Fixing Chrome Launch Issues"
echo "================================"
echo ""

# Kill any stale Chrome processes
echo "1. Killing stale Chrome processes..."
pkill -9 "Google Chrome" 2>/dev/null || true
pkill -9 "chrome" 2>/dev/null || true
pkill -9 "chromedriver" 2>/dev/null || true
sleep 2
echo "✅ Done"
echo ""

# Clean up stale user data directories
echo "2. Cleaning up browser profiles..."
rm -rf ~/.audit-agent-universal-selenium/Singleton* 2>/dev/null || true
rm -rf ~/.audit-agent-universal-selenium/SingletonLock 2>/dev/null || true
rm -rf ~/.audit-agent-universal-selenium/SingletonCookie 2>/dev/null || true
echo "✅ Done"
echo ""

# Check if Chrome is installed
echo "3. Checking Chrome installation..."
if [ -d "/Applications/Google Chrome.app" ]; then
    echo "✅ Chrome is installed at: /Applications/Google Chrome.app"
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
else
    echo "❌ Chrome not found. Please install Chrome from: https://www.google.com/chrome/"
    exit 1
fi
echo ""

echo "================================"
echo "✅ Cleanup complete!"
echo ""
echo "Now try running your agent again:"
echo "  ./QUICK_START.sh"
echo ""

