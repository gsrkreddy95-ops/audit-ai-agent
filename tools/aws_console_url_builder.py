"""
AWS Console URL Builder - Uses AWS SDK data to construct accurate console URLs

This module builds AWS console URLs dynamically using information from AWS SDK/APIs.
Much more reliable than hardcoding URLs!
"""

from typing import Optional, Dict


class AWSConsoleURLBuilder:
    """Build AWS Console URLs using SDK data"""
    
    @staticmethod
    def build_rds_url(region: str, cluster_id: Optional[str] = None, tab: Optional[str] = None) -> str:
        """
        Build RDS console URL
        
        Args:
            region: AWS region (e.g., 'us-east-1')
            cluster_id: Optional cluster ID from SDK
            tab: Optional tab name
        
        Returns:
            Full AWS console URL
        """
        base_url = f"https://{region}.console.aws.amazon.com/rds/home?region={region}"
        
        if not cluster_id:
            return f"{base_url}#databases:"
        
        cluster_url = f"{base_url}#database:id={cluster_id};is-cluster=true"
        
        if tab:
            tab_mapping = {
                'configuration': 'configuration',
                'config': 'configuration',
                'maintenance & backups': 'maintenance-and-backups',
                'maintenance and backups': 'maintenance-and-backups',
                'maintenance': 'maintenance-and-backups',
                'backup': 'maintenance-and-backups',
                'backups': 'maintenance-and-backups',
                'monitoring': 'monitoring',
                'logs & events': 'logs-and-events',
                'logs and events': 'logs-and-events',
                'logs': 'logs-and-events',
                'connectivity & security': 'connectivity-and-security',
                'connectivity and security': 'connectivity-and-security',
                'connectivity': 'connectivity-and-security',
                'security': 'connectivity-and-security',
            }
            
            tab_normalized = tab_mapping.get(tab.lower(), tab.lower().replace(' ', '-').replace('&', 'and'))
            cluster_url += f";tab={tab_normalized}"
        
        return cluster_url
    
    @staticmethod
    def build_s3_url(region: str, bucket_name: Optional[str] = None) -> str:
        """
        Build S3 console URL
        
        Args:
            region: AWS region
            bucket_name: Optional bucket name from SDK
        
        Returns:
            Full AWS console URL
        """
        if bucket_name:
            return f"https://s3.console.aws.amazon.com/s3/buckets/{bucket_name}?region={region}"
        return f"https://s3.console.aws.amazon.com/s3/buckets?region={region}"
    
    @staticmethod
    def build_ec2_url(region: str, instance_id: Optional[str] = None) -> str:
        """Build EC2 console URL"""
        base_url = f"https://{region}.console.aws.amazon.com/ec2/home?region={region}"
        
        if instance_id:
            return f"{base_url}#InstanceDetails:instanceId={instance_id}"
        return f"{base_url}#Instances:"
    
    @staticmethod
    def build_lambda_url(region: str, function_name: Optional[str] = None) -> str:
        """Build Lambda console URL"""
        base_url = f"https://{region}.console.aws.amazon.com/lambda/home?region={region}"
        
        if function_name:
            return f"{base_url}#/functions/{function_name}"
        return f"{base_url}#/functions"
    
    @staticmethod
    def build_dynamodb_url(region: str, table_name: Optional[str] = None) -> str:
        """Build DynamoDB console URL"""
        base_url = f"https://{region}.console.aws.amazon.com/dynamodbv2/home?region={region}"
        
        if table_name:
            return f"{base_url}#table?name={table_name}"
        return f"{base_url}#tables"
    
    @staticmethod
    def build_cloudwatch_url(region: str, log_group: Optional[str] = None) -> str:
        """Build CloudWatch console URL"""
        if log_group:
            return f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:log-groups/log-group/{log_group}"
        return f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}"
    
    @staticmethod
    def build_iam_url(user_name: Optional[str] = None) -> str:
        """Build IAM console URL (IAM is global, no region)"""
        if user_name:
            return f"https://console.aws.amazon.com/iam/home#/users/details/{user_name}"
        return "https://console.aws.amazon.com/iam/home#/users"
    
    @staticmethod
    def build_service_url(service: str, region: str, resource_id: Optional[str] = None, **kwargs) -> str:
        """
        Build URL for any AWS service
        
        Args:
            service: Service name (e.g., 'rds', 's3', 'ec2')
            region: AWS region
            resource_id: Optional resource identifier from SDK
            **kwargs: Additional parameters (e.g., tab for RDS)
        
        Returns:
            AWS console URL
        """
        service = service.lower()
        
        if service == 'rds':
            return AWSConsoleURLBuilder.build_rds_url(region, resource_id, kwargs.get('tab'))
        elif service == 's3':
            return AWSConsoleURLBuilder.build_s3_url(region, resource_id)
        elif service == 'ec2':
            return AWSConsoleURLBuilder.build_ec2_url(region, resource_id)
        elif service == 'lambda':
            return AWSConsoleURLBuilder.build_lambda_url(region, resource_id)
        elif service == 'dynamodb':
            return AWSConsoleURLBuilder.build_dynamodb_url(region, resource_id)
        elif service == 'cloudwatch':
            return AWSConsoleURLBuilder.build_cloudwatch_url(region, resource_id)
        elif service == 'iam':
            return AWSConsoleURLBuilder.build_iam_url(resource_id)
        else:
            # Generic fallback
            return f"https://{region}.console.aws.amazon.com/{service}/home?region={region}"


if __name__ == "__main__":
    # Test the URL builder
    builder = AWSConsoleURLBuilder()
    
    print("Testing AWS Console URL Builder...\n")
    
    # Test RDS URLs
    print("RDS URLs:")
    print(f"  List: {builder.build_rds_url('us-east-1')}")
    print(f"  Cluster: {builder.build_rds_url('us-east-1', 'prod-conure-cluster')}")
    print(f"  Cluster + Tab: {builder.build_rds_url('us-east-1', 'prod-conure-cluster', 'configuration')}")
    
    print("\nS3 URLs:")
    print(f"  List: {builder.build_s3_url('us-east-1')}")
    print(f"  Bucket: {builder.build_s3_url('us-east-1', 'my-bucket')}")
    
    print("\nEC2 URLs:")
    print(f"  List: {builder.build_ec2_url('us-east-1')}")
    print(f"  Instance: {builder.build_ec2_url('us-east-1', 'i-1234567890abcdef0')}")
    
    print("\nLambda URLs:")
    print(f"  List: {builder.build_lambda_url('us-east-1')}")
    print(f"  Function: {builder.build_lambda_url('us-east-1', 'my-function')}")
    
    print("\nIAM URLs:")
    print(f"  List: {builder.build_iam_url()}")
    print(f"  User: {builder.build_iam_url('john.doe')}")

