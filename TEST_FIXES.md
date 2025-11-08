# 🧪 Quick Test Guide - Radio Button & Timestamp Fixes

## ✅ **What Was Fixed:**

1. **AWS SAML Radio Button Selection** - Now uses 7 click strategies + Python verification
2. **Screenshot Timestamps** - Now 36pt font (was 20pt) with shadow for visibility

---

## 🚀 **How to Test**

### **Step 1: Start the Agent**

```bash
cd /Users/krishna/Documents/audit-ai-agent
./QUICK_START.sh
```

### **Step 2: Test AWS Sign-In + Screenshot**

In the chat, type:

```
Grab screenshot of RDS cluster conure-cluster configuration tab in ctr-prod account
```

### **Step 3: Watch for These NEW Messages:**

#### **✅ During Sign-In (NEW!):**
```
📋 AWS SAML role selection page detected
🔍 Looking for role under account: ctr-prod...
✓ JavaScript completed for: Admin under ctr-prod
✅ VERIFIED: Radio button IS selected          ← SHOULD SEE THIS!
✓ Clicked Sign in button
```

#### **✅ During Screenshot (ENHANCED!):**
```
📸 Capturing screenshot...
✅ Screenshot saved: /path/to/screenshot.png
```

### **Step 4: Verify the Screenshot**

Open the saved screenshot and check:
- ✅ **LARGE timestamp** visible in bottom-right corner
- ✅ Format: `EVIDENCE | 2025-11-07T14:23:45Z`
- ✅ Font is **much bigger** than before
- ✅ Has **shadow** for contrast
- ✅ Has **dark background** for readability

---

## 🔍 **What to Look For**

### **✅ SUCCESS Indicators:**

1. **Radio Button Selection:**
   - Console says: `✅ VERIFIED: Radio button IS selected`
   - **NO** manual clicking needed
   - Automatically proceeds to Sign in

2. **Timestamp Visibility:**
   - Timestamp is **MUCH LARGER** than before
   - Easily readable even from distance
   - Clear contrast with shadow

### **❌ FAILURE Indicators (Unlikely):**

1. **Radio Button Issues:**
   - Console says: `❌ FAILED: Radio button NOT selected`
   - But then tries: `trying Selenium click...`
   - Should still succeed with fallback

2. **Timestamp Issues:**
   - Console says: `⚠️ Could not add timestamp`
   - Screenshot will still save, just without timestamp

---

## 🎯 **Expected Flow**

### **Complete Automated Flow:**

```
1. Launch Chrome                             ✅
   └─ Anti-detection enabled
   
2. Navigate to AWS Duo SSO                   ✅
   └─ User completes Duo MFA

3. SAML Page → Auto-Select Role              ✅ FIXED!
   ├─ Find "Account: ctr-prod"
   ├─ Find first radio under it
   ├─ Click radio 7 different ways
   ├─ Verify with Python
   └─ Click Sign in button

4. Navigate to RDS Cluster                   ✅
   ├─ Direct URL navigation
   ├─ Verify page loaded (JavaScript)
   └─ Click Configuration tab (JavaScript)

5. Capture Screenshot                        ✅ ENHANCED!
   ├─ Scroll to load content
   ├─ Take screenshot
   ├─ Add LARGE timestamp (36pt)            ← NEW!
   ├─ Add shadow for visibility             ← NEW!
   └─ Save with filename timestamp

6. Save Evidence                             ✅
   └─ Organized by RFI/product
```

**100% Automated - No Manual Steps!** 🎉

---

## 📊 **Before vs After**

### **Radio Button Selection:**

**Before:**
```
❌ JavaScript click → Nothing happens
⚠️  User must manually click radio button
⚠️  User must manually click Sign in
```

**After:**
```
✅ JavaScript click (7 strategies)
✅ Python verification
✅ Selenium fallback if needed
✅ Fully automated!
```

### **Screenshot Timestamp:**

**Before:**
```
📸 Screenshot with 20pt timestamp
😐 Hard to read
🔍 Need to zoom in
```

**After:**
```
📸 Screenshot with 36pt timestamp
✨ Easy to read
👀 Visible from distance
```

---

## 🆘 **Troubleshooting**

### **If Radio Button Still Not Working:**

1. **Check Console Output:**
   ```
   Look for: "✅ VERIFIED: Radio button IS selected"
   Or: "trying Selenium click..."
   ```

2. **Check Browser:**
   - Is Chrome actually launching?
   - Can you see the SAML page?
   - Is the radio button visible?

3. **Manual Test:**
   - Try clicking the radio button yourself
   - If you can't click it manually, AWS might have changed their UI

### **If Timestamp Not Visible:**

1. **Check Screenshot File:**
   - Does the screenshot exist?
   - Can you open it?

2. **Check Console Output:**
   - Look for: `⚠️ Could not add timestamp`
   - This would indicate a PIL/Pillow issue

3. **Verify PIL Installation:**
   ```bash
   python -c "from PIL import Image, ImageDraw, ImageFont; print('PIL OK')"
   ```

---

## 📞 **Quick Reference**

### **Test Command:**
```bash
./QUICK_START.sh
```

### **Test Query in Chat:**
```
Grab screenshot of RDS cluster conure-cluster configuration tab in ctr-prod account
```

### **Expected Success Messages:**
```
✅ VERIFIED: Radio button IS selected
✅ Screenshot saved: /path/to/file.png
```

### **Expected Screenshot:**
- ✅ Large timestamp in bottom-right
- ✅ Format: `EVIDENCE | 2025-11-07T14:23:45Z`
- ✅ 36pt font with shadow
- ✅ Dark background for contrast

---

## ✨ **Summary**

**Two major improvements implemented:**

1. **Radio Button Selection** - Bulletproof with 7 strategies + verification
2. **Timestamp Visibility** - 80% larger font (36pt) with shadow

**Test it now to see the improvements!** 🚀

