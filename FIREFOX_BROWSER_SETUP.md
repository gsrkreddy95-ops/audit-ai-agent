# 🦊 Firefox Browser Setup - Fix Chrome Update Issue

## ⚠️ Issue: Chrome Update Required Prompt

You're seeing this in Chromium:
```
Back
Chrome update required
Select the menu icon at the top of the browser
Navigate to Help, then select About Google Chrome
...
```

**This blocks authentication!**

---

## ✅ Solution: Switch to Firefox (Recommended)

Firefox doesn't have update prompts and works perfectly with SharePoint and AWS Console!

---

## 🚀 Quick Setup (3 Steps):

### **Step 1: Install Firefox for Playwright**

```bash
cd /Users/krishna/Documents/audit-ai-agent
source venv/bin/activate
playwright install firefox
```

**What this does:**
- Downloads Playwright's bundled Firefox browser (~70MB)
- Installs it to: `~/Library/Caches/ms-playwright/firefox-*`
- No conflicts with your existing Firefox browser (if you have one)

---

### **Step 2: Update Your `.env` File**

```bash
nano /Users/krishna/Documents/audit-ai-agent/.env
```

**Add this line:**
```bash
# Browser Configuration
SHAREPOINT_BROWSER=firefox
AWS_SCREENSHOT_BROWSER=firefox
```

**Or simply don't add these lines - Firefox is now the default!**

---

### **Step 3: Clear Old Browser Profile (Optional)**

If you had issues with Chromium before, clear the old profile:

```bash
rm -rf ~/.audit-agent-browser/
rm -rf ~/.audit-agent-aws-browser/
```

This ensures a fresh start with Firefox.

---

## 🧪 Test It:

### **Restart Agent**
```bash
cd /Users/krishna/Documents/audit-ai-agent
./QUICK_START.sh
```

### **Try SharePoint Access**
```
Review evidence for BCR-06.01 in XDR Platform
```

**You should see:**
```
🌐 Launching browser for SharePoint access...
🦊 Using Firefox browser (no update prompts!)
📱 Using audit agent browser profile...

[Firefox opens - no Chrome update prompt! 🎉]
```

---

## 🔄 Want to Switch Back to Chromium?

If you prefer Chromium for some reason (not recommended due to update prompts):

**Update `.env`:**
```bash
SHAREPOINT_BROWSER=chromium
AWS_SCREENSHOT_BROWSER=chromium
```

**Or remove the lines entirely to use Firefox (default).**

---

## 📊 Browser Comparison:

| Feature | Firefox ✅ | Chromium ❌ |
|---------|-----------|------------|
| No update prompts | ✅ Yes | ❌ No (blocks auth) |
| SharePoint compatible | ✅ Yes | ✅ Yes |
| AWS Console compatible | ✅ Yes | ✅ Yes |
| Duo MFA support | ✅ Yes | ✅ Yes |
| Screenshot quality | ✅ Excellent | ✅ Excellent |
| Session persistence | ✅ Yes | ✅ Yes |
| File size | ~70MB | ~150MB |
| Stability | ✅ Better | ⚠️ Update issues |

**Winner: Firefox!** 🦊🏆

---

## 🛠️ Installation Verification:

Check if Firefox is installed:

```bash
ls ~/Library/Caches/ms-playwright/ | grep firefox
```

**Expected output:**
```
firefox-1443
```

(Version number may vary)

---

## 🔧 Troubleshooting:

### Issue: "playwright: command not found"

**Solution:**
```bash
cd /Users/krishna/Documents/audit-ai-agent
source venv/bin/activate  # Make sure venv is activated!
playwright install firefox
```

---

### Issue: "Firefox not working"

**Solution 1: Reinstall Firefox**
```bash
playwright install --force firefox
```

**Solution 2: Clear and reinstall**
```bash
rm -rf ~/Library/Caches/ms-playwright/firefox-*
playwright install firefox
```

---

### Issue: "Still see Chrome update prompt"

**This means:**
- Your `.env` still has `SHAREPOINT_BROWSER=chromium`
- OR you forgot to restart the agent

**Solution:**
```bash
# Check your .env
cat .env | grep BROWSER

# If it says chromium, change it:
nano .env
# Set: SHAREPOINT_BROWSER=firefox

# Restart agent
./QUICK_START.sh
```

---

## ✅ Complete Setup Checklist:

- [ ] **Install Firefox:** `playwright install firefox`
- [ ] **Update .env:** Add `SHAREPOINT_BROWSER=firefox` (or leave default)
- [ ] **Clear old profiles:** `rm -rf ~/.audit-agent-browser/` (optional)
- [ ] **Restart agent:** `./QUICK_START.sh`
- [ ] **Test SharePoint access:** Should see "🦊 Using Firefox"
- [ ] **Test AWS screenshots:** Should see "🦊 Using Firefox"
- [ ] **No update prompts!** ✅

---

## 🎯 Why Firefox?

1. ✅ **No update prompts** - Chrome/Chromium constantly asks for updates
2. ✅ **Lightweight** - Smaller download than Chromium
3. ✅ **Stable** - Fewer breaking changes
4. ✅ **Privacy-focused** - Better default settings
5. ✅ **Works perfectly** - All features supported

---

## 📝 Technical Details:

### What Changed:

**File:** `integrations/sharepoint_browser.py`
- Added `SHAREPOINT_BROWSER` environment variable
- Defaults to `firefox`
- Automatically selects Firefox engine
- Falls back to Chromium if specified

**File:** `tools/aws_screenshot_tool.py`
- Added `AWS_SCREENSHOT_BROWSER` environment variable
- Defaults to `firefox`
- Automatically selects Firefox engine
- Falls back to Chromium if specified

**File:** `config/env.template`
- Added browser configuration examples
- Documented Firefox as recommended

---

## 🚀 Ready to Use!

**Just run:**
```bash
playwright install firefox
./QUICK_START.sh
```

**No more Chrome update prompts!** 🎉

The agent will automatically use Firefox for:
- ✅ SharePoint authentication and navigation
- ✅ AWS Console screenshots
- ✅ All browser-based evidence collection

**Enjoy seamless automation!** 🦊✨

