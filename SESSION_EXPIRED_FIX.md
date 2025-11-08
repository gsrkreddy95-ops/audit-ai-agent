# 🔒 SharePoint Session Expired - Quick Fix

## ⚠️ **Issue: Folder Not Found (But It Exists!)**

**You're seeing:**
```
⚠️  Folder not found: TD&R Evidence Collection/FY2025/XDR Platform/BCR-06.01
```

**But:**
- ✅ It worked 1 hour ago ("analyzing 12 files")
- ✅ The folder exists in SharePoint
- ✅ You can access it in your browser

**Root Cause:** SharePoint session expired in the browser profile!

---

## ✅ **Quick Fix (2 Steps):**

### **Step 1: Clear Browser Cache**

```bash
cd /Users/krishna/Documents/audit-ai-agent
./clear_browser_cache.sh
```

**What this does:**
- Removes expired browser profiles
- Forces fresh authentication on next run
- Takes 2 seconds

---

### **Step 2: Restart Agent & Re-authenticate**

```bash
./QUICK_START.sh
```

**Then try your request again:**
```
Review evidence for BCR-06.01 in XDR Platform
```

**What will happen:**
1. 🦊 Firefox opens
2. 🔐 You'll see Cisco SSO login page
3. ✅ Complete authentication + Duo MFA
4. ✅ Agent proceeds to access folder
5. ✅ Finds 12 files!

---

## 📊 **What Was Fixed in Code:**

### **1. Better Error Detection**
- ✅ Now detects when session expires mid-navigation
- ✅ Shows actual URL it's redirected to
- ✅ Identifies login pages immediately

### **2. Enhanced Logging**
```
📍 Actual URL after navigation: https://login.microsoftonline.com/...
⚠️  Session expired! Authentication required
💡 Please complete authentication in the browser
```

### **3. Automatic Re-authentication**
- ✅ Detects login redirects
- ✅ Waits for you to authenticate
- ✅ Automatically retries navigation after login
- ✅ Shows helpful tips if it keeps failing

### **4. Clear Instructions**
- ✅ If repeated failures: Suggests `./clear_browser_cache.sh`
- ✅ Shows progress at each step
- ✅ Displays URLs for debugging

---

## 🔍 **Why Sessions Expire:**

**SharePoint sessions expire after:**
- ⏰ **1 hour** of inactivity (most common)
- ⏰ **8 hours** maximum (even with activity)
- 🔄 **Policy changes** (company security updates)
- 🔐 **MFA token expiration**

**This is normal!** Just re-authenticate and continue.

---

## 🛠️ **Troubleshooting:**

### **Issue 1: Still says "folder not found" after clearing cache**

**Solution:**
```bash
# Make sure you're using Firefox (not Chromium)
cat .env | grep BROWSER

# Should show:
# SHAREPOINT_BROWSER=firefox
# AWS_SCREENSHOT_BROWSER=firefox

# If not, add them:
echo "SHAREPOINT_BROWSER=firefox" >> .env
echo "AWS_SCREENSHOT_BROWSER=firefox" >> .env

# Restart agent
./QUICK_START.sh
```

---

### **Issue 2: Browser doesn't open or crashes**

**Solution:**
```bash
# Reinstall Firefox
source venv/bin/activate
playwright install --force firefox

# Clear cache
./clear_browser_cache.sh

# Restart
./QUICK_START.sh
```

---

### **Issue 3: Authentication completes but still can't access folder**

**Check the actual URL in the logs:**
```
📍 Actual URL after navigation: https://...
```

**If URL shows:**
- `login.microsoftonline.com` → Still on login page, MFA not complete
- `accessdenied` → Permission issue (contact SharePoint admin)
- `404` or `notfound` → Path might be wrong (run `./diagnose_sharepoint_path.py`)
- `sharepoint.com/.../BCR-06.01` → Correct! Should work

---

### **Issue 4: Keeps asking to log in repeatedly**

**This means browser profile is corrupted.**

**Solution:**
```bash
# Complete reset
rm -rf ~/.audit-agent-browser
rm -rf ~/.audit-agent-aws-browser
rm -rf ~/Library/Caches/ms-playwright/firefox-*

# Reinstall Firefox
cd /Users/krishna/Documents/audit-ai-agent
source venv/bin/activate
playwright install firefox

# Restart agent
./QUICK_START.sh
```

---

## 📋 **Preventive Measures:**

### **1. Don't Leave Agent Idle Too Long**
If you stop using the agent for >1 hour, session will expire.
**Solution:** Just re-authenticate when you come back.

### **2. Complete Full Authentication**
When logging in:
- ✅ Enter username/password
- ✅ Complete Duo MFA
- ✅ Wait for SharePoint to fully load (green checkmark)

### **3. Run Cache Clear if Experiencing Issues**
```bash
./clear_browser_cache.sh
./QUICK_START.sh
```

---

## ✅ **Enhanced Features:**

| Feature | Before | After |
|---------|--------|-------|
| Session expiration detection | ❌ No | ✅ Yes |
| Shows actual redirect URL | ❌ No | ✅ Yes |
| Auto re-authentication | ⚠️ Partial | ✅ Full |
| Helpful error messages | ⚠️ Generic | ✅ Specific |
| Cache clearing tool | ❌ No | ✅ Yes |
| Debug logging | ⚠️ Minimal | ✅ Detailed |

---

## 🎯 **Quick Reference:**

**Session expired?**
```bash
./clear_browser_cache.sh && ./QUICK_START.sh
```

**Browser issues?**
```bash
playwright install --force firefox && ./clear_browser_cache.sh && ./QUICK_START.sh
```

**Path issues?**
```bash
python3 diagnose_sharepoint_path.py
```

**Still stuck?**
Check the URL shown in logs:
```
📍 Actual URL after navigation: [URL HERE]
```
Then decide:
- Login URL → Re-authenticate
- 404 URL → Path wrong
- Correct URL → Should work!

---

## 🎉 **Bottom Line:**

SharePoint sessions expire regularly (every 1-8 hours). This is normal security behavior.

**When you see "folder not found" but it exists:**
1. Run: `./clear_browser_cache.sh`
2. Restart: `./QUICK_START.sh`
3. Re-authenticate when prompted
4. Continue collecting evidence!

**Simple as that!** ✅🦊

---

## 📞 **Enhanced Error Messages You'll See:**

```
⚠️  Session expired! Authentication required for folder access
💡 Please complete Cisco SSO/Okta authentication in the browser
⏳ Waiting for login (120 seconds)...
💡 If this keeps happening, run: ./clear_browser_cache.sh

📍 Actual URL after navigation: https://login.microsoftonline.com/...
✅ Authentication complete! Trying navigation again...
📍 URL after re-authentication: https://cisco.sharepoint.com/...
✅ Navigation successful!
📊 Found 12 files
```

**Much better than before!** Now you know exactly what's happening. 🎯

