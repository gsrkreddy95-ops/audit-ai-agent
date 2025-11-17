"""
Evidence Validation & Self-Review System
=========================================

CRITICAL FOR AUDIT QUALITY:
The agent should VERIFY its own outputs before claiming success!

Problems this solves:
1. Agent claims "screenshot captured" but image is wrong page
2. Agent says "navigated to API Gateway" but actually on console home
3. Agent reports success but evidence is incomplete/incorrect

Solution:
- Validate screenshots (image analysis)
- Verify URLs (correct service page)
- Check content (expected elements present)
- Self-diagnose issues
- Suggest fixes automatically
"""

import os
import time
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from PIL import Image
import base64
from io import BytesIO

console = Console()


class EvidenceValidator:
    """
    Validates evidence quality and accuracy.
    
    Features:
    1. Screenshot validation (image analysis)
    2. URL verification (correct page?)
    3. Content verification (expected elements present?)
    4. Self-diagnosis (what went wrong?)
    5. Fix suggestions (how to correct it?)
    """
    
    # Expected URL patterns for AWS services
    SERVICE_URL_PATTERNS = {
        'kms': ['kms/home', 'console.aws.amazon.com/kms'],
        'secretsmanager': ['secretsmanager/home', 'secretsmanager/listsecrets'],
        'secrets-manager': ['secretsmanager/home', 'secretsmanager/listsecrets'],
        's3': ['s3.console.aws.amazon.com', 's3/buckets'],
        'rds': ['rds/home', 'console.aws.amazon.com/rds'],
        'ec2': ['ec2/home', 'console.aws.amazon.com/ec2'],
        'lambda': ['lambda/home', 'console.aws.amazon.com/lambda'],
        'apigateway': ['apigateway/main', 'apigateway/home'],
        'api-gateway': ['apigateway/main', 'apigateway/home'],
        'iam': ['console.aws.amazon.com/iam'],
        'cloudwatch': ['cloudwatch/home'],
        'dynamodb': ['dynamodbv2/home'],
        'vpc': ['vpc/home'],
        'cloudfront': ['cloudfront/home'],
    }
    
    # Expected page titles for AWS services
    SERVICE_PAGE_TITLES = {
        'kms': ['Key Management Service', 'KMS', 'Customer managed keys'],
        'secretsmanager': ['Secrets Manager', 'Secrets'],
        's3': ['S3', 'Buckets', 'Amazon S3'],
        'rds': ['RDS', 'Databases', 'DB Instances'],
        'ec2': ['EC2', 'Instances', 'Amazon EC2'],
        'lambda': ['Lambda', 'Functions'],
        'apigateway': ['API Gateway', 'APIs'],
        'iam': ['IAM', 'Users', 'Identity'],
    }
    
    # Common false positive pages (NOT the actual service)
    FALSE_POSITIVE_PATTERNS = [
        '/console/home',           # AWS Console homepage
        'recently-visited',        # Recently visited section
        'favorite-services',       # Favorite services
        'myApplications',          # My applications
        'getting-started',         # Getting started page
        'resource-groups',         # Resource groups
        'console/oauth',          # OAuth/session selector
    ]
    
    def __init__(self, driver=None):
        """
        Initialize evidence validator.
        
        Args:
            driver: Selenium WebDriver instance (optional, for live validation)
        """
        self.driver = driver
        self.debug = True
    
    def validate_screenshot_evidence(
        self,
        screenshot_path: str,
        expected_service: str,
        expected_content: Optional[List[str]] = None,
        current_url: Optional[str] = None
    ) -> Dict:
        """
        🔍 VALIDATE SCREENSHOT EVIDENCE
        
        Performs comprehensive validation:
        1. File exists and is readable
        2. Image is not blank/corrupted
        3. URL matches expected service
        4. Page content matches expected service
        5. Not a false positive (console home, etc.)
        
        Args:
            screenshot_path: Path to screenshot file
            expected_service: Expected AWS service (e.g., "kms", "apigateway")
            expected_content: List of expected text/elements (optional)
            current_url: Browser URL at time of screenshot (optional)
        
        Returns:
            Dict with validation results:
            {
                "valid": True/False,
                "confidence": 0.0-1.0,
                "issues": [...],
                "diagnosis": "...",
                "suggested_fix": "...",
                "checks": {
                    "file_exists": True/False,
                    "image_valid": True/False,
                    "url_correct": True/False,
                    "content_present": True/False,
                    "not_false_positive": True/False
                }
            }
        """
        console.print("\n[bold cyan]" + "="*60 + "[/bold cyan]")
        console.print("[bold cyan]🔍 VALIDATING EVIDENCE[/bold cyan]")
        console.print("[bold cyan]" + "="*60 + "[/bold cyan]\n")
        
        console.print(f"[cyan]📸 Screenshot: {os.path.basename(screenshot_path)}[/cyan]")
        console.print(f"[cyan]🎯 Expected Service: {expected_service.upper()}[/cyan]\n")
        
        validation_result = {
            "valid": False,
            "confidence": 0.0,
            "issues": [],
            "diagnosis": "",
            "suggested_fix": "",
            "checks": {
                "file_exists": False,
                "image_valid": False,
                "url_correct": False,
                "content_present": False,
                "not_false_positive": False
            }
        }
        
        # Check 1: File exists
        if not os.path.exists(screenshot_path):
            validation_result["issues"].append("Screenshot file not found")
            validation_result["diagnosis"] = "Screenshot file does not exist at specified path"
            validation_result["suggested_fix"] = "Check if screenshot was actually saved. Verify file permissions and disk space."
            console.print("[red]❌ File not found[/red]")
            return validation_result
        
        validation_result["checks"]["file_exists"] = True
        console.print("[green]✅ File exists[/green]")
        
        # Check 2: Image is valid
        try:
            img = Image.open(screenshot_path)
            width, height = img.size
            
            if width < 100 or height < 100:
                validation_result["issues"].append(f"Image too small ({width}x{height})")
                validation_result["diagnosis"] = "Screenshot appears to be blank or corrupt"
                validation_result["suggested_fix"] = "Re-capture screenshot with longer wait time for page load"
                console.print(f"[red]❌ Image too small: {width}x{height}[/red]")
                return validation_result
            
            validation_result["checks"]["image_valid"] = True
            console.print(f"[green]✅ Image valid: {width}x{height} pixels[/green]")
            
        except Exception as e:
            validation_result["issues"].append(f"Image corrupt: {e}")
            validation_result["diagnosis"] = "Screenshot file is corrupted or invalid"
            validation_result["suggested_fix"] = "Re-capture screenshot"
            console.print(f"[red]❌ Image corrupt: {e}[/red]")
            return validation_result
        
        # Check 3: URL validation (if provided or can be retrieved)
        if current_url or self.driver:
            url_to_check = current_url or (self.driver.current_url if self.driver else None)
            
            if url_to_check:
                url_valid = self._validate_url(url_to_check, expected_service)
                validation_result["checks"]["url_correct"] = url_valid["correct"]
                
                if url_valid["correct"]:
                    console.print(f"[green]✅ URL matches service: {expected_service}[/green]")
                else:
                    validation_result["issues"].append(f"URL mismatch: {url_valid['reason']}")
                    console.print(f"[red]❌ URL incorrect: {url_valid['reason']}[/red]")
                
                # Check for false positives
                if url_valid["is_false_positive"]:
                    validation_result["checks"]["not_false_positive"] = False
                    validation_result["issues"].append(f"False positive: {url_valid['false_positive_type']}")
                    validation_result["diagnosis"] = f"Screenshot is of {url_valid['false_positive_type']}, not {expected_service}"
                    validation_result["suggested_fix"] = "Use universal navigator with strict URL validation. Ensure navigation completes before screenshot."
                    console.print(f"[red]❌ FALSE POSITIVE: {url_valid['false_positive_type']}[/red]")
                else:
                    validation_result["checks"]["not_false_positive"] = True
                    console.print(f"[green]✅ Not a false positive[/green]")
        
        # Check 4: Content verification (if driver available)
        if self.driver and expected_content:
            content_valid = self._validate_content(expected_content, expected_service)
            validation_result["checks"]["content_present"] = content_valid["present"]
            
            if content_valid["present"]:
                console.print(f"[green]✅ Expected content present[/green]")
            else:
                validation_result["issues"].append(f"Content missing: {content_valid['missing']}")
                console.print(f"[yellow]⚠️  Some content missing[/yellow]")
        
        # Calculate confidence score
        checks_passed = sum(1 for v in validation_result["checks"].values() if v)
        total_checks = len(validation_result["checks"])
        validation_result["confidence"] = checks_passed / total_checks
        
        # Overall validation
        critical_checks = [
            validation_result["checks"]["file_exists"],
            validation_result["checks"]["image_valid"],
            validation_result["checks"]["not_false_positive"]
        ]
        
        validation_result["valid"] = all(critical_checks) and validation_result["confidence"] >= 0.6
        
        # Summary
        console.print(f"\n[bold cyan]📊 VALIDATION SUMMARY:[/bold cyan]")
        console.print(f"[cyan]   Confidence: {validation_result['confidence']*100:.0f}%[/cyan]")
        console.print(f"[cyan]   Checks Passed: {checks_passed}/{total_checks}[/cyan]")
        
        if validation_result["valid"]:
            console.print(f"\n[bold green]✅ EVIDENCE VALID[/bold green]\n")
        else:
            console.print(f"\n[bold red]❌ EVIDENCE INVALID[/bold red]")
            console.print(f"[red]   Issues: {len(validation_result['issues'])}[/red]")
            for issue in validation_result["issues"]:
                console.print(f"[red]   - {issue}[/red]")
            
            if validation_result["diagnosis"]:
                console.print(f"\n[yellow]🔍 Diagnosis:[/yellow]")
                console.print(f"[yellow]   {validation_result['diagnosis']}[/yellow]")
            
            if validation_result["suggested_fix"]:
                console.print(f"\n[cyan]💡 Suggested Fix:[/cyan]")
                console.print(f"[cyan]   {validation_result['suggested_fix']}[/cyan]\n")
        
        return validation_result
    
    def _validate_url(self, url: str, expected_service: str) -> Dict:
        """
        Validate URL matches expected service.
        
        Returns:
            Dict with validation results
        """
        url_lower = url.lower()
        service_lower = expected_service.lower()
        
        # Check for false positives first
        for pattern in self.FALSE_POSITIVE_PATTERNS:
            if pattern in url_lower:
                return {
                    "correct": False,
                    "reason": f"URL is a false positive: {pattern}",
                    "is_false_positive": True,
                    "false_positive_type": pattern
                }
        
        # Check for expected patterns
        patterns = self.SERVICE_URL_PATTERNS.get(service_lower, [service_lower])
        
        for pattern in patterns:
            if pattern.lower() in url_lower:
                return {
                    "correct": True,
                    "reason": f"URL contains expected pattern: {pattern}",
                    "is_false_positive": False,
                    "false_positive_type": None
                }
        
        return {
            "correct": False,
            "reason": f"URL does not match {expected_service} patterns",
            "is_false_positive": False,
            "false_positive_type": None
        }
    
    def _validate_content(self, expected_content: List[str], expected_service: str) -> Dict:
        """
        Validate page content matches expectations.
        
        Returns:
            Dict with validation results
        """
        if not self.driver:
            return {"present": True, "missing": []}
        
        try:
            page_text = self.driver.find_element("tag name", "body").text.lower()
            
            missing = []
            for content in expected_content:
                if content.lower() not in page_text:
                    missing.append(content)
            
            return {
                "present": len(missing) == 0,
                "missing": missing
            }
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Content validation failed: {e}[/yellow]")
            return {"present": False, "missing": expected_content}
    
    def suggest_retry_strategy(self, validation_result: Dict, service: str) -> Dict:
        """
        Suggest retry strategy based on validation failures.
        
        Returns:
            Dict with retry suggestions:
            {
                "should_retry": True/False,
                "strategy": "...",
                "parameters": {...}
            }
        """
        if validation_result["valid"]:
            return {"should_retry": False, "strategy": None, "parameters": {}}
        
        issues = validation_result["issues"]
        
        # False positive detected
        if any("false positive" in issue.lower() for issue in issues):
            return {
                "should_retry": True,
                "strategy": "Use strict URL validation and longer wait times",
                "parameters": {
                    "use_direct_url": True,
                    "wait_time": 5,
                    "verify_url_before_screenshot": True
                }
            }
        
        # URL mismatch
        if any("url" in issue.lower() for issue in issues):
            return {
                "should_retry": True,
                "strategy": "Re-navigate using universal navigator with search",
                "parameters": {
                    "use_search": True,
                    "verify_navigation": True
                }
            }
        
        # Content missing
        if any("content" in issue.lower() for issue in issues):
            return {
                "should_retry": True,
                "strategy": "Wait longer for page load",
                "parameters": {
                    "wait_time": 10,
                    "scroll_page": True
                }
            }
        
        return {
            "should_retry": True,
            "strategy": "General retry with increased timeouts",
            "parameters": {
                "wait_time": 5
            }
        }

