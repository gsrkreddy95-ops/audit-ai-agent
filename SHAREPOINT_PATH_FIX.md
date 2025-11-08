# 🔧 SharePoint Path Fix Guide

## ⚠️ Issue: "Folder not found" Even Though It Exists

You're seeing:
```
⚠️  Folder not found: TD&R Documentation Train 5/TD&R Evidence Collection/FY2025/XDR Platform/BCR-06.01
```

But you know the folder exists!

---

## 🎯 Quick Fix (3 Steps):

### **Step 1: Run Diagnostic Tool**

This will help identify the correct path:

```bash
cd /Users/krishna/Documents/audit-ai-agent
source venv/bin/activate
python3 diagnose_sharepoint_path.py
```

**What it does:**
1. Shows your current `.env` configuration
2. Asks you to paste the SharePoint URL
3. Parses the URL and extracts the correct paths
4. Recommends exact `.env` configuration
5. Tests the connection (optional)

---

### **Step 2: Get Your SharePoint URL**

**In your browser:**
1. Open SharePoint: https://cisco.sharepoint.com/sites/SPRSecurityTeam
2. Navigate manually to: `XDR Platform` → `BCR-06.01` folder
3. **Copy the full URL** from address bar

**Example URL:**
```
https://cisco.sharepoint.com/sites/SPRSecurityTeam/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FSPRSecurityTeam%2FShared%20Documents%2FTD%26R%20Documentation%20Train%205%2FTD%26R%20Evidence%20Collection%2FFY2025%2FXDR%20Platform%2FBCR%2D06%2E01
```

**Paste this into the diagnostic tool!**

---

### **Step 3: Update Your `.env` File**

The diagnostic tool will show you recommended values like:

```bash
SHAREPOINT_DOC_LIBRARY=Shared%20Documents
SHAREPOINT_BASE_PATH=TD&R Documentation Train 5/TD&R Evidence Collection
SHAREPOINT_CURRENT_YEAR=FY2025
```

**Edit your `.env` file:**
```bash
cd /Users/krishna/Documents/audit-ai-agent
nano .env  # or open in your editor
```

**Add/update these lines:**
```bash
# SharePoint Configuration
SHAREPOINT_SITE_URL=https://cisco.sharepoint.com/sites/SPRSecurityTeam
SHAREPOINT_DOC_LIBRARY=Shared%20Documents
SHAREPOINT_BASE_PATH=TD&R Documentation Train 5/TD&R Evidence Collection
SHAREPOINT_CURRENT_YEAR=FY2025
SHAREPOINT_PREVIOUS_YEAR=FY2024
```

**Save and restart agent:**
```bash
./QUICK_START.sh
```

---

## 🔍 Common Path Issues:

### Issue 1: Document Library Name Wrong

**Symptom:** URL shows "Documents" but config says "Shared Documents"

**Fix:**
```bash
# Check your actual SharePoint URL
# If it's /Documents/ instead of /Shared%20Documents/
SHAREPOINT_DOC_LIBRARY=Documents
```

---

### Issue 2: Base Path Different

**Symptom:** Your evidence is not under "TD&R Documentation Train 5"

**Example:** If your path is:
```
/Shared Documents/Audit Evidence/FY2025/XDR Platform/BCR-06.01
```

**Fix:**
```bash
SHAREPOINT_BASE_PATH=Audit Evidence
```

---

### Issue 3: No Product Folder (Flat Structure)

**Symptom:** Files are directly in RFI folders, no "XDR Platform"

**Example path:**
```
/Shared Documents/TD&R Evidence/FY2025/BCR-06.01
```

**Fix:**
```bash
SHAREPOINT_BASE_PATH=TD&R Evidence
# When requesting, don't specify product:
"Review evidence for BCR-06.01" (no "in XDR Platform")
```

---

## 🧪 Manual Test (Without Agent):

Test if your path works:

```bash
cd /Users/krishna/Documents/audit-ai-agent
source venv/bin/activate
python3 -c "
from integrations.sharepoint_browser import SharePointBrowserAccess
import os

sp = SharePointBrowserAccess(headless=False)
print('Connecting...')
sp.connect()

# Replace with YOUR path:
test_path = 'TD&R Documentation Train 5/TD&R Evidence Collection/FY2025/XDR Platform/BCR-06.01'

print(f'Testing: {test_path}')
if sp.navigate_to_path(test_path):
    print('✅ SUCCESS!')
    files = sp.list_folder_contents()
    print(f'Found {len(files)} files')
    for f in files[:5]:
        print(f'  • {f[\"name\"]}')
else:
    print('❌ FAILED - Path not found')

input('Press Enter to close...')
sp.close()
"
```

---

## ✅ What I Fixed in Code:

### Fix 1: Proper URL Encoding
**Before:**
```python
folder_url = f"{base_url}/{self.doc_library}/{encoded_path}"
# If doc_library = "Shared Documents" (with space), URL is broken!
```

**After:**
```python
encoded_doc_library = urllib.parse.quote(self.doc_library)
folder_url = f"{base_url}/{encoded_doc_library}/{encoded_path}"
# Now "Shared Documents" → "Shared%20Documents" ✅
```

### Fix 2: Better Path Encoding
**Before:**
```python
encoded_path = relative_path.replace(' ', '%20').replace('&', '%26')
# Only handles space and &
```

**After:**
```python
encoded_path = urllib.parse.quote(relative_path, safe='/')
# Properly encodes ALL special characters ✅
```

---

## 🚀 Quick Steps Summary:

1. **Run diagnostic:** `python3 diagnose_sharepoint_path.py`
2. **Paste your SharePoint URL** when prompted
3. **Copy recommended `.env` values**
4. **Update your `.env` file**
5. **Restart agent:** `./QUICK_START.sh`
6. **Try again:** "Collect evidence for BCR-06.01 in XDR Platform"

---

## 🆘 Still Not Working?

**Reply with:**
1. The FULL SharePoint URL from your browser (when viewing BCR-06.01 folder)
2. Output from: `cat .env | grep SHAREPOINT`
3. The exact error message you see

I'll configure the exact path for you!

---

## 📊 Path Structure Examples:

### Example 1: Standard Structure
```
Site: cisco.sharepoint.com/sites/SPRSecurityTeam
Doc Library: Shared Documents
Path: TD&R Documentation Train 5/TD&R Evidence Collection/FY2025/XDR Platform/BCR-06.01
```

**Config:**
```bash
SHAREPOINT_DOC_LIBRARY=Shared%20Documents
SHAREPOINT_BASE_PATH=TD&R Documentation Train 5/TD&R Evidence Collection
```

### Example 2: Simple Structure
```
Site: cisco.sharepoint.com/sites/AuditTeam
Doc Library: Documents
Path: Evidence/FY2025/BCR-06.01
```

**Config:**
```bash
SHAREPOINT_DOC_LIBRARY=Documents
SHAREPOINT_BASE_PATH=Evidence
```

### Example 3: Nested Structure
```
Site: cisco.sharepoint.com/sites/Security
Doc Library: Shared Documents
Path: Compliance/Audits/2025/SOC2/XDR Platform/BCR-06.01
```

**Config:**
```bash
SHAREPOINT_DOC_LIBRARY=Shared%20Documents
SHAREPOINT_BASE_PATH=Compliance/Audits/2025/SOC2
```

---

**The diagnostic tool will figure this out for you automatically!** 🎉

Run: `python3 diagnose_sharepoint_path.py`

