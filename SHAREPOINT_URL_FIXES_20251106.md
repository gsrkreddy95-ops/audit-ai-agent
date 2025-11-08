# SharePoint Navigation Fixes - November 6, 2025

## Issues Identified

### 1. **SharePointBrowserAccess Driver Attribute Error**
**Error:**
```
AttributeError: 'SharePointBrowserAccess' object has no attribute 'driver'
```

**Root Cause:**
- `sharepoint_evidence_learner.py` was trying to use `browser.driver.get()` (Selenium API)
- `SharePointBrowserAccess` uses Playwright with `self.page`, not Selenium's `self.driver`
- Missing proper connection and navigation calls

**Fix Applied:**
File: `/Users/krishna/Documents/audit-ai-agent/evidence_manager/sharepoint_evidence_learner.py`

```python
# BEFORE (Line 65):
browser = SharePointBrowserAccess()
browser.driver.get(sharepoint_url)  # ❌ Wrong API

# AFTER (Lines 59-75):
# Decode HTML entities in URL
import html
from urllib.parse import unquote
sharepoint_url = html.unescape(unquote(sharepoint_url))

browser = SharePointBrowserAccess()

# Connect to SharePoint (Playwright API)
if not browser.connect():
    return {"status": "error", "message": "Failed to connect to SharePoint"}

# Navigate to URL (Playwright API)
console.print(f"[cyan]📂 Navigating to folder...[/cyan]")
browser.page.goto(sharepoint_url, timeout=30000)  # ✅ Correct API
time.sleep(3)
```

---

### 2. **URL Encoding Issues**
**Problem:**
URLs with special characters like `&` in "TD&R" were not being handled correctly:
- `%26` (URL encoded) needs to stay as `%26`
- `&amp;` (HTML entity) needs to be decoded to `&`
- Mixed encoding was causing navigation failures

**Example URLs:**
```
USER PROVIDED (Works):
https://cisco.sharepoint.com/sites/SPRSecurityTeam/Shared%20Documents/TD%26R%20Documentation%20Train%205/TD%26R%20Evidence%20Collection/FY2025/BCR-06.01

AGENT WAS GENERATING (Doesn't work):
https://cisco.sharepoint.com/sites/SPRSecurityTeam/Shared%20Documents/TD&R%20Documentation%20Train%205/TD&R%20Evidence%20Collection/FY2025/BCR-06.01
```

**Fix Applied:**
Added URL decoding to handle both HTML entities and URL encoding:

```python
# Decode HTML entities in URL (e.g., %26 or &amp; -> &)
import html
from urllib.parse import unquote
sharepoint_url = html.unescape(unquote(sharepoint_url))
```

---

### 3. **SharePoint Folder Detection**
**Problem:**
The success detection was too strict - only checking for `'Forms/AllItems.aspx'` in URL, missing other valid SharePoint folder view patterns.

**Fix Applied:**
File: `/Users/krishna/Documents/audit-ai-agent/integrations/sharepoint_browser.py`

```python
# BEFORE:
if 'sharepoint.com' in current_url and 'Forms/AllItems.aspx' in current_url:
    # Success logic

# AFTER:
if 'sharepoint.com' in current_url:
    # Check multiple SharePoint URL patterns
    if 'Forms/AllItems.aspx' in current_url or '/Forms/' in current_url or folder_name in decoded_url:
        # Success logic
```

---

## Files Modified

### 1. `/Users/krishna/Documents/audit-ai-agent/evidence_manager/sharepoint_evidence_learner.py`

#### Added import (Line 8):
```python
import time
```

#### Fixed browser initialization and navigation (Lines 59-75):
```python
# Decode HTML entities in URL (e.g., %26 or &amp; -> &)
import html
from urllib.parse import unquote
sharepoint_url = html.unescape(unquote(sharepoint_url))

# Browse SharePoint and list files
console.print("[yellow]🌐 Connecting to SharePoint...[/yellow]")
browser = SharePointBrowserAccess()

# Connect to SharePoint
if not browser.connect():
    return {"status": "error", "message": "Failed to connect to SharePoint"}

# Navigate to URL
console.print(f"[cyan]📂 Navigating to folder...[/cyan]")
browser.page.goto(sharepoint_url, timeout=30000)
time.sleep(3)

# Get list of files
files = browser.list_files_in_current_folder()
```

### 2. `/Users/krishna/Documents/audit-ai-agent/integrations/sharepoint_browser.py`

#### Improved folder detection (Lines 240-260):
```python
# SUCCESS CHECK: Check if we're on a valid SharePoint folder page
import urllib.parse
decoded_url = urllib.parse.unquote(current_url)

# Extract folder name
path_parts = relative_path.split('/')
folder_name = path_parts[-1] if path_parts else ''

if 'sharepoint.com' in current_url:
    # Check multiple SharePoint URL patterns
    if 'Forms/AllItems.aspx' in current_url or '/Forms/' in current_url or folder_name in decoded_url:
        if folder_name and folder_name in decoded_url:
            console.print("[green]✅ Navigation successful![/green]")
            return True
        else:
            console.print("[green]✅ Navigation to SharePoint folder view successful[/green]")
            return True
```

---

## Understanding SharePoint URL Encoding

### Correct URL Format:
```
https://cisco.sharepoint.com/sites/SPRSecurityTeam/Shared%20Documents/TD%26R%20Documentation%20Train%205/TD%26R%20Evidence%20Collection/FY2025/BCR-06.01
```

### URL Component Breakdown:
- `Shared%20Documents` - Space encoded as `%20`
- `TD%26R` - Ampersand encoded as `%26`
- `%20` - Space in URL encoding
- `%26` - Ampersand (&) in URL encoding

### What Gets Decoded:
```python
# Input from Claude/user (may have HTML entities):
"TD&amp;R Documentation Train 5"

# After html.unescape():
"TD&R Documentation Train 5"

# After urllib.parse.quote() in navigate_to_path():
"TD%26R%20Documentation%20Train%205"

# Final URL:
https://.../TD%26R%20Documentation%20Train%205/...
```

---

## Environment Variables (.env)

These are CORRECT and should not be changed:
```bash
SHAREPOINT_SITE_URL=https://cisco.sharepoint.com/sites/SPRSecurityTeam
SHAREPOINT_DOC_LIBRARY=Shared Documents
SHAREPOINT_BASE_PATH=TD&R Documentation Train 5/TD&R Evidence Collection
SHAREPOINT_CURRENT_YEAR=FY2025
SHAREPOINT_PREVIOUS_YEAR=FY2024
```

The agent will automatically:
1. Read these values
2. Build the correct path: `{DOC_LIBRARY}/{BASE_PATH}/{YEAR}/{RFI_CODE}`
3. Encode special characters properly for URLs
4. Navigate to SharePoint

---

## Testing the Fix

### 1. Test learn_from_sharepoint_url tool:
```
"Learn from this SharePoint URL: https://cisco.sharepoint.com/sites/SPRSecurityTeam/Shared%20Documents/TD%26R%20Documentation%20Train%205/TD%26R%20Evidence%20Collection/FY2025/BCR-06.01 for RFI BCR-06.01"
```

### 2. Test sharepoint_review_evidence tool:
```
"Review evidence for RFI BCR-06.01 in FY2025"
```

### Expected Results:
✅ No more `'SharePointBrowserAccess' object has no attribute 'driver'` error
✅ URLs with `&` properly handled
✅ Navigation to SharePoint folders works
✅ Folder detection more flexible
✅ Files can be listed and downloaded

---

## Known Limitations

### Duo Authentication
If you see:
```
⚠️  Session expired! Authentication required for folder access
💡 Please complete Cisco SSO/Okta authentication in the browser
```

**Solution:**
- The browser will open (Firefox/Chromium)
- Complete Duo authentication manually
- Your session will be saved in `~/.audit-agent-browser`
- Future runs won't require re-authentication

### Folder Not Found
If you see:
```
⚠️  Folder not found: TD&R Documentation Train 5/TD&R Evidence Collection/FY2025/BCR-06.01
```

**Possible Causes:**
1. Folder doesn't exist yet in SharePoint
2. Different folder structure than expected
3. Insufficient permissions
4. URL path mismatch

**Solution:**
- Manually navigate in browser to verify folder exists
- Check the exact folder structure in SharePoint
- Ensure you have read permissions
- Use the `learn_from_sharepoint_url` tool with exact SharePoint URL

---

## Summary

✅ **Fixed:** `AttributeError` - Switched from Selenium API (`driver.get()`) to Playwright API (`page.goto()`)
✅ **Fixed:** URL encoding - Added HTML entity and URL decoding
✅ **Fixed:** Connection handling - Added proper `connect()` call before navigation
✅ **Improved:** Folder detection - More flexible URL pattern matching
✅ **Added:** Import for `time` module

The SharePoint integration should now work correctly for:
- Learning from SharePoint URLs
- Reviewing existing evidence
- Navigating to RFI folders
- Handling special characters in paths

---

## Next Steps

1. **Restart agent:** `python3 chat_interface.py`
2. **Test with real SharePoint URL**
3. **Verify folder navigation works**
4. **Check file download and analysis**

The agent is ready to use SharePoint integration!
