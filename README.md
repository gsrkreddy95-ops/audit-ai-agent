# 🧠 Intelligent Audit AI Agent

## 🎯 What This Agent Does

Your intelligent assistant for SOC2/ISO audit evidence collection that:

1. **DOWNLOADS & ANALYZES** previous year's screenshots (OCR + image recognition)
2. **UNDERSTANDS** what was collected (terminal outputs, AWS console, scripts)
3. **RUNS** Python/shell scripts if present
4. **REPLICATES** exact evidence with current data
5. **TIMESTAMPS** everything
6. **FLAGS** for manual review when uncertain

---

## ⚡ Key Intelligence Features

### **Visual Understanding (NEW!)**
- ✅ Downloads and analyzes previous screenshots
- ✅ OCR to read terminal outputs
- ✅ Detects screenshot types (terminal, AWS console, dashboards)
- ✅ Understands which AWS service/page was captured
- ✅ Identifies Python/shell scripts in screenshots

### **Script Execution**
- ✅ Finds associated Python/shell scripts
- ✅ Updates date parameters
- ✅ Runs scripts and captures output
- ✅ Takes screenshot of terminal with results

### **AWS Console Intelligence**
- ✅ Understands RDS backup config screenshots
- ✅ Identifies specific tabs/pages
- ✅ Extracts resource names (clusters, instances)
- ✅ Navigates to exact same page
- ✅ Captures fresh screenshot

### **Word Document Generation**
- ✅ Verifies conditions automatically
- ✅ Generates NEW explanations
- ✅ Writes "No occurrences found" when appropriate
- ✅ Flags for manual review when uncertain

---

## 📋 Example: Terminal Screenshot Analysis

**From your screenshot showing KMS key deletion search:**

```
Previous Year Evidence:
  📸 Screenshot shows: Python script execution with KMS search results
  🐍 Associated script: kms_key_deletion_search.py

Agent's Process:
  1. Downloads screenshot
  2. OCR analysis detects: "Searching for KMS Key Deletion events"
  3. Understands: This is a Python script execution result
  4. Finds: kms_key_deletion_search.py in same folder
  5. Updates: Date range in script (2025-01-01 to 2025-11-06)
  6. Runs: python3 kms_key_deletion_search.py
  7. Captures: Terminal screenshot with current results
  8. Names: KMS_Key_Deletion_Search_2025-11-06_15-30-45.png
```

---

## 📋 Example: AWS Console Screenshot

**RDS Backup Configuration:**

```
Previous Year Evidence:
  📸 Screenshot shows: RDS cluster backup configuration tab

Agent's Process:
  1. Downloads screenshot
  2. OCR + image analysis
  3. Detects: AWS Console, RDS service
  4. Identifies: "Backup" configuration tab
  5. Extracts: Cluster name "prod-main-db"
  6. Navigates to: AWS Console → RDS → prod-main-db → Backup tab
  7. Captures: Fresh screenshot
  8. Names: RDS_prod-main-db_backup_2025-11-06_15-30-45.png
```

---

## 🚀 Quick Start

### **1. Install (5 minutes)**
```bash
cd /Users/krishna/Documents/audit-ai-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Tesseract OCR (for screenshot analysis)
brew install tesseract
```

### **2. Configure (.env file)**
```bash
cp config/env.template .env

# Edit .env:
LLM_PROVIDER=bedrock  # Or openai, anthropic, azure
AWS_PROFILE=ctr-int
AWS_REGION=us-east-1

# SharePoint (if using)
SHAREPOINT_CLIENT_ID=your-client-id
SHAREPOINT_CLIENT_SECRET=your-secret
```

### **3. Run duo-sso**
```bash
duo-sso
# Approve MFA in browser
```

### **4. Test Agent**
```python
from evidence_manager.smart_evidence_analyzer import SmartEvidenceAnalyzer
from integrations.sharepoint_integration import SharePointIntegration

# Initialize
sp = SharePointIntegration()
analyzer = SmartEvidenceAnalyzer(sp)

# Analyze previous year's evidence intelligently
analysis = analyzer.analyze_rfi_folder_intelligent(
    rfi_code="10.1.2.12",
    product="XDR",
    previous_year="FY24"
)

# Result: Intelligent analysis with visual understanding
# - Screenshots analyzed via OCR
# - Scripts identified
# - Exact replication instructions
```

---

## 📁 Project Structure

```
audit-ai-agent/
├── README.md                    ⭐ This file
├── SETUP_GUIDE.md               Setup instructions
├── CORRECTED_FINAL_SUMMARY.md   What was corrected
├── INTELLIGENT_EVIDENCE_COLLECTION.md  Detailed workflow
│
├── ai_brain/
│   ├── agent.py                 Main AI agent (LangChain)
│   ├── llm_config.py            Flexible LLM (4 providers)
│   └── tools.py                 LangChain tools
│
├── auth/
│   └── auth_manager.py          Smart duo-sso handling
│
├── integrations/
│   ├── sharepoint_integration.py   Dynamic RFI discovery
│   └── aws_integration.py          Multi-account AWS
│
├── evidence_manager/
│   ├── smart_evidence_analyzer.py  ⭐ NEW! Visual intelligence
│   ├── evidence_replicator.py      Collects fresh evidence
│   └── word_doc_handler.py         Intelligent Word docs
│
└── chat_interface.py            Interactive terminal chat
```

---

## 💡 Key Advantages

| Feature | Capability |
|---------|-----------|
| **Visual Intelligence** | OCR + image analysis of screenshots |
| **Script Execution** | Finds and runs Python/shell scripts |
| **AWS Console Understanding** | Identifies exact pages/tabs |
| **No Hardcoding** | Learns from previous evidence |
| **Timestamps** | All evidence properly timestamped |
| **Smart Decisions** | Flags uncertain cases |
| **Multi-Service** | AWS, PagerDuty, Datadog, Splunk, etc. |
| **Flexible LLM** | Supports 4 providers (Bedrock, GPT-4, Claude, Azure) |

---

## 📚 Documentation

1. **README.md** (This file) - Quick start
2. **SETUP_GUIDE.md** - Detailed setup instructions
3. **CORRECTED_FINAL_SUMMARY.md** - What changed after clarifications
4. **INTELLIGENT_EVIDENCE_COLLECTION.md** - Complete workflow with examples

---

## 🎊 What Makes This Intelligent

**Traditional approach:**
- Read filenames → guess what to collect

**This agent:**
- Downloads screenshots → OCR analysis → understands content →
  finds scripts → runs them → captures output → 
  navigates AWS console → exact page replication →
  generates explanations → flags uncertainties

**Result: Fresh, accurate, timestamped, auditor-ready evidence!** 🚀

---

## 💰 Cost Estimate

- **LLM (AWS Bedrock recommended):** $5-15/month
- **Evidence collection time:** 2-3 hours (vs 2-3 weeks manual)
- **Storage:** ~2-3 MB per RFI

---

## 🚀 Start Collecting Evidence

```bash
cd /Users/krishna/Documents/audit-ai-agent
source venv/bin/activate
python3 chat_interface.py

# Try:
"Analyze RFI 10.1.2.12 from last year and collect fresh evidence"
"Run KMS key deletion script and capture results"
"Get RDS backup config screenshot for prod-cluster"
```

---

**Your audit evidence collection is now truly intelligent!** 🧠✅
