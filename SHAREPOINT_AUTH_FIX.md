# ✅ SharePoint Authentication Fix

## 🔧 Issue Fixed: "Folder not found" Due to Missing Authentication

**Your Issue:**
- URL works in your browser: ✅ (you're logged in)
- Agent says "folder not found": ❌ (not logged in)

**Root Cause:**
The agent's browser wasn't maintaining SharePoint authentication, so when it tried to navigate to the folder, SharePoint redirected it to a login page instead of showing the folder.

---

## 🛠️ What I Fixed:

### Fix 1: Enhanced Authentication Detection
**File:** `integrations/sharepoint_browser.py` → `connect()` method

**Before:**
- Only checked for Microsoft login pages
- Short timeout (60 seconds)
- No fallback for Cisco SSO

**After:**
- ✅ Detects Cisco SSO (`sso.cisco.com`)
- ✅ Detects Okta (`cisco.okta.com`)
- ✅ Detects Microsoft login (`login.microsoftonline.com`)
- ✅ Longer timeout (120 seconds)
- ✅ Extra 30 seconds for manual authentication if needed

**What You'll See:**
```
🌐 Launching browser for SharePoint access...
📱 Using audit agent browser profile...
💡 If you see a login page, log in once - your session will be saved
🔗 Navigating to: https://cisco.sharepoint.com/sites/SPRSecurityTeam

⚠️  Login required. Please log in manually in the browser...
💡 Complete Cisco SSO/Okta authentication
⏳ Waiting for login to complete (120 seconds)...
✅ Login successful!
✅ Connected to SharePoint!
```

---

### Fix 2: Re-authentication on Folder Navigation
**File:** `integrations/sharepoint_browser.py` → `navigate_to_path()` method

**Before:**
- Navigated directly to folder
- If redirected to login, failed immediately
- No retry after authentication

**After:**
- ✅ Detects login redirects during navigation
- ✅ Prompts user to authenticate
- ✅ Waits for authentication (120 seconds)
- ✅ Automatically retries navigation after successful login

**What You'll See:**
```
📁 Navigating to: TD&R Evidence Collection/FY2025/XDR Platform/BCR-06.01...
🔗 Full URL: https://cisco.sharepoint.com/...

⚠️  Authentication required for folder access
💡 Please complete Cisco SSO/Okta authentication in the browser
⏳ Waiting for login (120 seconds)...
✅ Authentication complete! Trying navigation again...
✅ Navigation successful!

Found 12 files
```

---

## 🚀 How to Use:

### **Step 1: Restart the Agent**

```bash
cd /Users/krishna/Documents/audit-ai-agent
./QUICK_START.sh
```

---

### **Step 2: Try Your Request Again**

```
Review evidence for BCR-06.01 in XDR Platform for FY2025
```

---

### **Step 3: Complete Authentication When Prompted**

**When you see this:**
```
⚠️  Login required. Please log in manually in the browser...
💡 Complete Cisco SSO/Okta authentication
⏳ Waiting for login to complete (120 seconds)...
```

**You should see a browser window open. Complete these steps:**

1. ✅ **Enter your Cisco username and password**
2. ✅ **Complete Duo MFA** (push notification or code)
3. ✅ **Wait for SharePoint to load**

**Once authenticated:**
```
✅ Login successful!
✅ Connected to SharePoint!
```

**Your login is saved in the browser profile!** Next time, you won't need to log in again (unless session expires).

---

## 💾 Browser Profile Location:

Your SharePoint login is saved in:
```
~/.audit-agent-browser/
```

This is a **separate browser profile** from your main Chrome/Edge, so:
- ✅ No interference with your personal browsing
- ✅ Login persists between agent runs
- ✅ Secure (only the agent uses this profile)

---

## 🧪 Test the Fix:

### **Test 1: Initial Connection**
```
You: Review evidence for BCR-06.01 in XDR Platform

Expected:
🌐 Launching browser for SharePoint...
⚠️  Login required (if first time)
[You complete Cisco SSO + Duo]
✅ Login successful!
✅ Connected to SharePoint!
📁 Navigating to folder...
✅ Navigation successful!
📊 Found 12 files
```

### **Test 2: Subsequent Connections (No Login Needed)**
```
You: Review evidence for BCR-06.02 in XDR Platform

Expected:
🌐 Launching browser for SharePoint...
✅ Connected to SharePoint! (no login prompt)
📁 Navigating to folder...
✅ Navigation successful!
```

---

## 🔑 Authentication Flow:

### **First Time:**
```
1. Agent opens browser → SharePoint redirects to Cisco SSO
2. You log in with Cisco credentials
3. Complete Duo MFA
4. SharePoint loads
5. Session saved in ~/.audit-agent-browser/
6. Agent proceeds to collect evidence
```

### **Subsequent Times:**
```
1. Agent opens browser → Uses saved session
2. SharePoint loads immediately (no login!)
3. Agent proceeds to collect evidence
```

### **If Session Expires:**
```
1. Agent tries to navigate → SharePoint redirects to login
2. Agent detects redirect and prompts you
3. You re-authenticate
4. Agent retries navigation automatically
5. Evidence collection continues
```

---

## ⚙️ Configuration Check:

Make sure your `.env` has:

```bash
# SharePoint Configuration
SHAREPOINT_SITE_URL=https://cisco.sharepoint.com/sites/SPRSecurityTeam
SHAREPOINT_DOC_LIBRARY=Shared%20Documents
SHAREPOINT_BASE_PATH=TD&R Documentation Train 5/TD&R Evidence Collection
SHAREPOINT_CURRENT_YEAR=FY2025
SHAREPOINT_PREVIOUS_YEAR=FY2024
```

---

## 🐛 Troubleshooting:

### Issue: "Still says folder not found"

**Solution 1: Clear browser profile and re-authenticate**
```bash
rm -rf ~/.audit-agent-browser/
./QUICK_START.sh
# Agent will prompt for login again
```

**Solution 2: Verify SharePoint URL**
- Open SharePoint manually in your browser
- Navigate to BCR-06.01 folder
- Copy the URL
- Run: `python3 diagnose_sharepoint_path.py`
- Paste URL when prompted
- Update `.env` with recommended values

---

### Issue: "Browser opens but doesn't show login page"

**Solution: The session might be saved but invalid**
```bash
# Clear saved session
rm -rf ~/.audit-agent-browser/

# Restart agent
./QUICK_START.sh

# Try again - you'll get a fresh login prompt
```

---

### Issue: "Login timeout"

**If you see:**
```
⚠️  Login timeout or still on login page
```

**This means:**
- Authentication didn't complete in 120 seconds
- OR you didn't complete all MFA steps

**Solution:**
- Restart the agent
- Be ready to complete authentication quickly:
  1. Have Duo app open on your phone
  2. Approve the push notification immediately
  3. Wait for SharePoint to load

---

## ✅ Summary of Changes:

| Component | What Changed | Benefit |
|-----------|-------------|---------|
| `connect()` | Added Cisco SSO detection | ✅ Detects Cisco login pages |
| `connect()` | Increased timeout to 120s | ✅ More time for MFA |
| `connect()` | Added 30s fallback | ✅ Extra time if needed |
| `navigate_to_path()` | Added login redirect detection | ✅ Catches re-auth requests |
| `navigate_to_path()` | Auto-retry after auth | ✅ Seamless experience |
| Browser Profile | Persistent `~/.audit-agent-browser/` | ✅ Remember login |

---

## 🎯 Bottom Line:

**Before:**
- ❌ Agent couldn't access SharePoint folders
- ❌ Said "folder not found" even though it exists
- ❌ No authentication handling

**After:**
- ✅ Agent prompts you to log in when needed
- ✅ Detects Cisco SSO + Duo authentication
- ✅ Saves session for future runs
- ✅ Auto-retries if redirected to login
- ✅ Works exactly like your browser

---

## 🚀 Ready to Test!

```bash
# Restart agent
./QUICK_START.sh

# Try your request
"Review evidence for BCR-06.01 in XDR Platform for FY2025"

# Complete authentication if prompted
# Watch it work! 🎉
```

The agent will now properly authenticate to SharePoint and access your folders! 🎉

