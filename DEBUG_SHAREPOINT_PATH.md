# 🔍 SharePoint Path Debugging Guide

## ⚠️ Issue: Folder Not Found (even though it exists)

You're seeing this error:
```
📁 Navigating to: TD&R Documentation Train 5/TD&R Evidence Collection/FY2025/XDR Platform/BCR-06.01...
⚠️  Folder not found
```

But you said the folder EXISTS. Let's debug this!

---

## 🛠️ Debugging Steps:

### Step 1: Check Your `.env` File

Run this in terminal to see your current SharePoint configuration:

```bash
cd /Users/krishna/Documents/audit-ai-agent
cat .env | grep SHAREPOINT
```

**What you should see:**
```
SHAREPOINT_SITE_URL=https://cisco.sharepoint.com/sites/SPRSecurityTeam
SHAREPOINT_DOC_LIBRARY=Shared%20Documents
SHAREPOINT_BASE_PATH=TD&R Documentation Train 5/TD&R Evidence Collection
SHAREPOINT_CURRENT_YEAR=FY2025
SHAREPOINT_PREVIOUS_YEAR=FY2024
```

**If these are missing, add them to your `.env` file!**

---

### Step 2: Verify Your SharePoint Folder Structure

Open SharePoint in your browser and navigate to the BCR-06.01 folder manually.

Once you're there, copy the FULL URL from your browser and paste it here.

**Example URL:**
```
https://cisco.sharepoint.com/sites/SPRSecurityTeam/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FSPRSecurityTeam%2FShared%20Documents%2FTD%26R%20Documentation%20Train%205%2FTD%26R%20Evidence%20Collection%2FFY2025%2FXDR%20Platform%2FBCR%2D06%2E01
```

From this URL, extract the path structure:
- Site URL: `https://cisco.sharepoint.com/sites/SPRSecurityTeam`
- Doc Library: `Shared Documents`
- Folder Path: `TD&R Documentation Train 5/TD&R Evidence Collection/FY2025/XDR Platform/BCR-06.01`

---

### Step 3: Check Document Library Name

The document library might not be "Shared%20Documents". It could be:
- `Shared Documents` (with space)
- `Shared%20Documents` (URL encoded)
- `Documents`
- Something custom

**To find it:**
1. Open SharePoint in browser
2. Click on "Documents" in left sidebar
3. Look at the URL
4. The part right after the site URL is your document library

**Example:**
```
https://cisco.sharepoint.com/sites/SPRSecurityTeam/Shared%20Documents/
                                                    ^^^^^^^^^^^^^^^^^^^^
                                                    This is your doc library
```

---

### Step 4: Test Path in Browser

The agent constructs this URL:
```
{SHAREPOINT_SITE_URL}/{SHAREPOINT_DOC_LIBRARY}/{SHAREPOINT_BASE_PATH}/{YEAR}/{PRODUCT}/{RFI_CODE}
```

For your case:
```
https://cisco.sharepoint.com/sites/SPRSecurityTeam/
Shared%20Documents/
TD&R%20Documentation%20Train%205/TD&R%20Evidence%20Collection/
FY2025/
XDR%20Platform/
BCR-06.01
```

**Try opening this URL directly in your browser (replace spaces with %20):**
```
https://cisco.sharepoint.com/sites/SPRSecurityTeam/Shared%20Documents/TD&R%20Documentation%20Train%205/TD&R%20Evidence%20Collection/FY2025/XDR%20Platform/BCR-06.01
```

**Does it work?**
- ✅ **YES** → The path is correct, it's a browser automation issue
- ❌ **NO** → The path is wrong, we need to adjust the `.env` variables

---

## 🔧 Common Path Issues:

### Issue 1: Document Library is Wrong
**Fix:** Update your `.env`:
```bash
# If your doc library is "Documents" instead of "Shared Documents"
SHAREPOINT_DOC_LIBRARY=Documents
```

### Issue 2: Base Path is Different
**Fix:** Update your `.env`:
```bash
# If your evidence is not under "TD&R Documentation Train 5"
SHAREPOINT_BASE_PATH=Audit Evidence Collection  # Your actual base path here
```

### Issue 3: Year Format is Different
**Fix:** Update your `.env`:
```bash
# If your folders use "2025" instead of "FY2025"
SHAREPOINT_CURRENT_YEAR=2025
```

### Issue 4: No Product Folder (flat structure)
**Fix:** When calling the agent, don't specify product:
```
Review evidence for BCR-06.01 (no product specified)
```

Or the path should be:
```
TD&R Evidence Collection/FY2025/BCR-06.01  (no "XDR Platform" folder)
```

---

## 📝 To Fix Your Issue:

1. **Check your `.env` file** - Make sure all SHAREPOINT_* variables are set
2. **Verify the path in browser** - Navigate manually and copy the URL
3. **Update `.env` with correct values**
4. **Restart the agent**

---

## 🧪 Quick Test Script

Run this to verify your SharePoint connection:

```bash
cd /Users/krishna/Documents/audit-ai-agent
source venv/bin/activate
python3 -c "
from integrations.sharepoint_browser import SharePointBrowserAccess
sp = SharePointBrowserAccess(headless=False)
print('Connecting...')
sp.connect()
print('Testing navigation...')
sp.navigate_to_path('TD&R Documentation Train 5/TD&R Evidence Collection/FY2025/XDR Platform/BCR-06.01')
print('Check browser - did it work?')
input('Press Enter to close...')
sp.close()
"
```

This will:
1. Open browser
2. Connect to SharePoint
3. Try to navigate to the folder
4. You can visually see if it worked

---

## 💡 Next Steps:

Once you identify the correct paths:
1. Update your `.env` file
2. Restart the agent: `./QUICK_START.sh`
3. Try again: `Collect evidence for BCR-06.01 in XDR Platform`

---

## 🆘 Still Not Working?

Reply with:
1. The full URL from your browser when you're in the BCR-06.01 folder
2. The output from `cat .env | grep SHAREPOINT`

I'll help you configure the correct paths!

