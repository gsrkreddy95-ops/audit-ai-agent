"""
Complete SharePoint Integration
Dynamically discovers RFI folders, uploads evidence, manages audit structure
"""

import os
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
from office365.sharepoint.folders.folder import Folder
from rich.console import Console
from rich.progress import Progress

console = Console()


class SharePointIntegration:
    """
    Dynamic SharePoint integration for audit evidence management
    """
    
    def __init__(self, auth_manager=None):
        self.auth_manager = auth_manager
        self.ctx = None
        self.site_url = os.getenv('SHAREPOINT_SITE_URL')
        self.rfi_cache = {}  # Cache discovered RFI folders
        self.audit_root = None
        
        # Connect to SharePoint
        self._connect()
    
    def _connect(self):
        """Establish SharePoint connection"""
        if self.auth_manager:
            creds = self.auth_manager.get_sharepoint_auth()
        else:
            creds = {
                'tenant_id': os.getenv('SHAREPOINT_TENANT_ID'),
                'client_id': os.getenv('SHAREPOINT_CLIENT_ID'),
                'client_secret': os.getenv('SHAREPOINT_CLIENT_SECRET')
            }
        
        if not all(creds.values()):
            console.print("[red]❌ SharePoint credentials not configured[/red]")
            return False
        
        try:
            # Create client credentials
            credentials = ClientCredential(
                creds['client_id'],
                creds['client_secret']
            )
            
            # Create SharePoint context
            self.ctx = ClientContext(self.site_url).with_credentials(credentials)
            
            # Test connection
            web = self.ctx.web
            self.ctx.load(web)
            self.ctx.execute_query()
            
            console.print(f"[green]✅ Connected to SharePoint: {web.properties['Title']}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ SharePoint connection failed: {e}[/red]")
            return False
    
    def discover_audit_structure(self, audit_year: str = "FY25", audit_type: str = "ISMAP") -> Dict:
        """
        Dynamically discover audit folder structure in SharePoint
        Returns: Dictionary of discovered structure
        
        Example structure:
        Documents/
          └── TD&R Documentation Train 5/
              └── FY25 - ISMAP Audit/
                  ├── #164 - Reference/
                  ├── CSE and Orbital/
                  ├── DC Controls/
                  ├── TD&R ISMAP Audit Docs/
                  └── XDR/
                      ├── 10.1.2.12/
                      ├── 10.1.2.17/
                      ├── 10.1.2.3/
                      └── ... (many more RFI folders)
        """
        console.print(f"\n[cyan]🔍 Discovering SharePoint audit structure for {audit_year} - {audit_type}...[/cyan]")
        
        try:
            # Navigate to document library
            doc_lib = self.ctx.web.lists.get_by_title("Documents")
            
            # Search for audit root folder
            audit_folder_name = f"{audit_year} - {audit_type} Audit"
            
            # Get all folders recursively
            folders = doc_lib.root_folder.folders
            self.ctx.load(folders)
            self.ctx.execute_query()
            
            # Find audit root
            audit_root = None
            for folder in folders:
                if audit_folder_name.lower() in folder.properties['Name'].lower():
                    audit_root = folder
                    break
            
            if not audit_root:
                # Try alternate path: TD&R Documentation Train 5
                train_folder = self._find_folder_by_pattern(folders, "TD&R Documentation Train")
                if train_folder:
                    self.ctx.load(train_folder.folders)
                    self.ctx.execute_query()
                    for subfolder in train_folder.folders:
                        if audit_folder_name.lower() in subfolder.properties['Name'].lower():
                            audit_root = subfolder
                            break
            
            if not audit_root:
                console.print(f"[red]❌ Audit folder '{audit_folder_name}' not found in SharePoint[/red]")
                return {}
            
            self.audit_root = audit_root
            console.print(f"[green]✅ Found audit root: {audit_root.properties['Name']}[/green]")
            
            # Discover all RFI folders
            structure = self._discover_rfi_folders(audit_root)
            
            # Cache the structure
            self.rfi_cache = structure
            
            # Print summary
            console.print(f"\n[green]📊 Discovered Structure:[/green]")
            console.print(f"  Total product folders: {len(structure)}")
            total_rfis = sum(len(product['rfi_folders']) for product in structure.values())
            console.print(f"  Total RFI folders: {total_rfis}")
            
            return structure
            
        except Exception as e:
            console.print(f"[red]❌ Error discovering audit structure: {e}[/red]")
            return {}
    
    def _discover_rfi_folders(self, parent_folder: Folder) -> Dict:
        """
        Recursively discover all RFI folders under parent
        Returns structure like:
        {
            'XDR': {
                'path': 'Documents/.../XDR',
                'rfi_folders': {
                    '10.1.2.12': {'path': '...', 'description': 'RDS Configuration'},
                    '10.1.2.17': {'path': '...', 'description': 'EC2 Configuration'},
                    ...
                }
            },
            'CSE and Orbital': {...},
            ...
        }
        """
        structure = {}
        
        try:
            # Load child folders
            self.ctx.load(parent_folder.folders)
            self.ctx.execute_query()
            
            for folder in parent_folder.folders:
                folder_name = folder.properties['Name']
                
                # Check if this is an RFI code (e.g., "10.1.2.12")
                if self._is_rfi_code(folder_name):
                    # This is an RFI folder
                    continue
                
                # This is a product/category folder
                console.print(f"  📁 Scanning: {folder_name}")
                
                # Load its subfolders (RFI codes)
                self.ctx.load(folder.folders)
                self.ctx.execute_query()
                
                rfi_folders = {}
                for subfolder in folder.folders:
                    subfolder_name = subfolder.properties['Name']
                    
                    # Check if this is an RFI code
                    if self._is_rfi_code(subfolder_name):
                        rfi_folders[subfolder_name] = {
                            'path': subfolder.properties['ServerRelativeUrl'],
                            'folder_object': subfolder,
                            'description': self._infer_rfi_description(subfolder_name)
                        }
                        console.print(f"    ✅ Found RFI: {subfolder_name}")
                
                if rfi_folders:
                    structure[folder_name] = {
                        'path': folder.properties['ServerRelativeUrl'],
                        'folder_object': folder,
                        'rfi_folders': rfi_folders
                    }
            
            return structure
            
        except Exception as e:
            console.print(f"[red]❌ Error discovering RFI folders: {e}[/red]")
            return {}
    
    def _is_rfi_code(self, folder_name: str) -> bool:
        """
        Determine if folder name is an RFI code
        Examples: "10.1.2.12", "11.2.4.7", "12.1.2.14", etc.
        """
        # Pattern 1: X.X.X.X (numbers with dots)
        pattern1 = r'^\d+\.\d+\.\d+\.\d+$'
        
        # Pattern 2: XX.X.X.X (with more digits)
        pattern2 = r'^\d+\.\d+\.\d+\.\d+'
        
        # Pattern 3: Other patterns like "12.1.5.1.PB"
        pattern3 = r'^\d+\.\d+\.\d+\.\d+\.[A-Z]+'
        
        return bool(re.match(pattern1, folder_name) or 
                   re.match(pattern2, folder_name) or 
                   re.match(pattern3, folder_name))
    
    def _infer_rfi_description(self, rfi_code: str) -> str:
        """
        Infer what the RFI is about based on code pattern
        This is supplementary - the agent should learn from folder contents
        """
        descriptions = {
            '10.1.2': 'Infrastructure Configuration',
            '11.2': 'Security Controls',
            '12.1': 'Change Management',
            '12.2': 'Incident Management',
            # Add more patterns as discovered
        }
        
        for pattern, desc in descriptions.items():
            if rfi_code.startswith(pattern):
                return desc
        
        return 'Unknown - To be determined'
    
    def _find_folder_by_pattern(self, folders, pattern: str) -> Optional[Folder]:
        """Find folder by name pattern"""
        for folder in folders:
            if pattern.lower() in folder.properties['Name'].lower():
                return folder
        return None
    
    def find_rfi_folder(self, rfi_code: str, product: Optional[str] = None) -> Optional[Dict]:
        """
        Find RFI folder by code, optionally within a product
        Returns: {'path': str, 'folder_object': Folder} or None
        """
        if not self.rfi_cache:
            console.print("[yellow]⚠️  RFI cache empty. Run discover_audit_structure() first[/yellow]")
            return None
        
        # Search in specific product
        if product and product in self.rfi_cache:
            if rfi_code in self.rfi_cache[product]['rfi_folders']:
                return self.rfi_cache[product]['rfi_folders'][rfi_code]
        
        # Search across all products
        for product_name, product_data in self.rfi_cache.items():
            if rfi_code in product_data['rfi_folders']:
                console.print(f"[cyan]📁 Found RFI {rfi_code} in {product_name}[/cyan]")
                return product_data['rfi_folders'][rfi_code]
        
        console.print(f"[red]❌ RFI folder {rfi_code} not found[/red]")
        return None
    
    def upload_evidence(self, file_path: str, rfi_code: str, product: Optional[str] = None) -> Tuple[bool, str]:
        """
        Upload evidence file to correct RFI folder
        
        Args:
            file_path: Local file path
            rfi_code: RFI folder code (e.g., "10.1.2.12")
            product: Optional product name (e.g., "XDR")
        
        Returns:
            (success: bool, sharepoint_url: str)
        """
        try:
            # Find RFI folder
            rfi_folder_info = self.find_rfi_folder(rfi_code, product)
            
            if not rfi_folder_info:
                # RFI folder doesn't exist
                if os.getenv('CREATE_MISSING_RFI_FOLDERS', 'true').lower() == 'true':
                    console.print(f"[yellow]⚠️  RFI folder {rfi_code} not found. Creating...[/yellow]")
                    rfi_folder_info = self._create_rfi_folder(rfi_code, product)
                    if not rfi_folder_info:
                        return False, f"Failed to create RFI folder {rfi_code}"
                else:
                    console.print(f"[red]❌ RFI folder {rfi_code} not found and auto-create disabled[/red]")
                    return False, f"RFI folder {rfi_code} not found"
            
            # Read file
            with open(file_path, 'rb') as file_content:
                file_name = Path(file_path).name
                
                # Upload file
                target_folder = rfi_folder_info['folder_object']
                uploaded_file = target_folder.upload_file(file_name, file_content).execute_query()
                
                # Get SharePoint URL
                sharepoint_url = f"{self.site_url}{uploaded_file.serverRelativeUrl}"
                
                console.print(f"[green]✅ Uploaded: {file_name} → RFI {rfi_code}[/green]")
                console.print(f"[cyan]🔗 URL: {sharepoint_url}[/cyan]")
                
                return True, sharepoint_url
        
        except Exception as e:
            console.print(f"[red]❌ Upload failed: {e}[/red]")
            return False, str(e)
    
    def _create_rfi_folder(self, rfi_code: str, product: Optional[str] = None) -> Optional[Dict]:
        """Create new RFI folder in SharePoint"""
        try:
            if not product:
                console.print("[yellow]⚠️  Product not specified. Cannot create RFI folder.[/yellow]")
                console.print("[cyan]Available products:[/cyan]")
                for prod_name in self.rfi_cache.keys():
                    console.print(f"  - {prod_name}")
                return None
            
            if product not in self.rfi_cache:
                console.print(f"[red]❌ Product '{product}' not found in audit structure[/red]")
                return None
            
            # Get product folder
            product_folder = self.rfi_cache[product]['folder_object']
            
            # Create RFI folder
            new_folder = product_folder.folders.add(rfi_code).execute_query()
            
            # Add to cache
            folder_info = {
                'path': new_folder.properties['ServerRelativeUrl'],
                'folder_object': new_folder,
                'description': self._infer_rfi_description(rfi_code)
            }
            
            self.rfi_cache[product]['rfi_folders'][rfi_code] = folder_info
            
            console.print(f"[green]✅ Created RFI folder: {product}/{rfi_code}[/green]")
            
            return folder_info
            
        except Exception as e:
            console.print(f"[red]❌ Failed to create RFI folder: {e}[/red]")
            return None
    
    def list_all_rfi_codes(self) -> List[str]:
        """Get list of all discovered RFI codes"""
        all_rfis = []
        for product_data in self.rfi_cache.values():
            all_rfis.extend(product_data['rfi_folders'].keys())
        return sorted(set(all_rfis))
    
    def get_rfi_suggestions(self, evidence_type: str) -> List[str]:
        """
        Suggest RFI codes based on evidence type
        Uses basic pattern matching - can be enhanced with ML
        """
        suggestions = []
        
        evidence_map = {
            'rds': ['10.1.2.12'],
            'ec2': ['10.1.2.17'],
            'iam': ['10.1.2.3'],
            'database': ['10.1.2.12'],
            'compute': ['10.1.2.17'],
            'access': ['10.1.2.3'],
            'network': ['10.1.2.5'],
            'security': ['10.1.2.5', '11.2.4.7'],
            'kubernetes': ['11.2.4.7'],
            'container': ['11.2.4.7'],
            'incident': ['12.1.2.14'],
            'pagerduty': ['12.1.2.14'],
            'change': ['12.1.4.1'],
            'monitoring': ['12.1.4.7']
        }
        
        evidence_lower = evidence_type.lower()
        for keyword, rfis in evidence_map.items():
            if keyword in evidence_lower:
                suggestions.extend(rfis)
        
        return list(set(suggestions))

