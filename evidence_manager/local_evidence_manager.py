"""
Local Evidence Manager
Collects evidence locally, organizes by RFI, allows review before SharePoint upload
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

console = Console()


class LocalEvidenceManager:
    """
    Manages local evidence collection and organization before SharePoint upload
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize local evidence manager
        
        Args:
            base_dir: Base directory for evidence (default: ~/Documents/audit-evidence)
        """
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path.home() / "Documents" / "audit-evidence"
        
        self.current_year = os.getenv('SHAREPOINT_CURRENT_YEAR', 'FY2025')
        self.evidence_dir = self.base_dir / self.current_year
        
        # Initialize collected files tracking
        self.collected_files = []
        
        # Create base directories
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
    
    def get_rfi_directory(self, rfi_code: str) -> Path:
        """
        Get or create RFI directory
        
        Args:
            rfi_code: RFI code (e.g., "10.1.2.12")
        
        Returns:
            Path to RFI directory
        """
        rfi_dir = self.evidence_dir / rfi_code
        rfi_dir.mkdir(parents=True, exist_ok=True)
        return rfi_dir
    
    def save_evidence(
        self,
        file_path: Optional[str] = None,
        file_content: Optional[bytes] = None,
        file_name: Optional[str] = None,
        rfi_code: str = None,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, str, str]:
        """
        Save evidence file to local RFI folder
        
        Args:
            file_path: Path to evidence file (if already exists)
            file_content: Raw file content bytes (alternative to file_path)
            file_name: Filename to use when saving file_content
            rfi_code: RFI code to organize under
            description: Optional description of evidence
            metadata: Optional metadata (source, timestamp, etc.)
        
        Returns:
            (success, local_path, message)
        """
        try:
            # Handle file_content directly
            if file_content is not None and file_name:
                # Get RFI directory
                rfi_dir = self.get_rfi_directory(rfi_code)
                dest_path = rfi_dir / file_name
                
                # Write content
                with open(dest_path, 'wb') as f:
                    f.write(file_content)
                
                # Track file
                self.collected_files.append({
                    'path': str(dest_path),
                    'name': file_name,
                    'rfi_code': rfi_code,
                    'size': len(file_content),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'description': description or '',
                    'metadata': metadata or {}
                })
                
                console.print(f"[green]✅ Evidence saved: {dest_path}[/green]")
                return True, str(dest_path), "Success"
            
            # Handle file_path (original behavior)
            elif file_path:
                source_file = Path(file_path)
                
                if not source_file.exists():
                    return False, "", f"Source file not found: {file_path}"
                
                # Get RFI directory
                rfi_dir = self.get_rfi_directory(rfi_code)
                
                # Determine destination filename (keep original name with timestamp)
                file_name = source_file.name
                dest_file = rfi_dir / file_name
            
            # Copy file
            import shutil
            shutil.copy2(source_file, dest_file)
            
            # Save metadata if provided
            if metadata:
                metadata_file = dest_file.with_suffix(dest_file.suffix + '.meta.json')
                import json
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            console.print(f"[green]✅ Saved: {rfi_code}/{file_name}[/green]")
            if description:
                console.print(f"[dim]   📝 {description}[/dim]")
            
            return True, str(dest_file), f"Saved to {rfi_code}/"
            
        except Exception as e:
            console.print(f"[red]❌ Failed to save evidence: {e}[/red]")
            return False, "", str(e)
    
    def list_collected_evidence(self, rfi_code: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        List all collected evidence
        
        Args:
            rfi_code: Optional RFI code to filter (None = all)
        
        Returns:
            Dictionary mapping RFI codes to lists of evidence files
        """
        evidence = {}
        
        if rfi_code:
            # List specific RFI
            rfi_dir = self.evidence_dir / rfi_code
            if rfi_dir.exists():
                evidence[rfi_code] = self._list_files_in_dir(rfi_dir)
        else:
            # List all RFIs
            for rfi_dir in sorted(self.evidence_dir.iterdir()):
                if rfi_dir.is_dir():
                    files = self._list_files_in_dir(rfi_dir)
                    if files:
                        evidence[rfi_dir.name] = files
        
        return evidence
    
    def _list_files_in_dir(self, directory: Path) -> List[Dict]:
        """List files in directory with metadata"""
        files = []
        
        for file_path in sorted(directory.iterdir()):
            if file_path.is_file() and not file_path.name.endswith('.meta.json'):
                file_info = {
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'type': file_path.suffix.lstrip('.')
                }
                
                # Load metadata if exists
                meta_file = file_path.with_suffix(file_path.suffix + '.meta.json')
                if meta_file.exists():
                    import json
                    with open(meta_file) as f:
                        file_info['metadata'] = json.load(f)
                
                files.append(file_info)
        
        return files
    
    def display_evidence_summary(self, rfi_code: Optional[str] = None):
        """
        Display a formatted summary of collected evidence
        
        Args:
            rfi_code: Optional RFI code to filter
        """
        evidence = self.list_collected_evidence(rfi_code)
        
        if not evidence:
            console.print("[yellow]📭 No evidence collected yet[/yellow]")
            return
        
        console.print(f"\n[bold cyan]📊 Collected Evidence Summary[/bold cyan]")
        console.print(f"[cyan]Location: {self.evidence_dir}[/cyan]\n")
        
        total_files = 0
        total_size = 0
        
        for rfi, files in evidence.items():
            console.print(f"\n[bold green]📁 RFI {rfi}[/bold green] ({len(files)} files)")
            
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("File Name", style="cyan")
            table.add_column("Type", style="yellow")
            table.add_column("Size", style="green", justify="right")
            table.add_column("Modified", style="dim")
            
            for file_info in files:
                size_kb = file_info['size'] / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
                
                table.add_row(
                    file_info['name'],
                    file_info['type'].upper(),
                    size_str,
                    file_info['modified']
                )
                
                total_files += 1
                total_size += file_info['size']
            
            console.print(table)
        
        # Summary
        total_size_mb = total_size / (1024 * 1024)
        console.print(f"\n[bold]Total:[/bold] {total_files} files, {total_size_mb:.2f} MB")
        console.print(f"[dim]Organized in {len(evidence)} RFI folder(s)[/dim]\n")
    
    def prompt_for_upload_approval(self, rfi_code: Optional[str] = None) -> bool:
        """
        Display evidence and ask user if they want to upload to SharePoint
        
        Args:
            rfi_code: Optional RFI code to review (None = all)
        
        Returns:
            True if user approves upload, False otherwise
        """
        console.print("\n" + "="*80)
        console.print("[bold yellow]📋 EVIDENCE REVIEW[/bold yellow]")
        console.print("="*80 + "\n")
        
        # Display evidence summary
        self.display_evidence_summary(rfi_code)
        
        # Provide instructions
        console.print("[bold cyan]📝 Review Instructions:[/bold cyan]")
        console.print(f"1. Please review the evidence files in: [green]{self.evidence_dir}[/green]")
        console.print("2. Check filenames, content, and organization")
        console.print("3. Verify timestamps and RFI folder assignments")
        console.print("4. Make any necessary corrections before uploading\n")
        
        # Ask for approval
        if rfi_code:
            question = f"Would you like to proceed with uploading RFI {rfi_code} evidence to SharePoint FY2025?"
        else:
            question = "Would you like to proceed with uploading all collected evidence to SharePoint FY2025?"
        
        approved = Confirm.ask(question, default=False)
        
        if approved:
            console.print("\n[green]✅ Upload approved! Proceeding to SharePoint...[/green]\n")
        else:
            console.print("\n[yellow]⏸️  Upload cancelled. Evidence remains in local directory for further review.[/yellow]\n")
        
        return approved
    
    def get_upload_ready_files(self, rfi_code: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get list of files ready for upload
        
        Args:
            rfi_code: Optional RFI code filter
        
        Returns:
            Dictionary mapping RFI codes to file paths
        """
        evidence = self.list_collected_evidence(rfi_code)
        
        upload_files = {}
        for rfi, files in evidence.items():
            upload_files[rfi] = [f['path'] for f in files]
        
        return upload_files
    
    def clear_uploaded_evidence(self, rfi_code: str, files: List[str]):
        """
        Clear evidence after successful upload
        
        Args:
            rfi_code: RFI code
            files: List of file paths that were uploaded
        """
        for file_path in files:
            try:
                file_obj = Path(file_path)
                if file_obj.exists():
                    file_obj.unlink()
                    
                    # Remove metadata file if exists
                    meta_file = file_obj.with_suffix(file_obj.suffix + '.meta.json')
                    if meta_file.exists():
                        meta_file.unlink()
                
                console.print(f"[dim]🗑️  Cleaned up: {file_obj.name}[/dim]")
            except Exception as e:
                console.print(f"[yellow]⚠️  Could not remove {file_path}: {e}[/yellow]")
        
        # Remove empty RFI directory
        rfi_dir = self.evidence_dir / rfi_code
        if rfi_dir.exists() and not any(rfi_dir.iterdir()):
            rfi_dir.rmdir()
            console.print(f"[dim]🗑️  Removed empty RFI folder: {rfi_code}[/dim]")
    
    def open_evidence_folder(self, rfi_code: Optional[str] = None):
        """
        Open evidence folder in Finder/Explorer
        
        Args:
            rfi_code: Optional RFI code (None = open base folder)
        """
        if rfi_code:
            folder = self.get_rfi_directory(rfi_code)
        else:
            folder = self.evidence_dir
        
        import subprocess
        import platform
        
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", str(folder)])
        elif platform.system() == "Windows":
            subprocess.run(["explorer", str(folder)])
        else:  # Linux
            subprocess.run(["xdg-open", str(folder)])
        
        console.print(f"[cyan]📂 Opened: {folder}[/cyan]")


# Example usage
if __name__ == "__main__":
    manager = LocalEvidenceManager()
    
    # Example: Save some evidence
    console.print("\n[bold]Example: Saving Evidence[/bold]\n")
    
    # Simulate saving evidence files
    manager.save_evidence(
        file_path="/tmp/test_screenshot.png",
        rfi_code="10.1.2.12",
        description="RDS backup configuration screenshot",
        metadata={
            "source": "AWS Console",
            "account": "ctr-int",
            "service": "RDS",
            "timestamp": datetime.now().isoformat()
        }
    )
    
    # Display summary
    manager.display_evidence_summary()
    
    # Prompt for upload approval
    if manager.prompt_for_upload_approval():
        console.print("[green]User approved upload![/green]")
    else:
        console.print("[yellow]User declined upload[/yellow]")

