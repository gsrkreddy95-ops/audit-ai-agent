"""
AWS Data Export Tool
Exports AWS resource data to CSV/JSON/XLSX using boto3
"""

import os
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import pandas as pd
from rich.console import Console

console = Console()


class AWSExportTool:
    """
    Exports AWS resource data via boto3 API
    Supports multiple services and export formats
    """
    
    def __init__(self, aws_profile: Optional[str] = None, region: str = 'us-east-1'):
        self.profile = aws_profile
        self.region = region
        self.session = None
    
    def _get_session(self) -> boto3.Session:
        """Get or create boto3 session"""
        if not self.session:
            if self.profile:
                self.session = boto3.Session(profile_name=self.profile, region_name=self.region)
            else:
                self.session = boto3.Session(region_name=self.region)
        return self.session
    
    def export_iam_users(self) -> List[Dict]:
        """Export IAM users"""
        console.print("[cyan]📥 Exporting IAM users...[/cyan]")
        
        try:
            session = self._get_session()
            iam = session.client('iam')
            
            users = []
            paginator = iam.get_paginator('list_users')
            
            for page in paginator.paginate():
                for user in page['Users']:
                    user_data = {
                        'UserName': user['UserName'],
                        'UserId': user['UserId'],
                        'Arn': user['Arn'],
                        'CreateDate': user['CreateDate'].isoformat(),
                        'PasswordLastUsed': user.get('PasswordLastUsed', 'Never').isoformat() if isinstance(user.get('PasswordLastUsed'), datetime) else 'Never'
                    }
                    
                    # Get user tags
                    try:
                        tags_response = iam.list_user_tags(UserName=user['UserName'])
                        user_data['Tags'] = json.dumps(tags_response.get('Tags', []))
                    except:
                        user_data['Tags'] = '[]'
                    
                    # Get groups
                    try:
                        groups_response = iam.list_groups_for_user(UserName=user['UserName'])
                        user_data['Groups'] = ', '.join([g['GroupName'] for g in groups_response.get('Groups', [])])
                    except:
                        user_data['Groups'] = ''
                    
                    users.append(user_data)
            
            console.print(f"[green]✅ Exported {len(users)} IAM users[/green]")
            return users
            
        except NoCredentialsError:
            console.print("[red]❌ AWS credentials not found. Run duo-sso first.[/red]")
            return []
        except Exception as e:
            console.print(f"[red]❌ Error exporting IAM users: {e}[/red]")
            return []
    
    def export_iam_roles(self) -> List[Dict]:
        """Export IAM roles"""
        console.print("[cyan]📥 Exporting IAM roles...[/cyan]")
        
        try:
            session = self._get_session()
            iam = session.client('iam')
            
            roles = []
            paginator = iam.get_paginator('list_roles')
            
            for page in paginator.paginate():
                for role in page['Roles']:
                    roles.append({
                        'RoleName': role['RoleName'],
                        'RoleId': role['RoleId'],
                        'Arn': role['Arn'],
                        'CreateDate': role['CreateDate'].isoformat(),
                        'Description': role.get('Description', ''),
                        'MaxSessionDuration': role.get('MaxSessionDuration', '')
                    })
            
            console.print(f"[green]✅ Exported {len(roles)} IAM roles[/green]")
            return roles
            
        except Exception as e:
            console.print(f"[red]❌ Error exporting IAM roles: {e}[/red]")
            return []
    
    def export_s3_buckets(self) -> List[Dict]:
        """Export S3 buckets with configurations"""
        console.print("[cyan]📥 Exporting S3 buckets...[/cyan]")
        
        try:
            session = self._get_session()
            s3 = session.client('s3')
            
            buckets = []
            response = s3.list_buckets()
            
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                bucket_data = {
                    'Name': bucket_name,
                    'CreationDate': bucket['CreationDate'].isoformat()
                }
                
                # Get bucket versioning
                try:
                    versioning = s3.get_bucket_versioning(Bucket=bucket_name)
                    bucket_data['Versioning'] = versioning.get('Status', 'Disabled')
                except:
                    bucket_data['Versioning'] = 'Unknown'
                
                # Get bucket encryption
                try:
                    encryption = s3.get_bucket_encryption(Bucket=bucket_name)
                    bucket_data['Encryption'] = 'Enabled'
                except:
                    bucket_data['Encryption'] = 'Disabled'
                
                # Get bucket location
                try:
                    location = s3.get_bucket_location(Bucket=bucket_name)
                    bucket_data['Region'] = location.get('LocationConstraint', 'us-east-1')
                except:
                    bucket_data['Region'] = 'Unknown'
                
                # Get bucket tags
                try:
                    tags = s3.get_bucket_tagging(Bucket=bucket_name)
                    bucket_data['Tags'] = json.dumps(tags.get('TagSet', []))
                except:
                    bucket_data['Tags'] = '[]'
                
                buckets.append(bucket_data)
            
            console.print(f"[green]✅ Exported {len(buckets)} S3 buckets[/green]")
            return buckets
            
        except Exception as e:
            console.print(f"[red]❌ Error exporting S3 buckets: {e}[/red]")
            return []
    
    def export_rds_instances(self) -> List[Dict]:
        """Export RDS instances"""
        console.print("[cyan]📥 Exporting RDS instances...[/cyan]")
        
        try:
            session = self._get_session()
            rds = session.client('rds')
            
            instances = []
            paginator = rds.get_paginator('describe_db_instances')
            
            for page in paginator.paginate():
                for instance in page['DBInstances']:
                    instances.append({
                        'DBInstanceIdentifier': instance['DBInstanceIdentifier'],
                        'DBInstanceClass': instance['DBInstanceClass'],
                        'Engine': instance['Engine'],
                        'EngineVersion': instance['EngineVersion'],
                        'DBInstanceStatus': instance['DBInstanceStatus'],
                        'AllocatedStorage': instance['AllocatedStorage'],
                        'MultiAZ': instance['MultiAZ'],
                        'BackupRetentionPeriod': instance['BackupRetentionPeriod'],
                        'PreferredBackupWindow': instance.get('PreferredBackupWindow', ''),
                        'AvailabilityZone': instance['AvailabilityZone'],
                        'InstanceCreateTime': instance['InstanceCreateTime'].isoformat() if 'InstanceCreateTime' in instance else ''
                    })
            
            console.print(f"[green]✅ Exported {len(instances)} RDS instances[/green]")
            return instances
            
        except Exception as e:
            console.print(f"[red]❌ Error exporting RDS instances: {e}[/red]")
            return []
    
    def export_rds_clusters(self) -> List[Dict]:
        """Export RDS clusters"""
        console.print("[cyan]📥 Exporting RDS clusters...[/cyan]")
        
        try:
            session = self._get_session()
            rds = session.client('rds')
            
            clusters = []
            paginator = rds.get_paginator('describe_db_clusters')
            
            for page in paginator.paginate():
                for cluster in page['DBClusters']:
                    clusters.append({
                        'DBClusterIdentifier': cluster['DBClusterIdentifier'],
                        'Engine': cluster['Engine'],
                        'EngineVersion': cluster['EngineVersion'],
                        'Status': cluster['Status'],
                        'MultiAZ': cluster.get('MultiAZ', False),
                        'BackupRetentionPeriod': cluster['BackupRetentionPeriod'],
                        'PreferredBackupWindow': cluster.get('PreferredBackupWindow', ''),
                        'AvailabilityZones': ', '.join(cluster.get('AvailabilityZones', [])),
                        'ClusterCreateTime': cluster['ClusterCreateTime'].isoformat() if 'ClusterCreateTime' in cluster else ''
                    })
            
            console.print(f"[green]✅ Exported {len(clusters)} RDS clusters[/green]")
            return clusters
            
        except Exception as e:
            console.print(f"[red]❌ Error exporting RDS clusters: {e}[/red]")
            return []
    
    def export_ec2_instances(self) -> List[Dict]:
        """Export EC2 instances"""
        console.print("[cyan]📥 Exporting EC2 instances...[/cyan]")
        
        try:
            session = self._get_session()
            ec2 = session.client('ec2')
            
            instances = []
            paginator = ec2.get_paginator('describe_instances')
            
            for page in paginator.paginate():
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        # Get instance name from tags
                        name = ''
                        for tag in instance.get('Tags', []):
                            if tag['Key'] == 'Name':
                                name = tag['Value']
                                break
                        
                        instances.append({
                            'InstanceId': instance['InstanceId'],
                            'Name': name,
                            'InstanceType': instance['InstanceType'],
                            'State': instance['State']['Name'],
                            'AvailabilityZone': instance['Placement']['AvailabilityZone'],
                            'PrivateIpAddress': instance.get('PrivateIpAddress', ''),
                            'PublicIpAddress': instance.get('PublicIpAddress', ''),
                            'LaunchTime': instance['LaunchTime'].isoformat(),
                            'VpcId': instance.get('VpcId', ''),
                            'SubnetId': instance.get('SubnetId', '')
                        })
            
            console.print(f"[green]✅ Exported {len(instances)} EC2 instances[/green]")
            return instances
            
        except Exception as e:
            console.print(f"[red]❌ Error exporting EC2 instances: {e}[/red]")
            return []
    
    def save_to_csv(self, data: List[Dict], output_path: str) -> bool:
        """Save data to CSV file"""
        try:
            if not data:
                console.print("[yellow]⚠️  No data to export[/yellow]")
                return False
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False)
            
            console.print(f"[green]✅ Saved to CSV: {output_path}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error saving CSV: {e}[/red]")
            return False
    
    def save_to_json(self, data: List[Dict], output_path: str) -> bool:
        """Save data to JSON file"""
        try:
            if not data:
                console.print("[yellow]⚠️  No data to export[/yellow]")
                return False
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            console.print(f"[green]✅ Saved to JSON: {output_path}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error saving JSON: {e}[/red]")
            return False
    
    def save_to_xlsx(self, data: List[Dict], output_path: str) -> bool:
        """Save data to Excel file"""
        try:
            if not data:
                console.print("[yellow]⚠️  No data to export[/yellow]")
                return False
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            df = pd.DataFrame(data)
            df.to_excel(output_path, index=False, engine='openpyxl')
            
            console.print(f"[green]✅ Saved to Excel: {output_path}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error saving Excel: {e}[/red]")
            return False


def export_aws_data(
    service: str,
    export_type: str,
    format: str,
    aws_account: str,
    aws_region: str,
    output_path: str
) -> bool:
    """
    High-level function to export AWS data
    
    Args:
        service: AWS service (iam, s3, rds, ec2)
        export_type: What to export (users, roles, buckets, instances, clusters)
        format: Output format (csv, json, xlsx)
        aws_account: AWS profile name
        aws_region: AWS region
        output_path: Where to save file
    
    Returns:
        True if successful
    """
    
    console.print(f"\n[bold cyan]📊 AWS Data Export[/bold cyan]")
    console.print(f"[cyan]Service: {service.upper()}[/cyan]")
    console.print(f"[cyan]Export Type: {export_type}[/cyan]")
    console.print(f"[cyan]Account: {aws_account}[/cyan]")
    console.print(f"[cyan]Region: {aws_region}[/cyan]")
    console.print(f"[cyan]Format: {format.upper()}[/cyan]\n")
    
    # Set AWS profile
    if aws_account:
        os.environ['AWS_PROFILE'] = aws_account
    
    exporter = AWSExportTool(aws_profile=aws_account, region=aws_region)
    
    # Get data based on service and export type
    data = []
    
    if service == 'iam':
        if export_type in ['users', 'user']:
            data = exporter.export_iam_users()
        elif export_type in ['roles', 'role']:
            data = exporter.export_iam_roles()
    
    elif service == 's3':
        if export_type in ['buckets', 'bucket']:
            data = exporter.export_s3_buckets()
    
    elif service == 'rds':
        if export_type in ['instances', 'instance']:
            data = exporter.export_rds_instances()
        elif export_type in ['clusters', 'cluster']:
            data = exporter.export_rds_clusters()
    
    elif service == 'ec2':
        if export_type in ['instances', 'instance']:
            data = exporter.export_ec2_instances()
    
    if not data:
        console.print("[yellow]⚠️  No data retrieved[/yellow]")
        return False
    
    # Save in requested format
    if format == 'csv':
        return exporter.save_to_csv(data, output_path)
    elif format == 'json':
        return exporter.save_to_json(data, output_path)
    elif format == 'xlsx':
        return exporter.save_to_xlsx(data, output_path)
    else:
        console.print(f"[red]❌ Unknown format: {format}[/red]")
        return False

