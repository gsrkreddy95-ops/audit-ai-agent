# 🔐 Integration Configuration Guide

This guide shows you how to set up API tokens for Jira, Confluence, and GitHub integrations.

---

## 📋 **Quick Setup**

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Add your API tokens to `.env`

3. Keep `.env` file secure (already in `.gitignore`)

---

## 🎫 **Jira Integration Setup**

### Step 1: Generate Jira API Token

1. Go to: https://id.atlassian.com/manage/api-tokens
2. Click "Create API token"
3. Name it: "Audit AI Agent"
4. Click "Create"
5. Copy the token (you won't see it again!)

### Step 2: Add to `.env`

```bash
# Jira Configuration
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token_here
```

### Step 3: Test Connection

```bash
python -c "from integrations import JiraIntegration; j = JiraIntegration(); print(j.get_projects())"
```

---

## 📄 **Confluence Integration Setup**

### Step 1: Use Same Jira Token

Confluence uses the same API token as Jira (if you're using Atlassian Cloud).

### Step 2: Add to `.env`

```bash
# Confluence Configuration
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your_jira_api_token_here  # Same as Jira!
```

### Step 3: Test Connection

```bash
python -c "from integrations import ConfluenceIntegration; c = ConfluenceIntegration(); print(c.get_spaces())"
```

---

## 🐙 **GitHub Integration Setup**

### Step 1: Generate GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name it: "Audit AI Agent"
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `read:org` (Read org and team membership)
   - ✅ `read:discussion` (Read discussions)
5. Click "Generate token"
6. Copy the token (you won't see it again!)

### Step 2: Add to `.env`

```bash
# GitHub Configuration
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_ORG=your-organization-name  # Optional
```

### Step 3: Test Connection

```bash
python -c "from integrations import GitHubIntegration; g = GitHubIntegration(); print(g.github.get_user().login)"
```

---

## 📝 **Complete `.env` Template**

Create a `.env` file in your project root with this content:

```bash
# ============================================
# AWS Configuration (existing)
# ============================================
AWS_PROFILE=ctr-prod
AWS_REGION=us-east-1

# ============================================
# Claude API Configuration (existing)
# ============================================
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key

# ============================================
# Jira Integration
# ============================================
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token_here

# ============================================
# Confluence Integration
# ============================================
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your_jira_api_token_here  # Same as Jira

# ============================================
# GitHub Integration
# ============================================
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_ORG=your-organization-name  # Optional: default org for queries

# ============================================
# Evidence Collection Paths (existing)
# ============================================
EVIDENCE_BASE_PATH=/Users/yourname/Documents/audit-evidence
SHAREPOINT_EVIDENCE_PATH=TD&R Documentation Train 5/TD&R Evidence Collection
```

---

## ✅ **Verify Setup**

### Install Required Packages

```bash
pip install jira==3.5.2 atlassian-python-api==3.41.0 PyGithub==2.1.1
```

### Test All Integrations

```python
from integrations import JiraIntegration, ConfluenceIntegration, GitHubIntegration

# Test Jira
jira = JiraIntegration()
print("Jira projects:", [p['key'] for p in jira.get_projects()[:3]])

# Test Confluence
confluence = ConfluenceIntegration()
print("Confluence spaces:", [s['key'] for s in confluence.get_spaces()[:3]])

# Test GitHub
github = GitHubIntegration()
print("GitHub user:", github.github.get_user().login if github.github else "Not connected")
```

---

## 🔒 **Security Best Practices**

1. **Never commit `.env` file** (already in `.gitignore`)
2. **Use token rotation**:
   - Jira/Confluence: Rotate every 90 days
   - GitHub: Rotate every 90 days
3. **Limit token scopes**:
   - Only grant minimum required permissions
4. **Revoke unused tokens**:
   - Clean up old tokens regularly
5. **Use environment-specific tokens**:
   - Different tokens for dev/staging/prod

---

## 🆘 **Troubleshooting**

### "Jira not connected" Error

**Problem:** Can't connect to Jira

**Solutions:**
1. Check URL format: `https://your-company.atlassian.net` (no `/wiki`)
2. Verify email matches your Atlassian account
3. Regenerate API token if expired
4. Check firewall/VPN settings

### "Confluence not connected" Error

**Problem:** Can't connect to Confluence

**Solutions:**
1. Check URL format: `https://your-company.atlassian.net/wiki`
2. Use same token as Jira
3. Verify Confluence is enabled for your org

### "GitHub token not found" Error

**Problem:** GitHub token not detected

**Solutions:**
1. Check token starts with `ghp_`
2. Verify token has required scopes
3. Check token hasn't expired
4. Regenerate if needed

### "HTTP 401 Unauthorized" Error

**Problem:** Invalid credentials

**Solutions:**
1. Regenerate API tokens
2. Check for typos in `.env`
3. Verify email is correct
4. Check token hasn't been revoked

---

## 📚 **Usage Examples**

### List Jira Tickets

```bash
python chat_interface.py

You: list all open Jira tickets in the AUDIT project
```

### Search Confluence

```bash
You: search Confluence for "security procedures" in the SEC space
```

### List GitHub PRs

```bash
You: list open pull requests in the audit-ai-agent repository
```

### Export Data

```bash
You: export all Jira tickets with label "security" to CSV
```

---

## 🎉 **Ready to Use!**

Once your `.env` file is configured, the agent will automatically:
- ✅ Connect to Jira/Confluence/GitHub
- ✅ Use your credentials securely
- ✅ Handle authentication transparently
- ✅ Export data when requested
- ✅ Never expose tokens in logs

**Test it now:**
```bash
python chat_interface.py

You: list Jira projects
```

---

## 🔗 **Useful Links**

- **Jira API Tokens:** https://id.atlassian.com/manage/api-tokens
- **GitHub Tokens:** https://github.com/settings/tokens
- **Jira REST API Docs:** https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- **Confluence REST API Docs:** https://developer.atlassian.com/cloud/confluence/rest/v1/
- **GitHub REST API Docs:** https://docs.github.com/en/rest

---

**Questions?** The agent can help! Just ask: "How do I set up Jira integration?"

