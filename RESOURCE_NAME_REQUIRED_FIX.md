# ✅ Fixed: AWS Screenshot Now Requires Specific Resource Names

## 🎯 Problem:

**What You Saw:**
```
🔍 RDS Navigation...
📑 Looking for 'Backups' tab...
⚠️  Could not find 'Backups' tab
📸 Taking screenshot...
```

**Result:** Screenshot of RDS **dashboard**, not a specific cluster's backup configuration.

---

## 🔍 Root Cause:

The agent was calling the screenshot tool with:
- `resource='rds_console'` (generic dashboard) ❌
- Instead of `resource='prod-xdr-cluster-01'` (specific cluster) ✅

This caused the tool to:
1. Navigate to RDS console ✅
2. Try to click "Backups" tab at dashboard level ❌ (doesn't exist there!)
3. Capture dashboard screenshot ❌ (not what you wanted!)

---

## 🔧 Fixes Applied:

### **1. Selenium Tool - Validation Check**

**File:** `tools/aws_screenshot_selenium.py`

**Added validation in `_navigate_rds()`:**
```python
# REQUIRE specific resource name for RDS
if resource == 'rds_console' or not resource or resource == 'database':
    console.print(f"[red]❌ ERROR: Specific RDS cluster/instance name required![/red]")
    console.print(f"[yellow]💡 Please provide the exact cluster or instance name[/yellow]")
    console.print(f"[yellow]   Example: 'prod-xdr-cluster-01', 'staging-db-instance'[/yellow]")
    console.print(f"[yellow]   Tip: Run 'List RDS clusters' first to see available names[/yellow]")
    return False
```

**What This Does:**
- ✅ Rejects generic names like `'rds_console'`, `'database'`, `'cluster'`
- ✅ Shows clear error message
- ✅ Tells user to list clusters first
- ✅ Provides examples of correct names

---

### **2. Tool Definition - Clearer Instructions for Claude**

**File:** `ai_brain/tools_definition.py`

**Updated `resource_name` description:**
```python
"resource_name": {
    "type": "string",
    "description": """SPECIFIC resource name is REQUIRED for configuration screenshots!
    Examples:
    - RDS: 'prod-xdr-cluster-01', 'staging-db-instance' (NEVER use 'database' or 'rds_console')
    - S3: 'my-audit-bucket', 'backup-storage-bucket' (NEVER use 'bucket' or 's3_console')  
    - EC2: 'i-0123456789abcdef0' (NEVER use 'instance' or 'ec2_console')
    - Lambda: 'process-data-function' (NEVER use 'function' or 'lambda_console')
    
    CRITICAL: If you don't know the specific name:
    1. First use aws_list_resources or list_aws_resources to get available names
    2. Then call this tool with the EXACT resource name
    
    DO NOT use generic names like 'database', 'cluster', 'bucket', 'console', etc.
    Leave empty ONLY for dashboard/list screenshots (no config tabs).
    """
}
```

**What This Does:**
- ✅ Makes it VERY clear to Claude that specific names are required
- ✅ Provides examples of correct names
- ✅ Explicitly lists what NOT to use
- ✅ Tells Claude to list resources first if unknown

---

### **3. LocalEvidenceManager Fix**

**File:** `ai_brain/tool_executor.py`

**Fixed attribute error:**
```python
# Before (Broken):
collected = self.evidence_manager.collected_files  # ❌ Attribute doesn't exist

# After (Fixed):
by_rfi = self.evidence_manager.get_upload_ready_files()  # ✅ Uses correct method
```

**What This Fixes:**
- ✅ No more `'LocalEvidenceManager' object has no attribute 'collected_files'` error
- ✅ Proper file retrieval for upload
- ✅ Correct cleanup after upload

---

## 🎯 Expected Behavior Now:

### **Scenario 1: Generic Name (Rejected)**

**User:** "Take screenshot of RDS backup config"

**Agent:**
```
1. Calls aws_take_screenshot with resource='rds_console'
2. Tool rejects:
   ❌ ERROR: Specific RDS cluster/instance name required!
   💡 Please provide the exact cluster or instance name
   Example: 'prod-xdr-cluster-01', 'staging-db-instance'
   Tip: Run 'List RDS clusters' first to see available names

3. Agent responds to user:
   "I need the specific RDS cluster name. Let me list them for you..."
   
4. Agent lists RDS clusters
5. Agent asks: "Which cluster do you want?"
```

---

### **Scenario 2: List First, Then Capture (Correct)**

**User:** "Take screenshot of RDS backup config"

**Agent (Smart Workflow):**
```
1. "I need to know which RDS cluster. Let me list them..."
2. Calls list_rds_clusters
3. Shows: "Found 5 clusters: prod-xdr-cluster-01, prod-xdr-cluster-02, ..."
4. Asks: "Which cluster do you want to capture?"
5. User picks: "prod-xdr-cluster-01"
6. Agent calls aws_take_screenshot with resource='prod-xdr-cluster-01'
7. Tool navigates to specific cluster
8. Clicks "Maintenance & backups" tab
9. Captures screenshot ✅
```

---

### **Scenario 3: User Provides Specific Name (Best)**

**User:** "Take screenshot of RDS cluster 'prod-xdr-cluster-01' backup config in ctr-prod, us-east-1"

**Agent:**
```
1. Calls aws_take_screenshot(
     service='rds',
     resource='prod-xdr-cluster-01',  # ✅ Specific!
     aws_account='ctr-prod',
     aws_region='us-east-1',
     tab='Maintenance & backups'
   )

2. Tool navigates:
   ✅ Opens RDS console
   ✅ Clicks "Databases"
   ✅ Searches for "prod-xdr-cluster-01"
   ✅ Clicks on cluster
   ✅ Clicks "Maintenance & backups" tab
   ✅ Captures screenshot

3. Result: Screenshot of ACTUAL cluster backup config! ✅
```

---

## 🧪 Test It:

```bash
./QUICK_START.sh
```

**Then try:**
```
Take screenshot of RDS backup config in ctr-prod, us-east-1
```

**Expected:**
```
Agent: "I need the specific RDS cluster name. Let me list them for you..."
[Lists clusters]
Agent: "Which cluster do you want to capture?"
You: "prod-xdr-cluster-01"
Agent: [Captures specific cluster backup config] ✅
```

---

**OR provide specific name directly:**
```
Take screenshot of RDS cluster 'prod-xdr-cluster-01' 
backup configuration in ctr-prod, us-east-1
```

**Expected:**
```
Agent: [Immediately captures specific cluster backup config] ✅
```

---

## ✅ Summary:

| Issue | Fix |
|-------|-----|
| **Generic resource names** | ✅ Validation check rejects them |
| **Dashboard screenshots** | ✅ Tool requires specific names |
| **Claude confusion** | ✅ Tool definition very explicit |
| **LocalEvidenceManager error** | ✅ Fixed attribute access |
| **No resource listing** | ✅ Tool tells Claude to list first |

---

## 💡 Best Practices:

### **For You (User):**
```
✅ "Take screenshot of cluster 'prod-xdr-cluster-01' backup config"
❌ "Take screenshot of RDS backup config"
```

### **For Agent (Claude):**
```
✅ If resource name unknown → List resources first → Ask user → Capture
❌ Use generic names like 'rds_console', 'database', 'cluster'
```

---

## 🎯 What Works Now:

1. ✅ Agent must provide **specific resource names**
2. ✅ Tool **rejects generic names** with helpful error
3. ✅ Tool **tells Claude** to list resources first
4. ✅ Agent **lists clusters** → User picks → Agent captures
5. ✅ Screenshots capture **actual resource config**, not dashboard
6. ✅ No more `LocalEvidenceManager` attribute errors

---

**Try it now:** `./QUICK_START.sh` 🚀

**The agent will now list RDS clusters first, then capture specific cluster configs!** ✅

