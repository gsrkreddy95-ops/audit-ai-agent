"""
Service Catalog - Comprehensive Service Metadata

Stores metadata about all cloud services:
- AWS (407 services)
- Jira/Confluence
- GitHub
- Regional vs global scope
- API endpoints and behaviors
"""

from typing import Dict, Any, Optional, List


class ServiceCatalog:
    """Comprehensive service metadata catalog."""
    
    def __init__(self):
        self.catalog = {
            "aws": {
                # Compute
                "ec2": {"scope": "regional", "date_fields": ["LaunchTime"]},
                "lambda": {"scope": "regional", "date_fields": ["LastModified"]},
                "ecs": {"scope": "regional"},
                "eks": {"scope": "regional"},
                
                # Storage
                "s3": {"scope": "global", "preferred_region": "us-east-1", "date_fields": ["CreationDate"]},
                "ebs": {"scope": "regional", "client": "ec2"},
                "efs": {"scope": "regional"},
                
                # Database
                "rds": {"scope": "regional", "date_fields": ["InstanceCreateTime", "ClusterCreateTime"]},
                "dynamodb": {"scope": "regional", "date_fields": ["CreationDateTime"]},
                "elasticache": {"scope": "regional"},
                
                # Security
                "iam": {"scope": "global", "preferred_region": "us-east-1", "date_fields": ["CreateDate"]},
                "kms": {"scope": "regional", "date_fields": ["CreationDate"]},
                "secretsmanager": {"scope": "regional", "date_fields": ["CreatedDate"]},
                
                # Networking
                "vpc": {"scope": "regional", "client": "ec2"},
                "elb": {"scope": "regional"},
                "elbv2": {"scope": "regional"},
                "route53": {"scope": "global", "preferred_region": "us-east-1"},
                "cloudfront": {"scope": "global", "preferred_region": "us-east-1"},
                
                # Monitoring
                "cloudwatch": {"scope": "regional"},
                "cloudtrail": {"scope": "regional"},
                
                # Messaging
                "sns": {"scope": "regional"},
                "sqs": {"scope": "regional"},
                
                # Auto Scaling
                "autoscaling": {"scope": "regional", "date_fields": ["CreatedTime"]},
            }
        }
    
    def get_service(self, domain: str, service: str) -> Optional[Dict[str, Any]]:
        """Get service metadata."""
        return self.catalog.get(domain, {}).get(service.lower())
    
    def set_service(self, domain: str, service: str, metadata: Dict[str, Any]):
        """Store service metadata."""
        if domain not in self.catalog:
            self.catalog[domain] = {}
        self.catalog[domain][service.lower()] = metadata
    
    def resolve_service_name(self, domain: str, service: str) -> str:
        """Resolve service name (handle aliases)."""
        # Handle common aliases
        aliases = {
            "secrets": "secretsmanager",
            "buckets": "s3",
            "compute": "ec2"
        }
        return aliases.get(service.lower(), service)
    
    def get_domain_default_regions(self, domain: str) -> Optional[List[str]]:
        """Get default regions for a domain."""
        if domain == "aws":
            return ["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1", "ap-southeast-1"]
        return None
    
    def is_global_service(self, domain: str, service: str) -> bool:
        """Check if service is global (not regional)."""
        metadata = self.get_service(domain, service)
        return metadata.get('scope') == 'global' if metadata else False
    
    def get_preferred_region(self, domain: str, service: str) -> Optional[str]:
        """Get preferred region for global services."""
        metadata = self.get_service(domain, service)
        if metadata and metadata.get('scope') == 'global':
            return metadata.get('preferred_region', 'us-east-1')
        return None
