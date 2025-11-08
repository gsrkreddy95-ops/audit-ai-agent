#!/bin/bash

# Quick start script for AuditMate AI Agent
# Usage: ./QUICK_START.sh

cd /Users/krishna/Documents/audit-ai-agent
source venv/bin/activate

echo "🤖 Starting AuditMate AI Agent..."
echo ""
echo "💡 To test BCR-06.01 evidence collection, type:"
echo "   Review and collect evidence for RFI BCR-06.01 under XDR Platform"
echo ""

python3 chat_interface.py

