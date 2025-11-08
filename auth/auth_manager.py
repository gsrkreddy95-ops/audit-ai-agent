"""
Centralized Authentication Manager
Handles authentication for all integrated services with smart detection
"""

import os
import subprocess
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from rich.console import Console
from rich.prompt import Prompt
import keyring

console = Console()

class AuthManager:
    """Manages authentication across all services"""
    
    def __init__(self):
        self.auth_cache = {}
        self.last_duo_sso_time = None
        self.duo_sso_validity = timedelta(hours=12)  # Assume 12-hour token validity
    
    def check_aws_auth(self, profile: str = "ctr-int") -> Tuple[bool, Optional[str]]:
        """
        Check if AWS credentials are valid for given profile
        Returns: (is_valid, error_message)
        """
        try:
            session = boto3.Session(profile_name=profile)
            sts = session.client('sts')
            sts.get_caller_identity()
            return True, None
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ExpiredToken':
                return False, "AWS credentials expired"
            elif error_code == 'InvalidClientTokenId':
                return False, "AWS credentials invalid"
            else:
                return False, f"AWS auth error: {error_code}"
        except Exception as e:
            return False, f"AWS auth error: {str(e)}"
    
    def run_duo_sso(self) -> bool:
        """
        Run duo-sso to refresh AWS credentials
        Returns: True if successful, False otherwise
        """
        console.print("\n[yellow]🔐 AWS credentials expired or invalid[/yellow]")
        console.print("[cyan]Running duo-sso to refresh credentials...[/cyan]")
        console.print("[yellow]⚠️  Please approve the MFA prompt in your browser[/yellow]\n")
        
        try:
            result = subprocess.run(
                ['duo-sso'],
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode == 0:
                console.print("[green]✅ duo-sso completed successfully![/green]\n")
                self.last_duo_sso_time = datetime.now()
                return True
            else:
                console.print(f"[red]❌ duo-sso failed: {result.stderr}[/red]\n")
                return False
                
        except subprocess.TimeoutExpired:
            console.print("[red]❌ duo-sso timed out. Did you approve the MFA prompt?[/red]\n")
            return False
        except FileNotFoundError:
            console.print("[red]❌ duo-sso command not found. Is it installed?[/red]\n")
            return False
        except Exception as e:
            console.print(f"[red]❌ Error running duo-sso: {e}[/red]\n")
            return False
    
    def ensure_aws_auth(self, profile: str = "ctr-int") -> bool:
        """
        Ensure AWS authentication is valid, run duo-sso if needed
        Returns: True if authenticated, False otherwise
        """
        is_valid, error = self.check_aws_auth(profile)
        
        if is_valid:
            return True
        
        # Check if we recently ran duo-sso
        if self.last_duo_sso_time:
            time_since_sso = datetime.now() - self.last_duo_sso_time
            if time_since_sso < timedelta(minutes=5):
                console.print(f"[red]❌ duo-sso was just run, but auth still failing: {error}[/red]")
                return False
        
        # Need to run duo-sso
        console.print(f"[yellow]⚠️  {error}[/yellow]")
        return self.run_duo_sso()
    
    def get_sharepoint_auth(self) -> Optional[Dict]:
        """Get SharePoint authentication credentials"""
        tenant_id = os.getenv('SHAREPOINT_TENANT_ID')
        client_id = os.getenv('SHAREPOINT_CLIENT_ID')
        client_secret = os.getenv('SHAREPOINT_CLIENT_SECRET')
        
        if not all([tenant_id, client_id, client_secret]):
            console.print("[yellow]⚠️  SharePoint credentials not found in environment[/yellow]")
            console.print("[cyan]Please configure in .env file or provide now:[/cyan]\n")
            
            if not tenant_id:
                tenant_id = Prompt.ask("SharePoint Tenant ID")
            if not client_id:
                client_id = Prompt.ask("SharePoint Client ID")
            if not client_secret:
                client_secret = Prompt.ask("SharePoint Client Secret", password=True)
        
        return {
            'tenant_id': tenant_id,
            'client_id': client_id,
            'client_secret': client_secret
        }
    
    def get_service_auth(self, service_name: str) -> Optional[Dict]:
        """
        Get authentication credentials for any service
        Tries environment variables first, then prompts user
        """
        # Map service names to environment variable prefixes
        service_env_map = {
            'webex': 'WEBEX',
            'pagerduty': 'PAGERDUTY',
            'datadog': 'DATADOG',
            'splunk': 'SPLUNK',
            'wiz': 'WIZ',
            'elasticsearch': 'ELASTICSEARCH',
            'kibana': 'KIBANA'
        }
        
        prefix = service_env_map.get(service_name.lower())
        if not prefix:
            console.print(f"[red]❌ Unknown service: {service_name}[/red]")
            return None
        
        # Try to get from environment
        auth_data = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                auth_data[key] = value
        
        if auth_data:
            return auth_data
        
        # Prompt user for credentials
        console.print(f"\n[yellow]⚠️  {service_name} credentials not found[/yellow]")
        console.print(f"[cyan]Please provide {service_name} credentials:[/cyan]\n")
        
        # Service-specific credential prompts
        if service_name.lower() == 'webex':
            return {
                'WEBEX_ACCESS_TOKEN': Prompt.ask("Webex Access Token", password=True),
                'WEBEX_USER_EMAIL': Prompt.ask("Webex Email")
            }
        elif service_name.lower() == 'pagerduty':
            return {
                'PAGERDUTY_API_KEY': Prompt.ask("PagerDuty API Key", password=True)
            }
        elif service_name.lower() == 'datadog':
            return {
                'DATADOG_API_KEY': Prompt.ask("Datadog API Key", password=True),
                'DATADOG_APP_KEY': Prompt.ask("Datadog Application Key", password=True)
            }
        # Add more services as needed
        
        return None
    
    def detect_auth_failure_type(self, error: Exception) -> str:
        """
        Analyze error and determine authentication failure type
        Returns: Human-readable description of the auth issue
        """
        error_str = str(error).lower()
        
        if 'expiredtoken' in error_str or 'expired' in error_str:
            return "duo-sso"
        elif 'unauthorized' in error_str or '401' in error_str:
            return "invalid_credentials"
        elif 'forbidden' in error_str or '403' in error_str:
            return "insufficient_permissions"
        elif 'mfa' in error_str or 'multi-factor' in error_str:
            return "mfa_required"
        else:
            return "unknown_auth_error"
    
    def handle_auth_error(self, service: str, error: Exception) -> bool:
        """
        Handle authentication error for any service
        Returns: True if user should retry, False if unrecoverable
        """
        auth_type = self.detect_auth_failure_type(error)
        
        if auth_type == "duo-sso":
            console.print(f"\n[yellow]🔐 {service} authentication failed - AWS credentials expired[/yellow]")
            return self.run_duo_sso()
        
        elif auth_type == "invalid_credentials":
            console.print(f"\n[red]❌ {service} authentication failed - Invalid credentials[/red]")
            console.print(f"[cyan]Please update your credentials in .env or provide now:[/cyan]\n")
            # Prompt for new credentials
            new_creds = self.get_service_auth(service)
            if new_creds:
                # Update environment
                os.environ.update(new_creds)
                return True
            return False
        
        elif auth_type == "mfa_required":
            console.print(f"\n[yellow]🔐 {service} requires MFA authentication[/yellow]")
            console.print("[cyan]Please complete MFA authentication in your browser[/cyan]")
            Prompt.ask("\nPress ENTER after completing MFA")
            return True
        
        else:
            console.print(f"\n[red]❌ {service} authentication error: {error}[/red]")
            return False


# Global auth manager instance
auth_manager = AuthManager()

