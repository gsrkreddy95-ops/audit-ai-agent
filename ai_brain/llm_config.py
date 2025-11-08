"""
Flexible LLM Configuration
Supports: OpenAI GPT-4, Anthropic Claude, AWS Bedrock, Azure OpenAI
"""

import os
from typing import Optional
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_aws import ChatBedrock
import boto3


class LLMFactory:
    """
    Factory to create LLM instances based on configuration
    Supports multiple providers with easy switching
    """
    
    @staticmethod
    def create_llm(provider: Optional[str] = None, **kwargs):
        """
        Create LLM instance based on provider
        
        Args:
            provider: 'openai', 'anthropic', 'bedrock', 'azure', or auto-detect
            **kwargs: Provider-specific configuration
        
        Returns:
            LangChain LLM instance
        """
        # Auto-detect provider from environment if not specified
        if not provider:
            provider = os.getenv('LLM_PROVIDER', 'openai').lower()
        
        if provider == 'openai':
            return LLMFactory._create_openai(**kwargs)
        elif provider == 'anthropic':
            return LLMFactory._create_anthropic(**kwargs)
        elif provider == 'bedrock':
            return LLMFactory._create_bedrock(**kwargs)
        elif provider == 'azure':
            return LLMFactory._create_azure(**kwargs)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def _create_openai(**kwargs):
        """Create OpenAI GPT-4 instance"""
        return ChatOpenAI(
            model=kwargs.get('model', os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')),
            temperature=kwargs.get('temperature', 0),
            api_key=kwargs.get('api_key', os.getenv('OPENAI_API_KEY')),
            max_tokens=kwargs.get('max_tokens', 4096)
        )
    
    @staticmethod
    def _create_anthropic(**kwargs):
        """Create Anthropic Claude instance"""
        return ChatAnthropic(
            model=kwargs.get('model', os.getenv('ANTHROPIC_MODEL', 'claude-3-opus-20240229')),
            temperature=kwargs.get('temperature', 0),
            anthropic_api_key=kwargs.get('api_key', os.getenv('ANTHROPIC_API_KEY')),
            max_tokens=kwargs.get('max_tokens', 4096)
        )
    
    @staticmethod
    def _create_bedrock(**kwargs):
        """
        Create AWS Bedrock instance
        Supports: Claude, Titan, Llama, etc.
        """
        # Default to Claude 3.5 Sonnet on Bedrock
        model_id = kwargs.get('model', os.getenv(
            'BEDROCK_MODEL_ID',
            'anthropic.claude-3-5-sonnet-20240229-v1:0'
        ))
        
        # Get region
        region = kwargs.get('region', os.getenv('BEDROCK_REGION', os.getenv('AWS_REGION', 'us-east-1')))
        
        return ChatBedrock(
            model_id=model_id,
            region_name=region,
            model_kwargs={
                'temperature': kwargs.get('temperature', 0),
                'max_tokens': kwargs.get('max_tokens', 4096)
            }
        )
    
    @staticmethod
    def _create_azure(**kwargs):
        """Create Azure OpenAI instance"""
        return AzureChatOpenAI(
            azure_deployment=kwargs.get('deployment', os.getenv('AZURE_OPENAI_DEPLOYMENT')),
            azure_endpoint=kwargs.get('endpoint', os.getenv('AZURE_OPENAI_ENDPOINT')),
            api_key=kwargs.get('api_key', os.getenv('AZURE_OPENAI_API_KEY')),
            api_version=kwargs.get('api_version', os.getenv('AZURE_OPENAI_API_VERSION', '2023-05-15')),
            temperature=kwargs.get('temperature', 0),
            max_tokens=kwargs.get('max_tokens', 4096)
        )
    
    @staticmethod
    def get_available_models() -> dict:
        """
        Return available models for each provider
        """
        return {
            'openai': [
                'gpt-4-turbo-preview',
                'gpt-4-1106-preview',
                'gpt-4',
                'gpt-3.5-turbo'
            ],
            'anthropic': [
                'claude-3-opus-20240229',
                'claude-3-sonnet-20240229',
                'claude-3-haiku-20240307',
                'claude-2.1',
                'claude-2.0'
            ],
            'bedrock': [
                'anthropic.claude-3-opus-20240229-v1:0',
                'anthropic.claude-3-sonnet-20240229-v1:0',
                'anthropic.claude-3-haiku-20240307-v1:0',
                'amazon.titan-text-express-v1',
                'meta.llama3-70b-instruct-v1:0'
            ],
            'azure': [
                'gpt-4',
                'gpt-4-32k',
                'gpt-35-turbo'
            ]
        }
    
    @staticmethod
    def validate_configuration(provider: str) -> tuple[bool, Optional[str]]:
        """
        Validate that required environment variables are set for provider
        Returns: (is_valid, error_message)
        """
        if provider == 'openai':
            if not os.getenv('OPENAI_API_KEY'):
                return False, "OPENAI_API_KEY not set"
        
        elif provider == 'anthropic':
            if not os.getenv('ANTHROPIC_API_KEY'):
                return False, "ANTHROPIC_API_KEY not set"
        
        elif provider == 'bedrock':
            # Bedrock uses AWS credentials (duo-sso)
            # Check for any of the region env vars
            if not (os.getenv('BEDROCK_REGION') or os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION')):
                return False, "AWS region not set (BEDROCK_REGION, AWS_REGION, or AWS_DEFAULT_REGION required)"
            # AWS credentials checked via duo-sso
        
        elif provider == 'azure':
            required = ['AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_DEPLOYMENT']
            missing = [key for key in required if not os.getenv(key)]
            if missing:
                return False, f"Missing Azure config: {', '.join(missing)}"
        
        else:
            return False, f"Unknown provider: {provider}"
        
        return True, None


# Example usage configurations for different providers
EXAMPLE_CONFIGS = {
    'openai': """
# OpenAI GPT-4 Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
""",
    
    'anthropic': """
# Anthropic Claude Configuration
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-opus-20240229
""",
    
    'bedrock': """
# AWS Bedrock Configuration (uses duo-sso for auth)
LLM_PROVIDER=bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-opus-20240229-v1:0
AWS_BEDROCK_REGION=us-east-1
# AWS credentials via duo-sso
""",
    
    'azure': """
# Azure OpenAI Configuration
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2023-05-15
"""
}

