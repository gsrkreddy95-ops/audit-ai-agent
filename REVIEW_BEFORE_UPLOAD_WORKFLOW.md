# 📋 Review-Before-Upload Workflow

## ✅ **Your Safety Feature: Review Before Upload**

All evidence is collected locally first, allowing you to review before committing to SharePoint!

---

## 🔄 **Complete Workflow:**

### **Step 1: Request Evidence Collection**

Ask the agent to collect evidence:

```
You: "Collect RDS backup configuration screenshots from ctr-int for RFI 10.1.2.12"
```

**Agent will:**
- ✅ Connect to AWS (via duo-sso if needed)
- ✅ Take screenshots/export data
- ✅ Add timestamps automatically
- ✅ Save to local folder: `~/Documents/audit-evidence/FY2025/10.1.2.12/`

---

### **Step 2: Review Collected Evidence**

**Type:** `review` or `show evidence`

**You'll see:**
```
╔═══════════════════════════════════════════════════════╗
║               📊 Collected Evidence Summary           ║
╚═══════════════════════════════════════════════════════╝

Location: /Users/krishna/Documents/audit-evidence/FY2025

📁 RFI 10.1.2.12 (3 files)
┌────────────────────────────────────────┬──────┬──────┬─────────────────┐
│ File Name                              │ Type │ Size │ Modified        │
├────────────────────────────────────────┼──────┼──────┼─────────────────┤
│ rds_backup_config_ctr-int_20250611_... │ PNG  │ 2.1M │ 2025-06-11 14:30│
│ rds_instances_list_ctr-int_20250611_...│ XLSX │ 45K  │ 2025-06-11 14:31│
│ rds_backup_retention_ctr-int_202506... │ PDF  │ 120K │ 2025-06-11 14:32│
└────────────────────────────────────────┴──────┴──────┴─────────────────┘

Total: 3 files, 2.26 MB
```

---

### **Step 3: Manual Review (Optional)**

**Type:** `open evidence` or `open folder`

**This opens Finder to:**
```
/Users/krishna/Documents/audit-evidence/FY2025/

You can:
✅ View screenshots
✅ Check Excel/CSV exports
✅ Read PDF documents
✅ Verify filenames and timestamps
✅ Make corrections if needed
✅ Delete unwanted files
```

---

### **Step 4: Upload Approval**

**Type:** `upload`

**Agent asks:**
```
╔═══════════════════════════════════════════════════════╗
║                  📋 EVIDENCE REVIEW                   ║
╚═══════════════════════════════════════════════════════╝

[Shows evidence summary again]

📝 Review Instructions:
1. Please review the evidence files in: /Users/krishna/Documents/audit-evidence/FY2025
2. Check filenames, content, and organization
3. Verify timestamps and RFI folder assignments
4. Make any necessary corrections before uploading

Would you like to proceed with uploading all collected evidence to SharePoint FY2025? (y/n)
```

**Your choices:**

- **Yes (y):** ✅ Agent uploads to SharePoint FY2025
- **No (n):** ⏸️  Upload cancelled, files remain local for more review

---

## 📂 **Local Storage Structure:**

```
~/Documents/audit-evidence/
└── FY2025/
    ├── 10.1.2.12/  (RDS Configuration)
    │   ├── rds_backup_config_ctr-int_20250611_143022.png
    │   ├── rds_instances_list_ctr-int_20250611_143045.xlsx
    │   └── rds_backup_retention_ctr-int_20250611_143200.pdf
    │
    ├── 10.1.2.17/  (EC2 Configuration)
    │   ├── ec2_instances_ctr-int_20250611_144512.png
    │   ├── ec2_security_groups_ctr-int_20250611_144600.xlsx
    │   └── ec2_volumes_ctr-int_20250611_144700.csv
    │
    └── 10.1.2.3/   (IAM Configuration)
        ├── iam_users_list_ctr-prod_20250611_145000.png
        ├── iam_policies_export_ctr-prod_20250611_145100.xlsx
        └── iam_roles_summary_ctr-prod_20250611_145200.json
```

---

## 🎯 **Quick Commands:**

| Command | Action |
|---------|--------|
| `review` | Show evidence summary |
| `show evidence` | Show evidence summary |
| `open evidence` | Open folder in Finder |
| `open folder` | Open folder in Finder |
| `upload` | Start upload approval process |
| `status` | Show agent status + evidence location |

---

## 💡 **Example Conversation:**

```
You: Collect S3 bucket screenshots from ctr-int

Agent: 🤖 Collecting S3 bucket evidence from ctr-int...
       [duo-sso authentication if needed]
       📸 Taking scrolling screenshots (87 buckets)...
       ✅ Saved 5 screenshots to ~/Documents/audit-evidence/FY2025/10.1.2.5/
       
       Evidence collected:
       - s3_buckets_ctr-int_part01_20250611_150000.png
       - s3_buckets_ctr-int_part02_20250611_150005.png
       - s3_buckets_ctr-int_part03_20250611_150010.png
       - s3_buckets_ctr-int_part04_20250611_150015.png
       - s3_buckets_ctr-int_part05_20250611_150020.png
       
       Type 'review' to see summary or 'upload' when ready!

You: review

[Shows detailed table of files]

You: open evidence

[Finder opens to /Users/krishna/Documents/audit-evidence/FY2025/10.1.2.5/]
[You manually review screenshots]

You: upload

Agent: 📋 EVIDENCE REVIEW
       [Shows summary again]
       
       Would you like to proceed with uploading all collected evidence to SharePoint FY2025? (y/n)

You: y

Agent: ✅ Upload approved! Uploading to SharePoint...
       🔄 Uploading to FY2025/10.1.2.5/...
       ✅ Uploaded 5 files successfully!
       🗑️  Cleaned up local files
```

---

## 🔒 **Safety Features:**

1. **No Automatic Uploads:** Agent NEVER uploads without your approval
2. **Local Review:** Always saved locally first
3. **Grammatically Correct Prompts:** Clear, professional questions
4. **Detailed Summaries:** See exactly what will be uploaded
5. **Cancellation Anytime:** Say "no" to keep files local
6. **Cleanup After Upload:** Local files removed after successful upload

---

## 🎊 **Benefits:**

| Benefit | Description |
|---------|-------------|
| ✅ **Safety** | Review before committing to SharePoint |
| ✅ **Flexibility** | Make corrections before upload |
| ✅ **Transparency** | See all files, sizes, timestamps |
| ✅ **Control** | You decide when to upload |
| ✅ **Organization** | Proper RFI folder structure |
| ✅ **Timestamps** | Automatic YYYYMMDD_HHMMSS naming |

---

## 📝 **File Naming Convention:**

```
[description]_[account]_[timestamp].[ext]

Examples:
- rds_backup_config_ctr-int_20250611_143022.png
- iam_users_export_ctr-prod_20250611_143045.xlsx
- s3_buckets_list_ctr-int_part01_20250611_150000.png
```

**Format:**
- `description`: What the evidence shows (rds_backup_config, iam_users_export)
- `account`: AWS account (ctr-int, ctr-prod, sxo101)
- `timestamp`: YYYYMMDD_HHMMSS
- `ext`: File extension (png, xlsx, pdf, csv, json)

---

## 🚀 **Ready to Use!**

Start the agent:
```bash
cd /Users/krishna/Documents/audit-ai-agent
./START_AGENT.sh
```

Then follow the workflow:
1. **Request** evidence
2. **Review** locally
3. **Approve** upload
4. **Done!**

**Your evidence is safe and organized!** 🎉

