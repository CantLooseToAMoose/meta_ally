"""
Pydantic AI Agents Module

This module provides factory classes and configurations for creating pydantic-ai agents
with specific tool groups and model configurations, including Azure OpenAI support.
"""

from .agent_factory import AgentFactory, AgentConfiguration
from .model_config import (
    ModelConfiguration,
    AzureAuthMechanism,
    create_azure_model_config,
)

__all__ = [
    # Agent factory and configuration
    "AgentFactory",
    "AgentConfiguration",
    
    # Model configuration and Azure support
    "ModelConfiguration",
    "AzureAuthMechanism", 
    "create_azure_model_config",
]
