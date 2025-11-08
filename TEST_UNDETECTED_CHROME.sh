#!/bin/bash
# Quick test script for undetected-chromedriver

cd /Users/krishna/Documents/audit-ai-agent

echo "🧪 Testing undetected-chromedriver with Cisco Duo..."
echo ""

# Activate venv
source venv/bin/activate

# Install if needed
pip install undetected-chromedriver==3.5.5 -q

# Run test
python3 test_undetected_chrome.py

