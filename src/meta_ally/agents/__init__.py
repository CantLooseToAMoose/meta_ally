"""
Pydantic AI Agents Module

This module provides factory classes and configurations for creating pydantic-ai agents
with specific tool groups and model configurations, including Azure OpenAI support.
"""

from .agent_factory import AgentConfiguration, AgentFactory
from .model_config import (
    AzureAuthMechanism,
    ModelConfiguration,
    create_azure_model_config,
)

__all__ = [
    # Agent factory and configuration
    "AgentConfiguration",
    "AgentFactory",

    # Model configuration and Azure support
    "AzureAuthMechanism",
    "ModelConfiguration",
    "create_azure_model_config",
]
