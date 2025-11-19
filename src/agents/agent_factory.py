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
from ..util.context_tools import get_context_tools
from ..lib.auth_manager import AuthManager
from ..lib.openapi_to_tools import OpenAPIToolDependencies
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
    """
    Factory for creating pydantic-ai agents with specific tool groups and configurations.
    
    This factory manages the creation of agents that use OpenAPI-based tools with authentication.
    All agents created by this factory require dependencies to run, which include authentication
    management for API calls.
    
    Example usage:
        ```python
        # Create factory with AuthManager
        factory = AgentFactory()
        
        # Setup tools
        factory.setup_ai_knowledge_tools()
        factory.setup_ally_config_tools()
        
        # Create agent
        agent = factory.create_hybrid_assistant()
        
        # Create dependencies and refresh token for authentication
        deps = factory.create_dependencies()
        deps.auth_manager._refresh_token()  # IMPORTANT: Triggers browser auth flow
        
        # Run agent with dependencies
        result = agent.run_sync("Your question", deps=deps)
        ```
    
    Note: The auth_manager._refresh_token() call is essential before running agents as it
    initiates the browser-based authentication process required for API access.
    """
    
    def __init__(
        self, 
        auth_manager: Optional[AuthManager] = None,
        keycloak_url: str = "https://keycloak.acc.iam-services.aws.inform-cloud.io/",
        realm_name: str = "inform-ai",
        client_id: str = "ally-portal-frontend-dev",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the AgentFactory
        
        Args:
            auth_manager: Optional AuthManager instance. If not provided, one will be created
            keycloak_url: Keycloak URL for authentication (used if auth_manager not provided)
            realm_name: Keycloak realm name (used if auth_manager not provided)
            client_id: Client ID for authentication (used if auth_manager not provided)
            logger: Optional logger instance
        """
        if auth_manager is None:
            auth_manager = AuthManager(
                keycloak_url=keycloak_url,
                realm_name=realm_name,
                client_id=client_id
            )
        
        self.auth_manager = auth_manager
        self.tool_manager = ToolGroupManager(auth_manager)
        self.logger = logger or logging.getLogger(__name__)
        
    def setup_ai_knowledge_tools(
        self, 
        openapi_url: str = "https://backend-api.dev.ai-knowledge.aws.inform-cloud.io/openapi.json",
        models_filename: str = "ai_knowledge_api_models.py",
        regenerate_models: bool = True,
        require_human_approval: bool = False
    ) -> None:
        """Setup AI Knowledge tools with custom configuration"""
        self.tool_manager.load_ai_knowledge_tools(
            openapi_url=openapi_url,
            models_filename=models_filename,
            regenerate_models=regenerate_models,
            require_human_approval=require_human_approval
        )
        
    def setup_ally_config_tools(
        self,
        openapi_url: str = "https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        models_filename: str = "ally_config_api_models.py",
        regenerate_models: bool = True,
        require_human_approval: bool = False
    ) -> None:
        """Setup Ally Config tools with custom configuration"""
        self.tool_manager.load_ally_config_tools(
            openapi_url=openapi_url,
            models_filename=models_filename,
            regenerate_models=regenerate_models,
            require_human_approval=require_human_approval
        )
    
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
        include_context_tools: bool = True,
        **agent_kwargs
    ) -> Agent[OpenAPIToolDependencies]:
        """
        Create a pydantic-ai agent with specified configuration.
        
        Args:
            name: Name of the agent
            system_prompt: System prompt for the agent
            tool_groups: List of tool groups to include
            model: Model to use (string or ModelConfiguration)
            additional_instructions: Optional additional instructions
            max_retries: Maximum number of retries for failed operations
            include_context_tools: Whether to include context management tools (default: True)
            **agent_kwargs: Additional keyword arguments for Agent
            
        Returns:
            Configured Agent instance
        """
        
        # Get tools for the specified groups
        tools = self.tool_manager.get_tools_for_groups(tool_groups)
        
        # Add context management tools if requested
        if include_context_tools:
            context_tools = get_context_tools()
            tools.extend(context_tools)
            self.logger.info("Added %d context management tools to agent '%s'", len(context_tools), name)
        
        # Build the complete system prompt
        complete_prompt = system_prompt
        if additional_instructions:
            complete_prompt += f"\n\nAdditional Instructions:\n{additional_instructions}"
        
        # Add context management instructions to system prompt
        if include_context_tools:
            complete_prompt += """

Context Management:
You have access to tools for tracking user context information:
- Business Area (Geschäftsbereich): The user's business domain or department
- Project Number: The project the user is working on
- Endpoint Name: The specific endpoint configuration being discussed

When the user mentions any of these, use the appropriate set_* tool to remember it.
Before performing operations that require this context, use the get_* tools to check if the information is available.
If required information is missing, the get_* tool will return a message asking you to gather it from the user.
"""
        
        # Resolve model configuration
        resolved_model = self._resolve_model(model)
            
        # Create and configure the agent with dependencies
        agent = Agent(
            resolved_model,
            deps_type=OpenAPIToolDependencies,
            instructions=complete_prompt,
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
        include_context_tools: bool = True,
        **agent_kwargs
    ) -> Agent[OpenAPIToolDependencies]:
        """Create an AI Knowledge specialist agent"""
        if tool_groups is None:
            tool_groups = [AIKnowledgeToolGroup.ALL]
            
        return self.create_agent(
            name="ai_knowledge_specialist",
            system_prompt=SystemPrompts.AI_KNOWLEDGE_SPECIALIST,
            tool_groups=tool_groups,  # type: ignore
            model=model,
            additional_instructions=additional_instructions,
            include_context_tools=include_context_tools,
            **agent_kwargs
        )
        
    def create_ally_config_admin(
        self,
        tool_groups: Optional[List[AllyConfigToolGroup]] = None,
        model: Union[str, ModelConfiguration] = "openai:gpt-4o",
        additional_instructions: Optional[str] = None,
        include_context_tools: bool = True,
        **agent_kwargs
    ) -> Agent[OpenAPIToolDependencies]:
        """Create an Ally Config administrator agent"""
        if tool_groups is None:
            tool_groups = [AllyConfigToolGroup.ALL]
            
        return self.create_agent(
            name="ally_config_admin",
            system_prompt=SystemPrompts.ALLY_CONFIG_ADMIN,
            tool_groups=tool_groups,  # type: ignore
            model=model,
            additional_instructions=additional_instructions,
            include_context_tools=include_context_tools,
            **agent_kwargs
        )
        
    def create_hybrid_assistant(
        self,
        ai_knowledge_groups: Optional[List[AIKnowledgeToolGroup]] = None,
        ally_config_groups: Optional[List[AllyConfigToolGroup]] = None,
        model: Union[str, ModelConfiguration] = "openai:gpt-4o",
        additional_instructions: Optional[str] = None,
        include_context_tools: bool = True,
        **agent_kwargs
    ) -> Agent[OpenAPIToolDependencies]:
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
            include_context_tools=include_context_tools,
            **agent_kwargs
        )
        
    def create_dependencies(self) -> OpenAPIToolDependencies:
        """
        Create dependencies for running agents with OpenAPI tools.
        
        IMPORTANT: After creating dependencies, you must call deps.auth_manager._refresh_token()
        to initiate the browser-based authentication flow before running any agents.
        
        Example:
            ```python
            deps = factory.create_dependencies()
            deps.auth_manager._refresh_token()  # Opens browser for authentication
            result = agent.run_sync("question", deps=deps)
            ```
        
        Returns:
            OpenAPIToolDependencies instance with the configured AuthManager
        """
        return OpenAPIToolDependencies(auth_manager=self.auth_manager)
        
        
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