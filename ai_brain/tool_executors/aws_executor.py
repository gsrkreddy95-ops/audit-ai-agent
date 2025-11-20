"""
AWS Tool Executor - Handles all AWS-related tool execution

Extracted from tool_executor.py for better organization.
"""

from typing import Dict, Any
from rich.console import Console
from .base_executor import BaseToolExecutor
from ai_brain.shared import ErrorHandler, CacheManager, ConnectionPool

console = Console()


class AWSExecutor(BaseToolExecutor):
    """Executor for AWS-related tools."""
    
    def __init__(
        self,
        evidence_manager,
        error_handler: ErrorHandler = None,
        cache_manager: CacheManager = None,
        connection_pool: ConnectionPool = None
    ):
        """
        Initialize AWS executor.
        
        Args:
            evidence_manager: Evidence manager instance
            error_handler: Error handler
            cache_manager: Cache manager
            connection_pool: Connection pool for AWS clients
        """
        super().__init__(error_handler, cache_manager)
        self.evidence_manager = evidence_manager
        self.connection_pool = connection_pool
        
        # Lazy imports
        self._export_tool = None
        self._list_tool = None
    
    def _execute_impl(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute AWS tool."""
        if tool_name == "aws_export_data":
            return self._execute_aws_export(params)
        elif tool_name == "aws_take_screenshot":
            return self._execute_aws_screenshot(params)
        elif tool_name == "aws_console_action":
            return self._execute_aws_console_action(params)
        elif tool_name == "list_aws_resources":
            return self._execute_list_aws(params)
        elif tool_name == "bulk_aws_export":
            return self._execute_bulk_aws_export(params)
        else:
            raise ValueError(f"Unknown AWS tool: {tool_name}")
    
    def _execute_aws_export(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AWS export."""
        # Lazy load export tool
        if self._export_tool is None:
            from tools.aws_export_unified import UnifiedAWSExportTool
            self._export_tool = UnifiedAWSExportTool()
        
        result = self._export_tool.execute(params)
        return result
    
    def _execute_aws_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AWS screenshot (delegates to main tool_executor)."""
        # This will be handled by main tool_executor
        # Keeping as placeholder for future refactoring
        raise NotImplementedError("AWS screenshot execution")
    
    def _execute_aws_console_action(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AWS console action (delegates to main tool_executor)."""
        raise NotImplementedError("AWS console action execution")
    
    def _execute_list_aws(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AWS list operation."""
        # Lazy load list tool
        if self._list_tool is None:
            from tools.aws_list_tool import (
                list_s3_buckets, list_rds_instances, list_rds_clusters,
                list_iam_users, list_ec2_instances, list_lambda_functions
            )
            self._list_tool = {
                "s3": list_s3_buckets,
                "rds": list_rds_instances,
                "rds_clusters": list_rds_clusters,
                "iam": list_iam_users,
                "ec2": list_ec2_instances,
                "lambda": list_lambda_functions
            }
        
        service = params.get("service", "").lower()
        if service not in self._list_tool:
            raise ValueError(f"Unsupported service for listing: {service}")
        
        list_func = self._list_tool[service]
        result = list_func(
            aws_account=params.get("aws_account"),
            aws_region=params.get("aws_region", "us-east-1")
        )
        
        return {"resources": result}
    
    def _execute_bulk_aws_export(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bulk AWS export."""
        # Delegate to main executor for now
        raise NotImplementedError("Bulk AWS export execution")

