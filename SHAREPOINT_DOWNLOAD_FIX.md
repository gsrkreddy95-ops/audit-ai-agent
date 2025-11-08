# 🔧 SharePoint Download Fix - Complete Solution

## 🔍 **What Was Wrong:**

The agent was successfully **listing** files from SharePoint (finding 12 PNG files) but **failing to download** them. Here's what was happening:

### **The Problem:**

1. **Incomplete URLs Being Constructed**
   ```
   Built fallback href: https://cisco.sharepoint.com/sites/SPRSecurityTeam/Shared%20Documents/TD%26R%20Documentat ion%20Train%205/TD%26R%20Eviden
   ```
   The URLs were **truncated** (cut off mid-path)!

2. **Download Failures:**
   - Direct URL download → **Timeout** (invalid/incomplete URL)
   - DOM fallback method → **"File not found in DOM"** (couldn't find file elements)

### **Root Causes:**

1. **Bad URL Construction Logic:**
   - The JavaScript code was trying to build file URLs from the folder ID query parameter
   - It was using: `window.location.origin + '/' + encodedFolder`
   - This resulted in incomplete paths like: `https://cisco.sharepoint.com/Shared%20Documents/...` (missing `/sites/SITENAME`)

2. **Wrong SharePoint URL Format:**
   - SharePoint files need specific URL formats depending on file type:
     - Images: `/:i:/r/sites/SITE/PATH/FILE.png?csf=1&web=1`
     - PDFs: `/:b:/r/sites/SITE/PATH/FILE.pdf?csf=1&web=1`
     - Excel: `/:x:/r/sites/SITE/PATH/FILE.xlsx?csf=1&web=1`
   - The code wasn't using these proper SharePoint viewer/download URL formats

3. **Weak DOM Fallback:**
   - When URL download failed, it tried to find files in the DOM
   - But it was only looking for `<a>` links with the file name
   - SharePoint modern UI uses `<span role="button" data-id="heroField">` for file names, not links

---

## ✅ **What I Fixed:**

### **Fix 1: Improved URL Construction (Lines 336-347)**

**Before:**
```javascript
const folderRelative = folderIdRaw.startsWith('/') ? folderIdRaw : ('/' + folderIdRaw);
const encodedFolder = folderRelative.split('/').filter(Boolean).map(part => encodeURIComponent(part)).join('/');
const baseDownloadUrl = window.location.origin + '/' + encodedFolder;  // ❌ INCOMPLETE!
```

**After:**
```javascript
// Build proper base URL from current page location
// SharePoint URLs are like: https://cisco.sharepoint.com/sites/SITE/Shared%20Documents/PATH/TO/FOLDER/FILE.ext
const currentUrl = window.location.href.split('?')[0];  // Remove query params
let baseDownloadUrl = '';
if (folderIdRaw) {
    // Extract the origin and site path from current URL
    const match = currentUrl.match(/(https:\/\/[^\/]+\/[^\/]+\/[^\/]+)/);
    if (match) {
        // Combine origin+site with the folder path
        baseDownloadUrl = match[1] + folderIdRaw;  // ✅ COMPLETE URL!
    }
}
```

### **Fix 2: Added Backup URL Construction (Lines 515-528)**

Added a second fallback that extracts the full site URL pattern:

```javascript
// If still no href and we have the file name, try to find it via SharePoint's direct link pattern
if (!href && !isFolder && name) {
    try {
        // Try to construct from current location
        const siteMatch = window.location.href.match(/(https:\/\/[^\/]+\/sites\/[^\/]+)/);
        if (siteMatch && folderIdRaw) {
            const encodedName = encodeURIComponent(name);
            // Format: https://SITE/sites/SITENAME/FOLDERPATH/FILENAME
            href = siteMatch[1] + folderIdRaw + '/' + encodedName;
            console.log('[SharePoint Extraction] Built site-based href: ' + href);
        }
    } catch (siteErr) {
        console.log('[SharePoint Extraction] Failed to build site href: ' + siteErr);
    }
}
```

### **Fix 3: Proper SharePoint Viewer URLs (Lines 680-715)**

Added logic to convert file URLs to SharePoint's proper viewer/download format:

```python
# For SharePoint, convert to proper viewer/download URL
# Format: https://cisco.sharepoint.com/:i:/r/sites/SITE/Shared%20Documents/PATH/FILE.png?csf=1&web=1
if 'sharepoint.com' in file_url:
    # Determine file extension for SharePoint type code
    ext_map = {
        'png': ':i:', 'jpg': ':i:', 'jpeg': ':i:', 'gif': ':i:', 'bmp': ':i:',  # Images
        'pdf': ':b:',  # PDF
        'docx': ':w:', 'doc': ':w:',  # Word
        'xlsx': ':x:', 'xls': ':x:',  # Excel  
        'pptx': ':p:', 'ppt': ':p:',  # PowerPoint
    }
    ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
    type_code = ext_map.get(ext, ':u:')  # :u: for unknown/download
    
    # Build viewer URL with proper format
    viewer_url = f"{site_part}/{type_code}/r/sites/{site_name}/{file_part}?csf=1&web=1&download=1"
```

### **Fix 4: Enhanced DOM Fallback (Lines 717-787)**

Completely rewrote the DOM-based download fallback with **4 strategies**:

**Strategy 1: Look for heroField span** (SharePoint modern UI)
```python
file_element = self.page.query_selector(f'span[role="button"][data-id="heroField"]:has-text("{file_name}")')
```

**Strategy 2: Look for link elements**
```python
file_links = self.page.query_selector_all(f'[role="gridcell"] a:has-text("{file_name}")')
```

**Strategy 3: Try partial match** (in case SharePoint truncates names)
```python
short_name = file_name.split('.')[0]
file_element = self.page.query_selector(f'span[role="button"][data-id="heroField"]:has-text("{short_name}")')
```

**Strategy 4: Context menu download** (most reliable!)
```python
# Right-click to open context menu
file_element.click(button='right')
time.sleep(1)

# Look for "Download" option
download_option = self.page.query_selector('[role="menuitem"]:has-text("Download")')
if download_option:
    with self.page.expect_download(timeout=30000) as download_info:
        download_option.click()
```

**Strategy 5: Toolbar download** (fallback)
```python
# Click file to select it
file_element.click()
time.sleep(1.5)

# Use toolbar download button
download_button = self.page.query_selector('[data-automationid="downloadCommand"]')
if download_button:
    with self.page.expect_download(timeout=30000) as download_info:
        download_button.click()
```

---

## 🎯 **How It Works Now:**

### **Download Flow:**

1. **Extract file list** with complete URLs
   - ✅ Uses proper SharePoint URL patterns
   - ✅ Includes full site path (`/sites/SITENAME/Shared Documents/...`)

2. **Try URL-based download first**
   - ✅ Converts to SharePoint viewer format (`:i:`, `:b:`, etc.)
   - ✅ Adds `?csf=1&web=1&download=1` params
   - ✅ Navigates to download URL

3. **If URL fails, try DOM methods**
   - ✅ Find file element (span or link)
   - ✅ Right-click → context menu → Download
   - ✅ Or: Click file → toolbar Download button
   - ✅ Or: Extract href and navigate

4. **Multiple retries and fallbacks**
   - Each method has error handling
   - Falls back to next method if one fails
   - Detailed logging for debugging

---

## 📊 **Expected Results:**

### **Before:**
```
✅ Found 12 items
📥 Downloading 12 files...
⬇️  Downloading: APJC Aurora RDS Dahsboard.png...
⚠️  Direct URL download failed, will fallback: Timeout 30000ms exceeded
❌ File not found in DOM: APJC Aurora RDS Dahsboard.png
⚠️  Failed: APJC Aurora RDS Dahsboard.png
[Repeat for all 12 files...]
✅ Downloaded 0/12 files
❌ Tool Error: Failed to download files
```

### **After:**
```
✅ Found 12 items
📥 Downloading 12 files...
⬇️  Downloading: APJC Aurora RDS Dahsboard.png...
📎 Using SharePoint viewer URL
✅ URL download succeeded: APJC Aurora RDS Dahsboard.png
⬇️  Downloading: EU Aurora RDS Dahsboard.png...
📎 Using SharePoint viewer URL
✅ URL download succeeded: EU Aurora RDS Dahsboard.png
[Continue for all files...]
✅ Downloaded 12/12 files
🧠 Analyzing 12 files with LLM...
```

OR (if URL method fails, DOM method will succeed):
```
⬇️  Downloading: APJC Aurora RDS Dahsboard.png...
⚠️  URL download failed, trying DOM method
🔍 Searching for file in DOM...
✓ Found file element in DOM
📋 Opening context menu...
✅ Downloaded via context menu: APJC Aurora RDS Dahsboard.png
```

---

## 🧪 **How to Test:**

### **Test 1: Try the Download Again**

```bash
cd /Users/krishna/Documents/audit-ai-agent
./QUICK_START.sh
```

Then in the agent:
```
Review and collect evidence for RFI BCR-06.01 under XDR Platform in FY2025
```

Expected: All 12 PNG files should download successfully now!

### **Test 2: Check Specific File URL**

The file link you provided:
```
https://cisco.sharepoint.com/:i:/r/sites/SPRSecurityTeam/Shared%20Documents/TD%26R%20Documentation%20Train%205/TD%26R%20Evidence%20Collection/FY2025/XDR%20Platform/BCR-06.01/EU%20Aurora%20RDS%20Dahsboard.png?csf=1&web=1&e=ArNvQP
```

This is **exactly** the format I'm now generating! 
- `:i:` = image type code
- `/r/` = reference path
- `?csf=1&web=1` = SharePoint viewer params

---

## 🔍 **Debugging:**

If downloads still fail, you'll now see much better error messages:

```
⬇️  Downloading: APJC Aurora RDS Dahsboard.png...
📎 Using SharePoint viewer URL
⚠️  URL download failed, trying DOM method: [specific error]
🔍 Searching for file in DOM...
✓ Found file element in DOM
📋 Opening context menu...
⚠️  Context menu download failed: [specific error]
🖱️ Clicking file to select it...
⚠️  Toolbar download failed: [specific error]
⚠️  Could not extract href: [specific error]
❌ No download method succeeded
💡 The file may have been moved or permissions may have changed
```

This tells you **exactly** which method failed and why!

---

## 📝 **Key Changes Summary:**

| Issue | Before | After |
|-------|--------|-------|
| **URL Construction** | Incomplete paths | Full SharePoint URLs with site path |
| **URL Format** | Generic links | Proper SharePoint viewer URLs (`:i:`, `:b:`, etc.) |
| **DOM Finding** | Only looked for `<a>` links | Finds heroField spans AND links |
| **Download Method** | Only tried clicking link | 5 different strategies with fallbacks |
| **Error Handling** | Generic "failed" message | Detailed logging per method |
| **Timeout** | 30 seconds total | 30 seconds **per method** |

---

## 🎉 **Result:**

**SharePoint file downloads should now work reliably!** 

The agent will:
1. ✅ Extract files with complete URLs
2. ✅ Try proper SharePoint viewer/download URLs first
3. ✅ Fall back to DOM-based downloads if needed
4. ✅ Use right-click context menu (most reliable)
5. ✅ Try toolbar download button as backup
6. ✅ Give detailed error messages if something fails

**Try it now!** 🚀

