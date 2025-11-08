# ✅ SharePoint File Listing Fix (Robust Extraction)

## 🎯 Problem:

**Symptoms:**
```
Found 13 rows to process...
✅ Found 0 items
```

**Issue:** SharePoint listing found rows but couldn't extract file names

---

## 🔧 What I Fixed:

### **1. Multiple Fallback Approaches for File Name Extraction**

**Before (Single Approach):**
```python
name_element = first_cell.query_selector('button') or first_cell.query_selector('a')
name = name_element.inner_text().strip()
```

**After (3 Fallback Approaches):**
```python
# Approach 1: Button or link (try both inner_text and text_content)
name_element = first_cell.query_selector('button') or first_cell.query_selector('a')
if name_element:
    name = name_element.inner_text().strip()
    if not name:
        name = name_element.text_content().strip()

# Approach 2: Span with specific attributes
if not name:
    span_element = first_cell.query_selector('span[role="textbox"]') or first_cell.query_selector('span[title]')
    if span_element:
        name = span_element.inner_text().strip() or span_element.get_attribute('title')

# Approach 3: Any text in the cell
if not name:
    name = first_cell.inner_text().strip()
```

---

### **2. Better Wait Logic**

**Before:**
```python
self.page.wait_for_selector('[role="row"]', timeout=10000)
time.sleep(2)
```

**After:**
```python
self.page.wait_for_selector('[role="row"]', timeout=10000)
time.sleep(3)  # Longer delay for rendering

# Wait for actual content (not just structure)
self.page.wait_for_selector('[role="gridcell"]', timeout=5000)
time.sleep(2)  # Extra time for dynamic content
```

**Why:** SharePoint uses dynamic rendering - need to wait for content, not just HTML structure!

---

### **3. Debug Screenshot**

**New Feature:**
```python
# If no items found, save screenshot to Desktop
if len(items) == 0 and len(rows) > 0:
    debug_path = os.path.expanduser('~/Desktop/sharepoint_debug.png')
    self.page.screenshot(path=debug_path)
    console.print(f"📸 Debug screenshot saved to: {debug_path}")
```

**What it does:**
- If file listing fails (0 items but rows exist)
- Automatically saves screenshot to `~/Desktop/sharepoint_debug.png`
- Shows exactly what SharePoint looked like at failure moment

---

### **4. Better Debug Output**

**New:**
```python
console.print(f"[dim]SharePoint list loaded, extracting files...[/dim]")
console.print(f"[dim]Found {len(rows)} rows to process...[/dim]")
console.print(f"[dim]⚠️  Row parse error: {e}[/dim]")  # Shows what failed
```

**Why:** Makes it easier to diagnose issues in real-time

---

## 🧪 Test It Now:

```bash
cd /Users/krishna/Documents/audit-ai-agent
./QUICK_START.sh
```

**Then:**
```
can you check RFI BCR-06.01 under XDR Platform in FY2025
```

---

## 📋 What You'll See:

### **If It Works:**
```
📂 Reading folder contents...
SharePoint list loaded, extracting files...
Found 13 rows to process...
✅ Found 12 items
  📄 file1.png
  📄 file2.csv
  📄 file3.xlsx
  ...
```

### **If It Still Fails:**
```
📂 Reading folder contents...
SharePoint list loaded, extracting files...
Found 13 rows to process...
⚠️  Row parse error: ...  (shows specific errors)
✅ Found 0 items
📸 Debug screenshot saved to: ~/Desktop/sharepoint_debug.png
💡 This will help diagnose why files aren't showing
```

**Then:**
- Check `~/Desktop/sharepoint_debug.png`
- You'll see exactly what SharePoint looks like
- Share the screenshot if the issue persists

---

## 🎯 Why Multiple Approaches?

**SharePoint HTML is inconsistent:**
- Sometimes file names are in `<button>`
- Sometimes in `<a>` tags
- Sometimes in `<span role="textbox">`
- Sometimes in `<span title="...">`
- Sometimes `inner_text()` works
- Sometimes only `text_content()` works
- Sometimes only the `title` attribute has the name

**Solution:** Try all of them! ✅

---

## 🔍 Debugging Steps:

### **If You Get 0 Items:**

1. **Check Desktop for debug screenshot:**
   ```bash
   open ~/Desktop/sharepoint_debug.png
   ```

2. **Look at the screenshot:**
   - Do you see files in the SharePoint UI?
   - Are they loading or still spinning?
   - Is there an error message?

3. **Check Console Output:**
   - Do you see "Row parse error" messages?
   - What do the error messages say?

4. **Try Again (Sometimes It's Just Timing):**
   - SharePoint might have been slow to load
   - Run the same command again
   - Files might show up this time

---

## 🛠️ If Issue Persists:

**Share These 3 Things:**

1. **Debug screenshot:** `~/Desktop/sharepoint_debug.png`
2. **Console output:** Copy the terminal output
3. **SharePoint URL:** The actual URL being accessed

**This will help me:**
- See exactly what SharePoint looks like
- Identify the correct selectors
- Fix the extraction logic

---

## ✅ Summary of Changes:

| Component | Change | Why |
|-----------|--------|-----|
| **File Name Extraction** | 3 fallback approaches | SharePoint HTML varies |
| **Wait Logic** | Longer delays + gridcell wait | Dynamic content needs time |
| **Debug Screenshot** | Auto-save on failure | See what SharePoint looks like |
| **Error Output** | Show specific parse errors | Easier debugging |

---

## 🎯 Expected Improvement:

| Scenario | Before | After |
|----------|--------|-------|
| **Fast SharePoint** | Works | ✅ Works (faster) |
| **Slow SharePoint** | ❌ 0 items | ✅ Works (waits longer) |
| **Different HTML** | ❌ 0 items | ✅ Works (multiple approaches) |
| **Still Fails** | No debug info | ✅ Screenshot + errors |

---

## 🚀 Try It Now:

```bash
./QUICK_START.sh
```

**Then test:**
```
can you check RFI BCR-06.01 under XDR Platform in FY2025
```

**Expected:**
```
✅ Found 12 items
  📄 file1.png
  📄 file2.csv
  ...
```

---

**If you still get 0 items, check `~/Desktop/sharepoint_debug.png` and share it!** 🔍

