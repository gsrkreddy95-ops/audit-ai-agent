"""Service Catalog - Minimal compatibility stub"""

class ServiceCatalog:
    def get_service(self, domain, service):
        return None
    
    def set_service(self, domain, service, metadata):
        pass
    
    def resolve_service_name(self, domain, service):
        return service
    
    def get_domain_default_regions(self, domain):
        if domain == "aws":
            return ["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1"]
        return None

