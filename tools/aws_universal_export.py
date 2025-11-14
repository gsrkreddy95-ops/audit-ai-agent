"""
AWS Universal Export Tool - Production Ready
Combines comprehensive 100+ service coverage with detailed configuration extraction
"""

import os
from typing import Dict, List, Optional
from rich.console import Console

# Import both tools
from tools.aws_export_tool import (
    AWSExportToolEnhanced,
    export_aws_data as export_detailed
)
from tools.aws_comprehensive_audit_collector import (
    AWSComprehensiveAuditCollector,
    collect_comprehensive_audit_evidence
)

console = Console()


def export_aws_universal(
    service: str,
    export_type: str,
    format: str,
    aws_account: str,
    aws_region: str,
    output_path: str,
    use_comprehensive: bool = None
) -> bool:
    """
    Universal AWS export function - automatically chooses best tool
    
    Strategy:
    - For IAM, S3, RDS, EC2: Use enhanced detailed exporter (more fields)
    - For other services: Use comprehensive collector (100+ services)
    - If use_comprehensive=True: Force comprehensive collector
    
    Args:
        service: AWS service (iam, s3, rds, ec2, lambda, dynamodb, etc.)
        export_type: Resource type (users, buckets, functions, tables, etc.)
        format: Output format (csv, json)
        aws_account: AWS profile name
        aws_region: AWS region
        output_path: Where to save file
        use_comprehensive: Force comprehensive collector (default: auto-detect)
    
    Returns:
        True if successful
    """
    
    # Services with enhanced detailed exports
    DETAILED_SERVICES = {
        'iam': ['users', 'user', 'roles', 'role'],
        's3': ['buckets', 'bucket'],
        'rds': ['instances', 'instance', 'clusters', 'cluster'],
        'ec2': ['instances', 'instance']
    }
    
    # Auto-detect which tool to use
    if use_comprehensive is None:
        use_comprehensive = service not in DETAILED_SERVICES or export_type not in DETAILED_SERVICES.get(service, [])
    
    if use_comprehensive:
        # Use comprehensive collector for 100+ services
        console.print(f"\n[bold cyan]📊 AWS Comprehensive Export[/bold cyan]")
        console.print(f"[cyan]Using comprehensive collector (100+ services supported)[/cyan]")
        console.print(f"[cyan]Service: {service.upper()}[/cyan]")
        console.print(f"[cyan]Export Type: {export_type}[/cyan]")
        console.print(f"[cyan]Account: {aws_account}[/cyan]")
        console.print(f"[cyan]Region: {aws_region}[/cyan]")
        console.print(f"[cyan]Format: {format.upper()}[/cyan]\n")
        
        # Set AWS profile
        if aws_account:
            os.environ['AWS_PROFILE'] = aws_account
        
        collector = AWSComprehensiveAuditCollector(aws_account, aws_region)
        
        # Collect specific service
        all_data = collector.collect_all_services(services=[service])
        
        if not all_data or service not in all_data:
            console.print(f"[yellow]⚠️  No data found for {service}[/yellow]")
            return False
        
        # Export single service data
        if format == 'csv':
            files = collector.export_to_csv({service: all_data[service]}, os.path.dirname(output_path))
            if files:
                console.print(f"[green]✅ Exported {len(files)} file(s)[/green]")
                return True
            return False
        elif format == 'json':
            success = collector.export_to_json({service: all_data[service]}, output_path)
            return success
        else:
            console.print(f"[red]❌ Unknown format: {format}[/red]")
            return False
    
    else:
        # Use enhanced detailed exporter for core services
        console.print(f"\n[bold cyan]📊 AWS Enhanced Detailed Export[/bold cyan]")
        console.print(f"[cyan]Using enhanced exporter (complete configuration details)[/cyan]")
        return export_detailed(
            service=service,
            export_type=export_type,
            format=format,
            aws_account=aws_account,
            aws_region=aws_region,
            output_path=output_path
        )


# Wrapper function for backward compatibility
def export_aws_data(
    service: str,
    export_type: str,
    format: str,
    aws_account: str,
    aws_region: str,
    output_path: str
) -> bool:
    """
    Backward compatible export function
    Automatically chooses best tool based on service
    """
    return export_aws_universal(
        service=service,
        export_type=export_type,
        format=format,
        aws_account=aws_account,
        aws_region=aws_region,
        output_path=output_path,
        use_comprehensive=None  # Auto-detect
    )


def export_all_aws_services(
    aws_account: str,
    aws_region: str,
    output_dir: str,
    format: str = 'csv',
    services: Optional[List[str]] = None
) -> tuple:
    """
    Export ALL AWS services (100+ services) with comprehensive collector
    
    Args:
        aws_account: AWS profile name
        aws_region: AWS region
        output_dir: Output directory
        format: Output format (csv or json)
        services: Specific services to collect (None = all)
    
    Returns:
        (success, summary_message)
    """
    return collect_comprehensive_audit_evidence(
        aws_account=aws_account,
        aws_region=aws_region,
        output_dir=output_dir,
        services=services,
        format=format
    )

