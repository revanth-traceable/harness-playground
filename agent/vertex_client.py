"""
Anthropic Vertex AI client for AutoGen.
Wraps AnthropicVertex to work with AutoGen's model client interface.
"""
import os
from typing import Any, Dict, Optional, Sequence
from anthropic import AsyncAnthropicVertex

from autogen_core import CancellationToken
from autogen_core.models import (
    CreateResult,
    LLMMessage,
    RequestUsage,
)
from autogen_core.tools import Tool, ToolSchema
from autogen_ext.models.anthropic import BaseAnthropicChatCompletionClient


class AnthropicVertexChatCompletionClient(BaseAnthropicChatCompletionClient):
    """
    Chat completion client for Anthropic's Claude models via Vertex AI.
    
    Args:
        model: The Claude model to use (e.g., "claude-sonnet-4-5@20250929")
        project_id: GCP project ID
        region: GCP region (e.g., "us-east5")
        max_tokens: Maximum tokens in the response (default: 4096)
        temperature: Controls randomness (default: 0.1)
        credentials_path: Optional path to service account JSON file
    """
    
    def __init__(
        self,
        model: str,
        project_id: str,
        region: str = "us-east5",
        max_tokens: int = 4096,
        temperature: float = 0.1,
        credentials_path: Optional[str] = None,
        **kwargs
    ):
        # Store config for serialization
        self._raw_config = {
            "model": model,
            "project_id": project_id,
            "region": region,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "credentials_path": credentials_path,
            **kwargs
        }
        
        # Set up credentials if provided
        credentials = None
        creds_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if creds_path and os.path.exists(creds_path):
            try:
                from google.oauth2 import service_account
                import google.auth.transport.requests
                
                print(f"🔐 Using credentials from: {creds_path}")
                
                credentials = service_account.Credentials.from_service_account_file(
                    creds_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                ).with_quota_project(project_id)
                
                # Refresh token
                try:
                    request = google.auth.transport.requests.Request()
                    credentials.refresh(request)
                except Exception as e:
                    print(f"⚠️  Warning: Could not refresh token: {e}")
                    
            except Exception as e:
                print(f"⚠️  Warning: Could not load credentials: {e}")
                credentials = None
        else:
            print("🔐 Using application default credentials")
        
        # Create Vertex AI client
        vertex_kwargs = {
            "project_id": project_id,
            "region": region,
        }
        
        if credentials:
            vertex_kwargs["credentials"] = credentials
        
        client = AsyncAnthropicVertex(**vertex_kwargs)
        
        # Create arguments for API calls
        create_args = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Initialize parent class
        super().__init__(
            client=client,
            create_args=create_args,
        )
        
        print(f"✅ Vertex AI client initialized: {model} in {region}")


def create_vertex_client(
    model: str = None,
    project_id: str = None,
    region: str = None,
    max_tokens: int = 4096,
    temperature: float = 0.1,
    credentials_path: str = None,
) -> AnthropicVertexChatCompletionClient:
    """
    Factory function to create a Vertex AI client with environment variable defaults.
    
    Args:
        model: Model name (default: ANTHROPIC_VERTEX_MODEL env var)
        project_id: GCP project ID (default: ANTHROPIC_VERTEX_GCP_PROJECT_ID env var)
        region: GCP region (default: ANTHROPIC_VERTEX_GCP_REGION env var)
        max_tokens: Maximum tokens (default: 4096)
        temperature: Temperature (default: 0.1)
        credentials_path: Path to service account JSON (default: GOOGLE_APPLICATION_CREDENTIALS env var)
    
    Returns:
        AnthropicVertexChatCompletionClient instance
    """
    model = model or os.getenv("ANTHROPIC_VERTEX_MODEL", "claude-sonnet-4-5@20250929")
    project_id = project_id or os.getenv("ANTHROPIC_VERTEX_GCP_PROJECT_ID")
    region = region or os.getenv("ANTHROPIC_VERTEX_GCP_REGION", "us-east5")
    credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not project_id:
        raise ValueError(
            "project_id is required. Set ANTHROPIC_VERTEX_GCP_PROJECT_ID environment variable."
        )
    
    return AnthropicVertexChatCompletionClient(
        model=model,
        project_id=project_id,
        region=region,
        max_tokens=max_tokens,
        temperature=temperature,
        credentials_path=credentials_path,
    )