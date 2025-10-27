#!/usr/bin/env python3
"""
Pydantic AI Agent Factory

A comprehensive factory for creating pydantic-ai agents with specific tool groups and system prompts.
Based on the tool categorization patterns found in the AI Knowledge and Ally Config notebooks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Union
import logging

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

from ..util.system_prompts import SystemPrompts
from ..util.tool_group_manager import (
    ToolGroupManager, 
    AIKnowledgeToolGroup, 
    AllyConfigToolGroup, 
    ToolGroupType
)
from .model_config import ModelConfiguration


@dataclass
class AgentConfiguration:
    """Configuration for creating an agent"""
    name: str
    system_prompt: str
    tool_groups: List[ToolGroupType]
    model: Optional[Union[str, ModelConfiguration]] = None
    additional_instructions: Optional[str] = None
    max_retries: int = 3


class AgentFactory:
    """Factory for creating pydantic-ai agents with specific tool groups and configurations"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.tool_manager = ToolGroupManager()
        self.logger = logger or logging.getLogger(__name__)
        
    def setup_ai_knowledge_tools(self, **kwargs) -> None:
        """Setup AI Knowledge tools with custom configuration"""
        self.tool_manager.load_ai_knowledge_tools(**kwargs)
        
    def setup_ally_config_tools(self, **kwargs) -> None:
        """Setup Ally Config tools with custom configuration"""
        self.tool_manager.load_ally_config_tools(**kwargs)
    
    def _resolve_model(self, model: Union[str, ModelConfiguration]) -> Union[str, OpenAIChatModel]:
        """
        Resolve model specification to either a string or configured OpenAIChatModel.
        
        Parameters
        ----------
        model : Union[str, ModelConfiguration]
            Model specification - either a model string or ModelConfiguration.
            
        Returns
        -------
        Union[str, OpenAIChatModel]
            Resolved model for pydantic-ai Agent.
        """
        if isinstance(model, ModelConfiguration):
            return model.create_model()
        return model
        
    def create_agent(
        self,
        name: str,
        system_prompt: str,
        tool_groups: List[ToolGroupType],
        model: Union[str, ModelConfiguration] = "openai:gpt-4o",
        additional_instructions: Optional[str] = None,
        max_retries: int = 3,
        **agent_kwargs
    ) -> Agent:
        """Create a pydantic-ai agent with specified configuration"""
        
        # Get tools for the specified groups
        tools = self.tool_manager.get_tools_for_groups(tool_groups)
        
        # Build the complete system prompt
        complete_prompt = system_prompt
        if additional_instructions:
            complete_prompt += f"\n\nAdditional Instructions:\n{additional_instructions}"
        
        # Resolve model configuration
        resolved_model = self._resolve_model(model)
            
        # Create and configure the agent
        agent = Agent(
            resolved_model,
            system_prompt=complete_prompt,
            tools=tools,
            retries=max_retries,
            name=name,
            **agent_kwargs
        )
        
        self.logger.info("Created agent '%s' with %d tools", name, len(tools))
        
        return agent
        
    def create_ai_knowledge_specialist(
        self,
        tool_groups: Optional[List[AIKnowledgeToolGroup]] = None,
        model: Union[str, ModelConfiguration] = "openai:gpt-4o",
        additional_instructions: Optional[str] = None,
        **agent_kwargs
    ) -> Agent:
        """Create an AI Knowledge specialist agent"""
        if tool_groups is None:
            tool_groups = [AIKnowledgeToolGroup.ALL]
            
        return self.create_agent(
            name="ai_knowledge_specialist",
            system_prompt=SystemPrompts.AI_KNOWLEDGE_SPECIALIST,
            tool_groups=tool_groups,  # type: ignore
            model=model,
            additional_instructions=additional_instructions,
            **agent_kwargs
        )
        
    def create_ally_config_admin(
        self,
        tool_groups: Optional[List[AllyConfigToolGroup]] = None,
        model: Union[str, ModelConfiguration] = "openai:gpt-4o",
        additional_instructions: Optional[str] = None,
        **agent_kwargs
    ) -> Agent:
        """Create an Ally Config administrator agent"""
        if tool_groups is None:
            tool_groups = [AllyConfigToolGroup.ALL]
            
        return self.create_agent(
            name="ally_config_admin",
            system_prompt=SystemPrompts.ALLY_CONFIG_ADMIN,
            tool_groups=tool_groups,  # type: ignore
            model=model,
            additional_instructions=additional_instructions,
            **agent_kwargs
        )
        
    def create_hybrid_assistant(
        self,
        ai_knowledge_groups: Optional[List[AIKnowledgeToolGroup]] = None,
        ally_config_groups: Optional[List[AllyConfigToolGroup]] = None,
        model: Union[str, ModelConfiguration] = "openai:gpt-4o",
        additional_instructions: Optional[str] = None,
        **agent_kwargs
    ) -> Agent:
        """Create a hybrid agent with both AI Knowledge and Ally Config capabilities"""
        all_groups = []
        
        if ai_knowledge_groups:
            all_groups.extend(ai_knowledge_groups)
        if ally_config_groups:
            all_groups.extend(ally_config_groups)
            
        if not all_groups:
            all_groups = [AIKnowledgeToolGroup.ALL, AllyConfigToolGroup.ALL]
            
        return self.create_agent(
            name="hybrid_ai_assistant",
            system_prompt=SystemPrompts.HYBRID_AI_ASSISTANT,
            tool_groups=all_groups,
            model=model,
            additional_instructions=additional_instructions,
            **agent_kwargs
        )
        
        
    def get_available_groups(self) -> Dict[str, Dict[str, List[str]]]:
        """Get information about available tool groups"""
        return self.tool_manager.get_available_groups()
    
    def create_azure_model_config(
        self,
        deployment_name: str="gpt-4.1-mini",
        endpoint: str = "https://ally-frcentral.openai.azure.com/",
        azure_auth_mechanism: str = "auto",
        api_version: Optional[str] = None,
        temperature: float = 0.0,
    ) -> ModelConfiguration:
        """
        Convenience method to create Azure model configuration.
        
        Parameters
        ----------
        deployment_name : str
            The name of the model deployment in Azure OpenAI.
        endpoint : str
            The endpoint URL for the Azure OpenAI service.
        azure_auth_mechanism : str, optional
            The authentication mechanism to use ('auto', 'api-key', 'active_directory').
        api_version : str, optional
            The API version to use.
        temperature : float, optional
            The temperature setting for the model.
            
        Returns
        -------
        ModelConfiguration
            Configured ModelConfiguration instance for Azure OpenAI.
        """
        from .model_config import create_azure_model_config
        return create_azure_model_config(
            deployment_name=deployment_name,
            endpoint=endpoint,
            azure_auth_mechanism=azure_auth_mechanism,
            api_version=api_version,
            temperature=temperature,
            logger=self.logger,
        )