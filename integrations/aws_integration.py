"""
Complete AWS Integration
Handles all AWS services across multiple accounts with duo-sso authentication
"""

import boto3
import pandas as pd
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import json
from botocore.exceptions import ClientError
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()


class AWSIntegration:
    """
    Complete AWS integration for audit evidence collection
    Supports 10+ AWS accounts with automatic duo-sso authentication
    """
    
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.accounts = self._load_account_config()
        self.current_account = None
        self.session = None
    
    def _load_account_config(self) -> List[str]:
        """
        Load AWS account profiles from configuration
        Default: Common Cisco profiles from duo-sso
        """
        return [
            'ctr-prod',
            'ctr-int',
            'ctr-test',
            'sxo101',
            'sxo202',
            'sxo1tf',
            'sxo3tf',
            'sxo5tf',
            # Add more as needed
        ]
    
    def set_account(self, profile: str) -> bool:
        """
        Switch to specified AWS account profile
        Ensures authentication is valid
        """
        # Check authentication
        if not self.auth_manager.ensure_aws_auth(profile):
            return False
        
        self.current_account = profile
        self.session = boto3.Session(profile_name=profile)
        console.print(f"[green]✅ Using AWS account: {profile}[/green]")
        return True
    
    # ==================== RDS Functions ====================
    
    def list_rds_instances(self, region: str = 'us-east-1') -> List[Dict]:
        """List all RDS instances in account/region"""
        if not self.session:
            console.print("[red]❌ No active AWS session. Call set_account() first[/red]")
            return []
        
        try:
            rds = self.session.client('rds', region_name=region)
            response = rds.describe_db_instances()
            
            instances = []
            for db in response['DBInstances']:
                instances.append({
                    'DBInstanceIdentifier': db['DBInstanceIdentifier'],
                    'DBInstanceClass': db['DBInstanceClass'],
                    'Engine': db['Engine'],
                    'EngineVersion': db['EngineVersion'],
                    'DBInstanceStatus': db['DBInstanceStatus'],
                    'AllocatedStorage': db['AllocatedStorage'],
                    'MultiAZ': db['MultiAZ'],
                    'PubliclyAccessible': db['PubliclyAccessible'],
                    'AvailabilityZone': db['AvailabilityZone'],
                    'BackupRetentionPeriod': db['BackupRetentionPeriod'],
                    'Encrypted': db.get('StorageEncrypted', False)
                })
            
            return instances
        
        except ClientError as e:
            console.print(f"[red]❌ RDS list failed: {e}[/red]")
            return []
    
    def export_rds_instances(self, accounts: Optional[List[str]] = None, 
                            output_file: Optional[str] = None) -> str:
        """
        Export RDS instances from multiple accounts to Excel
        Returns: Output file path
        """
        if not accounts:
            accounts = self.accounts
        
        all_data = []
        
        for account in track(accounts, description="Collecting RDS data..."):
            if not self.set_account(account):
                continue
            
            instances = self.list_rds_instances()
            for inst in instances:
                inst['Account'] = account
                all_data.append(inst)
        
        if not all_data:
            console.print("[yellow]⚠️  No RDS instances found[/yellow]")
            return ""
        
        # Create DataFrame
        df = pd.DataFrame(all_data)
        
        # Generate output filename
        if not output_file:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_file = f"rds_instances_all_accounts_{timestamp}.xlsx"
        
        # Export to Excel with formatting
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='RDS Instances', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['RDS Instances']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = column_width + 2
        
        console.print(f"[green]✅ Exported RDS data to: {output_file}[/green]")
        return output_file
    
    # ==================== IAM Functions ====================
    
    def list_iam_users(self) -> List[Dict]:
        """List all IAM users in account"""
        if not self.session:
            return []
        
        try:
            iam = self.session.client('iam')
            paginator = iam.get_paginator('list_users')
            
            users = []
            for page in paginator.paginate():
                for user in page['Users']:
                    # Get MFA devices
                    mfa_devices = iam.list_mfa_devices(UserName=user['UserName'])
                    has_mfa = len(mfa_devices['MFADevices']) > 0
                    
                    # Get access keys
                    access_keys = iam.list_access_keys(UserName=user['UserName'])
                    num_keys = len(access_keys['AccessKeyMetadata'])
                    
                    users.append({
                        'UserName': user['UserName'],
                        'UserId': user['UserId'],
                        'CreateDate': user['CreateDate'].strftime('%Y-%m-%d'),
                        'HasMFA': has_mfa,
                        'NumAccessKeys': num_keys
                    })
            
            return users
        
        except ClientError as e:
            console.print(f"[red]❌ IAM list failed: {e}[/red]")
            return []
    
    def export_iam_users(self, accounts: Optional[List[str]] = None,
                        output_file: Optional[str] = None) -> str:
        """Export IAM users from multiple accounts to Excel"""
        if not accounts:
            accounts = self.accounts
        
        all_data = []
        
        for account in track(accounts, description="Collecting IAM data..."):
            if not self.set_account(account):
                continue
            
            users = self.list_iam_users()
            for user in users:
                user['Account'] = account
                all_data.append(user)
        
        if not all_data:
            console.print("[yellow]⚠️  No IAM users found[/yellow]")
            return ""
        
        # Create DataFrame
        df = pd.DataFrame(all_data)
        
        # Generate output filename
        if not output_file:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_file = f"iam_users_all_accounts_{timestamp}.xlsx"
        
        # Export to Excel
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='IAM Users', index=False)
            
            worksheet = writer.sheets['IAM Users']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = column_width + 2
        
        console.print(f"[green]✅ Exported IAM data to: {output_file}[/green]")
        return output_file
    
    # ==================== EC2 Functions ====================
    
    def list_ec2_instances(self, region: str = 'us-east-1') -> List[Dict]:
        """List all EC2 instances"""
        if not self.session:
            return []
        
        try:
            ec2 = self.session.client('ec2', region_name=region)
            response = ec2.describe_instances()
            
            instances = []
            for reservation in response['Reservations']:
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
                        'LaunchTime': instance['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S'),
                        'PrivateIpAddress': instance.get('PrivateIpAddress', 'N/A'),
                        'PublicIpAddress': instance.get('PublicIpAddress', 'N/A'),
                        'SubnetId': instance.get('SubnetId', 'N/A'),
                        'VpcId': instance.get('VpcId', 'N/A')
                    })
            
            return instances
        
        except ClientError as e:
            console.print(f"[red]❌ EC2 list failed: {e}[/red]")
            return []
    
    # ==================== S3 Functions ====================
    
    def list_s3_buckets(self) -> List[Dict]:
        """List all S3 buckets"""
        if not self.session:
            return []
        
        try:
            s3 = self.session.client('s3')
            response = s3.list_buckets()
            
            buckets = []
            for bucket in response['Buckets']:
                # Get bucket region
                try:
                    location = s3.get_bucket_location(Bucket=bucket['Name'])
                    region = location['LocationConstraint'] or 'us-east-1'
                except:
                    region = 'Unknown'
                
                # Get encryption status
                try:
                    encryption = s3.get_bucket_encryption(Bucket=bucket['Name'])
                    encrypted = True
                except:
                    encrypted = False
                
                buckets.append({
                    'BucketName': bucket['Name'],
                    'CreationDate': bucket['CreationDate'].strftime('%Y-%m-%d'),
                    'Region': region,
                    'Encrypted': encrypted
                })
            
            return buckets
        
        except ClientError as e:
            console.print(f"[red]❌ S3 list failed: {e}[/red]")
            return []
    
    # ==================== CloudTrail Functions ====================
    
    def list_cloudtrail_trails(self, region: str = 'us-east-1') -> List[Dict]:
        """List all CloudTrail trails"""
        if not self.session:
            return []
        
        try:
            cloudtrail = self.session.client('cloudtrail', region_name=region)
            response = cloudtrail.describe_trails()
            
            trails = []
            for trail in response['trailList']:
                trails.append({
                    'Name': trail['Name'],
                    'S3BucketName': trail['S3BucketName'],
                    'IsMultiRegionTrail': trail.get('IsMultiRegionTrail', False),
                    'LogFileValidationEnabled': trail.get('LogFileValidationEnabled', False),
                    'IsOrganizationTrail': trail.get('IsOrganizationTrail', False)
                })
            
            return trails
        
        except ClientError as e:
            console.print(f"[red]❌ CloudTrail list failed: {e}[/red]")
            return []
    
    # ==================== Generic Export Function ====================
    
    def export_service_data(self, service: str, accounts: Optional[List[str]] = None) -> str:
        """
        Generic export function for any AWS service
        Automatically calls appropriate service function
        """
        service_map = {
            'rds': self.export_rds_instances,
            'iam': self.export_iam_users,
            # Add more as needed
        }
        
        if service.lower() not in service_map:
            console.print(f"[red]❌ Service '{service}' not supported yet[/red]")
            return ""
        
        return service_map[service.lower()](accounts=accounts)
    
    # ==================== Multi-Service Export ====================
    
    def export_all_services(self, accounts: Optional[List[str]] = None,
                           output_dir: str = "./aws_evidence") -> Dict[str, str]:
        """
        Export all supported services to separate Excel files
        Returns: Dictionary of {service: file_path}
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        exports = {}
        services = ['rds', 'iam']  # Add more as implemented
        
        for service in services:
            console.print(f"\n[cyan]📊 Exporting {service.upper()} data...[/cyan]")
            file_path = self.export_service_data(service, accounts)
            if file_path:
                # Move to output directory
                new_path = Path(output_dir) / Path(file_path).name
                Path(file_path).rename(new_path)
                exports[service] = str(new_path)
        
        console.print(f"\n[green]✅ All exports complete! Files saved to: {output_dir}[/green]")
        return exports

