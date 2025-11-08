#!/bin/bash
# Quick Test Script for RDS Timeout Fixes
# ========================================

set -e

CLUSTER="prod-conure-aurora-cluster-phase2"
REGION="us-east-1"

echo "=================================================="
echo "RDS Tab Timeout Fix - Quick Test"
echo "=================================================="
echo ""

# Check which Python files changed
echo "📋 Modified Files:"
echo "  ✅ ai_brain/tool_executor.py (timeout: 30s → 180s for RDS)"
echo "  ✅ tools/rds_navigator_enhanced.py (added content anchors)"
echo "  ✅ tools/rds_screenshot_playwright.py (NEW - Playwright alternative)"
echo ""

# Check if Playwright available
if python3 -c "import playwright" 2>/dev/null; then
    PLAYWRIGHT_AVAILABLE=true
    echo "✅ Playwright installed"
else
    PLAYWRIGHT_AVAILABLE=false
    echo "⚠️  Playwright not installed (optional)"
fi
echo ""

echo "=================================================="
echo "Test Options:"
echo "=================================================="
echo ""
echo "1️⃣  Test Selenium with Extended Timeouts (180s)"
echo "   - Restart agent"
echo "   - Run RDS screenshot via agent"
echo "   - Should succeed now (was timing out at 30s)"
echo ""
echo "2️⃣  Test Playwright Alternative (Recommended)"
echo "   - Direct script execution"
echo "   - More stable, faster"
echo "   - Requires: pip install playwright"
echo ""

# Prompt user
read -p "Choose test (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "=================================================="
    echo "Option 1: Testing Selenium (Extended Timeouts)"
    echo "=================================================="
    echo ""
    
    # Kill existing agent
    echo "🛑 Stopping existing agent..."
    pkill -f "python3 chat_interface.py" || true
    sleep 2
    
    # Clear cache
    echo "🗑️  Clearing Python cache..."
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    echo ""
    echo "✅ Ready to test!"
    echo ""
    echo "Now run:"
    echo "  python3 chat_interface.py"
    echo ""
    echo "Then try:"
    echo "  capture rds screenshot for $CLUSTER in $REGION"
    echo ""
    echo "Expected behavior:"
    echo "  - UniversalScreenshotEnhanced initialized (timeout=180)"
    echo "  - Tab clicks should wait up to 3 minutes"
    echo "  - Logs show: '✅ Tab content verified (found: Parameter group)'"
    echo "  - Screenshots saved successfully"
    echo ""
    
elif [ "$choice" = "2" ]; then
    echo ""
    echo "=================================================="
    echo "Option 2: Testing Playwright Alternative"
    echo "=================================================="
    echo ""
    
    if [ "$PLAYWRIGHT_AVAILABLE" = false ]; then
        echo "📦 Installing Playwright..."
        pip3 install playwright
        python3 -m playwright install chromium
        echo ""
    fi
    
    echo "🚀 Running Playwright script..."
    echo ""
    echo "Command:"
    echo "  python3 tools/rds_screenshot_playwright.py \\"
    echo "    --region $REGION \\"
    echo "    --identifier $CLUSTER \\"
    echo "    --stamp \\"
    echo "    --verbose \\"
    echo "    --no-headless"
    echo ""
    
    read -p "Press Enter to execute, or Ctrl+C to abort..."
    
    python3 tools/rds_screenshot_playwright.py \
        --region "$REGION" \
        --identifier "$CLUSTER" \
        --stamp \
        --verbose \
        --no-headless
    
    echo ""
    echo "✅ Test complete! Check rds_screenshots/ directory"
    
else
    echo "Invalid choice. Exiting."
    exit 1
fi

echo ""
echo "=================================================="
echo "📊 Results Checklist:"
echo "=================================================="
echo ""
echo "✅ No timeout errors?"
echo "✅ Screenshots contain actual data (not loading spinners)?"
echo "✅ Watermarks visible in bottom-right?"
echo "✅ Both Configuration and Maintenance & backups captured?"
echo ""
echo "If YES to all: SUCCESS! ✨"
echo "If NO to any: Check RDS_TAB_TIMEOUT_SOLUTION.md for troubleshooting"
echo ""
