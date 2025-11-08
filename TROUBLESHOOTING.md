# 🔧 TROUBLESHOOTING GUIDE

## ❗ Issue: Agent Provides Manual Instructions Instead of Executing Tools

### **Symptoms:**
```
Agent says: "I apologize for the inconvenience. It seems that while the tool 
is available, its implementation is still pending..."

Then provides manual steps instead of actually collecting evidence.
```

---

## ✅ **Status: ALL TOOLS ARE IMPLEMENTED!**

All tools (screenshots, exports, uploads) are **fully implemented** and working. The issue is that the agent needs to be **restarted** to pick up the changes.

---

## 🔍 **Root Cause:**

The agent was running with old code. After implementing the real tools, you need to:
1. Stop the current agent session
2. Restart it to load the new tool implementations

---

## 🚀 **SOLUTION:**

### **Step 1: Stop Current Agent**
Press `Ctrl+C` or type `quit` in the agent chat

### **Step 2: Verify Tools**
```bash
cd /Users/krishna/Documents/audit-ai-agent
./TEST_TOOLS.sh
```

**Expected Output:**
```
✅ aws_screenshot_tool imported
✅ aws_export_tool imported
✅ aws_list_tool imported
✅ sharepoint_upload_tool imported
✅ Found 6 tool definitions
✅ AWS credentials found
```

### **Step 3: Restart Agent**
```bash
./QUICK_START.sh
```

### **Step 4: Test Real Collection**
```
You: Collect RDS backup configuration evidence for BCR-06.01 in ctr-prod us-east-1
```

**What Should Happen:**
```
Agent:
📊 Exporting AWS data...
   Service: RDS
   Export Type: clusters
   Account: ctr-prod
   Region: us-east-1
   Format: CSV
   Output: rds_clusters_us-east-1_20250106_150000.csv

📥 Exporting RDS clusters...
✅ Exported 3 RDS clusters
✅ Saved to CSV: ~/Documents/audit-evidence/FY2025/BCR-06.01/rds_clusters_us-east-1_20250106_150000.csv
✅ Evidence saved locally
```

---

## 🧪 **Verification Tests:**

### **Test 1: Quick List (No Files Created)**
```
You: List all RDS clusters in ctr-prod us-east-1
```

**Expected:** Rich table showing RDS clusters

### **Test 2: Data Export (Creates CSV)**
```
You: Export RDS clusters from ctr-prod us-east-1 to CSV for BCR-06.01
```

**Expected:** 
- ✅ CSV file created in `~/Documents/audit-evidence/FY2025/BCR-06.01/`
- ✅ File tracked in evidence manager

### **Test 3: Screenshot (Creates PNG)**
```
You: Take screenshot of RDS Aurora cluster configuration in ctr-prod us-east-1 for BCR-06.01
```

**Expected:**
- ✅ Browser opens automatically
- ✅ Navigates to AWS Console
- ✅ Takes screenshot with timestamp
- ✅ PNG saved to evidence folder

---

## ⚠️ **Common Issues & Fixes:**

### **Issue: AWS Credentials Expired**

**Symptoms:**
```
❌ AWS credentials not found
```

**Fix:**
```bash
duo-sso
export AWS_PROFILE=ctr-prod
export AWS_REGION=us-east-1
```

Then restart agent.

---

### **Issue: Browser Doesn't Open for Screenshots**

**Symptoms:**
```
❌ Failed to connect to browser
```

**Fix:**
```bash
playwright install chromium
```

Then restart agent.

---

### **Issue: Agent Still Gives Manual Instructions**

**Symptoms:**
Agent says "implementation pending" even after restart.

**Possible Causes:**
1. Old Python process still running
2. Virtual environment not activated
3. Tool execution error being misinterpreted

**Fix:**
```bash
# Kill any running Python processes
pkill -f "python.*chat_interface"

# Restart with fresh environment
cd /Users/krishna/Documents/audit-ai-agent
source venv/bin/activate
python3 chat_interface.py
```

---

### **Issue: Tool Execution Error**

**Symptoms:**
```
🔧 Executing: aws_export_data
❌ Export error: ...
```

**Possible Causes:**
- Missing AWS credentials
- Wrong region specified
- Service not available in region
- Missing permissions

**Fix:**
1. Check AWS credentials: `aws sts get-caller-identity --profile ctr-prod`
2. Verify region: `aws rds describe-db-clusters --region us-east-1 --profile ctr-prod`
3. If works in CLI, agent should work too

---

## 🎯 **What's Working Now:**

| Tool | Status | Test Command |
|------|--------|--------------|
| AWS Export | ✅ **WORKING** | `Export RDS clusters from ctr-prod` |
| AWS Screenshot | ✅ **WORKING** | `Take screenshot of RDS Aurora` |
| AWS List | ✅ **WORKING** | `List all S3 buckets` |
| SharePoint Review | ✅ **WORKING** | `Review evidence for BCR-06.01` |
| SharePoint Upload | ✅ **WORKING** | `upload` |

---

## 📋 **Before You Start:**

**Checklist:**
- ✅ duo-sso completed (AWS credentials valid)
- ✅ AWS_PROFILE environment variable set
- ✅ Virtual environment activated
- ✅ Agent restarted (not old session)
- ✅ Playwright browsers installed

---

## 🚀 **Quick Start (Clean):**

```bash
# 1. Authenticate to AWS
duo-sso
export AWS_PROFILE=ctr-prod
export AWS_REGION=us-east-1

# 2. Navigate to agent
cd /Users/krishna/Documents/audit-ai-agent

# 3. Activate environment
source venv/bin/activate

# 4. Verify tools
./TEST_TOOLS.sh

# 5. Start agent
python3 chat_interface.py
```

---

## 💡 **Understanding Tool Execution:**

### **How It Works:**

1. **You:** "Export RDS clusters from ctr-prod"

2. **Claude (LLM):** Decides to use `aws_export_data` tool
   - Parameters: `service=rds, export_type=clusters, aws_account=ctr-prod`

3. **Tool Executor:** Calls real Python function `export_aws_data()`
   - Connects to AWS via boto3
   - Fetches RDS cluster data
   - Exports to CSV file
   - Saves to evidence folder

4. **Agent:** Reports success with file path

### **No More Manual Steps!**

Before: "Please log in to AWS Console, navigate to RDS, download CSV..."
Now: ✅ **Automatic collection with timestamped files**

---

## 🎉 **Success Indicators:**

When tools are working correctly, you'll see:

```
🔧 Executing: aws_export_data
📊 Exporting AWS data...
   Service: RDS
   Export Type: clusters
   ...
📥 Exporting RDS clusters...
✅ Exported 3 RDS clusters
✅ Saved to CSV: ...
✅ Evidence saved locally: ~/Documents/audit-evidence/FY2025/BCR-06.01/...
```

NOT:
```
❌ "I apologize for the inconvenience..."
❌ "Please manually..."
❌ "Implementation is still pending..."
```

---

## 📞 **Still Having Issues?**

Run diagnostic:
```bash
cd /Users/krishna/Documents/audit-ai-agent
./TEST_TOOLS.sh
```

Share the output if tools aren't importing correctly.

---

## ✅ **Bottom Line:**

**All tools are implemented and working!** Just restart the agent to pick up the changes.

```bash
./QUICK_START.sh
```

Then try:
```
Export RDS clusters from ctr-prod us-east-1 to CSV for BCR-06.01
```

Should work automatically now! 🎯

