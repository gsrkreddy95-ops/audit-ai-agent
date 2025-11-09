# 🎯 **VERSION CONTROL FOR SELF-HEALING**

## **Current Status: Git Tracking NOT Automated**

The self-healing system can fix code, but it **doesn't automatically commit changes**. Let's fix that!

---

## **📊 What We Need:**

### **Before Every Fix:**
1. ✅ **Create a git branch** - Isolate changes
2. ✅ **Take a snapshot** - Can always revert
3. ✅ **Log the attempt** - Track what was tried

### **After Every Fix:**
1. ✅ **Run syntax check** - Ensure code is valid
2. ✅ **Commit changes** - Git history
3. ✅ **Add detailed message** - What was fixed, why
4. ✅ **Tag the commit** - Easy to find
5. ✅ **Create changelog** - Human-readable history

### **If Fix Breaks Things:**
1. ✅ **Detect the breakage** - Run tests
2. ✅ **Auto-revert** - Roll back immediately
3. ✅ **Log the failure** - Learn from mistakes
4. ✅ **Try alternative fix** - Self-healing the self-healer!

---

## **🔧 Enhanced Self-Healing with Git Integration**

Let me create an enhanced version:

```python
# File: ai_brain/self_healing_git_tracker.py
"""
Git-integrated self-healing tracker
Automatically commits, tags, and tracks all AI-generated fixes
"""

import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

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
            console.print("[yellow]⚠️  Not a git repository! Initializing...[/yellow]")
            self._init_git_repo()
    
    def _init_git_repo(self):
        """Initialize git repo if needed"""
        try:
            subprocess.run(["git", "init"], cwd=self.repo_root, check=True)
            console.print("[green]✅ Git repository initialized[/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to initialize git: {e}[/red]")
    
    def _run_git_command(self, cmd: list, check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command"""
        return subprocess.run(
            cmd,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=check
        )
    
    def create_fix_branch(self, tool_name: str, issue: str) -> str:
        """Create a new branch for the fix"""
        try:
            # Sanitize branch name
            branch_name = f"self-heal/{tool_name}/{issue[:30]}".replace(" ", "-").replace("/", "-")
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            branch_name = f"{branch_name}-{timestamp}"
            
            # Create and checkout branch
            self._run_git_command(["git", "checkout", "-b", branch_name])
            
            console.print(f"[green]✅ Created branch: {branch_name}[/green]")
            return branch_name
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to create branch: {e}[/yellow]")
            return "main"
    
    def commit_fix(
        self,
        tool_name: str,
        issue: str,
        files_changed: list,
        fix_details: Dict[str, Any]
    ) -> bool:
        """Commit the fix with detailed message"""
        try:
            # Stage changed files
            for file in files_changed:
                self._run_git_command(["git", "add", str(file)])
            
            # Create detailed commit message
            commit_msg = self._create_commit_message(tool_name, issue, fix_details)
            
            # Commit
            self._run_git_command(["git", "commit", "-m", commit_msg])
            
            # Tag the commit
            tag_name = f"self-heal-{tool_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            self._run_git_command(["git", "tag", "-a", tag_name, "-m", f"Self-healing fix for {tool_name}"])
            
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
            msg += "Changes:\n"
            msg += f"- Lines affected: ~{len(details.get('old_code', '').splitlines())} lines\n"
        
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
            
            # Add new entry at the top
            entry = f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {tool_name}\n\n"
            entry += f"**Issue:** {issue}\n\n"
            entry += f"**Tag:** `{tag}`\n\n"
            entry += "**Details:**\n"
            
            if 'file' in details:
                entry += f"- File: `{details['file']}`\n"
            
            if 'test_result' in details:
                entry += f"- Test Result: {details['test_result']}\n"
            
            entry += f"\n**Revert Command:**\n```bash\ngit revert {tag}\n```\n\n"
            entry += "---\n"
            
            # Insert after header
            lines = content.split('\n')
            header_end = 3  # After title and description
            new_content = '\n'.join(lines[:header_end]) + entry + '\n'.join(lines[header_end:])
            
            # Write back
            with open(self.changelog_file, 'w') as f:
                f.write(new_content)
            
            # Commit the changelog
            self._run_git_command(["git", "add", str(self.changelog_file)])
            self._run_git_command(["git", "commit", "--amend", "--no-edit"], check=False)
            
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
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to log fix attempt: {e}[/yellow]")
    
    def revert_last_fix(self) -> bool:
        """Revert the last self-healing fix"""
        try:
            # Get last commit
            result = self._run_git_command(["git", "log", "-1", "--pretty=%H"])
            last_commit = result.stdout.strip()
            
            # Check if it's a self-healing commit
            result = self._run_git_command(["git", "log", "-1", "--pretty=%B"])
            commit_msg = result.stdout
            
            if "AUTOMATED SELF-HEALING FIX" not in commit_msg:
                console.print("[yellow]⚠️  Last commit is not a self-healing fix[/yellow]")
                return False
            
            # Revert
            self._run_git_command(["git", "revert", "HEAD", "--no-edit"])
            
            console.print(f"[green]✅ Reverted last self-healing fix: {last_commit[:7]}[/green]")
            return True
        
        except Exception as e:
            console.print(f"[red]❌ Failed to revert: {e}[/red]")
            return False
    
    def list_self_healing_commits(self, limit: int = 10) -> list:
        """List recent self-healing commits"""
        try:
            result = self._run_git_command([
                "git", "log",
                "--grep=AUTOMATED SELF-HEALING FIX",
                f"--max-count={limit}",
                "--pretty=format:%h|%ai|%s"
            ])
            
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
                return {"total": 0, "successful": 0, "failed": 0}
            
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
            return {}


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
    tracker = get_tracker()
    
    # List recent fixes
    commits = tracker.list_self_healing_commits()
    console.print("\n[bold]Recent Self-Healing Fixes:[/bold]")
    for commit in commits:
        console.print(f"  {commit['hash']} - {commit['date']} - {commit['message']}")
    
    # Show statistics
    stats = tracker.get_fix_statistics()
    console.print(f"\n[bold]Statistics:[/bold]")
    console.print(f"  Total fixes: {stats.get('total', 0)}")
    console.print(f"  Successful: {stats.get('successful', 0)}")
    console.print(f"  Failed: {stats.get('failed', 0)}")
    console.print(f"  Success rate: {stats.get('success_rate', 'N/A')}")
```

**This new system provides:**

1. ✅ **Automatic Git commits** - Every fix is committed
2. ✅ **Detailed commit messages** - Know exactly what was changed
3. ✅ **Git tags** - Easy to find specific fixes
4. ✅ **Changelog** - Human-readable history
5. ✅ **JSON log** - Machine-readable tracking
6. ✅ **Statistics** - Success rates, most-fixed tools
7. ✅ **Easy revert** - One command to undo
8. ✅ **Branches** - Isolate each fix (optional)

---

## **Usage Examples:**

### **View All Self-Healing Fixes:**
```bash
# See all self-healing commits
git log --grep="AUTOMATED SELF-HEALING FIX" --oneline

# Or use the tracker:
python -c "from ai_brain.self_healing_git_tracker import get_tracker; \
           tracker = get_tracker(); \
           for c in tracker.list_self_healing_commits(20): \
               print(f'{c[\"hash\"]} - {c[\"message\"]}')"
```

### **Revert a Bad Fix:**
```bash
# Find the fix
git log --grep="AUTOMATED SELF-HEALING FIX" --oneline

# Revert by hash
git revert abc1234

# Or revert last self-healing fix
python -c "from ai_brain.self_healing_git_tracker import get_tracker; \
           get_tracker().revert_last_fix()"
```

### **View Statistics:**
```bash
python -c "from ai_brain.self_healing_git_tracker import get_tracker; \
           import json; \
           print(json.dumps(get_tracker().get_fix_statistics(), indent=2))"
```

### **Read Changelog:**
```bash
cat SELF_HEALING_CHANGELOG.md
```

---

## **What Gets Tracked:**

### **For Every Fix:**
```json
{
  "timestamp": "2025-11-09T15:30:45",
  "tool_name": "aws_universal_service_navigator",
  "issue": "Clicking on Recently Viewed instead of actual service",
  "success": true,
  "details": {
    "file": "tools/aws_universal_service_navigator.py",
    "old_code": "if self._page_contains_text(service_name):",
    "new_code": "if service_key.lower() in current_url.lower():",
    "test_result": "success"
  },
  "git_commit": "abc1234",
  "git_tag": "self-heal-aws-navigator-20251109-153045"
}
```

### **Commit Message Example:**
```
fix(self-heal): aws_universal_service_navigator - URL validation too loose

🤖 AUTOMATED SELF-HEALING FIX

Tool: aws_universal_service_navigator
Issue: Clicking on Recently Viewed instead of actual service
Timestamp: 2025-11-09T15:30:45
AI Model: Claude 3.5 Sonnet

Changes:
- Lines affected: ~15 lines
- Test result: success

⚠️  This is an AI-generated fix. Review before deploying to production.
```

### **Changelog Entry:**
```markdown
## 2025-11-09 15:30:45 - aws_universal_service_navigator

**Issue:** Clicking on Recently Viewed instead of actual service

**Tag:** `self-heal-aws-navigator-20251109-153045`

**Details:**
- File: `tools/aws_universal_service_navigator.py`
- Test Result: success

**Revert Command:**
```bash
git revert self-heal-aws-navigator-20251109-153045
```
```

---

## **Safety Features:**

### **1. Every Fix is Reversible:**
```bash
# Revert by tag
git revert self-heal-aws-navigator-20251109-153045

# Revert last 3 self-healing fixes
git revert HEAD~2..HEAD

# Revert all today's fixes
git log --grep="2025-11-09" --grep="AUTOMATED SELF-HEALING" --format="%H" | \
    xargs git revert --no-edit
```

### **2. Branch Isolation (Optional):**
Each fix can be made on a separate branch:
```
main
  ├─ self-heal/aws-navigator/url-validation-20251109
  ├─ self-heal/screenshot-tool/timing-fix-20251109
  └─ self-heal/jira-integration/auth-error-20251109
```

### **3. Audit Trail:**
- Git log: Full history
- Changelog: Human-readable
- JSON log: Machine-readable
- Tags: Quick access

---

## **Dashboard View:**

### **Command:**
```bash
python -c "
from ai_brain.self_healing_git_tracker import get_tracker
from rich.console import Console
from rich.table import Table

tracker = get_tracker()
console = Console()

# Show recent fixes
console.print('\n[bold cyan]Recent Self-Healing Fixes:[/bold cyan]')
commits = tracker.list_self_healing_commits(10)

table = Table(show_header=True)
table.add_column('Hash', style='yellow')
table.add_column('Date', style='green')
table.add_column('Fix', style='white')

for c in commits:
    table.add_row(c['hash'], c['date'][:10], c['message'][:60])

console.print(table)

# Show statistics
console.print('\n[bold cyan]Statistics:[/bold cyan]')
stats = tracker.get_fix_statistics()

stats_table = Table(show_header=False)
stats_table.add_column('Metric', style='cyan')
stats_table.add_column('Value', style='green')

stats_table.add_row('Total Fixes', str(stats.get('total', 0)))
stats_table.add_row('Successful', str(stats.get('successful', 0)))
stats_table.add_row('Failed', str(stats.get('failed', 0)))
stats_table.add_row('Success Rate', stats.get('success_rate', 'N/A'))

console.print(stats_table)

# Most fixed tools
if stats.get('most_fixed_tools'):
    console.print('\n[bold cyan]Most Fixed Tools:[/bold cyan]')
    for tool, count in stats['most_fixed_tools']:
        console.print(f'  {tool}: {count} fixes')
"
```

---

## **Integration with Existing Self-Healing:**

Update `ai_brain/self_healing_tools.py`:

```python
from ai_brain.self_healing_git_tracker import get_tracker

def fix_tool_code_with_validation(tool_name: str, issue: str, old_code: str, new_code: str) -> Dict[str, Any]:
    """Fix a bug in tool code with validation AND git tracking"""
    
    tracker = get_tracker()
    
    try:
        # Create a branch for this fix
        branch = tracker.create_fix_branch(tool_name, issue)
        
        # ... existing fix logic ...
        
        # If fix successful:
        files_changed = [source_file]
        fix_details = {
            "file": str(source_file),
            "old_code": old_code,
            "new_code": new_code,
            "test_result": "pending"
        }
        
        # Commit the fix
        tracker.commit_fix(tool_name, issue, files_changed, fix_details)
        
        return {
            "status": "success",
            "message": f"Fixed and committed {tool_name}",
            "git_branch": branch,
            "next_step": "Test the fix and merge if successful"
        }
        
    except Exception as e:
        # Log the failure
        tracker._log_fix_attempt(tool_name, issue, {}, success=False, error=str(e))
        return {"status": "error", "error": str(e)}
```

---

**Would you like me to implement this enhanced Git tracking system?** 🚀

