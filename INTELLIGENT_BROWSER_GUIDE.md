# 🧠 Intelligent Browser Automation - Complete Guide

## Overview

The audit agent now has a **"brain"** - an LLM-powered intelligence layer that makes the browser automation self-aware, adaptive, and autonomous. The agent can now:

1. **Understand Context**: Analyzes screenshots and DOM to understand what's on screen
2. **Handle Modals Automatically**: Detects and closes overlays/previews that block automation
3. **Make Smart Decisions**: Decides which tabs to click based on evidence requirements
4. **Learn from Errors**: Suggests recovery actions when things go wrong
5. **Reuse Sessions**: Signs in ONCE and reuses authentication across all operations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Browser Intelligence Layer                  │
│                   (browser_intelligence.py)                  │
├─────────────────────────────────────────────────────────────┤
│  • analyze_page_state() - Visual + DOM analysis             │
│  • auto_handle_modals() - Smart modal detection & closing   │
│  • smart_tab_navigation() - LLM decides which tabs to click  │
│  • should_take_screenshot() - Validates evidence match       │
│  • get_error_recovery_suggestion() - Self-healing on errors  │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ Uses
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────┴───────────┐              ┌───────────┴──────────┐
│  SharePoint       │              │  AWS Screenshot      │
│  Browser Access   │              │  Collector           │
├───────────────────┤              ├──────────────────────┤
│ • Auto-closes     │              │ • Single SSO login   │
│   file previews   │              │ • Reuses session     │
│ • Checkbox        │              │ • Smart tab clicks   │
│   selection       │              │ • Multi-cluster      │
│ • Context-aware   │              │   collection         │
└───────────────────┘              └──────────────────────┘
```

## Key Components

### 1. BrowserIntelligence (integrations/browser_intelligence.py)

The "brain" that gives browsers intelligence:

```python
intelligence = BrowserIntelligence(llm, page)

# Analyze what's on screen
state = intelligence.analyze_page_state()
# Returns: {
#   "page_type": "aws_console|sharepoint_list|...",
#   "modal_or_overlay_open": true/false,
#   "recommended_action": "close_modal|click_tab|...",
#   "reasoning": "..."
# }

# Auto-handle modals (detects and closes automatically)
intelligence.auto_handle_modals()

# Decide which tabs to click
tabs = intelligence.smart_tab_navigation(evidence_requirements)
# Returns: ["Connectivity & security", "Configuration", ...]

# Validate if screenshot is needed
decision = intelligence.should_take_screenshot(evidence_requirements)
# Returns: {
#   "should_screenshot": true,
#   "confidence": 85,
#   "filename": "aws_rds_cluster_connectivity.png",
#   "reasoning": "..."
# }
```

### 2. Enhanced SharePoint Browser (integrations/sharepoint_browser.py)

Now with intelligence:

```python
# Initialize with LLM
sp = SharePointBrowserAccess(headless=False, llm=llm_instance)
sp.connect()

# When downloading files:
# - Automatically detects and closes preview modals
# - Uses checkbox selection to avoid opening previews
# - Falls back intelligently if one method fails
```

**Key Improvements:**
- ✅ **Auto-closes file preview modals** after each download
- ✅ **Checkbox selection** avoids opening previews entirely
- ✅ **Multiple fallback methods** (toolbar → context menu → keyboard)
- ✅ **Intelligent error recovery** using LLM suggestions

### 3. Intelligent AWS Screenshot Collector (integrations/aws_intelligent_screenshot.py)

**Single Sign-On, Multiple Captures:**

```python
collector = IntelligentAWSScreenshotCollector(llm, headless=False)
collector.connect()  # Login ONCE via SSO

# Collect evidence for ALL RDS clusters in one session
evidence_req = {
    "service": "RDS",
    "tabs_needed": ["Connectivity & security", "Configuration", "Maintenance & backups"],
    "purpose": "Backup and encryption verification"
}

all_screenshots = collector.collect_all_rds_clusters(
    evidence_requirements=evidence_req,
    save_dir="./evidence/rds",
    region="us-east-1"
)
# Returns: {
#   "prod-conure-aurora-cluster-phase2": ["screenshot1.png", "screenshot2.png", ...],
#   "prod-conure-phase2": [...],
#   ...
# }
```

**Features:**
- ✅ **Persistent session**: Login once, saved for future runs
- ✅ **Bulk collection**: Process all clusters without re-authenticating
- ✅ **Smart tab navigation**: LLM decides which tabs to visit
- ✅ **Screenshot validation**: LLM confirms each view matches requirements
- ✅ **Auto-modal handling**: Dismisses popups automatically
- ✅ **Error recovery**: Self-healing when things go wrong

## How Intelligence Works

### Modal/Overlay Detection & Closure

The agent automatically handles blocking UI elements:

```python
def auto_handle_modals(self) -> bool:
    """
    1. Detects modals using multiple selectors
    2. Tries close buttons (aria-label, title, data attributes)
    3. Falls back to Escape key
    4. Clicks backdrop if available
    """
```

**Before Intelligence:**
```
Download file → Preview opens → STUCK → Manual intervention needed
```

**After Intelligence:**
```
Download file → Preview opens → Auto-detected → Closed → Next file → Success!
```

### Smart Tab Navigation

LLM analyzes evidence requirements and decides which tabs to visit:

```python
# Evidence from previous year shows these tabs were captured
evidence_requirements = {
    "service": "RDS",
    "previous_evidence": [
        {"filename": "connectivity_screenshot.png", "tab": "Connectivity & security"},
        {"filename": "config_screenshot.png", "tab": "Configuration"}
    ]
}

# LLM analyzes available tabs on page
tabs_on_page = ["Connectivity & security", "Monitoring", "Logs & events", 
                "Configuration", "Maintenance & backups"]

# LLM decides which to visit
decided_tabs = intelligence.smart_tab_navigation(evidence_requirements)
# Returns: ["Connectivity & security", "Configuration"]
```

### Screenshot Validation

Before taking each screenshot, LLM validates it matches requirements:

```python
decision = intelligence.should_take_screenshot(evidence_requirements)

if decision["should_screenshot"] and decision["confidence"] > 70:
    page.screenshot(path=decision["filename"])
```

**Benefits:**
- Avoids capturing wrong views
- Suggests proper filenames
- Provides reasoning for auditors

### Error Recovery

When errors occur, LLM suggests recovery:

```python
try:
    tab.click()
except Exception as e:
    # LLM analyzes error and recent actions
    recovery = intelligence.get_error_recovery_suggestion(str(e))
    
    if recovery["recovery_action"] == "close_modal":
        intelligence.auto_handle_modals()
    elif recovery["recovery_action"] == "retry":
        time.sleep(recovery["wait_time"])
        tab.click()
```

## Usage Examples

### Example 1: SharePoint Evidence Collection

```python
from evidence_manager.llm_evidence_analyzer import LLMEvidenceAnalyzer
from integrations.sharepoint_browser import SharePointBrowserAccess
from langchain_aws import ChatBedrock

# Initialize LLM
llm = ChatBedrock(
    model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    region="us-east-1"
)

# Create intelligent SharePoint browser
sp = SharePointBrowserAccess(headless=False, llm=llm)
sp.connect()

# Navigate to RFI folder
sp.navigate_to_path("TD&R Evidence Collection/FY2025/RFI/BCR-06.01 - XDR Platform")

# List and download all files (intelligence handles modals automatically)
files = sp.list_folder_contents()
for file in files:
    if file['type'] == 'file':
        # Auto-closes preview if it opens
        sp.download_file(file['name'], save_path=f"./downloads/{file['name']}")
```

### Example 2: AWS RDS Evidence Collection

```python
from integrations.aws_intelligent_screenshot import IntelligentAWSScreenshotCollector
from langchain_aws import ChatBedrock

# Initialize
llm = ChatBedrock(model="anthropic.claude-3-5-sonnet-20241022-v2:0")
collector = IntelligentAWSScreenshotCollector(llm, headless=False)

# Connect (login once via SSO)
collector.connect()

# Define what evidence is needed (from previous year analysis)
evidence_requirements = {
    "service": "RDS Aurora",
    "purpose": "Verify backup configuration and encryption",
    "tabs_required": [
        "Connectivity & security",  # For VPC, security groups
        "Configuration",             # For engine version, parameters
        "Maintenance & backups"      # For backup retention, windows
    ]
}

# Collect evidence for ALL clusters (single session!)
results = collector.collect_all_rds_clusters(
    evidence_requirements=evidence_requirements,
    save_dir="./evidence/FY2025/RDS",
    region="us-east-1"
)

# Results show what was captured
for cluster, screenshots in results.items():
    print(f"\n{cluster}:")
    for ss in screenshots:
        print(f"  ✓ {ss}")

collector.close()
```

### Example 3: LLM-Guided Evidence Analysis

```python
from evidence_manager.llm_evidence_analyzer import LLMEvidenceAnalyzer
from langchain_aws import ChatBedrock

llm = ChatBedrock(model="anthropic.claude-3-5-sonnet-20241022-v2:0")
analyzer = LLMEvidenceAnalyzer(llm)

# Analyze previous year's evidence
analysis = analyzer.analyze_file(
    file_path="./evidence/FY2024/RDS/connectivity_screenshot.png",
    file_name="connectivity_screenshot.png"
)

# Get detailed instructions for current year
print(analysis['instructions'])
# Output:
# "Navigate to RDS console → Databases → Click 'prod-conure-aurora-cluster-phase2'
#  → Select 'Connectivity & security' tab → Ensure VPC, subnets, and security
#  groups are visible → Take full-page screenshot showing endpoint details"
```

## Benefits

### For SharePoint Downloads

**Before:**
- Click file → Preview opens → **STUCK** → Manual close → Next file
- **Problem**: Preview modal blocks sequential downloads

**After:**
- ✅ Uses checkbox selection (avoids preview)
- ✅ Auto-detects and closes modals
- ✅ Multiple fallback methods
- ✅ Fully automated batch downloads

### For AWS Screenshots

**Before:**
- Login to AWS → Navigate to RDS → Select cluster → Screenshot
- Repeat login for EACH cluster → Slow, repetitive, error-prone
- Manually guess which tabs to capture

**After:**
- ✅ Login ONCE, session saved
- ✅ Process ALL clusters in one session
- ✅ LLM decides which tabs to visit
- ✅ LLM validates each screenshot
- ✅ Auto-handles popups/modals

### For Error Handling

**Before:**
- Error occurs → Entire script fails → Manual debugging required

**After:**
- ✅ LLM analyzes error context
- ✅ Suggests recovery action
- ✅ Attempts self-healing
- ✅ Continues processing

## Configuration

### Environment Variables

```bash
# SharePoint
SHAREPOINT_SITE_URL=https://cisco.sharepoint.com/sites/YourSite
SHAREPOINT_DOC_LIBRARY="Shared Documents"
SHAREPOINT_BASE_PATH="TD&R Evidence Collection"
SHAREPOINT_BROWSER=firefox  # or chromium

# AWS Region
AWS_DEFAULT_REGION=us-east-1

# LLM Model
AWS_BEDROCK_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Browser Persistence

Both tools use persistent browser profiles:
- **SharePoint**: `~/.audit-agent-browser/`
- **AWS**: `~/.audit-agent-browser-aws/`

**Benefits:**
- Login once, session saved
- No repeated authentication
- Faster subsequent runs

**To clear sessions:**
```bash
rm -rf ~/.audit-agent-browser*
```

## Troubleshooting

### Modals Still Not Closing

If modals persist:
1. Check if LLM is initialized: `sp.intelligence is not None`
2. Manually trigger: `sp.intelligence.auto_handle_modals()`
3. Check console for modal detection messages

### AWS Session Expired

If AWS session expires:
```bash
# Clear saved session
rm -rf ~/.audit-agent-browser-aws/

# Re-run - will prompt for login
collector.connect()
```

### LLM Not Making Smart Decisions

Ensure evidence requirements are detailed:
```python
# ❌ Too vague
evidence_req = {"service": "RDS"}

# ✅ Detailed and specific
evidence_req = {
    "service": "RDS Aurora PostgreSQL",
    "purpose": "Verify automated backups and encryption at rest",
    "required_tabs": ["Connectivity & security", "Configuration", "Maintenance & backups"],
    "previous_year_files": [
        "connectivity_screenshot.png",
        "configuration_screenshot.png",
        "maintenance_screenshot.png"
    ]
}
```

## Future Enhancements

Potential improvements:
1. **Multi-region support**: Automatically switch regions and collect evidence
2. **Parallel collection**: Process multiple AWS services simultaneously
3. **Smart waiting**: LLM decides optimal wait times instead of fixed delays
4. **Visual diff**: Compare current vs previous year screenshots automatically
5. **Anomaly detection**: LLM flags unexpected configurations

## Summary

The intelligent browser automation layer transforms rigid, brittle scripts into adaptive, self-healing agents that:

- 🧠 **Think**: Understand context and make decisions
- 👀 **See**: Analyze visual state and DOM structure
- 🔧 **Adapt**: Handle errors and recover automatically
- 💾 **Remember**: Learn from actions to improve
- ⚡ **Optimize**: Reuse sessions, minimize repetition

This makes evidence collection **faster**, **more reliable**, and **fully autonomous**.
