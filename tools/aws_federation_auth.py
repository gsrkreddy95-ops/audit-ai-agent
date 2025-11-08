"""
AWS Federation Authentication

This module implements the official AWS Console Federation approach:
1. Extract SAML assertion after Duo authentication
2. Use STS AssumeRoleWithSAML to get temporary credentials
3. Call AWS Federation endpoint to get SigninToken
4. Build direct console URLs (bypasses SAML sign-in button!)

This is the industry-standard approach used by AWS SSO CLI and professional tools.
Much more reliable than clicking buttons on the SAML page.

Reference: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_enable-console-custom-url.html
"""

import base64
import json
import time
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Tuple
import requests
import boto3
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from rich.console import Console

console = Console()


class AWSFederationAuth:
    """
    Handles AWS Console authentication using Federation API.
    
    This bypasses the flaky SAML sign-in button by:
    1. Extracting SAML assertion from Duo auth response
    2. Getting temporary AWS credentials via STS
    3. Exchanging credentials for a Federation SigninToken
    4. Building direct console URLs for any AWS service
    """
    
    def __init__(self, driver, debug: bool = False):
        """
        Initialize AWS Federation authenticator.
        
        Args:
            driver: Selenium WebDriver instance
            debug: Enable debug logging
        """
        self.driver = driver
        self.debug = debug
        self.session_credentials = None
        self.signin_token = None
        self.token_expiry = None
    
    def extract_saml_assertion(self, timeout: int = 30) -> Optional[str]:
        """
        Extract SAML assertion from the page after Duo authentication.
        
        The SAML assertion is typically in a hidden form field named 'SAMLResponse'.
        
        Args:
            timeout: Maximum time to wait for SAML response (seconds)
        
        Returns:
            Base64-encoded SAML assertion string, or None if not found
        """
        try:
            console.print("[cyan]🔍 Extracting SAML assertion...[/cyan]")
            
            # Wait for SAML response form to appear
            wait = WebDriverWait(self.driver, timeout)
            saml_input = wait.until(
                EC.presence_of_element_located((By.NAME, 'SAMLResponse'))
            )
            
            # Get the SAML assertion (base64 encoded)
            saml_assertion = saml_input.get_attribute('value')
            
            if saml_assertion:
                console.print(f"[green]✅ SAML assertion extracted ({len(saml_assertion)} chars)[/green]")
                if self.debug:
                    # Decode and show first 200 chars
                    decoded = base64.b64decode(saml_assertion).decode('utf-8')
                    console.print(f"[dim]SAML preview: {decoded[:200]}...[/dim]")
                return saml_assertion
            else:
                console.print("[red]❌ SAML assertion field is empty[/red]")
                return None
                
        except Exception as e:
            console.print(f"[red]❌ Failed to extract SAML assertion: {e}[/red]")
            if self.debug:
                console.print(f"[dim]Current URL: {self.driver.current_url}[/dim]")
            return None
    
    def parse_saml_assertion(self, saml_assertion: str) -> Optional[Dict[str, str]]:
        """
        Parse SAML assertion to extract AWS role ARN and principal ARN.
        
        Args:
            saml_assertion: Base64-encoded SAML assertion
        
        Returns:
            Dictionary with 'role_arn' and 'principal_arn', or None if parsing fails
        """
        try:
            console.print("[cyan]📋 Parsing SAML assertion...[/cyan]")
            
            # Decode base64
            decoded_saml = base64.b64decode(saml_assertion).decode('utf-8')
            
            # Parse XML
            root = ET.fromstring(decoded_saml)
            
            # Find the SAML attribute containing AWS roles
            # AWS puts role info in: <Attribute Name="https://aws.amazon.com/SAML/Attributes/Role">
            namespaces = {
                'saml': 'urn:oasis:names:tc:SAML:2.0:assertion'
            }
            
            role_arn = None
            principal_arn = None
            
            # Find all attributes
            for attribute in root.findall('.//saml:Attribute', namespaces):
                attr_name = attribute.get('Name')
                
                if 'Role' in attr_name:
                    # Get the attribute value
                    for value in attribute.findall('saml:AttributeValue', namespaces):
                        role_value = value.text
                        
                        if role_value and ',' in role_value:
                            # AWS format: "arn:aws:iam::ACCOUNT:role/ROLE,arn:aws:iam::ACCOUNT:saml-provider/PROVIDER"
                            parts = role_value.split(',')
                            
                            # Identify which is role and which is principal
                            for part in parts:
                                if ':role/' in part:
                                    role_arn = part.strip()
                                elif ':saml-provider/' in part:
                                    principal_arn = part.strip()
                            
                            if role_arn and principal_arn:
                                break
                
                if role_arn and principal_arn:
                    break
            
            if role_arn and principal_arn:
                console.print(f"[green]✅ Parsed SAML assertion[/green]")
                if self.debug:
                    console.print(f"[dim]   Role ARN: {role_arn}[/dim]")
                    console.print(f"[dim]   Principal ARN: {principal_arn}[/dim]")
                
                return {
                    'role_arn': role_arn,
                    'principal_arn': principal_arn
                }
            else:
                console.print("[red]❌ Could not find role/principal ARNs in SAML assertion[/red]")
                return None
                
        except Exception as e:
            console.print(f"[red]❌ Failed to parse SAML assertion: {e}[/red]")
            return None
    
    def assume_role_with_saml(self, saml_assertion: str, role_arn: str, principal_arn: str) -> Optional[Dict]:
        """
        Use STS AssumeRoleWithSAML to get temporary AWS credentials.
        
        Args:
            saml_assertion: Base64-encoded SAML assertion
            role_arn: AWS role ARN to assume
            principal_arn: AWS SAML principal ARN
        
        Returns:
            Dictionary with AccessKeyId, SecretAccessKey, SessionToken, or None
        """
        try:
            console.print("[cyan]🔑 Getting temporary AWS credentials via STS...[/cyan]")
            
            # Create STS client (no credentials needed for AssumeRoleWithSAML)
            sts_client = boto3.client('sts')
            
            # Call AssumeRoleWithSAML
            response = sts_client.assume_role_with_saml(
                RoleArn=role_arn,
                PrincipalArn=principal_arn,
                SAMLAssertion=saml_assertion,
                DurationSeconds=3600  # 1 hour (max for console federation)
            )
            
            credentials = response['Credentials']
            
            console.print(f"[green]✅ Got temporary credentials (valid for 1 hour)[/green]")
            if self.debug:
                console.print(f"[dim]   Access Key ID: {credentials['AccessKeyId']}[/dim]")
                console.print(f"[dim]   Expiration: {credentials['Expiration']}[/dim]")
            
            # Store credentials for later use
            self.session_credentials = {
                'sessionId': credentials['AccessKeyId'],
                'sessionKey': credentials['SecretAccessKey'],
                'sessionToken': credentials['SessionToken']
            }
            
            return self.session_credentials
            
        except Exception as e:
            console.print(f"[red]❌ Failed to assume role with SAML: {e}[/red]")
            return None
    
    def get_signin_token(self, credentials: Dict) -> Optional[str]:
        """
        Call AWS Federation endpoint to get a SigninToken.
        
        This token allows direct console access without clicking buttons!
        
        Args:
            credentials: Dict with sessionId, sessionKey, sessionToken
        
        Returns:
            SigninToken string, or None if request fails
        """
        try:
            console.print("[cyan]🎫 Getting Federation signin token...[/cyan]")
            
            # AWS Federation endpoint
            federation_url = 'https://signin.aws.amazon.com/federation'
            
            # Prepare the session JSON
            session_json = json.dumps(credentials)
            
            # Request signin token
            params = {
                'Action': 'getSigninToken',
                'Session': session_json
            }
            
            response = requests.get(federation_url, params=params, timeout=10)
            response.raise_for_status()
            
            # Extract signin token
            result = response.json()
            signin_token = result.get('SigninToken')
            
            if signin_token:
                console.print(f"[green]✅ Got Federation signin token[/green]")
                if self.debug:
                    console.print(f"[dim]   Token: {signin_token[:50]}...[/dim]")
                
                # Store token
                self.signin_token = signin_token
                self.token_expiry = time.time() + 3600  # 1 hour
                
                return signin_token
            else:
                console.print("[red]❌ No SigninToken in response[/red]")
                return None
                
        except Exception as e:
            console.print(f"[red]❌ Failed to get signin token: {e}[/red]")
            return None
    
    def build_console_url(self, signin_token: str, destination: str, issuer: str = None) -> str:
        """
        Build a direct AWS Console URL using the signin token.
        
        This URL bypasses the SAML sign-in page entirely!
        
        Args:
            signin_token: Federation signin token
            destination: Target console URL (e.g., RDS page URL)
            issuer: Optional issuer for the request (default: localhost)
        
        Returns:
            Complete federation login URL
        """
        if not issuer:
            issuer = 'audit-ai-agent'
        
        # Build the federation login URL
        params = {
            'Action': 'login',
            'Issuer': issuer,
            'Destination': destination,
            'SigninToken': signin_token
        }
        
        federation_url = 'https://signin.aws.amazon.com/federation'
        login_url = f"{federation_url}?{urllib.parse.urlencode(params)}"
        
        if self.debug:
            console.print(f"[dim]   Destination: {destination}[/dim]")
            console.print(f"[dim]   Federation URL: {login_url[:100]}...[/dim]")
        
        return login_url
    
    def authenticate_and_get_console_url(
        self, 
        destination: str,
        account_name: str = None,
        wait_timeout: int = 300
    ) -> Optional[str]:
        """
        Complete authentication flow and return direct console URL.
        
        This is the main method that orchestrates the entire federation flow:
        1. Wait for Duo authentication to complete
        2. Extract SAML assertion
        3. Parse to get role/principal ARNs
        4. Get temporary credentials via STS
        5. Get federation signin token
        6. Build direct console URL
        
        Args:
            destination: Target AWS console page URL
            account_name: AWS account name (for logging)
            wait_timeout: Max time to wait for Duo auth (seconds)
        
        Returns:
            Direct console URL, or None if authentication fails
        """
        try:
            console.print(f"[bold cyan]🚀 AWS Federation Authentication[/bold cyan]")
            
            # Step 1: Extract SAML assertion (appears after Duo completes)
            saml_assertion = self.extract_saml_assertion(timeout=wait_timeout)
            if not saml_assertion:
                return None
            
            # Step 2: Parse SAML to get role/principal ARNs
            parsed = self.parse_saml_assertion(saml_assertion)
            if not parsed:
                return None
            
            role_arn = parsed['role_arn']
            principal_arn = parsed['principal_arn']
            
            # Step 3: Get temporary AWS credentials
            credentials = self.assume_role_with_saml(saml_assertion, role_arn, principal_arn)
            if not credentials:
                return None
            
            # Step 4: Get federation signin token
            signin_token = self.get_signin_token(credentials)
            if not signin_token:
                return None
            
            # Step 5: Build direct console URL
            console_url = self.build_console_url(signin_token, destination)
            
            console.print(f"[green]✅ Federation authentication complete![/green]")
            console.print(f"[cyan]🌐 Direct console URL ready (bypasses SAML page!)[/cyan]")
            
            return console_url
            
        except Exception as e:
            console.print(f"[red]❌ Federation authentication failed: {e}[/red]")
            return None
    
    def is_token_valid(self) -> bool:
        """Check if the current signin token is still valid."""
        if not self.signin_token or not self.token_expiry:
            return False
        return time.time() < self.token_expiry
    
    def get_cached_console_url(self, destination: str) -> Optional[str]:
        """
        Get console URL using cached signin token (if still valid).
        
        This avoids re-authentication if token is still valid.
        
        Args:
            destination: Target console page URL
        
        Returns:
            Console URL if token is valid, None otherwise
        """
        if self.is_token_valid():
            console.print("[green]♻️  Using cached signin token (still valid)[/green]")
            return self.build_console_url(self.signin_token, destination)
        else:
            console.print("[yellow]⚠️  Signin token expired, need re-authentication[/yellow]")
            return None

