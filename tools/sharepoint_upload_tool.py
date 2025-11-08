"""
SharePoint Upload Tool
Uploads evidence files to SharePoint using browser automation
"""

import os
from pathlib import Path
from typing import List, Tuple
from rich.console import Console
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from integrations.sharepoint_browser import SharePointBrowserAccess

console = Console()


def upload_to_sharepoint(
    local_files: List[str],
    rfi_code: str,
    product: str = '',
    year: str = 'FY2025'
) -> Tuple[bool, str]:
    """
    Upload evidence files to SharePoint
    
    Args:
        local_files: List of local file paths to upload
        rfi_code: RFI code (e.g., "BCR-06.01")
        product: Product name (e.g., "XDR Platform")
        year: Target year (default: FY2025)
    
    Returns:
        (success, message)
    """
    
    console.print(f"\n[bold cyan]📤 SharePoint Upload[/bold cyan]")
    console.print(f"[cyan]RFI Code: {rfi_code}[/cyan]")
    console.print(f"[cyan]Product: {product or 'Root'}[/cyan]")
    console.print(f"[cyan]Year: {year}[/cyan]")
    console.print(f"[cyan]Files: {len(local_files)}[/cyan]\n")
    
    if not local_files:
        return False, "No files to upload"
    
    # Verify all files exist
    for file_path in local_files:
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
    
    try:
        # Initialize SharePoint browser
        console.print("[cyan]🌐 Opening SharePoint...[/cyan]")
        sp = SharePointBrowserAccess(headless=False)
        
        if not sp.connect():
            return False, "Failed to connect to SharePoint"
        
        # Build target path
        base_path = os.getenv('SHAREPOINT_BASE_PATH', 'TD&R Documentation Train 5/TD&R Evidence Collection')
        
        if product:
            target_path = f"{base_path}/{year}/{product}/{rfi_code}"
        else:
            target_path = f"{base_path}/{year}/{rfi_code}"
        
        console.print(f"[cyan]📂 Navigating to: {target_path}...[/cyan]")
        
        # Try to navigate to folder
        if not sp.navigate_to_path(target_path):
            console.print(f"[yellow]⚠️  Folder doesn't exist: {target_path}[/yellow]")
            console.print(f"[yellow]Please create the folder manually or verify the path[/yellow]")
            sp.close()
            return False, f"Target folder not found: {target_path}"
        
        console.print(f"[green]✅ Navigated to target folder[/green]\n")
        
        # Upload each file
        uploaded = []
        failed = []
        
        for file_path in local_files:
            file_name = os.path.basename(file_path)
            console.print(f"[cyan]⬆️  Uploading: {file_name}...[/cyan]")
            
            if sp.upload_file(file_path, target_path):
                uploaded.append(file_name)
                console.print(f"[green]   ✅ Uploaded successfully[/green]")
            else:
                failed.append(file_name)
                console.print(f"[red]   ❌ Upload failed[/red]")
        
        sp.close()
        
        # Summary
        console.print(f"\n[bold cyan]📊 Upload Summary[/bold cyan]")
        console.print(f"[green]✅ Uploaded: {len(uploaded)} files[/green]")
        if failed:
            console.print(f"[red]❌ Failed: {len(failed)} files[/red]")
            console.print(f"[red]   {', '.join(failed)}[/red]")
        console.print()
        
        if failed:
            return True, f"Uploaded {len(uploaded)}/{len(local_files)} files. {len(failed)} failed."
        else:
            return True, f"Successfully uploaded all {len(uploaded)} files to {target_path}"
    
    except Exception as e:
        console.print(f"[red]❌ Upload error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False, f"Upload failed: {str(e)}"


def batch_upload_from_rfi_folder(
    local_rfi_folder: str,
    rfi_code: str,
    product: str = '',
    year: str = 'FY2025'
) -> Tuple[bool, str]:
    """
    Upload all files from a local RFI folder to SharePoint
    
    Args:
        local_rfi_folder: Local folder containing evidence files
        rfi_code: RFI code
        product: Product name
        year: Target year
    
    Returns:
        (success, message)
    """
    
    folder_path = Path(local_rfi_folder)
    
    if not folder_path.exists():
        return False, f"Local folder not found: {local_rfi_folder}"
    
    # Get all files in folder
    files = [str(f) for f in folder_path.glob('*') if f.is_file()]
    
    if not files:
        return False, f"No files found in: {local_rfi_folder}"
    
    console.print(f"[cyan]📁 Found {len(files)} files in local folder[/cyan]")
    
    return upload_to_sharepoint(files, rfi_code, product, year)

