"""
GitHub Integration - Query PRs, Discussions, Code, and Export Data

Features:
- List and filter pull requests
- Search GitHub Discussions
- Search code across repositories
- Get repository details
- List issues
- Export data to CSV/JSON
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from rich.console import Console

console = Console()


class GitHubIntegration:
    """GitHub API Integration for repository management"""
    
    def __init__(self, token: Optional[str] = None, org_name: Optional[str] = None):
        """
        Initialize GitHub integration
        
        Args:
            token: GitHub Personal Access Token (create at https://github.com/settings/tokens)
            org_name: Organization name (e.g., 'your-org')
        """
        from dotenv import load_dotenv
        load_dotenv()
        
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.org_name = org_name or os.getenv('GITHUB_ORG')
        
        if not self.token:
            console.print("[yellow]⚠️  GitHub token not found in environment![/yellow]")
            console.print("[yellow]   Please set GITHUB_TOKEN in .env file[/yellow]")
            self.github = None
            self.org = None
            return
        
        try:
            from github import Github
            self.github = Github(self.token)
            
            # Test connection
            user = self.github.get_user()
            console.print(f"[green]✅ Connected to GitHub as: {user.login}[/green]")
            
            # Get organization if specified
            if self.org_name:
                self.org = self.github.get_organization(self.org_name)
                console.print(f"[green]✅ Connected to organization: {self.org_name}[/green]")
            else:
                self.org = None
        
        except Exception as e:
            console.print(f"[red]❌ Failed to connect to GitHub: {e}[/red]")
            self.github = None
            self.org = None
    
    def _check_connection(self) -> bool:
        """Check if GitHub connection is active"""
        if not self.github:
            console.print("[red]❌ GitHub not connected! Please check token.[/red]")
            return False
        return True
    
    def list_repositories(self, org: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List repositories
        
        Args:
            org: Organization name (uses default if not specified)
        
        Returns:
            List of repository dictionaries
        """
        if not self._check_connection():
            return []
        
        try:
            org_name = org or self.org_name
            
            if org_name:
                console.print(f"[cyan]📚 Listing repositories in organization: {org_name}[/cyan]")
                org_obj = self.github.get_organization(org_name)
                repos = org_obj.get_repos()
            else:
                console.print("[cyan]📚 Listing your repositories[/cyan]")
                repos = self.github.get_user().get_repos()
            
            repo_list = []
            for repo in repos:
                repo_data = {
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description,
                    'language': repo.language,
                    'stars': repo.stargazers_count,
                    'forks': repo.forks_count,
                    'open_issues': repo.open_issues_count,
                    'private': repo.private,
                    'url': repo.html_url,
                    'created': str(repo.created_at),
                    'updated': str(repo.updated_at),
                }
                repo_list.append(repo_data)
            
            console.print(f"[green]✅ Found {len(repo_list)} repositories[/green]")
            return repo_list
        
        except Exception as e:
            console.print(f"[red]❌ Error listing repositories: {e}[/red]")
            return []
    
    def list_pull_requests(
        self,
        repo_name: str,
        state: str = 'all',
        author: Optional[str] = None,
        label: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List pull requests
        
        Args:
            repo_name: Repository name (e.g., 'org/repo' or 'user/repo')
            state: PR state ('open', 'closed', 'all')
            author: Filter by author username
            label: Filter by label
            limit: Maximum number of PRs to retrieve
        
        Returns:
            List of PR dictionaries
        """
        if not self._check_connection():
            return []
        
        try:
            console.print(f"[cyan]🔍 Listing PRs in {repo_name} (state: {state})[/cyan]")
            
            repo = self.github.get_repo(repo_name)
            pulls = repo.get_pulls(state=state)
            
            pr_list = []
            count = 0
            for pr in pulls:
                if count >= limit:
                    break
                
                # Filter by author if specified
                if author and pr.user.login != author:
                    continue
                
                # Filter by label if specified
                if label:
                    pr_labels = [l.name for l in pr.labels]
                    if label not in pr_labels:
                        continue
                
                pr_data = {
                    'number': pr.number,
                    'title': pr.title,
                    'state': pr.state,
                    'author': pr.user.login,
                    'created': str(pr.created_at),
                    'updated': str(pr.updated_at),
                    'merged': pr.merged,
                    'mergeable': pr.mergeable,
                    'comments': pr.comments,
                    'commits': pr.commits,
                    'additions': pr.additions,
                    'deletions': pr.deletions,
                    'changed_files': pr.changed_files,
                    'labels': [l.name for l in pr.labels],
                    'url': pr.html_url,
                }
                pr_list.append(pr_data)
                count += 1
            
            console.print(f"[green]✅ Found {len(pr_list)} PRs[/green]")
            return pr_list
        
        except Exception as e:
            console.print(f"[red]❌ Error listing PRs: {e}[/red]")
            return []
    
    def get_pull_request(self, repo_name: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed PR information
        
        Args:
            repo_name: Repository name (e.g., 'org/repo')
            pr_number: PR number
        
        Returns:
            PR dictionary with full details
        """
        if not self._check_connection():
            return None
        
        try:
            console.print(f"[cyan]📋 Fetching PR #{pr_number} from {repo_name}[/cyan]")
            
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Get review comments
            review_comments = []
            for comment in pr.get_review_comments():
                review_comments.append({
                    'author': comment.user.login,
                    'created': str(comment.created_at),
                    'body': comment.body,
                    'path': comment.path,
                })
            
            # Get regular comments
            comments = []
            for comment in pr.get_issue_comments():
                comments.append({
                    'author': comment.user.login,
                    'created': str(comment.created_at),
                    'body': comment.body,
                })
            
            pr_data = {
                'number': pr.number,
                'title': pr.title,
                'body': pr.body,
                'state': pr.state,
                'author': pr.user.login,
                'created': str(pr.created_at),
                'updated': str(pr.updated_at),
                'merged': pr.merged,
                'merged_at': str(pr.merged_at) if pr.merged_at else None,
                'merged_by': pr.merged_by.login if pr.merged_by else None,
                'comments': comments,
                'review_comments': review_comments,
                'commits': pr.commits,
                'additions': pr.additions,
                'deletions': pr.deletions,
                'changed_files': pr.changed_files,
                'labels': [l.name for l in pr.labels],
                'url': pr.html_url,
            }
            
            console.print(f"[green]✅ Retrieved PR #{pr_number}[/green]")
            return pr_data
        
        except Exception as e:
            console.print(f"[red]❌ Error fetching PR: {e}[/red]")
            return None
    
    def search_code(
        self,
        query: str,
        repo: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search code across repositories
        
        Args:
            query: Search query (code content to search for)
            repo: Limit search to specific repository (e.g., 'org/repo')
            language: Limit to specific language (e.g., 'python', 'javascript')
            limit: Maximum number of results
        
        Returns:
            List of code result dictionaries
        """
        if not self._check_connection():
            return []
        
        try:
            # Build search query
            search_query = query
            if repo:
                search_query += f' repo:{repo}'
            if language:
                search_query += f' language:{language}'
            
            console.print(f"[cyan]🔍 Searching code: {search_query}[/cyan]")
            
            results = self.github.search_code(search_query)
            
            code_results = []
            count = 0
            for result in results:
                if count >= limit:
                    break
                
                code_data = {
                    'name': result.name,
                    'path': result.path,
                    'repository': result.repository.full_name,
                    'url': result.html_url,
                    'sha': result.sha,
                }
                code_results.append(code_data)
                count += 1
            
            console.print(f"[green]✅ Found {len(code_results)} code matches[/green]")
            return code_results
        
        except Exception as e:
            console.print(f"[red]❌ Code search failed: {e}[/red]")
            return []
    
    def list_issues(
        self,
        repo_name: str,
        state: str = 'all',
        labels: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List issues in a repository
        
        Args:
            repo_name: Repository name (e.g., 'org/repo')
            state: Issue state ('open', 'closed', 'all')
            labels: Filter by labels
            assignee: Filter by assignee
            limit: Maximum number of issues
        
        Returns:
            List of issue dictionaries
        """
        if not self._check_connection():
            return []
        
        try:
            console.print(f"[cyan]🐛 Listing issues in {repo_name} (state: {state})[/cyan]")
            
            repo = self.github.get_repo(repo_name)
            issues = repo.get_issues(state=state, labels=labels or [], assignee=assignee or '')
            
            issue_list = []
            count = 0
            for issue in issues:
                if count >= limit:
                    break
                
                # Skip PRs (GitHub API returns PRs as issues)
                if issue.pull_request:
                    continue
                
                issue_data = {
                    'number': issue.number,
                    'title': issue.title,
                    'state': issue.state,
                    'author': issue.user.login,
                    'assignee': issue.assignee.login if issue.assignee else None,
                    'created': str(issue.created_at),
                    'updated': str(issue.updated_at),
                    'closed': str(issue.closed_at) if issue.closed_at else None,
                    'comments': issue.comments,
                    'labels': [l.name for l in issue.labels],
                    'url': issue.html_url,
                }
                issue_list.append(issue_data)
                count += 1
            
            console.print(f"[green]✅ Found {len(issue_list)} issues[/green]")
            return issue_list
        
        except Exception as e:
            console.print(f"[red]❌ Error listing issues: {e}[/red]")
            return []
    
    def export_data(
        self,
        data: List[Dict[str, Any]],
        output_format: str = 'json',
        output_file: Optional[str] = None
    ) -> str:
        """
        Export data to JSON or CSV
        
        Args:
            data: List of dictionaries to export
            output_format: 'json' or 'csv'
            output_file: Output file path
        
        Returns:
            Path to exported file
        """
        if not data:
            console.print("[yellow]⚠️  No data to export[/yellow]")
            return ""
        
        try:
            # Generate output filename if not provided
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"github_data_{timestamp}.{output_format}"
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if output_format == 'json':
                # Export to JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                console.print(f"[green]✅ Exported {len(data)} items to JSON: {output_path}[/green]")
            
            elif output_format == 'csv':
                # Export to CSV
                import csv
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    if data:
                        fieldnames = list(data[0].keys())
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        
                        for item in data:
                            # Convert lists to strings for CSV
                            row = {k: (', '.join(v) if isinstance(v, list) else v) for k, v in item.items()}
                            writer.writerow(row)
                
                console.print(f"[green]✅ Exported {len(data)} items to CSV: {output_path}[/green]")
            
            else:
                console.print(f"[red]❌ Unsupported format: {output_format}[/red]")
                return ""
            
            return str(output_path)
        
        except Exception as e:
            console.print(f"[red]❌ Export failed: {e}[/red]")
            return ""


# Example usage
if __name__ == "__main__":
    # Initialize GitHub
    github_client = GitHubIntegration()
    
    # List repositories
    repos = github_client.list_repositories()
    
    # List PRs
    prs = github_client.list_pull_requests('your-org/your-repo', state='open')
    
    # Export to CSV
    if prs:
        github_client.export_data(prs, output_format='csv', output_file='prs.csv')
    
    # Search code
    results = github_client.search_code('def authenticate', repo='your-org/your-repo', language='python')
    
    # List issues
    issues = github_client.list_issues('your-org/your-repo', state='open', labels=['bug'])

