# 🧠 Intelligent Agent Architecture

## You Were Right!

Instead of hardcoding rules, the agent now uses **Claude 3.5's intelligence** to decide what to do!

---

## ❌ OLD Approach (Hardcoded Rules)

```python
# Bad: Manual intent detection
if 'rfi' in user_input.lower() and 'review' in user_input.lower():
    rfi_code = extract_rfi_with_regex(user_input)
    go_to_sharepoint(rfi_code)
elif 's3' in user_input.lower() and 'list' in user_input.lower():
    list_s3_buckets()
...
```

**Problems:**
- ❌ Rigid rules
- ❌ Can't handle variations
- ❌ Maintenance nightmare
- ❌ Not intelligent

---

## ✅ NEW Approach (LLM Tool Use)

```python
# Good: Claude decides
agent.chat("Review evidence for RFI BCR-06.01")

# Claude thinks:
# "User wants to review evidence...
#  I have a 'sharepoint_review_evidence' tool...
#  I should call it with rfi_code='BCR-06.01'"

# Claude calls tool automatically
sharepoint_review_evidence(rfi_code="BCR-06.01", product="XDR")

# Gets results, continues reasoning...
```

**Benefits:**
- ✅ Understands natural language
- ✅ Handles variations naturally
- ✅ Chains multiple tools together
- ✅ Actually intelligent

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        USER                             │
│  "Review evidence for RFI BCR-06.01 under XDR Platform" │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│               INTELLIGENT AGENT                          │
│  • Powered by Claude 3.5 Sonnet (via Bedrock)          │
│  • Understands natural language                         │
│  • Decides which tools to use                           │
│  • Chains multiple actions                              │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ "I need sharepoint_review_evidence tool"
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│               TOOL DEFINITIONS                           │
│  • sharepoint_review_evidence                           │
│  • aws_take_screenshot                                   │
│  • aws_export_data                                       │
│  • list_aws_resources                                    │
│  • show_local_evidence                                   │
│  • upload_to_sharepoint                                  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ execute("sharepoint_review_evidence", {...})
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│               TOOL EXECUTOR                              │
│  • Connects to SharePoint                               │
│  • Lists previous evidence                               │
│  • Analyzes files (RDS screenshots, etc.)               │
│  • Returns results to Claude                             │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ results: "Found 9 RDS screenshots..."
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│               CLAUDE CONTINUES                           │
│  "I found 9 RDS screenshots. They need fresh            │
│   screenshots from AWS Console. I should tell the user  │
│   what was found and ask if they want me to collect."   │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    USER SEES                             │
│  "✅ Found 9 files from FY2024:                         │
│    - APIC Aurora RDS Dashboard.png                      │
│    - EU Aurora RDS Dashboard.png                        │
│    - ... and 7 more                                     │
│                                                          │
│   📊 Collection Plan:                                   │
│    • 9 AWS Console screenshots needed                   │
│    • Source: RDS Multi-AZ configurations                │
│                                                          │
│   Would you like me to collect these now?"              │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 How Tools Work

### 1. **Tool Definitions** (`tools_definition.py`)

Describes each tool to Claude in natural language:

```python
{
    "name": "sharepoint_review_evidence",
    "description": "Reviews previous year's audit evidence from SharePoint...",
    "input_schema": {
        "type": "object",
        "properties": {
            "rfi_code": {"type": "string", "description": "RFI code like BCR-06.01"},
            "product": {"type": "string", "description": "Product name like 'XDR Platform'"}
        }
    }
}
```

### 2. **Claude Decides**

Claude reads the tool definitions and decides:
- "This user request needs the sharepoint_review_evidence tool"
- "I should pass rfi_code='BCR-06.01' and product='XDR Platform'"

### 3. **Tool Executor** (`tool_executor.py`)

Executes the tool Claude requested:

```python
def execute_tool(tool_name, tool_input):
    if tool_name == "sharepoint_review_evidence":
        # Open SharePoint
        # Navigate to folder
        # List files
        # Analyze files
        # Return results
        return {...}
```

### 4. **Claude Continues**

Claude receives tool results and continues reasoning:
- "Great! I found the evidence"
- "Now I should tell the user what I found"
- "Maybe I need to call aws_take_screenshot next..."

---

## 💬 Example Conversation

### **You:**
```
Review evidence for RFI BCR-06.01 under XDR Platform
and collect similar evidence for FY2025
```

### **Claude's Internal Reasoning:**
```
1. User wants to review evidence → use sharepoint_review_evidence
2. Call: sharepoint_review_evidence(rfi_code="BCR-06.01", product="XDR Platform")
3. Got results: 9 RDS screenshots found
4. Files show: Aurora, Conure, IROH clusters across 3 regions
5. I should tell user what I found
6. Ask if they want me to collect fresh screenshots
```

### **Agent Response:**
```
✅ Reviewed FY2024 evidence for BCR-06.01

📋 Found 9 files:
  • 3 Aurora RDS dashboards (APIC, EU, NAM)
  • 3 Conure RDS Multi-AZ configs
  • 3 IROH RDS Multi-AZ configs

🎯 Collection Plan:
  • Need 9 fresh AWS Console screenshots
  • Source: RDS service, Multi-AZ configurations
  • Regions: ap-southeast-1, eu-west-1, us-east-1

Would you like me to collect these now? 
(Note: I'll need you to complete duo-sso authentication for AWS)
```

### **You:**
```
Yes, collect them
```

### **Claude's Reasoning:**
```
1. User approved collection
2. For each screenshot, call aws_take_screenshot
3. Loop through: Aurora/APIC, Aurora/EU, Aurora/NAM, Conure/APIC...
4. Each call needs: service="rds", resource="aurora", region="ap-southeast-1", etc.
5. Show progress as I collect
```

---

## 🎯 Key Differences

| Feature | OLD (Hardcoded) | NEW (Intelligent) |
|---------|----------------|-------------------|
| **Understanding** | Regex matching | Natural language |
| **Flexibility** | Fixed patterns | Adapts to variations |
| **Chaining** | Manual coding | Claude decides |
| **Errors** | Breaks easily | Self-corrects |
| **Maintenance** | Update rules constantly | Just improve tools |

---

## 🚀 Current Status

### ✅ **Working:**
- Claude understands natural language requests
- Claude decides which tools to use
- SharePoint review tool fully functional
- Evidence analysis working
- Collection plan generation

### ⚠️ **Pending:**
- AWS screenshot capture (tool defined, execution pending)
- AWS data export (tool defined, execution pending)
- SharePoint upload (tool defined, execution pending)

---

## 🔮 Future Enhancements

Since Claude is intelligent, we can easily add:

1. **More Tools:**
   - Jira ticket export
   - GitHub export
   - PagerDuty incidents
   - Just define the tool, Claude knows how to use it!

2. **Complex Workflows:**
   - Claude can chain 5+ tools together
   - "Review FY24, collect from AWS, verify, upload to SharePoint"
   - All automatically!

3. **Error Recovery:**
   - If AWS fails, Claude can retry
   - If region not found, Claude asks user
   - Self-healing workflows!

4. **Learning:**
   - We can add more context to tool descriptions
   - Claude gets smarter with better tool docs
   - No code changes needed!

---

## 🎓 Training the Model?

You asked about training - we don't need to!

**Claude 3.5 is already trained** on:
- AWS services and APIs
- SharePoint concepts  
- Audit terminology
- General reasoning

**We just need to:**
1. Define tools clearly
2. Provide good descriptions
3. Let Claude figure out the rest

**No custom training needed!** 🎉

---

## 🏃 Try It Now

```bash
cd /Users/krishna/Documents/audit-ai-agent
./START_AGENT.sh
```

**Try asking naturally:**
- "Review evidence for RFI BCR-06.01"
- "What evidence did we collect last year for XDR Platform?"
- "List S3 buckets in ctr-int account"
- "Show me what evidence you've collected"

**Claude will understand and decide what to do!**

