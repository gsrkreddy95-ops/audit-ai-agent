# 🏗️ Architecture Explained: Security & Intelligence

## Your Questions Answered:

### ❓ **"Does Claude calling mean it triggers agent to connect?"**

**YES! But it's secure.** Here's exactly how it works:

---

## 🔒 **Secure Architecture**

```
┌───────────────────────────────────────────────────────────┐
│  YOUR LOCAL MACHINE (MacBook)                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Audit AI Agent (Python process)                    │  │
│  │  • Has YOUR credentials                             │  │
│  │  • Can access SharePoint (your browser)             │  │
│  │  • Can access AWS (your duo-sso)                    │  │
│  │  • Executes tools locally                           │  │
│  └─────────────────────────────────────────────────────┘  │
│                         │                                  │
│                         │ Sends request + tool definitions │
│                         ▼                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Claude 3.5 in AWS Bedrock (Thinking Brain)         │  │
│  │  • Reads your request                               │  │
│  │  • Reads tool descriptions                          │  │
│  │  • Decides: "I need sharepoint_review tool"         │  │
│  │  • Returns: "Call this tool with these params"      │  │
│  │  • NO ACCESS to SharePoint/AWS!                     │  │
│  │  • NO ACCESS to your credentials!                   │  │
│  └─────────────────────────────────────────────────────┘  │
│                         │                                  │
│                         │ Returns tool call decision       │
│                         ▼                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Agent Receives Decision & EXECUTES                  │  │
│  │  • Opens YOUR browser to SharePoint                 │  │
│  │  • Uses YOUR AWS credentials                        │  │
│  │  • Collects evidence locally                        │  │
│  │  • Sends results back to Claude                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                         │                                  │
│                         │ Results                          │
│                         ▼                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Claude Processes Results                            │  │
│  │  • Reads: "Found 9 RDS screenshots"                 │  │
│  │  • Decides: "I should ask user about AWS account"   │  │
│  │  • Returns: "Which production account?"             │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

---

## 🔑 **Key Security Points:**

### ✅ **What Claude CAN Do:**
- Read your questions
- Read tool descriptions
- Decide which tools to use
- Decide what parameters to pass
- Process results from tools
- Generate responses

### ❌ **What Claude CANNOT Do:**
- Access SharePoint directly
- Access AWS directly
- Use your credentials
- Execute tools (only decides which to call)
- Connect to any external systems

### ✅ **What YOUR Local Agent Does:**
- Receives Claude's tool call decisions
- **Executes tools using YOUR credentials**
- Connects to SharePoint (your browser session)
- Runs duo-sso for AWS (your MFA)
- Collects evidence locally on your machine
- Sends results back to Claude for next decision

---

## 🎯 **Example Flow:**

### **1. You Ask:**
```
"Review evidence for RFI BCR-06.01 under XDR Platform and collect for FY2025"
```

### **2. Agent Sends to Claude:**
```json
{
  "message": "Review evidence for RFI BCR-06.01...",
  "tools": [
    {
      "name": "sharepoint_review_evidence",
      "description": "Reviews previous evidence from SharePoint..."
    },
    {
      "name": "aws_take_screenshot",
      "description": "Takes AWS Console screenshots..."
    }
  ]
}
```

### **3. Claude Thinks (in Bedrock cloud):**
```
"User wants to review evidence...
 I have sharepoint_review_evidence tool...
 I should call it with rfi_code='BCR-06.01', product='XDR Platform'"
```

### **4. Claude Returns Decision:**
```json
{
  "tool_calls": [
    {
      "name": "sharepoint_review_evidence",
      "arguments": {
        "rfi_code": "BCR-06.01",
        "product": "XDR Platform"
      }
    }
  ]
}
```

### **5. YOUR Agent Executes (locally):**
```python
# On YOUR machine, using YOUR credentials:
sharepoint = SharePointBrowserAccess()  # Uses your browser
sharepoint.connect()  # You log in (saved session)
sharepoint.navigate_to_path("FY2024/XDR Platform/BCR-06.01/")
files = sharepoint.list_folder_contents()  # YOUR access!

# Returns results:
return {
  "found": True,
  "files": ["Aurora RDS.png", "Conure RDS.png", ...],
  "file_count": 9
}
```

### **6. Results Sent Back to Claude:**
```json
{
  "status": "success",
  "result": {
    "found": True,
    "file_count": 9,
    "files": ["Aurora RDS.png", "Conure RDS.png", ...],
    "analysis": {
      "aws_console_tasks": 9,
      "source": "RDS Multi-AZ configurations"
    }
  }
}
```

### **7. Claude Processes & Responds:**
```
"✅ Found 9 files from FY2024/XDR Platform/BCR-06.01

📊 Previous evidence shows:
  • 9 RDS screenshots (Aurora, Conure, IROH)
  • 3 AWS regions (APIC, EU, NAM)
  • Multi-AZ configurations

🔍 To collect similar evidence, I need to know:
  
Which AWS PRODUCTION account should I use?
  • ctr-prod
  • sxo101
  • sxo202
  
Which region(s)?
  • us-east-1 (NAM)
  • eu-west-1 (EU)  
  • ap-southeast-1 (APIC)
  
(I see previous evidence used multiple regions - should I collect from all 3?)"
```

### **8. You Respond:**
```
"Use ctr-prod account for all regions (NAM, EU, APIC)"
```

### **9. Claude Decides Next:**
```
"User confirmed ctr-prod account and all 3 regions.
 I need to take 9 screenshots (3 clusters × 3 regions).
 I should call aws_take_screenshot 9 times with different parameters."
```

### **10. Agent Executes (locally):**
```python
# For each screenshot:
run_duo_sso(account='ctr-prod')  # You approve MFA
open_aws_console(region='us-east-1')  # Your browser
navigate_to_rds('aurora-cluster')  # Your access
take_screenshot(with_timestamp=True)  # Saved locally
```

---

## 🎯 **Production Account Selection**

You asked for this, and I've implemented it!

### **What Claude Now Does:**

1. **Before ANY AWS tool**, Claude must:
   - Check previous evidence for account/region used
   - Ask user: "Which production account?"
   - Suggest based on previous evidence: "I see FY24 used ctr-prod in us-east-1"
   - Wait for user confirmation

2. **Tool Definitions Updated:**
   ```
   aws_account: "AWS PRODUCTION account (REQUIRED - must ask user!)
                 For audit: ctr-prod, sxo101, sxo202
                 DO NOT use ctr-int or ctr-test"
   
   aws_region: "AWS region (REQUIRED - must ask user!)
                Common: us-east-1 (NAM), eu-west-1 (EU), 
                ap-southeast-1 (APIC)"
   ```

3. **System Prompt Updated:**
   ```
   CRITICAL: AWS Account Selection
   - Audit evidence is ONLY for PRODUCTION accounts
   - Before collecting AWS evidence, ALWAYS ask user:
     "Which AWS production account? (ctr-prod, sxo101, sxo202)"
     "Which AWS region?"
   - DO NOT assume ctr-int or test accounts
   ```

---

## ✅ **Workflow Intelligence**

Claude decides the workflow dynamically:

### **Example Workflow 1: Simple Review**
```
User: "Show me evidence for RFI BCR-06.01"

Claude's Workflow:
1. Call sharepoint_review_evidence(rfi_code="BCR-06.01")
2. Display results to user
3. Done!
```

### **Example Workflow 2: Review + Collect**
```
User: "Review and collect evidence for BCR-06.01"

Claude's Workflow:
1. Call sharepoint_review_evidence(rfi_code="BCR-06.01")
2. Analyze results - sees 9 RDS screenshots
3. Ask user: "Which production account/region?"
4. User confirms: ctr-prod, all regions
5. Call aws_take_screenshot 9 times (loop for each cluster/region)
6. Call show_local_evidence
7. Ask: "Ready to upload to SharePoint?"
8. If yes, call upload_to_sharepoint
```

### **Example Workflow 3: Multi-Service**
```
User: "Collect all evidence for RFI 10.1.2.12"

Claude's Workflow:
1. Call sharepoint_review_evidence(rfi_code="10.1.2.12")
2. Analyze - finds: 3 AWS screenshots, 2 CSV exports, 1 PDF doc
3. Ask user: Production account/regions?
4. Call aws_take_screenshot for each
5. Call aws_export_data for each
6. Note: PDF needs manual collection
7. Call show_local_evidence
8. Summarize what was collected vs what needs manual work
```

---

## 🎓 **No Training Needed!**

Claude 3.5 already knows:
- ✅ AWS services, resources, terminology
- ✅ How to reason about workflows
- ✅ How to chain multiple actions
- ✅ How to ask clarifying questions
- ✅ Audit concepts and requirements

**We just teach it about tools** via clear descriptions!

---

## 🔒 **Security Summary:**

| Component | Has Access To | Location | Controls |
|-----------|---------------|----------|----------|
| **Claude 3.5** | Tool descriptions only | AWS Bedrock Cloud | Can only decide, not execute |
| **Your Agent** | SharePoint, AWS, files | Your MacBook | YOU control via credentials |
| **SharePoint** | Your browser session | Browser | YOU logged in |
| **AWS** | duo-sso credentials | Your machine | YOU approve MFA |
| **Evidence** | Local files | ~/Documents/audit-evidence/ | On YOUR machine |

**Bottom Line:** 
- Claude is the **brain** (decides)
- Your agent is the **hands** (executes)
- You control **all access** (credentials, MFA, browser)

---

## 🚀 **Ready to Use!**

Start the agent:
```bash
cd /Users/krishna/Documents/audit-ai-agent
./START_AGENT.sh
```

**Try:**
```
"Review evidence for RFI BCR-06.01 under XDR Platform"
```

**Claude will:**
1. ✅ Access SharePoint (via your browser)
2. ✅ List previous evidence
3. ✅ Analyze files intelligently
4. ✅ **Ask you for production account confirmation**
5. ✅ Wait for your approval before collecting
6. ✅ Execute locally using your credentials

**All secure. All intelligent. All under YOUR control.** 🎉

