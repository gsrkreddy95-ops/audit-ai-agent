"""
Git-integrated self-healing tracker
Automatically commits, tags, and tracks all AI-generated fixes
"""

import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from rich.console import Console

console = Console()


class SelfHealingGitTracker:
    """Track all self-healing changes with Git"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.changelog_file = self.repo_root / "SELF_HEALING_CHANGELOG.md"
        self.fix_log_file = self.repo_root / ".self_healing_log.json"
        
        # Ensure we're in a git repo
        if not (self.repo_root / ".git").exists():
            console.print("[yellow]⚠️  Not a git repository! Skipping git tracking...[/yellow]")
    
    def _run_git_command(self, cmd: List[str], check: bool = True) -> Optional[subprocess.CompletedProcess]:
        """Run a git command"""
        try:
            return subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=check
            )
        except Exception as e:
            console.print(f"[yellow]⚠️  Git command failed: {e}[/yellow]")
            return None
    
    def commit_fix(
        self,
        tool_name: str,
        issue: str,
        files_changed: List[str],
        fix_details: Dict[str, Any]
    ) -> bool:
        """Commit the fix with detailed message"""
        try:
            # Stage changed files
            for file in files_changed:
                result = self._run_git_command(["git", "add", str(file)])
                if not result:
                    return False
            
            # Create detailed commit message
            commit_msg = self._create_commit_message(tool_name, issue, fix_details)
            
            # Commit
            result = self._run_git_command(["git", "commit", "-m", commit_msg])
            if not result:
                return False
            
            # Tag the commit
            tag_name = f"self-heal-{tool_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            self._run_git_command(["git", "tag", "-a", tag_name, "-m", f"Self-healing fix for {tool_name}"], check=False)
            
            console.print(f"[green]✅ Committed fix: {commit_msg[:60]}...[/green]")
            console.print(f"[cyan]🏷️  Tagged as: {tag_name}[/cyan]")
            
            # Update changelog
            self._update_changelog(tool_name, issue, fix_details, tag_name)
            
            # Log to JSON
            self._log_fix_attempt(tool_name, issue, fix_details, success=True)
            
            return True
        
        except Exception as e:
            console.print(f"[red]❌ Failed to commit: {e}[/red]")
            self._log_fix_attempt(tool_name, issue, fix_details, success=False, error=str(e))
            return False
    
    def _create_commit_message(self, tool_name: str, issue: str, details: Dict) -> str:
        """Create detailed commit message"""
        msg = f"fix(self-heal): {tool_name} - {issue}\n\n"
        msg += "🤖 AUTOMATED SELF-HEALING FIX\n\n"
        msg += f"Tool: {tool_name}\n"
        msg += f"Issue: {issue}\n"
        msg += f"Timestamp: {datetime.now().isoformat()}\n"
        msg += f"AI Model: Claude 3.5 Sonnet\n\n"
        
        if 'old_code' in details:
            old_lines = len(details.get('old_code', '').splitlines())
            new_lines = len(details.get('new_code', '').splitlines())
            msg += "Changes:\n"
            msg += f"- Lines changed: {old_lines} → {new_lines}\n"
        
        if 'test_result' in details:
            msg += f"- Test result: {details['test_result']}\n"
        
        msg += "\n⚠️  This is an AI-generated fix. Review before deploying to production.\n"
        
        return msg
    
    def _update_changelog(self, tool_name: str, issue: str, details: Dict, tag: str):
        """Update the self-healing changelog"""
        try:
            # Read existing changelog
            if self.changelog_file.exists():
                with open(self.changelog_file, 'r') as f:
                    content = f.read()
            else:
                content = "# Self-Healing Changelog\n\n"
                content += "This file tracks all automated fixes applied by the AI agent.\n\n"
                content += "---\n\n"
            
            # Add new entry at the top
            entry = f"## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {tool_name}\n\n"
            entry += f"**Issue:** {issue}\n\n"
            entry += f"**Tag:** `{tag}`\n\n"
            entry += "**Details:**\n"
            
            if 'file' in details:
                entry += f"- File: `{details['file']}`\n"
            
            if 'test_result' in details:
                entry += f"- Test Result: {details['test_result']}\n"
            
            entry += f"\n**Revert Command:**\n```bash\ngit revert {tag}\n```\n\n"
            entry += "---\n\n"
            
            # Insert after header
            parts = content.split('---\n\n', 1)
            if len(parts) == 2:
                new_content = parts[0] + '---\n\n' + entry + parts[1]
            else:
                new_content = content + entry
            
            # Write back
            with open(self.changelog_file, 'w') as f:
                f.write(new_content)
            
            # Stage and amend commit to include changelog
            self._run_git_command(["git", "add", str(self.changelog_file)])
            self._run_git_command(["git", "commit", "--amend", "--no-edit"], check=False)
            
            console.print(f"[green]✅ Updated changelog: {self.changelog_file}[/green]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to update changelog: {e}[/yellow]")
    
    def _log_fix_attempt(
        self,
        tool_name: str,
        issue: str,
        details: Dict,
        success: bool,
        error: Optional[str] = None
    ):
        """Log fix attempt to JSON file"""
        try:
            # Read existing log
            if self.fix_log_file.exists():
                with open(self.fix_log_file, 'r') as f:
                    log = json.load(f)
            else:
                log = {"fixes": []}
            
            # Add new entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "tool_name": tool_name,
                "issue": issue,
                "success": success,
                "details": details,
                "error": error
            }
            
            log["fixes"].append(entry)
            
            # Write back
            with open(self.fix_log_file, 'w') as f:
                json.dump(log, f, indent=2)
            
            console.print(f"[green]✅ Logged fix attempt to: {self.fix_log_file}[/green]")
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to log fix attempt: {e}[/yellow]")
    
    def list_self_healing_commits(self, limit: int = 10) -> List[Dict]:
        """List recent self-healing commits"""
        try:
            result = self._run_git_command([
                "git", "log",
                "--grep=AUTOMATED SELF-HEALING FIX",
                f"--max-count={limit}",
                "--pretty=format:%h|%ai|%s"
            ])
            
            if not result:
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 2)
                    if len(parts) == 3:
                        commits.append({
                            "hash": parts[0],
                            "date": parts[1],
                            "message": parts[2]
                        })
            
            return commits
        
        except Exception as e:
            console.print(f"[red]❌ Failed to list commits: {e}[/red]")
            return []
    
    def get_fix_statistics(self) -> Dict:
        """Get statistics about self-healing fixes"""
        try:
            if not self.fix_log_file.exists():
                return {"total": 0, "successful": 0, "failed": 0, "success_rate": "N/A"}
            
            with open(self.fix_log_file, 'r') as f:
                log = json.load(f)
            
            total = len(log.get("fixes", []))
            successful = sum(1 for f in log.get("fixes", []) if f.get("success"))
            failed = total - successful
            
            # Get most fixed tools
            tool_counts = {}
            for fix in log.get("fixes", []):
                tool = fix.get("tool_name")
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
            
            most_fixed = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "total": total,
                "successful": successful,
                "failed": failed,
                "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "N/A",
                "most_fixed_tools": most_fixed
            }
        
        except Exception as e:
            console.print(f"[red]❌ Failed to get statistics: {e}[/red]")
            return {"total": 0, "successful": 0, "failed": 0, "success_rate": "N/A"}
    
    def revert_last_fix(self) -> bool:
        """Revert the last self-healing fix"""
        try:
            # Get last self-healing commit
            result = self._run_git_command([
                "git", "log",
                "--grep=AUTOMATED SELF-HEALING FIX",
                "--max-count=1",
                "--pretty=format:%H"
            ])
            
            if not result or not result.stdout.strip():
                console.print("[yellow]⚠️  No self-healing fixes found to revert[/yellow]")
                return False
            
            commit_hash = result.stdout.strip()
            
            # Revert
            result = self._run_git_command(["git", "revert", commit_hash, "--no-edit"])
            if not result:
                return False
            
            console.print(f"[green]✅ Reverted last self-healing fix: {commit_hash[:7]}[/green]")
            return True
        
        except Exception as e:
            console.print(f"[red]❌ Failed to revert: {e}[/red]")
            return False


# Global instance
_tracker = None

def get_tracker() -> SelfHealingGitTracker:
    """Get global tracker instance"""
    global _tracker
    if _tracker is None:
        _tracker = SelfHealingGitTracker()
    return _tracker


# Example usage
if __name__ == "__main__":
    from rich.table import Table
    
    tracker = get_tracker()
    
    # List recent fixes
    commits = tracker.list_self_healing_commits()
    if commits:
        console.print("\n[bold cyan]Recent Self-Healing Fixes:[/bold cyan]\n")
        table = Table(show_header=True)
        table.add_column("Hash", style="yellow")
        table.add_column("Date", style="green")
        table.add_column("Fix", style="white")
        
        for commit in commits:
            table.add_row(commit['hash'], commit['date'][:10], commit['message'][:60])
        
        console.print(table)
    
    # Show statistics
    stats = tracker.get_fix_statistics()
    console.print(f"\n[bold cyan]Statistics:[/bold cyan]")
    console.print(f"  Total fixes: {stats.get('total', 0)}")
    console.print(f"  Successful: {stats.get('successful', 0)}")
    console.print(f"  Failed: {stats.get('failed', 0)}")
    console.print(f"  Success rate: {stats.get('success_rate', 'N/A')}\n")
    
    # Most fixed tools
    if stats.get('most_fixed_tools'):
        console.print("[bold cyan]Most Fixed Tools:[/bold cyan]")
        for tool, count in stats['most_fixed_tools']:
            console.print(f"  {tool}: {count} fixes")

