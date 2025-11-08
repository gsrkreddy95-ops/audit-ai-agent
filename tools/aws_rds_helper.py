"""
AWS RDS Helper - Uses boto3 SDK for intelligent cluster discovery
This makes the agent MUCH smarter - it can find clusters by partial names!
"""

import boto3
from typing import Optional, List, Dict
from rich.console import Console

console = Console()


class AWSRDSHelper:
    """Use AWS SDK (boto3) for intelligent RDS operations"""
    
    def __init__(self, region: str = 'us-east-1', profile: str = None):
        """
        Initialize AWS RDS helper
        
        Args:
            region: AWS region (default: us-east-1)
            profile: AWS profile name (e.g., 'ctr-prod', 'ctr-int')
        """
        self.region = region
        self.profile = profile
        
        try:
            # Use profile if specified, otherwise use default credentials
            if profile:
                session = boto3.Session(profile_name=profile, region_name=region)
            else:
                session = boto3.Session(region_name=region)
            
            self.rds_client = session.client('rds', region_name=region)
            console.print(f"[green]✅ AWS RDS SDK initialized (Region: {region}, Profile: {profile or 'default'})[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️  AWS SDK init failed: {e}[/yellow]")
            console.print(f"[dim]   Will fall back to browser-only navigation[/dim]")
            self.rds_client = None
    
    def find_cluster_by_partial_name(self, partial_name: str) -> Optional[Dict]:
        """
        Find RDS cluster using partial name match
        
        Example: "conure" will find "prod-conure-aurora-cluster-phase2"
        
        Args:
            partial_name: Partial cluster name (case-insensitive)
        
        Returns:
            Dict with cluster info: {'cluster_id': str, 'full_name': str, 'arn': str, 'engine': str}
            or None if not found
        """
        if not self.rds_client:
            console.print("[yellow]⚠️  RDS client not initialized, cannot search clusters[/yellow]")
            return None
        
        try:
            console.print(f"[cyan]🔍 Searching for cluster containing '{partial_name}'...[/cyan]")
            
            # List all DB clusters
            paginator = self.rds_client.get_paginator('describe_db_clusters')
            
            matches = []
            for page in paginator.paginate():
                for cluster in page['DBClusters']:
                    cluster_id = cluster['DBClusterIdentifier']
                    
                    # Case-insensitive partial match
                    if partial_name.lower() in cluster_id.lower():
                        matches.append({
                            'cluster_id': cluster_id,
                            'full_name': cluster_id,
                            'arn': cluster.get('DBClusterArn', ''),
                            'engine': cluster.get('Engine', 'unknown'),
                            'status': cluster.get('Status', 'unknown'),
                            'endpoint': cluster.get('Endpoint', ''),
                        })
            
            if matches:
                if len(matches) == 1:
                    cluster = matches[0]
                    console.print(f"[green]✅ Found cluster: '{cluster['cluster_id']}'[/green]")
                    console.print(f"[dim]   Engine: {cluster['engine']}, Status: {cluster['status']}[/dim]")
                    return cluster
                else:
                    console.print(f"[yellow]⚠️  Found {len(matches)} matching clusters:[/yellow]")
                    for i, cluster in enumerate(matches, 1):
                        console.print(f"[dim]   {i}. {cluster['cluster_id']}[/dim]")
                    console.print(f"[green]✅ Using first match: '{matches[0]['cluster_id']}'[/green]")
                    return matches[0]
            else:
                console.print(f"[yellow]⚠️  No clusters found containing '{partial_name}'[/yellow]")
                return None
        
        except Exception as e:
            console.print(f"[red]❌ AWS API error: {e}[/red]")
            return None
    
    def list_all_clusters(self) -> List[str]:
        """
        List all RDS cluster IDs in the region
        
        Returns:
            List of cluster IDs
        """
        if not self.rds_client:
            return []
        
        try:
            console.print(f"[cyan]📋 Listing all RDS clusters in {self.region}...[/cyan]")
            
            paginator = self.rds_client.get_paginator('describe_db_clusters')
            cluster_ids = []
            
            for page in paginator.paginate():
                for cluster in page['DBClusters']:
                    cluster_ids.append(cluster['DBClusterIdentifier'])
            
            console.print(f"[green]✅ Found {len(cluster_ids)} clusters[/green]")
            return cluster_ids
        
        except Exception as e:
            console.print(f"[red]❌ AWS API error: {e}[/red]")
            return []
    
    def get_cluster_details(self, cluster_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific cluster
        
        Args:
            cluster_id: Full cluster identifier
        
        Returns:
            Dict with cluster details or None if not found
        """
        if not self.rds_client:
            return None
        
        try:
            response = self.rds_client.describe_db_clusters(
                DBClusterIdentifier=cluster_id
            )
            
            if response['DBClusters']:
                cluster = response['DBClusters'][0]
                return {
                    'cluster_id': cluster['DBClusterIdentifier'],
                    'engine': cluster.get('Engine', 'unknown'),
                    'engine_version': cluster.get('EngineVersion', 'unknown'),
                    'status': cluster.get('Status', 'unknown'),
                    'endpoint': cluster.get('Endpoint', ''),
                    'port': cluster.get('Port', 3306),
                    'master_username': cluster.get('MasterUsername', ''),
                    'backup_retention_period': cluster.get('BackupRetentionPeriod', 0),
                    'preferred_backup_window': cluster.get('PreferredBackupWindow', ''),
                    'preferred_maintenance_window': cluster.get('PreferredMaintenanceWindow', ''),
                    'encrypted': cluster.get('StorageEncrypted', False),
                    'kms_key_id': cluster.get('KmsKeyId', ''),
                    'vpc_security_groups': [sg['VpcSecurityGroupId'] for sg in cluster.get('VpcSecurityGroups', [])],
                    'db_subnet_group': cluster.get('DBSubnetGroup', {}).get('DBSubnetGroupName', ''),
                }
            
            return None
        
        except Exception as e:
            console.print(f"[red]❌ Could not get cluster details: {e}[/red]")
            return None
    
    def build_console_url(self, cluster_id: str = None, tab: str = None) -> str:
        """
        Build AWS Console URL for RDS using SDK data
        
        This uses the cluster ID and region from SDK to construct proper console URLs.
        Much more reliable than guessing!
        
        Args:
            cluster_id: Optional cluster ID to navigate to specific cluster
            tab: Optional tab name (e.g., 'configuration', 'maintenance-and-backups')
        
        Returns:
            AWS Console URL string
        """
        base_url = f"https://{self.region}.console.aws.amazon.com/rds/home?region={self.region}"
        
        if not cluster_id:
            # URL to databases list
            return f"{base_url}#databases:"
        
        # URL to specific cluster
        cluster_url = f"{base_url}#database:id={cluster_id};is-cluster=true"
        
        if tab:
            # Normalize tab name
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


def find_rds_cluster_smart(partial_name: str, region: str = 'us-east-1', profile: str = None) -> Optional[str]:
    """
    Convenience function to find cluster ID by partial name
    
    Args:
        partial_name: Partial cluster name (e.g., "conure")
        region: AWS region
        profile: AWS profile name
    
    Returns:
        Full cluster ID or None
    """
    helper = AWSRDSHelper(region=region, profile=profile)
    result = helper.find_cluster_by_partial_name(partial_name)
    
    if result:
        return result['cluster_id']
    return None


if __name__ == "__main__":
    # Test the helper
    print("Testing AWS RDS Helper...")
    
    # Test finding cluster by partial name
    helper = AWSRDSHelper(region='us-east-1')
    result = helper.find_cluster_by_partial_name('conure')
    
    if result:
        print(f"\nFound cluster: {result['cluster_id']}")
        print(f"Details: {result}")
    else:
        print("\nNo cluster found")

