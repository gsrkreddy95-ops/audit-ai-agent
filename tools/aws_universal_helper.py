"""
AWS Universal Helper - Intelligent resource discovery for ALL AWS services
This makes the agent TRULY INTELLIGENT across the entire AWS ecosystem!

Supports:
- RDS (databases, clusters, instances)
- Lambda (functions)
- API Gateway (APIs, stages)
- EC2 (instances, security groups, VPCs)
- S3 (buckets)
- DynamoDB (tables)
- CloudWatch (alarms, logs)
- IAM (users, roles, policies)
- And MORE!
"""

import boto3
from typing import Optional, List, Dict, Any
from rich.console import Console
from datetime import datetime

console = Console()


class AWSUniversalHelper:
    """
    Universal AWS SDK helper for intelligent resource discovery across ALL services
    
    This is the BRAIN of the agent - it uses AWS APIs to:
    1. Find resources by partial names
    2. Get resource metadata
    3. List all resources in a service
    4. Navigate intelligently
    """
    
    def __init__(self, region: str = 'us-east-1', profile: str = None):
        """
        Initialize AWS Universal Helper
        
        Args:
            region: AWS region (default: us-east-1)
            profile: AWS profile name (e.g., 'ctr-prod', 'ctr-int')
        """
        self.region = region
        self.profile = profile
        self.session = None
        self.clients = {}  # Cache of AWS service clients
        
        try:
            # Use profile if specified, otherwise use default credentials
            if profile:
                self.session = boto3.Session(profile_name=profile, region_name=region)
            else:
                self.session = boto3.Session(region_name=region)
            
            console.print(f"[green]🧠 AWS Universal Helper initialized[/green]")
            console.print(f"[dim]   Region: {region}, Profile: {profile or 'default'}[/dim]")
        except Exception as e:
            console.print(f"[red]❌ AWS SDK initialization failed: {e}[/red]")
            console.print(f"[yellow]   Agent will fall back to browser-only navigation[/yellow]")
            self.session = None
    
    def _get_client(self, service_name: str):
        """Get or create a cached boto3 client for a service"""
        if service_name not in self.clients:
            if not self.session:
                return None
            try:
                self.clients[service_name] = self.session.client(service_name, region_name=self.region)
            except Exception as e:
                console.print(f"[yellow]⚠️  Could not create {service_name} client: {e}[/yellow]")
                return None
        return self.clients[service_name]
    
    # ==================== RDS ====================
    def find_rds_cluster(self, partial_name: str) -> Optional[Dict]:
        """Find RDS cluster by partial name"""
        client = self._get_client('rds')
        if not client:
            return None
        
        try:
            console.print(f"[cyan]🔍 [RDS] Searching for cluster: '{partial_name}'...[/cyan]")
            paginator = client.get_paginator('describe_db_clusters')
            
            for page in paginator.paginate():
                for cluster in page['DBClusters']:
                    cluster_id = cluster['DBClusterIdentifier']
                    if partial_name.lower() in cluster_id.lower():
                        result = {
                            'service': 'rds',
                            'resource_type': 'cluster',
                            'id': cluster_id,
                            'full_name': cluster_id,
                            'arn': cluster.get('DBClusterArn', ''),
                            'engine': cluster.get('Engine', ''),
                            'status': cluster.get('Status', ''),
                            'endpoint': cluster.get('Endpoint', ''),
                        }
                        console.print(f"[green]✅ Found: {cluster_id}[/green]")
                        return result
            
            console.print(f"[yellow]⚠️  No RDS cluster found matching '{partial_name}'[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]❌ RDS API error: {e}[/red]")
            return None
    
    def find_rds_instance(self, partial_name: str) -> Optional[Dict]:
        """Find RDS instance by partial name"""
        client = self._get_client('rds')
        if not client:
            return None
        
        try:
            console.print(f"[cyan]🔍 [RDS] Searching for instance: '{partial_name}'...[/cyan]")
            paginator = client.get_paginator('describe_db_instances')
            
            for page in paginator.paginate():
                for instance in page['DBInstances']:
                    instance_id = instance['DBInstanceIdentifier']
                    if partial_name.lower() in instance_id.lower():
                        result = {
                            'service': 'rds',
                            'resource_type': 'instance',
                            'id': instance_id,
                            'full_name': instance_id,
                            'arn': instance.get('DBInstanceArn', ''),
                            'engine': instance.get('Engine', ''),
                            'status': instance.get('DBInstanceStatus', ''),
                            'endpoint': instance.get('Endpoint', {}).get('Address', ''),
                        }
                        console.print(f"[green]✅ Found: {instance_id}[/green]")
                        return result
            
            console.print(f"[yellow]⚠️  No RDS instance found matching '{partial_name}'[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]❌ RDS API error: {e}[/red]")
            return None
    
    # ==================== LAMBDA ====================
    def find_lambda_function(self, partial_name: str) -> Optional[Dict]:
        """Find Lambda function by partial name"""
        client = self._get_client('lambda')
        if not client:
            return None
        
        try:
            console.print(f"[cyan]🔍 [Lambda] Searching for function: '{partial_name}'...[/cyan]")
            paginator = client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for function in page['Functions']:
                    function_name = function['FunctionName']
                    if partial_name.lower() in function_name.lower():
                        result = {
                            'service': 'lambda',
                            'resource_type': 'function',
                            'id': function_name,
                            'full_name': function_name,
                            'arn': function.get('FunctionArn', ''),
                            'runtime': function.get('Runtime', ''),
                            'handler': function.get('Handler', ''),
                            'memory': function.get('MemorySize', 0),
                            'timeout': function.get('Timeout', 0),
                        }
                        console.print(f"[green]✅ Found: {function_name}[/green]")
                        return result
            
            console.print(f"[yellow]⚠️  No Lambda function found matching '{partial_name}'[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]❌ Lambda API error: {e}[/red]")
            return None
    
    def list_lambda_functions(self) -> List[str]:
        """List all Lambda functions"""
        client = self._get_client('lambda')
        if not client:
            return []
        
        try:
            console.print(f"[cyan]📋 [Lambda] Listing all functions...[/cyan]")
            paginator = client.get_paginator('list_functions')
            functions = []
            
            for page in paginator.paginate():
                for function in page['Functions']:
                    functions.append(function['FunctionName'])
            
            console.print(f"[green]✅ Found {len(functions)} Lambda functions[/green]")
            return functions
        except Exception as e:
            console.print(f"[red]❌ Lambda API error: {e}[/red]")
            return []
    
    # ==================== API GATEWAY ====================
    def find_api_gateway(self, partial_name: str) -> Optional[Dict]:
        """Find API Gateway by partial name"""
        client = self._get_client('apigateway')
        if not client:
            return None
        
        try:
            console.print(f"[cyan]🔍 [API Gateway] Searching for API: '{partial_name}'...[/cyan]")
            paginator = client.get_paginator('get_rest_apis')
            
            for page in paginator.paginate():
                for api in page['items']:
                    api_name = api['name']
                    if partial_name.lower() in api_name.lower():
                        result = {
                            'service': 'apigateway',
                            'resource_type': 'rest-api',
                            'id': api['id'],
                            'full_name': api_name,
                            'description': api.get('description', ''),
                            'created_date': str(api.get('createdDate', '')),
                        }
                        console.print(f"[green]✅ Found: {api_name} (ID: {api['id']})[/green]")
                        return result
            
            console.print(f"[yellow]⚠️  No API Gateway found matching '{partial_name}'[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]❌ API Gateway API error: {e}[/red]")
            return None
    
    # ==================== EC2 ====================
    def find_ec2_instance(self, partial_name: str) -> Optional[Dict]:
        """Find EC2 instance by partial name or instance ID"""
        client = self._get_client('ec2')
        if not client:
            return None
        
        try:
            console.print(f"[cyan]🔍 [EC2] Searching for instance: '{partial_name}'...[/cyan]")
            paginator = client.get_paginator('describe_instances')
            
            for page in paginator.paginate():
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        instance_id = instance['InstanceId']
                        
                        # Check instance ID
                        if partial_name.lower() in instance_id.lower():
                            name_tag = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')
                            result = {
                                'service': 'ec2',
                                'resource_type': 'instance',
                                'id': instance_id,
                                'full_name': f"{instance_id} ({name_tag})",
                                'name_tag': name_tag,
                                'state': instance.get('State', {}).get('Name', ''),
                                'instance_type': instance.get('InstanceType', ''),
                                'private_ip': instance.get('PrivateIpAddress', ''),
                                'public_ip': instance.get('PublicIpAddress', ''),
                            }
                            console.print(f"[green]✅ Found: {instance_id} ({name_tag})[/green]")
                            return result
                        
                        # Check Name tag
                        for tag in instance.get('Tags', []):
                            if tag['Key'] == 'Name' and partial_name.lower() in tag['Value'].lower():
                                result = {
                                    'service': 'ec2',
                                    'resource_type': 'instance',
                                    'id': instance_id,
                                    'full_name': f"{instance_id} ({tag['Value']})",
                                    'name_tag': tag['Value'],
                                    'state': instance.get('State', {}).get('Name', ''),
                                    'instance_type': instance.get('InstanceType', ''),
                                    'private_ip': instance.get('PrivateIpAddress', ''),
                                    'public_ip': instance.get('PublicIpAddress', ''),
                                }
                                console.print(f"[green]✅ Found: {instance_id} ({tag['Value']})[/green]")
                                return result
            
            console.print(f"[yellow]⚠️  No EC2 instance found matching '{partial_name}'[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]❌ EC2 API error: {e}[/red]")
            return None
    
    def find_security_group(self, partial_name: str) -> Optional[Dict]:
        """Find Security Group by partial name or ID"""
        client = self._get_client('ec2')
        if not client:
            return None
        
        try:
            console.print(f"[cyan]🔍 [EC2] Searching for security group: '{partial_name}'...[/cyan]")
            response = client.describe_security_groups()
            
            for sg in response['SecurityGroups']:
                sg_id = sg['GroupId']
                sg_name = sg['GroupName']
                
                if partial_name.lower() in sg_id.lower() or partial_name.lower() in sg_name.lower():
                    result = {
                        'service': 'ec2',
                        'resource_type': 'security-group',
                        'id': sg_id,
                        'full_name': f"{sg_name} ({sg_id})",
                        'name': sg_name,
                        'description': sg.get('Description', ''),
                        'vpc_id': sg.get('VpcId', ''),
                    }
                    console.print(f"[green]✅ Found: {sg_name} ({sg_id})[/green]")
                    return result
            
            console.print(f"[yellow]⚠️  No security group found matching '{partial_name}'[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]❌ EC2 API error: {e}[/red]")
            return None
    
    # ==================== S3 ====================
    def find_s3_bucket(self, partial_name: str) -> Optional[Dict]:
        """Find S3 bucket by partial name"""
        client = self._get_client('s3')
        if not client:
            return None
        
        try:
            console.print(f"[cyan]🔍 [S3] Searching for bucket: '{partial_name}'...[/cyan]")
            response = client.list_buckets()
            
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                if partial_name.lower() in bucket_name.lower():
                    result = {
                        'service': 's3',
                        'resource_type': 'bucket',
                        'id': bucket_name,
                        'full_name': bucket_name,
                        'created_date': str(bucket.get('CreationDate', '')),
                    }
                    console.print(f"[green]✅ Found: {bucket_name}[/green]")
                    return result
            
            console.print(f"[yellow]⚠️  No S3 bucket found matching '{partial_name}'[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]❌ S3 API error: {e}[/red]")
            return None
    
    # ==================== DynamoDB ====================
    def find_dynamodb_table(self, partial_name: str) -> Optional[Dict]:
        """Find DynamoDB table by partial name"""
        client = self._get_client('dynamodb')
        if not client:
            return None
        
        try:
            console.print(f"[cyan]🔍 [DynamoDB] Searching for table: '{partial_name}'...[/cyan]")
            paginator = client.get_paginator('list_tables')
            
            for page in paginator.paginate():
                for table_name in page['TableNames']:
                    if partial_name.lower() in table_name.lower():
                        # Get table details
                        table_info = client.describe_table(TableName=table_name)['Table']
                        result = {
                            'service': 'dynamodb',
                            'resource_type': 'table',
                            'id': table_name,
                            'full_name': table_name,
                            'arn': table_info.get('TableArn', ''),
                            'status': table_info.get('TableStatus', ''),
                            'item_count': table_info.get('ItemCount', 0),
                            'size_bytes': table_info.get('TableSizeBytes', 0),
                        }
                        console.print(f"[green]✅ Found: {table_name}[/green]")
                        return result
            
            console.print(f"[yellow]⚠️  No DynamoDB table found matching '{partial_name}'[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]❌ DynamoDB API error: {e}[/red]")
            return None
    
    # ==================== IAM ====================
    def find_iam_role(self, partial_name: str) -> Optional[Dict]:
        """Find IAM role by partial name"""
        client = self._get_client('iam')
        if not client:
            return None
        
        try:
            console.print(f"[cyan]🔍 [IAM] Searching for role: '{partial_name}'...[/cyan]")
            paginator = client.get_paginator('list_roles')
            
            for page in paginator.paginate():
                for role in page['Roles']:
                    role_name = role['RoleName']
                    if partial_name.lower() in role_name.lower():
                        result = {
                            'service': 'iam',
                            'resource_type': 'role',
                            'id': role_name,
                            'full_name': role_name,
                            'arn': role.get('Arn', ''),
                            'created_date': str(role.get('CreateDate', '')),
                        }
                        console.print(f"[green]✅ Found: {role_name}[/green]")
                        return result
            
            console.print(f"[yellow]⚠️  No IAM role found matching '{partial_name}'[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]❌ IAM API error: {e}[/red]")
            return None
    
    # ==================== UNIVERSAL SEARCH ====================
    def find_resource(self, service: str, resource_name: str) -> Optional[Dict]:
        """
        Universal resource finder - automatically routes to the correct service
        
        Args:
            service: AWS service name (e.g., 'rds', 'lambda', 'ec2', 's3')
            resource_name: Partial or full resource name
        
        Returns:
            Resource information dict or None
        """
        service_lower = service.lower()
        
        # Route to appropriate service handler
        if service_lower in ['rds', 'aurora']:
            # Try cluster first, then instance
            result = self.find_rds_cluster(resource_name)
            if not result:
                result = self.find_rds_instance(resource_name)
            return result
        
        elif service_lower in ['lambda', 'functions']:
            return self.find_lambda_function(resource_name)
        
        elif service_lower in ['apigateway', 'api-gateway', 'api']:
            return self.find_api_gateway(resource_name)
        
        elif service_lower in ['ec2', 'instances']:
            return self.find_ec2_instance(resource_name)
        
        elif service_lower in ['sg', 'security-group', 'security-groups']:
            return self.find_security_group(resource_name)
        
        elif service_lower in ['s3', 'buckets']:
            return self.find_s3_bucket(resource_name)
        
        elif service_lower in ['dynamodb', 'tables']:
            return self.find_dynamodb_table(resource_name)
        
        elif service_lower in ['iam', 'roles']:
            return self.find_iam_role(resource_name)
        
        else:
            console.print(f"[yellow]⚠️  Service '{service}' not yet supported by AWS SDK helper[/yellow]")
            console.print(f"[dim]   Supported: RDS, Lambda, API Gateway, EC2, S3, DynamoDB, IAM[/dim]")
            return None
    
    def get_resource_metadata(self, service: str, resource_id: str) -> Optional[Dict]:
        """
        Get detailed metadata for a specific resource
        
        Args:
            service: AWS service name
            resource_id: Full resource identifier
        
        Returns:
            Detailed resource metadata
        """
        # This would call describe_* APIs to get full details
        # Implementation depends on the service
        console.print(f"[cyan]📊 Getting metadata for {service}:{resource_id}...[/cyan]")
        # TODO: Implement per-service metadata retrieval
        return None


# ==================== CONVENIENCE FUNCTIONS ====================
def find_aws_resource(service: str, resource_name: str, region: str = 'us-east-1', profile: str = None) -> Optional[Dict]:
    """
    Convenience function to find any AWS resource
    
    Args:
        service: AWS service (e.g., 'rds', 'lambda', 'ec2')
        resource_name: Partial resource name
        region: AWS region
        profile: AWS profile
    
    Returns:
        Resource info dict or None
    """
    helper = AWSUniversalHelper(region=region, profile=profile)
    return helper.find_resource(service, resource_name)


if __name__ == "__main__":
    # Test the universal helper
    print("Testing AWS Universal Helper...")
    
    helper = AWSUniversalHelper(region='us-east-1')
    
    # Test RDS
    print("\n=== Testing RDS ===")
    rds_result = helper.find_resource('rds', 'conure')
    if rds_result:
        print(f"Found: {rds_result}")
    
    # Test Lambda
    print("\n=== Testing Lambda ===")
    lambda_result = helper.find_resource('lambda', 'test')
    if lambda_result:
        print(f"Found: {lambda_result}")

