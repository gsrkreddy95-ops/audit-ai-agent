# 🚀 AuditMate Integration Roadmap

## Current Status: AWS Navigation Issues + Future Integrations

### 📍 **IMMEDIATE PRIORITY: Fix AWS Navigation**

**Problem:**
- Agent sees "API Gateway" in "Recently Viewed" section
- Thinks it's already on the service
- Returns without navigating
- Takes screenshot of home page instead of actual service

**Root Cause:**
```python
# Line 363 in aws_universal_service_navigator.py
if self._reuse_existing_service_view(service_key, service_name):
    return True  # BUG: Returns too early!
```

**Solution:**
1. Fix URL matching to be more strict
2. Verify actual service page, not just text on homepage
3. Always navigate if not on the ACTUAL service console page
4. Add section navigation within services

---

## 🎯 **Phase 1: AWS Navigation Fix** (IMMEDIATE - Next 2 hours)

### Tasks:
- [ ] Fix `_reuse_existing_service_view()` to check actual URL patterns
- [ ] Add strict URL validation (must be on service console, not just homepage)
- [ ] Implement service section navigation (e.g., "Custom Domain Names" in API Gateway)
- [ ] Add resource selection logic (first, by name, by index)
- [ ] Test with multiple services (API Gateway, RDS, EC2, Lambda, S3)

### Implementation:
```python
def _reuse_existing_service_view(self, service_key, service_name):
    current_url = self._safe_current_url()
    
    # STRICT CHECK: Must be on actual service console
    if not current_url or 'console.aws.amazon.com' not in current_url:
        return False
    
    # Check if URL contains service-specific path (not just homepage)
    service_patterns = {
        'apigateway': ['/apigateway/main', '/apigateway/home'],
        'rds': ['/rds/home', '/rds/#databases'],
        'ec2': ['/ec2/v2', '/ec2/home'],
        # ... more patterns
    }
    
    # If we're on AWS homepage, DON'T reuse!
    if '/console/home' in current_url and service_key not in current_url:
        return False  # Homepage != Service page!
    
    # ... strict validation
```

---

## 🎯 **Phase 2: Jira Integration** (2-3 days)

### Features Requested:
1. **List Jira tickets**
   - Filter by project
   - Filter by labels
   - Filter by status, assignee, priority
   - Export to CSV/JSON

2. **Search and analyze tickets**
   - Search by JQL (Jira Query Language)
   - Analyze ticket patterns
   - Generate reports

3. **Ticket operations**
   - Read ticket details
   - List comments
   - Export attachments
   - Get ticket history

### Implementation Plan:

**Tool: `jira_integration.py`**
```python
class JiraIntegration:
    def __init__(self, jira_url, email, api_token):
        from jira import JIRA
        self.jira = JIRA(server=jira_url, basic_auth=(email, api_token))
    
    def list_tickets(self, project=None, labels=None, status=None):
        """List tickets with filters"""
        jql = self._build_jql(project, labels, status)
        return self.jira.search_issues(jql)
    
    def export_tickets(self, tickets, format='csv'):
        """Export to CSV/JSON"""
        pass
```

**Agent Tools:**
- `jira_list_tickets` - List filtered tickets
- `jira_search_jql` - Advanced JQL search
- `jira_get_ticket` - Get ticket details
- `jira_export` - Export tickets

---

## 🎯 **Phase 3: Confluence Integration** (2-3 days)

### Features Requested:
1. **Search documents**
   - Search by title
   - Search by content
   - Search by space
   - Search by labels

2. **Analyze documents**
   - List all documents in space
   - Get document metadata
   - Extract content
   - Download attachments

3. **Document operations**
   - Read document content
   - Export to PDF/markdown
   - List page tree
   - Get page history

### Implementation Plan:

**Tool: `confluence_integration.py`**
```python
class ConfluenceIntegration:
    def __init__(self, confluence_url, email, api_token):
        from atlassian import Confluence
        self.confluence = Confluence(
            url=confluence_url,
            username=email,
            password=api_token
        )
    
    def search_documents(self, query, space=None):
        """Search Confluence docs"""
        cql = f'text ~ "{query}"'
        if space:
            cql += f' AND space = "{space}"'
        return self.confluence.cql(cql)
    
    def get_document(self, page_id):
        """Get full document content"""
        return self.confluence.get_page_by_id(page_id, expand='body.storage')
```

**Agent Tools:**
- `confluence_search` - Search documents
- `confluence_get_page` - Get specific page
- `confluence_list_space` - List all pages in space
- `confluence_export` - Export documents

---

## 🎯 **Phase 4: GitHub Integration** (2-3 days)

### Features Requested:
1. **Query Pull Requests**
   - List PRs by state (open, closed, merged)
   - Filter by author, labels, milestone
   - Get PR details and diff
   - Export PR list

2. **GitHub Discussions**
   - List discussions
   - Search discussions
   - Get discussion comments
   - Export discussions

3. **Repository operations**
   - List repos in organization
   - Search code
   - Get file contents
   - List issues

### Implementation Plan:

**Tool: `github_integration.py`**
```python
class GitHubIntegration:
    def __init__(self, token, org_name):
        from github import Github
        self.github = Github(token)
        self.org = self.github.get_organization(org_name)
    
    def list_prs(self, repo_name, state='all', author=None):
        """List PRs with filters"""
        repo = self.org.get_repo(repo_name)
        prs = repo.get_pulls(state=state)
        if author:
            prs = [pr for pr in prs if pr.user.login == author]
        return prs
    
    def search_discussions(self, query):
        """Search GitHub discussions"""
        # Uses GitHub GraphQL API
        pass
```

**Agent Tools:**
- `github_list_prs` - List pull requests
- `github_get_pr` - Get PR details
- `github_list_discussions` - List discussions
- `github_search_code` - Search code in repos
- `github_export` - Export data

---

## 📦 **Required Dependencies**

### For Jira:
```bash
pip install jira
pip install atlassian-python-api
```

### For Confluence:
```bash
pip install atlassian-python-api
pip install markdown
```

### For GitHub:
```bash
pip install PyGithub
pip install gql  # For GraphQL (Discussions)
```

---

## 🔧 **Configuration Setup**

### `.env` file additions:
```bash
# Jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token

# Confluence
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your-confluence-api-token

# GitHub
GITHUB_TOKEN=your-github-personal-access-token
GITHUB_ORG=your-organization-name
```

---

## 📅 **Timeline Estimate**

| Phase | Task | Time | Priority |
|-------|------|------|----------|
| 1 | Fix AWS Navigation | 2 hours | 🔴 CRITICAL |
| 1 | Add Service Sections | 4 hours | 🔴 CRITICAL |
| 1 | Test & Validate | 2 hours | 🔴 CRITICAL |
| 2 | Jira Integration | 2-3 days | 🟡 HIGH |
| 3 | Confluence Integration | 2-3 days | 🟡 HIGH |
| 4 | GitHub Integration | 2-3 days | 🟡 HIGH |

**Total: ~2-3 weeks for complete implementation**

---

## 🎯 **Next Steps (RIGHT NOW)**

1. **IMMEDIATE**: Fix AWS navigation (next 2 hours)
2. **TODAY**: Test with multiple AWS services
3. **THIS WEEK**: Plan Jira integration architecture
4. **NEXT WEEK**: Begin Jira implementation

---

## 💡 **Note**

This roadmap shows a comprehensive integration plan. We'll tackle AWS navigation first (CRITICAL), then move to Jira/Confluence/GitHub integrations systematically.

Each integration will follow the same pattern:
1. Create integration class
2. Add agent tools
3. Register with tool executor
4. Test and validate
5. Document usage

---

**Ready to start with AWS Navigation Fix?**
Reply "yes, fix AWS navigation now" to proceed!

