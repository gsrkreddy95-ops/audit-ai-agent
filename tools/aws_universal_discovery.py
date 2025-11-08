"""
AWS Universal Discovery - Uses boto3 SDK to discover resources across ALL AWS services

This makes the agent intelligent about ANY AWS service:
- RDS, Lambda, EC2, S3, DynamoDB, SNS, SQS, API Gateway, ECS, EKS, etc.
- Find resources by partial names
- Get resource metadata
- Build console URLs
"""

import boto3
from typing import Optional, List, Dict, Any
from rich.console import Console

console = Console()


class AWSUniversalDiscovery:
    """Discover resources across ALL AWS services using boto3"""
    
    def __init__(self, region: str = 'us-east-1', profile: str = None):
        """
        Initialize AWS discovery
        
        Args:
            region: AWS region
            profile: AWS profile name (optional)
        """
        self.region = region
        self.profile = profile
        
        try:
            if profile:
                self.session = boto3.Session(profile_name=profile, region_name=region)
            else:
                self.session = boto3.Session(region_name=region)
            
            console.print(f"[green]✅ AWS Discovery initialized (Region: {region}, Profile: {profile or 'default'})[/green]")
        except Exception as e:
            console.print(f"[red]❌ AWS SDK init failed: {e}[/red]")
            self.session = None
    
    # ========================================
    # RDS - Relational Database Service
    # ========================================
    
    def find_rds_cluster(self, partial_name: str) -> Optional[Dict]:
        """Find RDS cluster by partial name"""
        try:
            rds = self.session.client('rds')
            response = rds.describe_db_clusters()
            
            for cluster in response['DBClusters']:
                cluster_id = cluster['DBClusterIdentifier']
                
                if partial_name.lower() in cluster_id.lower():
                    return {
                        'service': 'rds',
                        'resource_type': 'cluster',
                        'id': cluster_id,
                        'name': cluster_id,
                        'arn': cluster.get('DBClusterArn'),
                        'engine': cluster.get('Engine'),
                        'status': cluster.get('Status'),
                        'endpoint': cluster.get('Endpoint'),
                        'metadata': cluster
                    }
            
            return None
        except Exception as e:
            console.print(f"[yellow]⚠️  RDS discovery error: {e}[/yellow]")
            return None
    
    def list_rds_clusters(self) -> List[str]:
        """List all RDS cluster IDs"""
        try:
            rds = self.session.client('rds')
            response = rds.describe_db_clusters()
            return [c['DBClusterIdentifier'] for c in response['DBClusters']]
        except:
            return []
    
    # ========================================
    # Lambda - Serverless Functions
    # ========================================
    
    def find_lambda_function(self, partial_name: str) -> Optional[Dict]:
        """Find Lambda function by partial name"""
        try:
            lambda_client = self.session.client('lambda')
            paginator = lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for func in page['Functions']:
                    func_name = func['FunctionName']
                    
                    if partial_name.lower() in func_name.lower():
                        return {
                            'service': 'lambda',
                            'resource_type': 'function',
                            'id': func_name,
                            'name': func_name,
                            'arn': func.get('FunctionArn'),
                            'runtime': func.get('Runtime'),
                            'handler': func.get('Handler'),
                            'memory': func.get('MemorySize'),
                            'timeout': func.get('Timeout'),
                            'metadata': func
                        }
            
            return None
        except Exception as e:
            console.print(f"[yellow]⚠️  Lambda discovery error: {e}[/yellow]")
            return None
    
    # ========================================
    # EC2 - Elastic Compute Cloud
    # ========================================
    
    def find_ec2_instance(self, partial_name: str) -> Optional[Dict]:
        """Find EC2 instance by partial name (searches Name tag and instance ID)"""
        try:
            ec2 = self.session.client('ec2')
            response = ec2.describe_instances()
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    
                    # Get Name tag
                    name = ''
                    for tag in instance.get('Tags', []):
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                    
                    # Check if partial name matches
                    if partial_name.lower() in instance_id.lower() or partial_name.lower() in name.lower():
                        return {
                            'service': 'ec2',
                            'resource_type': 'instance',
                            'id': instance_id,
                            'name': name or instance_id,
                            'instance_type': instance.get('InstanceType'),
                            'state': instance.get('State', {}).get('Name'),
                            'public_ip': instance.get('PublicIpAddress'),
                            'private_ip': instance.get('PrivateIpAddress'),
                            'metadata': instance
                        }
            
            return None
        except Exception as e:
            console.print(f"[yellow]⚠️  EC2 discovery error: {e}[/yellow]")
            return None
    
    # ========================================
    # S3 - Simple Storage Service
    # ========================================
    
    def find_s3_bucket(self, partial_name: str) -> Optional[Dict]:
        """Find S3 bucket by partial name"""
        try:
            s3 = self.session.client('s3')
            response = s3.list_buckets()
            
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                
                if partial_name.lower() in bucket_name.lower():
                    return {
                        'service': 's3',
                        'resource_type': 'bucket',
                        'id': bucket_name,
                        'name': bucket_name,
                        'creation_date': bucket.get('CreationDate'),
                        'metadata': bucket
                    }
            
            return None
        except Exception as e:
            console.print(f"[yellow]⚠️  S3 discovery error: {e}[/yellow]")
            return None
    
    # ========================================
    # DynamoDB - NoSQL Database
    # ========================================
    
    def find_dynamodb_table(self, partial_name: str) -> Optional[Dict]:
        """Find DynamoDB table by partial name"""
        try:
            dynamodb = self.session.client('dynamodb')
            paginator = dynamodb.get_paginator('list_tables')
            
            for page in paginator.paginate():
                for table_name in page['TableNames']:
                    if partial_name.lower() in table_name.lower():
                        # Get table details
                        table_info = dynamodb.describe_table(TableName=table_name)['Table']
                        
                        return {
                            'service': 'dynamodb',
                            'resource_type': 'table',
                            'id': table_name,
                            'name': table_name,
                            'arn': table_info.get('TableArn'),
                            'status': table_info.get('TableStatus'),
                            'item_count': table_info.get('ItemCount'),
                            'size_bytes': table_info.get('TableSizeBytes'),
                            'metadata': table_info
                        }
            
            return None
        except Exception as e:
            console.print(f"[yellow]⚠️  DynamoDB discovery error: {e}[/yellow]")
            return None
    
    # ========================================
    # API Gateway - REST/WebSocket APIs
    # ========================================
    
    def find_api_gateway(self, partial_name: str) -> Optional[Dict]:
        """Find API Gateway by partial name"""
        try:
            apigw = self.session.client('apigateway')
            response = apigw.get_rest_apis()
            
            for api in response['items']:
                api_name = api['name']
                
                if partial_name.lower() in api_name.lower():
                    return {
                        'service': 'apigateway',
                        'resource_type': 'rest_api',
                        'id': api['id'],
                        'name': api_name,
                        'description': api.get('description'),
                        'created_date': api.get('createdDate'),
                        'metadata': api
                    }
            
            return None
        except Exception as e:
            console.print(f"[yellow]⚠️  API Gateway discovery error: {e}[/yellow]")
            return None
    
    # ========================================
    # ECS - Elastic Container Service
    # ========================================
    
    def find_ecs_cluster(self, partial_name: str) -> Optional[Dict]:
        """Find ECS cluster by partial name"""
        try:
            ecs = self.session.client('ecs')
            response = ecs.list_clusters()
            
            for cluster_arn in response['clusterArns']:
                cluster_name = cluster_arn.split('/')[-1]
                
                if partial_name.lower() in cluster_name.lower():
                    # Get cluster details
                    details = ecs.describe_clusters(clusters=[cluster_arn])['clusters'][0]
                    
                    return {
                        'service': 'ecs',
                        'resource_type': 'cluster',
                        'id': cluster_name,
                        'name': cluster_name,
                        'arn': cluster_arn,
                        'status': details.get('status'),
                        'running_tasks': details.get('runningTasksCount'),
                        'metadata': details
                    }
            
            return None
        except Exception as e:
            console.print(f"[yellow]⚠️  ECS discovery error: {e}[/yellow]")
            return None
    
    # ========================================
    # Universal Discovery
    # ========================================
    
    def find_resource(self, service: str, partial_name: str) -> Optional[Dict]:
        """
        Universal resource finder - works for ANY AWS service!
        
        Args:
            service: Service name (e.g., 'rds', 'lambda', 'ec2')
            partial_name: Partial resource name
        
        Returns:
            Resource info dict or None
        """
        service = service.lower()
        
        console.print(f"[cyan]🔍 Searching {service.upper()} for '{partial_name}'...[/cyan]")
        
        discovery_methods = {
            'rds': self.find_rds_cluster,
            'lambda': self.find_lambda_function,
            'ec2': self.find_ec2_instance,
            's3': self.find_s3_bucket,
            'dynamodb': self.find_dynamodb_table,
            'apigateway': self.find_api_gateway,
            'ecs': self.find_ecs_cluster,
        }
        
        method = discovery_methods.get(service)
        if method:
            resource = method(partial_name)
            
            if resource:
                console.print(f"[green]✅ Found {service.upper()} resource: '{resource['name']}'[/green]")
                console.print(f"[dim]   Type: {resource['resource_type']}[/dim]")
                console.print(f"[dim]   ID: {resource['id']}[/dim]")
                return resource
            else:
                console.print(f"[yellow]⚠️  No {service.upper()} resource found matching '{partial_name}'[/yellow]")
                return None
        else:
            console.print(f"[yellow]⚠️  Service '{service}' not yet supported for discovery[/yellow]")
            console.print(f"[dim]   Supported: {', '.join(discovery_methods.keys())}[/dim]")
            return None
    
    def build_console_url(self, service: str, resource_id: Optional[str] = None, tab: Optional[str] = None) -> str:
        """
        Build AWS Console URL for any service
        
        Args:
            service: Service name (e.g., 'rds', 'lambda')
            resource_id: Optional resource ID from SDK
            tab: Optional tab name
        
        Returns:
            AWS Console URL
        """
        service = service.lower()
        
        # Service-specific URL builders
        if service == 'rds':
            base = f"https://{self.region}.console.aws.amazon.com/rds/home?region={self.region}"
            if resource_id:
                url = f"{base}#database:id={resource_id};is-cluster=true"
                if tab:
                    url += f";tab={tab.lower().replace(' ', '-')}"
                return url
            return f"{base}#databases:"
        
        elif service == 'lambda':
            base = f"https://{self.region}.console.aws.amazon.com/lambda/home?region={self.region}"
            if resource_id:
                return f"{base}#/functions/{resource_id}"
            return f"{base}#/functions"
        
        elif service == 'ec2':
            base = f"https://{self.region}.console.aws.amazon.com/ec2/home?region={self.region}"
            if resource_id:
                return f"{base}#InstanceDetails:instanceId={resource_id}"
            return f"{base}#Instances:"
        
        elif service == 's3':
            if resource_id:
                return f"https://s3.console.aws.amazon.com/s3/buckets/{resource_id}?region={self.region}"
            return f"https://s3.console.aws.amazon.com/s3/buckets?region={self.region}"
        
        elif service == 'dynamodb':
            base = f"https://{self.region}.console.aws.amazon.com/dynamodbv2/home?region={self.region}"
            if resource_id:
                return f"{base}#table?name={resource_id}"
            return f"{base}#tables"
        
        elif service == 'apigateway':
            base = f"https://{self.region}.console.aws.amazon.com/apigateway/home?region={self.region}"
            if resource_id:
                return f"{base}#/apis/{resource_id}"
            return f"{base}#/apis"
        
        elif service == 'ecs':
            base = f"https://{self.region}.console.aws.amazon.com/ecs/home?region={self.region}"
            if resource_id:
                return f"{base}#/clusters/{resource_id}"
            return f"{base}#/clusters"
        
        else:
            # Generic fallback
            return f"https://{self.region}.console.aws.amazon.com/{service}/home?region={self.region}"


if __name__ == "__main__":
    # Test universal discovery
    console.print("[bold cyan]Testing AWS Universal Discovery...[/bold cyan]\n")
    
    discovery = AWSUniversalDiscovery(region='us-east-1')
    
    # Test RDS
    resource = discovery.find_resource('rds', 'conure')
    if resource:
        url = discovery.build_console_url('rds', resource['id'], 'configuration')
        console.print(f"\n[green]Console URL:[/green] {url}")
    
    # Test Lambda
    resource = discovery.find_resource('lambda', 'my-function')
    if resource:
        url = discovery.build_console_url('lambda', resource['id'])
        console.print(f"\n[green]Console URL:[/green] {url}")

