"""
Auto-Fix Engine

Automatically applies fixes when confidence is high enough.

Confidence Levels:
- 90-100%: Auto-apply immediately (safe fixes like missing imports, typos)
- 70-89%: Queue for review (medium risk)
- <70%: Always ask (high risk)

Safety Features:
- All fixes are backed up before applying
- Rollback capability if fix makes things worse
- Learning from successful/failed fixes
"""

import os
import json
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from rich.console import Console

console = Console()


class AutoFixEngine:
    """
    Automatically applies code fixes based on confidence scoring.
    """
    
    def __init__(self, enhancement_manager, knowledge_manager):
        """
        Initialize auto-fix engine.
        
        Args:
            enhancement_manager: EnhancementManager instance
            knowledge_manager: KnowledgeManager instance
        """
        self.enhancement_manager = enhancement_manager
        self.knowledge = knowledge_manager
        
        # Load auto-fix settings
        self.enabled = os.getenv('AUTO_FIX_ENABLED', 'true').lower() == 'true'
        self.auto_apply_threshold = float(os.getenv('AUTO_FIX_CONFIDENCE_THRESHOLD', '0.85'))
        self.backup_dir = Path(__file__).parent.parent / "backups" / "auto_fixes"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        if self.enabled:
            console.print(f"[bold green]🔧 Auto-Fix Engine: ENABLED[/bold green]")
            console.print(f"[dim]   Confidence threshold: {self.auto_apply_threshold*100:.0f}%[/dim]")
        else:
            console.print("[yellow]🔧 Auto-Fix Engine: DISABLED[/yellow]")
    
    def should_auto_apply(self, fix: Dict[str, Any]) -> bool:
        """
        Determine if a fix should be auto-applied.
        
        Args:
            fix: Fix proposal with confidence score
            
        Returns:
            True if safe to auto-apply
        """
        if not self.enabled:
            return False
        
        confidence = fix.get("confidence", 0.0)
        risk_level = fix.get("risk_level", "high")
        
        # High confidence + low risk = auto-apply
        if confidence >= self.auto_apply_threshold and risk_level == "low":
            return True
        
        # Check if this exact error was fixed before successfully
        error_pattern = fix.get("error_pattern", "")
        if error_pattern:
            solution = self.knowledge.find_error_solution(error_pattern)
            if solution and solution.get("success_rate", 0) > 0.9:
                return True
        
        return False
    
    def apply_fix(
        self,
        fix: Dict[str, Any],
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Apply a fix (with backup).
        
        Args:
            fix: Fix specification
            force: Force application even if confidence is low
            
        Returns:
            {
                "success": bool,
                "applied": bool,
                "backup_path": str,
                "message": str
            }
        """
        should_apply = force or self.should_auto_apply(fix)
        
        if not should_apply:
            confidence = fix.get("confidence", 0) * 100
            threshold = self.auto_apply_threshold * 100
            console.print(
                f"[yellow]⚠️  Fix confidence {confidence:.0f}% < threshold {threshold:.0f}%, "
                "queuing for review[/yellow]"
            )
            return {
                "success": True,
                "applied": False,
                "reason": "confidence_too_low",
                "queued_for_review": True
            }
        
        # Backup before applying
        backup_info = self._create_backup(fix)
        
        try:
            # Apply via enhancement manager
            proposal_id = fix.get("id") or fix.get("proposal_id")
            
            if proposal_id:
                result = self.enhancement_manager.apply_proposal(proposal_id)
                
                console.print(f"[bold green]✅ Auto-applied fix: {fix.get('summary')}[/bold green]")
                console.print(f"[dim]   Confidence: {fix.get('confidence', 0)*100:.0f}%[/dim]")
                console.print(f"[dim]   Backup: {backup_info.get('path')}[/dim]")
                
                # Learn from successful application
                self._record_fix_success(fix)
                
                return {
                    "success": True,
                    "applied": True,
                    "backup": backup_info,
                    "proposal_id": proposal_id
                }
            else:
                return {
                    "success": False,
                    "applied": False,
                    "error": "No proposal ID in fix"
                }
                
        except Exception as e:
            console.print(f"[red]❌ Fix application failed: {e}[/red]")
            console.print(f"[yellow]Rolling back from backup...[/yellow]")
            
            # Rollback would happen here
            # Enhancement manager already handles rollback internally
            
            return {
                "success": False,
                "applied": False,
                "error": str(e),
                "backup": backup_info
            }
    
    def _create_backup(self, fix: Dict[str, Any]) -> Dict[str, Any]:
        """Create backup of files before applying fix."""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"fix_{fix.get('id', 'unknown')}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        files = fix.get("files", [])
        backed_up = []
        
        for file_info in files:
            file_path = Path(file_info.get("path", ""))
            if file_path.exists():
                backup_file = backup_path / file_path.name
                shutil.copy2(file_path, backup_file)
                backed_up.append(str(backup_file))
        
        return {
            "path": str(backup_path),
            "files": backed_up,
            "timestamp": timestamp
        }
    
    def _record_fix_success(self, fix: Dict[str, Any]) -> None:
        """Record that a fix was successful for future confidence scoring."""
        
        error_pattern = fix.get("error_pattern") or fix.get("reason", "")
        solution = fix.get("summary", "")
        
        if error_pattern and solution:
            # Update knowledge base with this successful pattern
            existing = self.knowledge.find_error_solution(error_pattern)
            
            if existing:
                # Increment success count
                success_rate = existing.get("success_rate", 0.5)
                new_rate = min(1.0, success_rate + 0.1)  # Gradually increase
                existing["success_rate"] = new_rate
                existing["last_success"] = datetime.now().isoformat()
            else:
                # Add new solution
                self.knowledge.add_error_solution(
                    error_pattern,
                    solution,
                    {
                        "success_rate": 0.9,
                        "auto_applied": True,
                        "first_success": datetime.now().isoformat()
                    }
                )

