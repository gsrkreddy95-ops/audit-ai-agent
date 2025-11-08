#!/usr/bin/env python3
"""
SharePoint Path Diagnostic Tool
Helps identify the correct SharePoint folder path
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from integrations.sharepoint_browser import SharePointBrowserAccess

console = Console()

def main():
    # Load environment variables
    load_dotenv()
    
    console.print("\n[bold cyan]🔍 SharePoint Path Diagnostic Tool[/bold cyan]\n")
    
    # Show current configuration
    console.print("[yellow]📋 Current Configuration:[/yellow]")
    site_url = os.getenv('SHAREPOINT_SITE_URL', 'Not set')
    doc_lib = os.getenv('SHAREPOINT_DOC_LIBRARY', 'Not set')
    base_path = os.getenv('SHAREPOINT_BASE_PATH', 'Not set')
    current_year = os.getenv('SHAREPOINT_CURRENT_YEAR', 'Not set')
    
    console.print(f"  Site URL: {site_url}")
    console.print(f"  Doc Library: {doc_lib}")
    console.print(f"  Base Path: {base_path}")
    console.print(f"  Current Year: {current_year}\n")
    
    # Ask user for the correct path
    console.print("[yellow]📝 Please provide the correct path:[/yellow]")
    console.print("[dim]Open SharePoint in your browser, navigate to the BCR-06.01 folder,")
    console.print("and copy the full URL from the address bar.[/dim]\n")
    
    sharepoint_url = Prompt.ask("Paste SharePoint URL here")
    
    # Parse the URL
    console.print(f"\n[cyan]🔍 Analyzing URL...[/cyan]")
    
    # Extract components
    if '/sites/' in sharepoint_url:
        parts = sharepoint_url.split('/sites/')
        if len(parts) > 1:
            site_path = parts[1].split('/')[0]
            console.print(f"  ✅ Site: {site_path}")
            
            # Find document library
            remaining = sharepoint_url.split(site_path + '/')[1] if site_path + '/' in sharepoint_url else ""
            
            # Common doc library patterns
            if 'Shared%20Documents' in remaining or 'Shared Documents' in remaining:
                console.print(f"  ✅ Doc Library: Shared Documents")
                doc_library = "Shared%20Documents"
                
                # Extract path after doc library
                if 'Shared%20Documents/' in remaining:
                    folder_path = remaining.split('Shared%20Documents/')[1]
                elif 'Shared Documents/' in remaining:
                    folder_path = remaining.split('Shared Documents/')[1]
                else:
                    folder_path = ""
                
                # Remove query parameters
                if '?' in folder_path:
                    folder_path = folder_path.split('?')[0]
                
                # Decode URL encoding
                import urllib.parse
                folder_path = urllib.parse.unquote(folder_path)
                
                console.print(f"  ✅ Folder Path: {folder_path}\n")
                
                # Determine base path and structure
                path_parts = [p for p in folder_path.split('/') if p]
                
                console.print("[green]📁 Detected Path Structure:[/green]")
                for i, part in enumerate(path_parts):
                    console.print(f"  {i+1}. {part}")
                
                console.print("\n[yellow]💡 Recommended .env Configuration:[/yellow]")
                
                # Try to determine base path (everything before FY20XX)
                base_parts = []
                year_found = False
                for part in path_parts:
                    if part.startswith('FY') and len(part) == 6:
                        year_found = True
                        current_year = part
                        break
                    base_parts.append(part)
                
                if base_parts:
                    recommended_base = '/'.join(base_parts)
                    console.print(f"SHAREPOINT_BASE_PATH={recommended_base}")
                
                if year_found:
                    console.print(f"SHAREPOINT_CURRENT_YEAR={current_year}")
                
                console.print(f"SHAREPOINT_DOC_LIBRARY={doc_library}")
                
                # Test the path
                console.print("\n[yellow]🧪 Test Connection? (Opens browser)[/yellow]")
                test = Prompt.ask("Test now?", choices=["yes", "no"], default="no")
                
                if test == "yes":
                    console.print("\n[cyan]🌐 Opening SharePoint...[/cyan]")
                    sp = SharePointBrowserAccess(headless=False)
                    
                    if sp.connect():
                        console.print("[green]✅ Connected to SharePoint[/green]")
                        
                        # Test navigation
                        test_path = '/'.join(path_parts)
                        console.print(f"[cyan]📁 Testing path: {test_path}[/cyan]")
                        
                        if sp.navigate_to_path(test_path):
                            console.print("[green]✅ Path works! Files found:[/green]")
                            files = sp.list_folder_contents()
                            for f in files[:10]:
                                console.print(f"  • {f['name']}")
                            if len(files) > 10:
                                console.print(f"  ... and {len(files) - 10} more")
                        else:
                            console.print("[red]❌ Path navigation failed[/red]")
                        
                        input("\nPress Enter to close browser...")
                        sp.close()
                    else:
                        console.print("[red]❌ Failed to connect[/red]")
    
    console.print("\n[green]✅ Diagnostic complete![/green]")
    console.print("\n[yellow]Next Steps:[/yellow]")
    console.print("1. Update your .env file with the recommended configuration above")
    console.print("2. Restart the agent: ./QUICK_START.sh")
    console.print("3. Try your evidence collection again\n")

if __name__ == "__main__":
    main()

