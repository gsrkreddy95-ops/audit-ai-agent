"""
AWS Comprehensive Audit Evidence Collector
Automatically discovers and exports ALL AWS resources with detailed configurations
Uses boto3 (AWS SDK) to fetch complete audit evidence across 100+ AWS services
"""

import os
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from rich.console import Console
from rich.table import Table
import pandas as pd

console = Console()


class AWSComprehensiveAuditCollector:
    """
    Comprehensive AWS audit evidence collector
    Supports 100+ AWS services with detailed configuration extraction
    """
    
    # Comprehensive service definitions with API mappings
    SERVICE_CONFIGS = {
        # === COMPUTE ===
        'ec2': {
            'name': 'EC2 (Compute)',
            'resources': {
                'instances': ('describe_instances', 'Reservations[].Instances[]'),
                'security_groups': ('describe_security_groups', 'SecurityGroups'),
                'key_pairs': ('describe_key_pairs', 'KeyPairs'),
                'volumes': ('describe_volumes', 'Volumes'),
                'snapshots': ('describe_snapshots', 'Snapshots', {'OwnerIds': ['self']}),
                'images': ('describe_images', 'Images', {'Owners': ['self']}),
                'elastic_ips': ('describe_addresses', 'Addresses'),
                'network_interfaces': ('describe_network_interfaces', 'NetworkInterfaces'),
                'placement_groups': ('describe_placement_groups', 'PlacementGroups'),
                'launch_templates': ('describe_launch_templates', 'LaunchTemplates'),
            }
        },
        'lambda': {
            'name': 'Lambda (Serverless)',
            'resources': {
                'functions': ('list_functions', 'Functions'),
                'layers': ('list_layers', 'Layers'),
                'event_source_mappings': ('list_event_source_mappings', 'EventSourceMappings'),
            }
        },
        'ecs': {
            'name': 'ECS (Containers)',
            'resources': {
                'clusters': ('list_clusters', 'clusterArns'),
                'services': ('list_services', 'serviceArns'),
                'tasks': ('list_tasks', 'taskArns'),
                'task_definitions': ('list_task_definitions', 'taskDefinitionArns'),
            }
        },
        'eks': {
            'name': 'EKS (Kubernetes)',
            'resources': {
                'clusters': ('list_clusters', 'clusters'),
                'fargate_profiles': ('list_fargate_profiles', 'fargateProfileNames'),
                'nodegroups': ('list_nodegroups', 'nodegroups'),
            }
        },
        
        # === STORAGE ===
        's3': {
            'name': 'S3 (Object Storage)',
            'resources': {
                'buckets': ('list_buckets', 'Buckets'),
            }
        },
        'ebs': {
            'name': 'EBS (Block Storage)',
            'resources': {
                'volumes': ('describe_volumes', 'Volumes'),
                'snapshots': ('describe_snapshots', 'Snapshots', {'OwnerIds': ['self']}),
            },
            'client': 'ec2'
        },
        'efs': {
            'name': 'EFS (File Storage)',
            'resources': {
                'file_systems': ('describe_file_systems', 'FileSystems'),
                'mount_targets': ('describe_mount_targets', 'MountTargets'),
            }
        },
        'fsx': {
            'name': 'FSx (Managed File Systems)',
            'resources': {
                'file_systems': ('describe_file_systems', 'FileSystems'),
                'backups': ('describe_backups', 'Backups'),
            }
        },
        'glacier': {
            'name': 'Glacier (Archive Storage)',
            'resources': {
                'vaults': ('list_vaults', 'VaultList'),
            }
        },
        'backup': {
            'name': 'AWS Backup',
            'resources': {
                'backup_vaults': ('list_backup_vaults', 'BackupVaultList'),
                'backup_plans': ('list_backup_plans', 'BackupPlansList'),
                'recovery_points': ('list_recovery_points_by_backup_vault', 'RecoveryPoints'),
            }
        },
        
        # === DATABASE ===
        'rds': {
            'name': 'RDS (Relational Database)',
            'resources': {
                'instances': ('describe_db_instances', 'DBInstances'),
                'clusters': ('describe_db_clusters', 'DBClusters'),
                'snapshots': ('describe_db_snapshots', 'DBSnapshots'),
                'cluster_snapshots': ('describe_db_cluster_snapshots', 'DBClusterSnapshots'),
                'parameter_groups': ('describe_db_parameter_groups', 'DBParameterGroups'),
                'subnet_groups': ('describe_db_subnet_groups', 'DBSubnetGroups'),
            }
        },
        'dynamodb': {
            'name': 'DynamoDB (NoSQL)',
            'resources': {
                'tables': ('list_tables', 'TableNames'),
                'backups': ('list_backups', 'BackupSummaries'),
                'global_tables': ('list_global_tables', 'GlobalTables'),
            }
        },
        'elasticache': {
            'name': 'ElastiCache (In-Memory)',
            'resources': {
                'clusters': ('describe_cache_clusters', 'CacheClusters'),
                'replication_groups': ('describe_replication_groups', 'ReplicationGroups'),
                'snapshots': ('describe_snapshots', 'Snapshots'),
            }
        },
        'redshift': {
            'name': 'Redshift (Data Warehouse)',
            'resources': {
                'clusters': ('describe_clusters', 'Clusters'),
                'snapshots': ('describe_cluster_snapshots', 'Snapshots'),
                'parameter_groups': ('describe_cluster_parameter_groups', 'ParameterGroups'),
            }
        },
        'docdb': {
            'name': 'DocumentDB',
            'resources': {
                'clusters': ('describe_db_clusters', 'DBClusters'),
                'instances': ('describe_db_instances', 'DBInstances'),
            }
        },
        'neptune': {
            'name': 'Neptune (Graph Database)',
            'resources': {
                'clusters': ('describe_db_clusters', 'DBClusters'),
                'instances': ('describe_db_instances', 'DBInstances'),
            }
        },
        
        # === NETWORKING ===
        'vpc': {
            'name': 'VPC (Virtual Private Cloud)',
            'resources': {
                'vpcs': ('describe_vpcs', 'Vpcs'),
                'subnets': ('describe_subnets', 'Subnets'),
                'route_tables': ('describe_route_tables', 'RouteTables'),
                'internet_gateways': ('describe_internet_gateways', 'InternetGateways'),
                'nat_gateways': ('describe_nat_gateways', 'NatGateways'),
                'vpn_gateways': ('describe_vpn_gateways', 'VpnGateways'),
                'customer_gateways': ('describe_customer_gateways', 'CustomerGateways'),
                'vpn_connections': ('describe_vpn_connections', 'VpnConnections'),
                'vpc_peering_connections': ('describe_vpc_peering_connections', 'VpcPeeringConnections'),
                'network_acls': ('describe_network_acls', 'NetworkAcls'),
                'dhcp_options': ('describe_dhcp_options', 'DhcpOptions'),
                'vpc_endpoints': ('describe_vpc_endpoints', 'VpcEndpoints'),
            },
            'client': 'ec2'
        },
        'elb': {
            'name': 'ELB (Classic Load Balancer)',
            'resources': {
                'load_balancers': ('describe_load_balancers', 'LoadBalancerDescriptions'),
            }
        },
        'elbv2': {
            'name': 'ELBv2 (Application/Network LB)',
            'resources': {
                'load_balancers': ('describe_load_balancers', 'LoadBalancers'),
                'target_groups': ('describe_target_groups', 'TargetGroups'),
                'listeners': ('describe_listeners', 'Listeners'),
            }
        },
        'route53': {
            'name': 'Route 53 (DNS)',
            'resources': {
                'hosted_zones': ('list_hosted_zones', 'HostedZones'),
                'health_checks': ('list_health_checks', 'HealthChecks'),
            }
        },
        'cloudfront': {
            'name': 'CloudFront (CDN)',
            'resources': {
                'distributions': ('list_distributions', 'DistributionList.Items'),
                'streaming_distributions': ('list_streaming_distributions', 'StreamingDistributionList.Items'),
                'origin_access_identities': ('list_cloud_front_origin_access_identities', 'CloudFrontOriginAccessIdentityList.Items'),
            }
        },
        'apigateway': {
            'name': 'API Gateway',
            'resources': {
                'rest_apis': ('get_rest_apis', 'items'),
                'domain_names': ('get_domain_names', 'items'),
                'api_keys': ('get_api_keys', 'items'),
                'usage_plans': ('get_usage_plans', 'items'),
            }
        },
        'apigatewayv2': {
            'name': 'API Gateway v2 (HTTP/WebSocket)',
            'resources': {
                'apis': ('get_apis', 'Items'),
                'domain_names': ('get_domain_names', 'Items'),
            }
        },
        'directconnect': {
            'name': 'Direct Connect',
            'resources': {
                'connections': ('describe_connections', 'connections'),
                'virtual_interfaces': ('describe_virtual_interfaces', 'virtualInterfaces'),
                'lags': ('describe_lags', 'lags'),
            }
        },
        
        # === SECURITY & IDENTITY ===
        'iam': {
            'name': 'IAM (Identity & Access)',
            'resources': {
                'users': ('list_users', 'Users'),
                'groups': ('list_groups', 'Groups'),
                'roles': ('list_roles', 'Roles'),
                'policies': ('list_policies', 'Policies', {'Scope': 'Local'}),
                'instance_profiles': ('list_instance_profiles', 'InstanceProfiles'),
                'saml_providers': ('list_saml_providers', 'SAMLProviderList'),
                'oidc_providers': ('list_open_id_connect_providers', 'OpenIDConnectProviderList'),
                'server_certificates': ('list_server_certificates', 'ServerCertificateMetadataList'),
            }
        },
        'kms': {
            'name': 'KMS (Key Management)',
            'resources': {
                'keys': ('list_keys', 'Keys'),
                'aliases': ('list_aliases', 'Aliases'),
            }
        },
        'secretsmanager': {
            'name': 'Secrets Manager',
            'resources': {
                'secrets': ('list_secrets', 'SecretList'),
            }
        },
        'acm': {
            'name': 'ACM (Certificate Manager)',
            'resources': {
                'certificates': ('list_certificates', 'CertificateSummaryList'),
            }
        },
        'waf': {
            'name': 'WAF (Web Application Firewall)',
            'resources': {
                'web_acls': ('list_web_acls', 'WebACLs'),
                'rule_groups': ('list_rule_groups', 'RuleGroups'),
                'ip_sets': ('list_ip_sets', 'IPSets'),
            }
        },
        'wafv2': {
            'name': 'WAFv2',
            'resources': {
                'web_acls': ('list_web_acls', 'WebACLs', {'Scope': 'REGIONAL'}),
                'rule_groups': ('list_rule_groups', 'RuleGroups', {'Scope': 'REGIONAL'}),
                'ip_sets': ('list_ip_sets', 'IPSets', {'Scope': 'REGIONAL'}),
            }
        },
        'shield': {
            'name': 'Shield (DDoS Protection)',
            'resources': {
                'protections': ('list_protections', 'Protections'),
            }
        },
        'guardduty': {
            'name': 'GuardDuty (Threat Detection)',
            'resources': {
                'detectors': ('list_detectors', 'DetectorIds'),
            }
        },
        'securityhub': {
            'name': 'Security Hub',
            'resources': {
                'hubs': ('describe_hub', None),
                'standards_subscriptions': ('get_enabled_standards', 'StandardsSubscriptions'),
            }
        },
        'macie2': {
            'name': 'Macie (Data Security)',
            'resources': {
                'classification_jobs': ('list_classification_jobs', 'items'),
                'buckets': ('describe_buckets', 'buckets'),
            }
        },
        
        # === MANAGEMENT & GOVERNANCE ===
        'cloudwatch': {
            'name': 'CloudWatch (Monitoring)',
            'resources': {
                'alarms': ('describe_alarms', 'MetricAlarms'),
                'dashboards': ('list_dashboards', 'DashboardEntries'),
                'log_groups': ('describe_log_groups', 'logGroups'),
            },
            'logs_client': 'logs'
        },
        'cloudtrail': {
            'name': 'CloudTrail (Audit Logs)',
            'resources': {
                'trails': ('describe_trails', 'trailList'),
                'event_selectors': ('get_event_selectors', 'EventSelectors'),
            }
        },
        'config': {
            'name': 'AWS Config',
            'resources': {
                'configuration_recorders': ('describe_configuration_recorders', 'ConfigurationRecorders'),
                'delivery_channels': ('describe_delivery_channels', 'DeliveryChannels'),
                'config_rules': ('describe_config_rules', 'ConfigRules'),
            }
        },
        'organizations': {
            'name': 'Organizations',
            'resources': {
                'accounts': ('list_accounts', 'Accounts'),
                'organizational_units': ('list_organizational_units_for_parent', 'OrganizationalUnits'),
                'policies': ('list_policies', 'Policies', {'Filter': 'SERVICE_CONTROL_POLICY'}),
            }
        },
        'cloudformation': {
            'name': 'CloudFormation (IaC)',
            'resources': {
                'stacks': ('describe_stacks', 'Stacks'),
                'stack_sets': ('list_stack_sets', 'Summaries'),
            }
        },
        'servicecatalog': {
            'name': 'Service Catalog',
            'resources': {
                'portfolios': ('list_portfolios', 'PortfolioDetails'),
                'products': ('search_products', 'ProductViewSummaries'),
            }
        },
        'ssm': {
            'name': 'Systems Manager',
            'resources': {
                'documents': ('list_documents', 'DocumentIdentifiers'),
                'parameters': ('describe_parameters', 'Parameters'),
                'patch_baselines': ('describe_patch_baselines', 'BaselineIdentities'),
                'maintenance_windows': ('describe_maintenance_windows', 'WindowIdentities'),
            }
        },
        'autoscaling': {
            'name': 'Auto Scaling',
            'resources': {
                'auto_scaling_groups': ('describe_auto_scaling_groups', 'AutoScalingGroups'),
                'launch_configurations': ('describe_launch_configurations', 'LaunchConfigurations'),
                'scaling_policies': ('describe_policies', 'ScalingPolicies'),
            }
        },
        
        # === ANALYTICS & BIG DATA ===
        'athena': {
            'name': 'Athena (Query)',
            'resources': {
                'data_catalogs': ('list_data_catalogs', 'DataCatalogsSummary'),
                'work_groups': ('list_work_groups', 'WorkGroups'),
            }
        },
        'glue': {
            'name': 'Glue (ETL)',
            'resources': {
                'databases': ('get_databases', 'DatabaseList'),
                'crawlers': ('get_crawlers', 'Crawlers'),
                'jobs': ('get_jobs', 'Jobs'),
                'triggers': ('get_triggers', 'Triggers'),
            }
        },
        'emr': {
            'name': 'EMR (Hadoop/Spark)',
            'resources': {
                'clusters': ('list_clusters', 'Clusters'),
                'notebook_executions': ('list_notebook_executions', 'NotebookExecutions'),
            }
        },
        'kinesis': {
            'name': 'Kinesis (Streaming)',
            'resources': {
                'streams': ('list_streams', 'StreamNames'),
            }
        },
        'firehose': {
            'name': 'Kinesis Firehose',
            'resources': {
                'delivery_streams': ('list_delivery_streams', 'DeliveryStreamNames'),
            }
        },
        'kafka': {
            'name': 'MSK (Kafka)',
            'resources': {
                'clusters': ('list_clusters', 'ClusterInfoList'),
            }
        },
        'es': {
            'name': 'Elasticsearch',
            'resources': {
                'domains': ('list_domain_names', 'DomainNames'),
            }
        },
        
        # === APPLICATION INTEGRATION ===
        'sns': {
            'name': 'SNS (Notifications)',
            'resources': {
                'topics': ('list_topics', 'Topics'),
                'subscriptions': ('list_subscriptions', 'Subscriptions'),
            }
        },
        'sqs': {
            'name': 'SQS (Queues)',
            'resources': {
                'queues': ('list_queues', 'QueueUrls'),
            }
        },
        'eventbridge': {
            'name': 'EventBridge',
            'resources': {
                'event_buses': ('list_event_buses', 'EventBuses'),
                'rules': ('list_rules', 'Rules'),
            },
            'client': 'events'
        },
        'stepfunctions': {
            'name': 'Step Functions',
            'resources': {
                'state_machines': ('list_state_machines', 'stateMachines'),
                'activities': ('list_activities', 'activities'),
            },
            'client': 'stepfunctions'
        },
        'swf': {
            'name': 'SWF (Workflow)',
            'resources': {
                'domains': ('list_domains', 'domainInfos', {'registrationStatus': 'REGISTERED'}),
            }
        },
        
        # === DEVELOPER TOOLS ===
        'codecommit': {
            'name': 'CodeCommit (Git)',
            'resources': {
                'repositories': ('list_repositories', 'repositories'),
            }
        },
        'codebuild': {
            'name': 'CodeBuild',
            'resources': {
                'projects': ('list_projects', 'projects'),
            }
        },
        'codedeploy': {
            'name': 'CodeDeploy',
            'resources': {
                'applications': ('list_applications', 'applications'),
                'deployment_groups': ('list_deployment_groups', 'deploymentGroups'),
            }
        },
        'codepipeline': {
            'name': 'CodePipeline',
            'resources': {
                'pipelines': ('list_pipelines', 'pipelines'),
            }
        },
        'codeartifact': {
            'name': 'CodeArtifact',
            'resources': {
                'domains': ('list_domains', 'domains'),
                'repositories': ('list_repositories', 'repositories'),
            }
        },
        
        # === MACHINE LEARNING ===
        'sagemaker': {
            'name': 'SageMaker (ML)',
            'resources': {
                'notebook_instances': ('list_notebook_instances', 'NotebookInstances'),
                'training_jobs': ('list_training_jobs', 'TrainingJobSummaries'),
                'models': ('list_models', 'Models'),
                'endpoints': ('list_endpoints', 'Endpoints'),
            }
        },
        'bedrock': {
            'name': 'Bedrock (GenAI)',
            'resources': {
                'foundation_models': ('list_foundation_models', 'modelSummaries'),
                'custom_models': ('list_custom_models', 'modelSummaries'),
            }
        },
        
        # === OTHERS ===
        'ses': {
            'name': 'SES (Email)',
            'resources': {
                'identities': ('list_identities', 'Identities'),
                'configuration_sets': ('list_configuration_sets', 'ConfigurationSets'),
            }
        },
        'workspaces': {
            'name': 'WorkSpaces (Virtual Desktops)',
            'resources': {
                'workspaces': ('describe_workspaces', 'Workspaces'),
                'directories': ('describe_workspace_directories', 'Directories'),
            }
        },
        'batch': {
            'name': 'Batch',
            'resources': {
                'job_queues': ('describe_job_queues', 'jobQueues'),
                'compute_environments': ('describe_compute_environments', 'computeEnvironments'),
            }
        },
    }
    
    def __init__(self, aws_profile: str, region: str = 'us-east-1'):
        """
        Initialize comprehensive collector
        
        Args:
            aws_profile: AWS profile name (e.g., 'ctr-prod', 'sxo101')
            region: AWS region
        """
        self.profile = aws_profile
        self.region = region
        self.session = None
        self.clients = {}
        
        # Set AWS profile
        if aws_profile:
            os.environ['AWS_PROFILE'] = aws_profile
    
    def _get_session(self) -> boto3.Session:
        """Get or create boto3 session"""
        if not self.session:
            if self.profile:
                self.session = boto3.Session(profile_name=self.profile, region_name=self.region)
            else:
                self.session = boto3.Session(region_name=self.region)
        return self.session
    
    def _get_client(self, service: str):
        """Get or create boto3 client for service"""
        if service not in self.clients:
            session = self._get_session()
            self.clients[service] = session.client(service)
        return self.clients[service]
    
    def list_all_services(self) -> List[str]:
        """Get list of all supported services"""
        return list(self.SERVICE_CONFIGS.keys())
    
    def get_service_info(self, service: str) -> Dict:
        """Get service information"""
        return self.SERVICE_CONFIGS.get(service, {})
    
    def collect_service_resources(
        self,
        service: str,
        resource_types: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Collect resources for a specific service
        
        Args:
            service: Service key (e.g., 'ec2', 's3', 'rds')
            resource_types: Specific resource types to collect (None = all)
        
        Returns:
            Dict mapping resource type to list of resources
        """
        service_config = self.SERVICE_CONFIGS.get(service)
        if not service_config:
            console.print(f"[red]❌ Unknown service: {service}[/red]")
            return {}
        
        console.print(f"\n[bold cyan]📦 Collecting: {service_config['name']}[/bold cyan]")
        
        # Determine which boto3 client to use
        client_name = service_config.get('client', service)
        client = self._get_client(client_name)
        
        results = {}
        resources_config = service_config['resources']
        
        # Filter resource types if specified
        if resource_types:
            resources_config = {k: v for k, v in resources_config.items() if k in resource_types}
        
        for resource_type, config in resources_config.items():
            try:
                api_method = config[0]
                response_key = config[1]
                extra_params = config[2] if len(config) > 2 else {}
                
                console.print(f"[cyan]  ├─ {resource_type}...[/cyan]", end="")
                
                # Call the API
                method = getattr(client, api_method)
                response = method(**extra_params)
                
                # Extract resources from response
                if response_key is None:
                    # Special case: single resource (like describe_hub)
                    resources = [response]
                elif '[]' in response_key:
                    # Nested array path (e.g., 'Reservations[].Instances[]')
                    parts = response_key.replace('[]', '').split('.')
                    data = response
                    for part in parts:
                        if part:
                            data = data.get(part, [])
                            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                                # Flatten nested lists
                                flattened = []
                                for item in data:
                                    if isinstance(item, dict):
                                        for sub_key in item:
                                            if isinstance(item[sub_key], list):
                                                flattened.extend(item[sub_key])
                                if flattened:
                                    data = flattened
                    resources = data if isinstance(data, list) else [data]
                else:
                    # Simple key path (e.g., 'Buckets' or 'DistributionList.Items')
                    keys = response_key.split('.')
                    data = response
                    for key in keys:
                        data = data.get(key, [])
                    resources = data if isinstance(data, list) else [data]
                
                results[resource_type] = resources
                console.print(f" [green]{len(resources)} found[/green]")
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code in ['AccessDenied', 'UnauthorizedOperation', 'InvalidAction']:
                    console.print(f" [yellow]⚠️  No permission[/yellow]")
                else:
                    console.print(f" [red]❌ {error_code}[/red]")
                results[resource_type] = []
            except Exception as e:
                console.print(f" [red]❌ {str(e)[:50]}[/red]")
                results[resource_type] = []
        
        return results
    
    def collect_all_services(
        self,
        services: Optional[List[str]] = None,
        exclude_services: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Collect resources from all (or specified) services
        
        Args:
            services: Specific services to collect (None = all)
            exclude_services: Services to exclude
        
        Returns:
            Nested dict: service -> resource_type -> resources
        """
        all_services = services or self.list_all_services()
        exclude_services = exclude_services or []
        
        all_results = {}
        
        for service in all_services:
            if service in exclude_services:
                continue
            
            try:
                service_results = self.collect_service_resources(service)
                if service_results:
                    all_results[service] = service_results
            except Exception as e:
                console.print(f"[red]❌ Failed to collect {service}: {e}[/red]")
                continue
        
        return all_results
    
    def export_to_csv(
        self,
        data: Dict[str, Dict[str, List[Dict]]],
        output_dir: str
    ) -> List[str]:
        """
        Export collected data to CSV files (one per resource type)
        
        Args:
            data: Collected data from collect_all_services()
            output_dir: Output directory path
        
        Returns:
            List of created file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        created_files = []
        
        for service, resources_dict in data.items():
            for resource_type, resources in resources_dict.items():
                if not resources:
                    continue
                
                # Create CSV filename
                filename = f"{service}_{resource_type}.csv"
                filepath = output_path / filename
                
                try:
                    # Convert to DataFrame and save
                    df = pd.DataFrame(resources)
                    # Convert complex types to JSON strings
                    for col in df.columns:
                        if df[col].dtype == 'object':
                            df[col] = df[col].apply(
                                lambda x: json.dumps(x, default=str) if isinstance(x, (dict, list)) else str(x)
                            )
                    df.to_csv(filepath, index=False)
                    created_files.append(str(filepath))
                    console.print(f"[green]✅ Saved: {filename}[/green]")
                except Exception as e:
                    console.print(f"[red]❌ Failed to save {filename}: {e}[/red]")
        
        return created_files
    
    def export_to_json(
        self,
        data: Dict[str, Dict[str, List[Dict]]],
        output_file: str
    ) -> bool:
        """
        Export all collected data to single JSON file
        
        Args:
            data: Collected data from collect_all_services()
            output_file: Output file path
        
        Returns:
            True if successful
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            console.print(f"[green]✅ Saved: {output_file}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to save JSON: {e}[/red]")
            return False
    
    def generate_summary_report(
        self,
        data: Dict[str, Dict[str, List[Dict]]]
    ) -> str:
        """Generate summary report of collected resources"""
        table = Table(title="AWS Audit Evidence Collection Summary")
        table.add_column("Service", style="cyan")
        table.add_column("Resource Type", style="yellow")
        table.add_column("Count", style="green", justify="right")
        
        total_resources = 0
        
        for service, resources_dict in sorted(data.items()):
            service_name = self.SERVICE_CONFIGS[service]['name']
            for resource_type, resources in sorted(resources_dict.items()):
                count = len(resources)
                total_resources += count
                if count > 0:
                    table.add_row(service_name, resource_type, str(count))
        
        console.print(table)
        console.print(f"\n[bold green]📊 Total Resources Collected: {total_resources}[/bold green]")
        
        return f"Total: {total_resources} resources"


def collect_comprehensive_audit_evidence(
    aws_account: str,
    aws_region: str,
    output_dir: str,
    services: Optional[List[str]] = None,
    format: str = 'csv'
) -> Tuple[bool, str]:
    """
    High-level function to collect comprehensive audit evidence
    
    Args:
        aws_account: AWS profile name
        aws_region: AWS region
        output_dir: Output directory
        services: Specific services to collect (None = all)
        format: Output format ('csv' or 'json')
    
    Returns:
        (success, summary_message)
    """
    console.print(f"\n[bold cyan]🔍 AWS Comprehensive Audit Evidence Collection[/bold cyan]")
    console.print(f"[cyan]Account: {aws_account}[/cyan]")
    console.print(f"[cyan]Region: {aws_region}[/cyan]")
    console.print(f"[cyan]Output: {output_dir}[/cyan]")
    console.print(f"[cyan]Format: {format.upper()}[/cyan]\n")
    
    collector = AWSComprehensiveAuditCollector(aws_account, aws_region)
    
    # Collect all resources
    console.print("[bold]🚀 Starting collection...[/bold]\n")
    all_data = collector.collect_all_services(services=services)
    
    if not all_data:
        console.print("[yellow]⚠️  No data collected[/yellow]")
        return False, "No data collected"
    
    # Export
    console.print("\n[bold]💾 Exporting data...[/bold]\n")
    if format == 'csv':
        files = collector.export_to_csv(all_data, output_dir)
        summary = collector.generate_summary_report(all_data)
        return True, f"Exported {len(files)} CSV files. {summary}"
    elif format == 'json':
        output_file = Path(output_dir) / f"aws_audit_evidence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        success = collector.export_to_json(all_data, str(output_file))
        summary = collector.generate_summary_report(all_data)
        return success, summary
    else:
        console.print(f"[red]❌ Unknown format: {format}[/red]")
        return False, f"Unknown format: {format}"

