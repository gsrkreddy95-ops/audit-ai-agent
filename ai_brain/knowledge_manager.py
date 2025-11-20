"""
Knowledge Manager - Persistent Learning and Real-Time Knowledge

The agent's knowledge base that stores:
- Learned facts from web searches
- Service behaviors (AWS regional/global, API patterns)
- Custom field mappings (Jira, Confluence)
- Error solutions that worked
- Best practices discovered

This enables the agent to become smarter over time and share knowledge
across sessions.
"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from rich.console import Console

console = Console()


class KnowledgeManager:
    """
    Manages the agent's persistent knowledge base.
    
    Knowledge is organized into domains:
    - aws: Service behaviors, regional info, API patterns
    - jira: Custom fields, board configs, query patterns
    - confluence: Space structures, page hierarchies
    - github: Repo patterns, API limits
    - general: Error solutions, best practices
    """
    
    def __init__(self, knowledge_file: Optional[str] = None):
        """
        Initialize knowledge manager.
        
        Args:
            knowledge_file: Path to JSON knowledge file (default: ./knowledge_base.json)
        """
        self.knowledge_file = knowledge_file or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'knowledge_base.json'
        )
        self.knowledge: Dict[str, Dict[str, Any]] = {}
        self._load_knowledge()
    
    def _load_knowledge(self) -> None:
        """Load knowledge from file if it exists."""
        if not os.path.exists(self.knowledge_file):
            self._initialize_base_knowledge()
            return
        
        try:
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                self.knowledge = json.load(f)
            console.print(f"[dim]📚 Loaded knowledge base ({len(self.knowledge)} domains)[/dim]")
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not load knowledge: {e}[/yellow]")
            self._initialize_base_knowledge()
    
    def _initialize_base_knowledge(self) -> None:
        """Initialize with base knowledge about AWS, Jira, etc."""
        self.knowledge = {
            "aws": {
                "global_services": ["s3", "iam", "cloudfront", "route53", "waf"],
                "regional_services": ["ec2", "rds", "kms", "secretsmanager", "lambda", "dynamodb", "ecs", "eks"],
                "service_behaviors": {
                    "s3": {
                        "type": "global",
                        "note": "S3 buckets are global; use any region or omit region parameter",
                        "default_date_field": "CreationDate"
                    },
                    "kms": {
                        "type": "regional",
                        "note": "KMS keys are regional; must specify region",
                        "default_date_field": "CreationDate"
                    },
                    "secretsmanager": {
                        "type": "regional",
                        "note": "Secrets are regional",
                        "default_date_field": "CreatedDate"
                    },
                    "ec2": {
                        "type": "regional",
                        "note": "EC2 resources are regional",
                        "default_date_field": "LaunchTime"
                    }
                },
                "default_regions": ["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1", "ap-southeast-1"]
            },
            "jira": {
                "custom_fields": {},
                "board_filters": {},
                "query_patterns": {}
            },
            "confluence": {
                "space_configs": {}
            },
            "github": {
                "rate_limits": {
                    "search": "10 requests per minute",
                    "core": "5000 requests per hour"
                }
            },
            "general": {
                "error_solutions": {},
                "best_practices": {}
            },
            "meta": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        }
        self._save_knowledge()
    
    def _save_knowledge(self) -> None:
        """Persist knowledge to file."""
        try:
            self.knowledge["meta"]["last_updated"] = datetime.now().isoformat()
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge, f, indent=2, ensure_ascii=False)
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not save knowledge: {e}[/yellow]")
    
    def get(self, domain: str, key: str, default: Any = None) -> Any:
        """
        Get knowledge from a specific domain.
        
        Args:
            domain: Domain name (aws, jira, confluence, etc.)
            key: Knowledge key within domain
            default: Default value if not found
            
        Returns:
            Knowledge value or default
        """
        return self.knowledge.get(domain, {}).get(key, default)
    
    def set(self, domain: str, key: str, value: Any) -> None:
        """
        Store knowledge in a domain.
        
        Args:
            domain: Domain name
            key: Knowledge key
            value: Value to store
        """
        if domain not in self.knowledge:
            self.knowledge[domain] = {}
        
        self.knowledge[domain][key] = value
        self._save_knowledge()
    
    def learn(
        self,
        domain: str,
        fact_key: str,
        fact_value: Any,
        source: str = "agent_experience",
        confidence: float = 1.0
    ) -> None:
        """
        Add a learned fact to the knowledge base.
        
        Args:
            domain: Domain (aws, jira, etc.)
            fact_key: Unique key for this fact
            fact_value: The learned information
            source: Where this came from (web_search, api_response, etc.)
            confidence: How confident we are (0.0-1.0)
        """
        if domain not in self.knowledge:
            self.knowledge[domain] = {}
        
        if "learned_facts" not in self.knowledge[domain]:
            self.knowledge[domain]["learned_facts"] = {}
        
        self.knowledge[domain]["learned_facts"][fact_key] = {
            "value": fact_value,
            "source": source,
            "confidence": confidence,
            "learned_at": datetime.now().isoformat()
        }
        
        console.print(f"[green]✅ Learned: {domain}.{fact_key}[/green]")
        self._save_knowledge()
    
    def query(self, domain: str, question: str) -> Optional[Any]:
        """
        Query knowledge base for an answer.
        
        Args:
            domain: Domain to search in
            question: Question in natural language
            
        Returns:
            Answer if found, None otherwise
        """
        # Simple keyword matching for now
        # Can be enhanced with semantic search later
        domain_data = self.knowledge.get(domain, {})
        
        question_lower = question.lower()
        
        # Check learned facts
        learned = domain_data.get("learned_facts", {})
        for key, fact in learned.items():
            if key.lower() in question_lower or question_lower in key.lower():
                return fact.get("value")
        
        # Check domain-specific keys
        for key, value in domain_data.items():
            if key != "learned_facts" and isinstance(key, str):
                if key.lower() in question_lower:
                    return value
        
        return None
    
    def is_aws_service_global(self, service: str) -> Optional[bool]:
        """
        Check if an AWS service is global or regional.
        
        Args:
            service: Service name (s3, ec2, kms, etc.)
            
        Returns:
            True if global, False if regional, None if unknown
        """
        service = service.lower().strip()
        
        global_services = self.knowledge.get("aws", {}).get("global_services", [])
        if service in global_services:
            return True
        
        regional_services = self.knowledge.get("aws", {}).get("regional_services", [])
        if service in regional_services:
            return False
        
        # Check learned facts
        learned = self.knowledge.get("aws", {}).get("learned_facts", {})
        fact = learned.get(f"{service}_is_global")
        if fact:
            return fact.get("value")
        
        return None
    
    def get_aws_default_regions(self) -> List[str]:
        """Get default AWS regions to use when 'all' is specified."""
        return self.knowledge.get("aws", {}).get("default_regions", ["us-east-1"])
    
    def get_aws_service_metadata(self, service: str) -> Dict[str, Any]:
        """
        Get metadata about an AWS service.
        
        Returns:
            {
                "type": "global" | "regional",
                "note": str,
                "default_date_field": str,
                ...
            }
        """
        behaviors = self.knowledge.get("aws", {}).get("service_behaviors", {})
        return behaviors.get(service.lower(), {})
    
    def add_error_solution(
        self,
        error_pattern: str,
        solution: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store a solution for a specific error pattern.
        
        Args:
            error_pattern: Error message pattern
            solution: How to fix it
            context: Additional context (tool, service, etc.)
        """
        if "general" not in self.knowledge:
            self.knowledge["general"] = {}
        
        if "error_solutions" not in self.knowledge["general"]:
            self.knowledge["general"]["error_solutions"] = {}
        
        self.knowledge["general"]["error_solutions"][error_pattern] = {
            "solution": solution,
            "context": context or {},
            "added_at": datetime.now().isoformat()
        }
        
        console.print(f"[green]✅ Stored solution for: {error_pattern}[/green]")
        self._save_knowledge()
    
    def find_error_solution(self, error_message: str) -> Optional[Dict[str, Any]]:
        """
        Find a stored solution for an error.
        
        Args:
            error_message: The error message
            
        Returns:
            Solution dict if found, None otherwise
        """
        solutions = self.knowledge.get("general", {}).get("error_solutions", {})
        
        error_lower = error_message.lower()
        
        # Exact match first
        if error_message in solutions:
            return solutions[error_message]
        
        # Partial match
        for pattern, solution in solutions.items():
            if pattern.lower() in error_lower or error_lower in pattern.lower():
                return solution
        
        return None
    
    def export_knowledge(self, output_file: Optional[str] = None) -> str:
        """
        Export knowledge base to JSON file.
        
        Args:
            output_file: Where to save (default: knowledge_export_{timestamp}.json)
            
        Returns:
            Path to exported file
        """
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"knowledge_export_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green]✅ Knowledge exported to: {output_file}[/green]")
        return output_file


# Global instance
_knowledge_manager = None

def get_knowledge_manager() -> KnowledgeManager:
    """Get or create global knowledge manager instance."""
    global _knowledge_manager
    if _knowledge_manager is None:
        _knowledge_manager = KnowledgeManager()
    return _knowledge_manager

