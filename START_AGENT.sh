#!/bin/bash

# AuditMate AI Agent Startup Script
# ===================================

cd /Users/krishna/Documents/audit-ai-agent

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                           ║"
echo "║                   🚀 STARTING AUDIT AI AGENT 🚀                          ║"
echo "║                                                                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ READY:"
echo "  • AWS Bedrock (Claude 3.5 Sonnet)"
echo "  • duo-sso MFA (automatic)"
echo "  • SharePoint browser access"
echo "  • Scrolling screenshots (87+ items!)"
echo "  • Multi-account AWS (8 accounts)"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Activate virtual environment
source venv/bin/activate

# Run the agent
python3 chat_interface.py

