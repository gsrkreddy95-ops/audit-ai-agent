"""
Integrations Package - Jira, Confluence, GitHub

Provides integrations with external services for the audit agent.
"""

from .jira_integration import JiraIntegration
from .confluence_integration import ConfluenceIntegration
from .github_integration import GitHubIntegration

__all__ = [
    'JiraIntegration',
    'ConfluenceIntegration',
    'GitHubIntegration',
]
