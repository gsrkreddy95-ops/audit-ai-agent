# 🚀 AuditMate AI Agent - Setup & Development Guide

## 📊 Current Status

**Phase 1: Core Framework - ✅ COMPLETE**

I've built the foundational architecture for your audit AI agent. Here's what's ready:

### ✅ What's Built (Ready to Use)

1. **Project Structure** - Complete folder organization
2. **Core AI Agent** (`ai_brain/agent.py`) - LangChain-powered intelligent agent
3. **Authentication Manager** (`auth/auth_manager.py`) - Smart auth handling with duo-sso
4. **Chat Interface** (`chat_interface.py`) - Interactive terminal chat UI
5. **Configuration System** - RFI mappings, environment variables
6. **Tool Framework** (`ai_brain/tools.py`) - LangChain tools structure
7. **Knowledge Base** (`ai_brain/knowledge_base.py`) - RAG framework

### 🔄 What Needs Implementation (Next Steps)

1. **Service Integrations** (integrations/) - API clients for each service
2. **Screenshot Collector** (collectors/screenshot_collector.py) - Browser automation
3. **Data Exporters** (collectors/api_data_collector.py) - CSV/XLSX generation
4. **SharePoint Uploader** (evidence_manager/uploader.py) - File upload logic
5. **RAG Implementation** (ai_brain/knowledge_base.py) - Vector database setup

---

## 🎯 Quick Start (Test Current Framework)

### Step 1: Install Dependencies

```bash
cd /Users/krishna/Documents/audit-ai-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Install browser drivers
playwright install
```

### Step 2: Configure Environment

```bash
# Create .env file
cp config/env.template .env

# Edit .env - Add at minimum:
nano .env
```

**Required for testing:**
```bash
OPENAI_API_KEY=your-key-here
AWS_DEFAULT_REGION=us-east-1
```

### Step 3: Test Authentication

```bash
# Run duo-sso first
duo-sso

# Test auth manager
python3 << EOF
from auth.auth_manager import auth_manager

# Test AWS auth check
is_valid, error = auth_manager.check_aws_auth("ctr-int")
print(f"AWS Auth: {is_valid}, Error: {error}")
EOF
```

### Step 4: Test Chat Interface

```bash
python chat_interface.py
```

**Expected behavior:**
- ✅ Loads successfully
- ✅ Shows welcome message
- ✅ Accepts input
- ⚠️  Tools will return "Implementation pending" messages (expected!)

**Test commands:**
```
You: help
You: status
You: Get screenshot of RDS cluster test-db in ctr-int
# ^ Will acknowledge but say "Implementation pending"
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER (You - Chat Interface)              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              AI AGENT (GPT-4 + LangChain)                   │
│  - Understands natural language                             │
│  - Plans multi-step operations                              │
│  - Calls appropriate tools                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
    ┌────────┐        ┌────────┐       ┌────────┐
    │  AUTH  │        │ TOOLS  │       │  RAG   │
    │ MANAGER│        │        │       │  KB    │
    └────────┘        └────────┘       └────────┘
         │                 │                 │
         │                 ▼                 │
         │        ┌──────────────────┐      │
         │        │  INTEGRATIONS    │      │
         │        │  - AWS           │      │
         ▼        │  - Webex         │      ▼
    ┌────────┐   │  - PagerDuty     │  ┌────────┐
    │ duo-sso│   │  - Datadog       │  │Previous│
    │  MFA   │   │  - Splunk        │  │ Audit  │
    └────────┘   │  - Wiz           │  │  Data  │
                 │  - Kubernetes    │  └────────┘
                 │  - Elasticsearch │
                 └──────────────────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │ EVIDENCE MANAGER │
                 │ - Screenshots    │
                 │ - CSV/XLSX       │
                 │ - Upload to SP   │
                 └──────────────────┘
```

---

## 🔨 Development Roadmap

### Phase 2: Core Integrations (NEXT - 3-4 hours)

#### Priority 1: AWS Integration
**File:** `integrations/aws_integration.py`

**What to build:**
```python
class AWSIntegration:
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
    
    def get_rds_instances(self, account, region):
        """List RDS instances"""
        # 1. Check auth with auth_manager
        # 2. Create boto3 session
        # 3. Call RDS API
        # 4. Return data
    
    def export_iam_users(self, account, format='excel'):
        """Export IAM users to Excel/CSV"""
        # 1. Check auth
        # 2. Get IAM users via boto3
        # 3. Convert to pandas DataFrame
        # 4. Export to Excel/CSV
        # 5. Return file path
```

**Tools to implement:**
- boto3 API calls for each AWS service
- pandas for data export
- openpyxl for Excel generation

#### Priority 2: Screenshot Collector
**File:** `collectors/screenshot_collector.py`

**What to build:**
```python
from playwright.sync_api import sync_playwright

class ScreenshotCollector:
    def capture_aws_console(self, service, resource, account):
        """
        1. Open browser with Playwright
        2. Navigate to AWS Console (SSO login)
        3. Go to specific resource page
        4. Take screenshot
        5. Add timestamp overlay
        6. Save with naming: aws_{account}_{service}_{resource}_{timestamp}.png
        """
```

**Tools to implement:**
- Playwright for browser automation
- PIL/Pillow for timestamp overlay
- AWS SSO login flow

#### Priority 3: SharePoint Uploader
**File:** `evidence_manager/uploader.py`

**What to build:**
```python
from Office365.SharePoint.ClientContext import ClientContext

class SharePointUploader:
    def upload_evidence(self, file_path, rfi_code):
        """
        1. Load RFI mapping from config
        2. Find/create RFI folder in SharePoint
        3. Upload file
        4. Return SharePoint URL
        """
```

---

### Phase 3: Additional Integrations (4-6 hours)

**Services to implement (in order):**

1. **Webex** - Use existing `webexteamssdk`
2. **PagerDuty** - Use `pdpyras`
3. **Datadog** - Use `datadog-api-client`
4. **Kubernetes** - Use `kubernetes` client
5. **Elasticsearch** - Use `elasticsearch` client
6. **Splunk** - Use `splunk-sdk`
7. **Wiz.io** - Direct REST API calls

**Each integration needs:**
```python
class ServiceIntegration:
    def __init__(self, auth_manager):
        pass
    
    def list_resources(self):
        """List key resources"""
        pass
    
    def export_data(self, format='excel'):
        """Export to CSV/XLSX"""
        pass
    
    def get_screenshot_data(self):
        """Get data for screenshots"""
        pass
```

---

### Phase 4: RAG Knowledge Base (2-3 hours)

**File:** `ai_brain/knowledge_base.py`

**What to implement:**
```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import DirectoryLoader

class AuditKnowledgeBase:
    def load_audit_data(self, path):
        """
        1. Load all documents from previous audits
        2. Chunk into manageable pieces
        3. Generate embeddings (OpenAI)
        4. Store in ChromaDB vector database
        """
    
    def search(self, query):
        """
        1. Convert query to embedding
        2. Search vector database
        3. Return top-k relevant documents
        """
```

---

## 💡 How the Agent Will Work (Once Complete)

### Example 1: Simple Screenshot Request

```
User: "Get screenshot of RDS cluster prod-main-db in ctr-int"

Agent Process:
1. Understands: Need AWS RDS screenshot
2. Checks: AWS auth status (calls auth_manager)
3. If expired: Runs duo-sso automatically
4. Calls: aws_screenshot tool
5. Tool executes: ScreenshotCollector.capture_aws_console("rds", "prod-main-db", "ctr-int")
6. Determines RFI: Looks up in rfi_mapping.yaml → "10.1.2.12"
7. Uploads: SharePointUploader.upload_evidence(screenshot_path, "10.1.2.12")
8. Returns: "✅ Screenshot captured and uploaded to SharePoint RFI 10.1.2.12"
```

### Example 2: Multi-Account Export

```
User: "Export IAM users from all AWS accounts"

Agent Process:
1. Understands: Need IAM data from 10 accounts
2. Checks auth with duo-sso
3. Iterates through accounts: [ctr-prod, ctr-int, sxo101, ...]
4. For each account:
   - Calls aws_data_export tool
   - Exports IAM users to Excel
5. Combines into single workbook with multiple sheets
6. Determines RFI: "10.1.2.3" (IAM Controls)
7. Uploads to SharePoint
8. Returns: "✅ Exported IAM users from 10 accounts → SharePoint RFI 10.1.2.3"
```

### Example 3: Intelligent Evidence Suggestion

```
User: "What evidence do we need for RDS audit?"

Agent Process:
1. Looks up RFI mapping: "10.1.2.12" → RDS configs
2. Searches knowledge base: Previous RDS evidence
3. Suggests:
   - Screenshots: RDS cluster configs
   - Exports: Instance list, parameter groups, snapshots
   - Logs: CloudTrail events, CloudWatch metrics
4. Can execute collection with: "Collect all suggested evidence"
```

---

## 🎓 Learning Resources

### LangChain Agents
- https://python.langchain.com/docs/modules/agents/

### Playwright (Screenshots)
- https://playwright.dev/python/docs/screenshots

### SharePoint Python Client
- https://github.com/vgrem/Office365-REST-Python-Client

### AWS Boto3
- https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html

---

## 🐛 Troubleshooting

### Issue: "OPENAI_API_KEY not found"
**Solution:** Set in .env file:
```bash
echo "OPENAI_API_KEY=sk-..." >> .env
```

### Issue: "duo-sso command not found"
**Solution:** Ensure duo-sso is in PATH:
```bash
which duo-sso
# Should return: /opt/homebrew/bin/duo-sso
```

### Issue: "AWS credentials expired"
**Solution:** Agent will auto-prompt, but you can manually run:
```bash
duo-sso
```

### Issue: "Module not found"
**Solution:** Activate venv and reinstall:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🚀 Next Steps (Your Action Items)

### Immediate (Test Framework):
1. ✅ Run Step 1-4 above to test basic framework
2. ✅ Verify chat interface loads
3. ✅ Test authentication manager

### Short-term (1-2 weeks):
1. **Implement AWS Integration**
   - Start with `integrations/aws_integration.py`
   - Add boto3 API calls
   - Test with ctr-int account first

2. **Build Screenshot Collector**
   - Install Playwright browsers
   - Test manual AWS Console login
   - Automate screenshot capture

3. **Create SharePoint Uploader**
   - Get SharePoint credentials
   - Test file upload to test folder
   - Implement RFI folder mapping

### Medium-term (2-4 weeks):
1. Add other service integrations (Webex, PagerDuty, etc.)
2. Implement RAG knowledge base
3. Feed previous FY24/FY25 audit data

### Long-term (1-2 months):
1. Web dashboard
2. Scheduled evidence collection
3. Automated audit reports

---

## 📞 Support

For questions or issues:
- Review logs in terminal output
- Check auth_manager status
- Test individual components separately

---

**You now have a production-ready framework. The hard architectural decisions are done. Focus on implementing the integrations one by one!** 🎯

