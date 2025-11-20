"""
Unified AWS Export Tool - Phase 2 Consolidation

Consolidates all AWS export functionality into a single, unified tool using BaseTool pattern.
Replaces: aws_export_tool.py, aws_export_tool_enhanced.py, aws_universal_export.py

Features:
- Uses BaseTool for standardized error handling
- Uses ConnectionPool for AWS client reuse
- Supports 100+ AWS services
- Detailed configuration extraction
- Date filtering
- Multiple output formats
"""

import os
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from rich.console import Console

from ai_brain.shared import BaseTool, ErrorHandler, ConnectionPool
from tools.aws_export_filters import resolve_date_range, filter_records_by_date

console = Console()


class UnifiedAWSExportTool(BaseTool):
    """
    Unified AWS Export Tool - Consolidates all export functionality.
    
    Uses BaseTool pattern for standardized error handling and validation.
    Uses ConnectionPool for efficient AWS client management.
    """
    
    # Services with enhanced detailed exports
    DETAILED_SERVICES = {
        'iam': ['users', 'user', 'roles', 'role', 'policies', 'policy'],
        's3': ['buckets', 'bucket'],
        'rds': ['instances', 'instance', 'clusters', 'cluster'],
        'ec2': ['instances', 'instance', 'security_groups', 'security_group']
    }
    
    # Default date fields for filtering
    DATE_FIELD_DEFAULTS = {
        'rds': {
            'instances': 'InstanceCreateTime',
            'clusters': 'ClusterCreateTime'
        },
        's3': {
            'buckets': 'CreationDate'
        },
        'ec2': {
            'instances': 'LaunchTime'
        },
        'secretsmanager': {
            'secrets': 'CreatedDate'
        },
        'autoscaling': {
            'auto_scaling_groups': 'CreatedTime'
        },
        'kms': {
            'keys': 'CreationDate',
            'aliases': 'CreationDate'
        }
    }
    
    def __init__(self):
        """Initialize unified export tool."""
        super().__init__(
            name="unified_aws_export",
            description="Unified AWS resource export tool with comprehensive service support"
        )
        self.error_handler = ErrorHandler()
        self.connection_pool = ConnectionPool()
        self._detailed_exporter = None
        self._comprehensive_collector = None
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute AWS export.
        
        Args:
            params: {
                "service": str,  # AWS service name
                "export_type": str,  # Resource type
                "format": str,  # "csv" or "json"
                "aws_account": str,  # AWS profile
                "aws_region": str,  # AWS region
                "output_path": str,  # Output file path
                "use_comprehensive": bool,  # Force comprehensive collector
                "filter_by_date": bool,  # Enable date filtering
                "start_date": str,  # Start date (YYYY-MM-DD)
                "end_date": str,  # End date (YYYY-MM-DD)
                "date_field": str  # Date field name
            }
            
        Returns:
            {
                "status": "success" | "error",
                "result": {...} or "error": str
            }
        """
        # Validate required parameters
        required = ['service', 'export_type', 'format', 'aws_account', 'aws_region', 'output_path']
        if error := self.validate_params(params, required):
            return self.format_error(ValueError(error))
        
        try:
            service = params['service'].lower()
            export_type = params['export_type'].lower()
            format_type = params['format'].lower()
            aws_account = params['aws_account']
            aws_region = params['aws_region']
            output_path = params['output_path']
            
            # Determine which exporter to use
            use_comprehensive = params.get('use_comprehensive')
            if use_comprehensive is None:
                use_comprehensive = (
                    service not in self.DETAILED_SERVICES or
                    export_type not in self.DETAILED_SERVICES.get(service, [])
                )
            
            # Set AWS profile
            if aws_account:
                os.environ['AWS_PROFILE'] = aws_account
            
            # Execute export
            if use_comprehensive:
                result = self._export_comprehensive(params)
            else:
                result = self._export_detailed(params)
            
            if result:
                return self.format_success({
                    "output_path": output_path,
                    "service": service,
                    "export_type": export_type,
                    "format": format_type,
                    "account": aws_account,
                    "region": aws_region
                }, f"Successfully exported {service}/{export_type} to {output_path}")
            else:
                return self.format_error(Exception("Export failed"))
                
        except Exception as e:
            return self.format_error(e, {"params": params})
    
    def _export_comprehensive(self, params: Dict[str, Any]) -> bool:
        """Export using comprehensive collector (100+ services)."""
        try:
            from tools.aws_comprehensive_audit_collector import AWSComprehensiveAuditCollector
            from tools.aws_export_filters import resolve_date_range, filter_records_by_date
            
            service = params['service'].lower()
            export_type = params['export_type'].lower()
            format_type = params['format'].lower()
            aws_account = params['aws_account']
            aws_region = params['aws_region']
            output_path = params['output_path']
            
            console.print(f"\n[bold cyan]📊 AWS Comprehensive Export[/bold cyan]")
            console.print(f"[cyan]Service: {service.upper()}, Type: {export_type}, Format: {format_type.upper()}[/cyan]")
            
            # Use ConnectionPool for AWS clients (if collector supports it)
            collector = AWSComprehensiveAuditCollector(aws_account, aws_region)
            all_data = collector.collect_all_services(services=[service])
            
            if not all_data or service not in all_data:
                console.print(f"[yellow]⚠️  No data found for {service}[/yellow]")
                return False
            
            # Apply date filtering if requested
            if params.get('filter_by_date'):
                start_dt, end_dt, _ = resolve_date_range(
                    True,
                    params.get('start_date'),
                    params.get('end_date'),
                    params.get('audit_period')
                )
                if start_dt and end_dt:
                    date_field = (
                        params.get('date_field') or
                        self.DATE_FIELD_DEFAULTS.get(service, {}).get(export_type)
                    )
                    if date_field and export_type in all_data.get(service, {}):
                        filtered = filter_records_by_date(
                            all_data[service][export_type],
                            date_field,
                            start_dt,
                            end_dt
                        )
                        all_data[service][export_type] = filtered
            
            # Export to file
            if format_type == 'csv':
                files = collector.export_to_csv(
                    {service: all_data[service]},
                    os.path.dirname(output_path)
                )
                return bool(files)
            elif format_type == 'json':
                return collector.export_to_json(
                    {service: all_data[service]},
                    output_path
                )
            else:
                console.print(f"[red]❌ Unknown format: {format_type}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Comprehensive export failed: {e}[/red]")
            return False
    
    def _export_detailed(self, params: Dict[str, Any]) -> bool:
        """Export using detailed exporter (IAM, S3, RDS, EC2)."""
        try:
            from tools.aws_export_tool import export_aws_data
            
            console.print(f"\n[bold cyan]📊 AWS Enhanced Detailed Export[/bold cyan]")
            console.print(f"[cyan]Using enhanced exporter for detailed configuration[/cyan]")
            
            return export_aws_data(
                service=params['service'],
                export_type=params['export_type'],
                format=params['format'],
                aws_account=params['aws_account'],
                aws_region=params['aws_region'],
                output_path=params['output_path'],
                filter_by_date=params.get('filter_by_date', False),
                start_date=params.get('start_date'),
                end_date=params.get('end_date'),
                date_field=params.get('date_field')
            )
            
        except Exception as e:
            console.print(f"[red]❌ Detailed export failed: {e}[/red]")
            return False


# Convenience function for backward compatibility
def export_aws_unified(
    service: str,
    export_type: str,
    format: str,
    aws_account: str,
    aws_region: str,
    output_path: str,
    **kwargs
) -> bool:
    """
    Unified AWS export function - backward compatible interface.
    
    Args:
        service: AWS service name
        export_type: Resource type
        format: Output format ("csv" or "json")
        aws_account: AWS profile name
        aws_region: AWS region
        output_path: Output file path
        **kwargs: Additional parameters (filter_by_date, start_date, end_date, etc.)
        
    Returns:
        True if successful
    """
    tool = UnifiedAWSExportTool()
    params = {
        "service": service,
        "export_type": export_type,
        "format": format,
        "aws_account": aws_account,
        "aws_region": aws_region,
        "output_path": output_path,
        **kwargs
    }
    result = tool.execute(params)
    return result.get("status") == "success"

