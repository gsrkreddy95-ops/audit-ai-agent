"""
AWS List Resources Tool
Quick listing of AWS resources without full export
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from rich.console import Console
from rich.table import Table
from typing import List, Dict, Optional

console = Console()


def list_s3_buckets(aws_profile: str, aws_region: str = 'us-east-1') -> List[str]:
    """Quick list of S3 buckets"""
    try:
        if aws_profile:
            os.environ['AWS_PROFILE'] = aws_profile
        
        session = boto3.Session(profile_name=aws_profile if aws_profile else None, region_name=aws_region)
        s3 = session.client('s3')
        
        response = s3.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        
        console.print(f"\n[bold cyan]📦 S3 Buckets ({len(buckets)} total)[/bold cyan]\n")
        
        table = Table(show_header=True)
        table.add_column("Bucket Name", style="cyan")
        table.add_column("Creation Date", style="green")
        
        for bucket in response['Buckets']:
            table.add_row(bucket['Name'], str(bucket['CreationDate']))
        
        console.print(table)
        console.print()
        
        return buckets
        
    except NoCredentialsError:
        console.print("[red]❌ AWS credentials not found. Run duo-sso first.[/red]")
        return []
    except Exception as e:
        console.print(f"[red]❌ Error listing S3 buckets: {e}[/red]")
        return []


def list_rds_instances(aws_profile: str, aws_region: str = 'us-east-1') -> List[Dict]:
    """Quick list of RDS instances"""
    try:
        if aws_profile:
            os.environ['AWS_PROFILE'] = aws_profile
        
        session = boto3.Session(profile_name=aws_profile if aws_profile else None, region_name=aws_region)
        rds = session.client('rds')
        
        response = rds.describe_db_instances()
        instances = response['DBInstances']
        
        console.print(f"\n[bold cyan]🗄️  RDS Instances in {aws_region} ({len(instances)} total)[/bold cyan]\n")
        
        table = Table(show_header=True)
        table.add_column("Instance ID", style="cyan")
        table.add_column("Engine", style="green")
        table.add_column("Class", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Multi-AZ", style="blue")
        
        for instance in instances:
            table.add_row(
                instance['DBInstanceIdentifier'],
                f"{instance['Engine']} {instance['EngineVersion']}",
                instance['DBInstanceClass'],
                instance['DBInstanceStatus'],
                "✓" if instance['MultiAZ'] else "✗"
            )
        
        console.print(table)
        console.print()
        
        return instances
        
    except Exception as e:
        console.print(f"[red]❌ Error listing RDS instances: {e}[/red]")
        return []


def list_rds_clusters(aws_profile: str, aws_region: str = 'us-east-1') -> List[Dict]:
    """Quick list of RDS clusters"""
    try:
        if aws_profile:
            os.environ['AWS_PROFILE'] = aws_profile
        
        session = boto3.Session(profile_name=aws_profile if aws_profile else None, region_name=aws_region)
        rds = session.client('rds')
        
        response = rds.describe_db_clusters()
        clusters = response['DBClusters']
        
        console.print(f"\n[bold cyan]🗄️  RDS Clusters in {aws_region} ({len(clusters)} total)[/bold cyan]\n")
        
        table = Table(show_header=True)
        table.add_column("Cluster ID", style="cyan")
        table.add_column("Engine", style="green")
        table.add_column("Status", style="magenta")
        table.add_column("Multi-AZ", style="blue")
        table.add_column("Members", style="yellow")
        
        for cluster in clusters:
            table.add_row(
                cluster['DBClusterIdentifier'],
                f"{cluster['Engine']} {cluster['EngineVersion']}",
                cluster['Status'],
                "✓" if cluster.get('MultiAZ', False) else "✗",
                str(len(cluster.get('DBClusterMembers', [])))
            )
        
        console.print(table)
        console.print()
        
        return clusters
        
    except Exception as e:
        console.print(f"[red]❌ Error listing RDS clusters: {e}[/red]")
        return []


def list_iam_users(aws_profile: str) -> List[str]:
    """Quick list of IAM users"""
    try:
        if aws_profile:
            os.environ['AWS_PROFILE'] = aws_profile
        
        session = boto3.Session(profile_name=aws_profile if aws_profile else None)
        iam = session.client('iam')
        
        response = iam.list_users()
        users = response['Users']
        
        console.print(f"\n[bold cyan]👥 IAM Users ({len(users)} total)[/bold cyan]\n")
        
        table = Table(show_header=True)
        table.add_column("User Name", style="cyan")
        table.add_column("User ID", style="green")
        table.add_column("Created", style="yellow")
        
        for user in users:
            table.add_row(
                user['UserName'],
                user['UserId'],
                str(user['CreateDate'].date())
            )
        
        console.print(table)
        console.print()
        
        return [user['UserName'] for user in users]
        
    except Exception as e:
        console.print(f"[red]❌ Error listing IAM users: {e}[/red]")
        return []


def list_ec2_instances(aws_profile: str, aws_region: str = 'us-east-1') -> List[Dict]:
    """Quick list of EC2 instances"""
    try:
        if aws_profile:
            os.environ['AWS_PROFILE'] = aws_profile
        
        session = boto3.Session(profile_name=aws_profile if aws_profile else None, region_name=aws_region)
        ec2 = session.client('ec2')
        
        response = ec2.describe_instances()
        instances = []
        
        for reservation in response['Reservations']:
            instances.extend(reservation['Instances'])
        
        console.print(f"\n[bold cyan]💻 EC2 Instances in {aws_region} ({len(instances)} total)[/bold cyan]\n")
        
        table = Table(show_header=True)
        table.add_column("Instance ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("State", style="magenta")
        table.add_column("Private IP", style="blue")
        
        for instance in instances:
            # Get name from tags
            name = ''
            for tag in instance.get('Tags', []):
                if tag['Key'] == 'Name':
                    name = tag['Value']
                    break
            
            table.add_row(
                instance['InstanceId'],
                name or '-',
                instance['InstanceType'],
                instance['State']['Name'],
                instance.get('PrivateIpAddress', '-')
            )
        
        console.print(table)
        console.print()
        
        return instances
        
    except Exception as e:
        console.print(f"[red]❌ Error listing EC2 instances: {e}[/red]")
        return []


def list_lambda_functions(aws_profile: str, aws_region: str = 'us-east-1') -> List[str]:
    """Quick list of Lambda functions"""
    try:
        if aws_profile:
            os.environ['AWS_PROFILE'] = aws_profile
        
        session = boto3.Session(profile_name=aws_profile if aws_profile else None, region_name=aws_region)
        lambda_client = session.client('lambda')
        
        response = lambda_client.list_functions()
        functions = response['Functions']
        
        console.print(f"\n[bold cyan]λ Lambda Functions in {aws_region} ({len(functions)} total)[/bold cyan]\n")
        
        table = Table(show_header=True)
        table.add_column("Function Name", style="cyan")
        table.add_column("Runtime", style="green")
        table.add_column("Memory", style="yellow")
        table.add_column("Timeout", style="magenta")
        
        for func in functions:
            table.add_row(
                func['FunctionName'],
                func['Runtime'],
                f"{func['MemorySize']} MB",
                f"{func['Timeout']}s"
            )
        
        console.print(table)
        console.print()
        
        return [func['FunctionName'] for func in functions]
        
    except Exception as e:
        console.print(f"[red]❌ Error listing Lambda functions: {e}[/red]")
        return []


def list_vpc_resources(aws_profile: str, aws_region: str = 'us-east-1') -> Dict:
    """Quick list of VPC resources"""
    try:
        if aws_profile:
            os.environ['AWS_PROFILE'] = aws_profile
        
        session = boto3.Session(profile_name=aws_profile if aws_profile else None, region_name=aws_region)
        ec2 = session.client('ec2')
        
        vpcs = ec2.describe_vpcs()['Vpcs']
        
        console.print(f"\n[bold cyan]🌐 VPCs in {aws_region} ({len(vpcs)} total)[/bold cyan]\n")
        
        table = Table(show_header=True)
        table.add_column("VPC ID", style="cyan")
        table.add_column("CIDR", style="green")
        table.add_column("State", style="magenta")
        table.add_column("Default", style="yellow")
        
        for vpc in vpcs:
            # Get VPC name
            name = ''
            for tag in vpc.get('Tags', []):
                if tag['Key'] == 'Name':
                    name = tag['Value']
                    break
            
            table.add_row(
                f"{vpc['VpcId']}{' (' + name + ')' if name else ''}",
                vpc['CidrBlock'],
                vpc['State'],
                "✓" if vpc['IsDefault'] else "✗"
            )
        
        console.print(table)
        console.print()
        
        return {'vpcs': vpcs}
        
    except Exception as e:
        console.print(f"[red]❌ Error listing VPCs: {e}[/red]")
        return {}

