#!/usr/bin/env python3
"""
Pydantic AI Agent Factory

A comprehensive factory for creating pydantic-ai agents with specific tool groups and system prompts.
Based on the tool categorization patterns found in the AI Knowledge and Ally Config notebooks.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

from ..lib.auth_manager import AuthManager
from ..lib.openapi_to_tools import OpenAPIToolDependencies
from ..util.context_tools import get_context_tools
from ..util.system_prompts import SystemPrompts
from ..util.tool_group_manager import (
    AIKnowledgeToolGroup,
    AllyConfigToolGroup,
    ToolGroupManager,
    ToolGroupType,
)
from .model_config import (
    ModelConfiguration,
    create_azure_model_config,
)


@dataclass
class AgentConfiguration:
    """Configuration for creating an agent"""
    name: str
    system_prompt: str
    tool_groups: list[ToolGroupType]
    model: str | ModelConfiguration | None = None
    additional_instructions: str | None = None
    max_retries: int = 3


class AgentFactory:
    """
    Factory for creating pydantic-ai agents with specific tool groups and configurations.

    This factory manages the creation of agents that use OpenAPI-based tools with authentication.
    All agents created by this factory require dependencies to run, which include authentication
    management for API calls.

    Example usage:
        ```python
        # Create factory
        factory = AgentFactory()

        # Create agent (tools are loaded automatically)
        agent = factory.create_hybrid_assistant()

        # Create dependencies and refresh token for authentication
        deps = factory.create_dependencies()
        deps.auth_manager._refresh_token()  # IMPORTANT: Triggers browser auth flow

        # Run agent with dependencies
        result = agent.run_sync("Your question", deps=deps)
        ```

    Advanced usage (custom model configuration):
        ```python
        from meta_ally.agents import AgentFactory
        from meta_ally.agents.model_config import create_azure_model_config

        # Create custom model configuration
        model_config = create_azure_model_config(
            deployment_name="gpt-4o",
            endpoint="https://ally-frcentral.openai.azure.com/",
            temperature=0.5
        )

        # Create agent with custom model
        factory = AgentFactory()
        agent = factory.create_hybrid_assistant(model=model_config)
        ```

    Advanced usage (custom tool configuration):
        ```python
        # If you need custom tool configuration, you can still call setup methods manually
        factory = AgentFactory()
        factory.setup_ai_knowledge_tools(regenerate_models=False)  # Custom config
        agent = factory.create_ai_knowledge_specialist()
        ```

    """

    def __init__(
        self,
        auth_manager: AuthManager | None = None,
        keycloak_url: str = "https://keycloak.acc.iam-services.aws.inform-cloud.io/",
        realm_name: str = "inform-ai",
        client_id: str = "ally-portal-frontend-dev",
        logger: logging.Logger | None = None,
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
        require_human_approval: bool = False,
        approval_callback: Callable | None = None,
    ) -> None:
        """Setup AI Knowledge tools with custom configuration"""
        self.tool_manager.load_ai_knowledge_tools(
            openapi_url=openapi_url,
            models_filename=models_filename,
            regenerate_models=regenerate_models,
            require_human_approval=require_human_approval,
            approval_callback=approval_callback
        )

    def setup_ally_config_tools(
        self,
        openapi_url: str = "https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        models_filename: str = "ally_config_api_models.py",
        regenerate_models: bool = True,
        require_human_approval: bool = False,
        approval_callback: Callable | None = None,
    ) -> None:
        """Setup Ally Config tools with custom configuration"""
        self.tool_manager.load_ally_config_tools(
            openapi_url=openapi_url,
            models_filename=models_filename,
            regenerate_models=regenerate_models,
            require_human_approval=require_human_approval,
            approval_callback=approval_callback
        )

    def _ensure_tools_loaded(
        self,
        tool_groups: list[ToolGroupType],
        require_human_approval: bool = False,
        approval_callback: Callable | None = None
    ) -> None:
        """
        Automatically load tools if they haven't been loaded yet.
        This makes the API more user-friendly by removing the need for explicit setup calls.

        Args:
            tool_groups: List of tool groups that will be used
            require_human_approval: Whether to require human approval for non-read-only operations
            approval_callback: Optional callback for human approval
        """
        # Check if we need AI Knowledge tools
        needs_ai_knowledge = any(isinstance(g, AIKnowledgeToolGroup) for g in tool_groups)
        if needs_ai_knowledge and not self.tool_manager._ai_knowledge_tools:  # noqa: SLF001
            self.logger.info("Auto-loading AI Knowledge tools...")
            self.setup_ai_knowledge_tools(
                require_human_approval=require_human_approval,
                approval_callback=approval_callback
            )

        # Check if we need Ally Config tools
        needs_ally_config = any(isinstance(g, AllyConfigToolGroup) for g in tool_groups)
        if needs_ally_config and not self.tool_manager._ally_config_tools:  # noqa: SLF001
            self.logger.info("Auto-loading Ally Config tools...")
            self.setup_ally_config_tools(
                require_human_approval=require_human_approval,
                approval_callback=approval_callback
            )

    def _resolve_model(self, model: str | ModelConfiguration) -> str | OpenAIChatModel:
        """
        Resolve model specification to either a string or configured OpenAIChatModel.

        Parameters
        ----------
        model : str | ModelConfiguration
            Model specification - either a model string or ModelConfiguration.

        Returns
        -------
        str | OpenAIChatModel
            Resolved model for pydantic-ai Agent.
        """
        if isinstance(model, ModelConfiguration):
            return model.create_model()
        return model

    def create_agent(  # noqa: PLR0913, PLR0917
        self,
        name: str,
        system_prompt: str,
        tool_groups: list[ToolGroupType],
        model: str | ModelConfiguration = "openai:gpt-4o",
        additional_instructions: str | None = None,
        max_retries: int = 3,
        include_context_tools: bool = True,
        require_human_approval: bool = False,
        approval_callback: Callable | None = None,
        tool_replacements: dict[str, Callable] | None = None,
        **agent_kwargs,
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
            require_human_approval: Whether to require human approval for non-read-only operations
            approval_callback: Optional callback for human approval
            tool_replacements: Optional dict mapping operation IDs to mock functions for testing
            **agent_kwargs: Additional keyword arguments for Agent

        Returns:
            Configured Agent instance
        """
        # Automatically load tools if needed
        self._ensure_tools_loaded(
            tool_groups,
            require_human_approval=require_human_approval,
            approval_callback=approval_callback
        )

        # Apply tool replacements to the tool manager if provided
        # This modifies the tool objects in-place to use mock functions
        if tool_replacements:
            print(f"\n[Mock API] Applying {len(tool_replacements)} tool replacement(s)...")
            self.tool_manager.apply_tool_replacements(tool_replacements)

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

        # Add current date and time information
        now = datetime.now(ZoneInfo("Europe/Berlin"))
        date_time_info = f"""

Current Date and Time:
- Date: {now.strftime('%A, %B %d, %Y')}
- Time: {now.strftime('%H:%M:%S')} (Europe/Berlin timezone)
- ISO Format: {now.isoformat()}

Use this information when the user asks about current dates, times, or when time-based context is relevant.
"""
        complete_prompt += date_time_info

        # Add context management instructions to system prompt
        if include_context_tools:
            complete_prompt += """

        Context Management:
        You have access to tools for tracking user context information:
        - Business Area (Geschäftsbereich): The user's business domain or department
        - Project Number: The project the user is working on
        - Endpoint Name: The specific endpoint configuration being discussed

        When the user mentions any of these, use the appropriate set_* tool to remember it.
        Before performing operations that require this context, use the get_* tools to check
        if the information is available.
        If required information is missing, the get_* tool will return a message asking you
        to gather it from the user.
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
        tool_groups: list[AIKnowledgeToolGroup] | None = None,
        model: str | ModelConfiguration | None = None,
        additional_instructions: str | None = None,
        include_context_tools: bool = True,
        require_human_approval: bool = False,
        approval_callback: Callable | None = None,
        tool_replacements: dict[str, Callable] | None = None,
        **agent_kwargs,
    ) -> Agent[OpenAPIToolDependencies]:
        """
        Create an AI Knowledge specialist agent.

        Args:
            tool_groups: Optional list of AI Knowledge tool groups (defaults to ALL)
            model: Model to use. If None, creates Azure GPT-4.1-mini model automatically
            additional_instructions: Optional additional instructions
            include_context_tools: Whether to include context management tools
            require_human_approval: Whether to require human approval for non-read-only operations
            approval_callback: Optional callback for human approval
            tool_replacements: Optional dict mapping operation IDs to mock functions for testing
            **agent_kwargs: Additional arguments for Agent

        Returns:
            Configured AI Knowledge specialist agent
        """
        if tool_groups is None:
            tool_groups = [AIKnowledgeToolGroup.ALL]

        # Auto-create Azure model config if no model specified
        if model is None:
            self.logger.info("No model specified, creating default Azure GPT-4.1-mini configuration")
            model = create_azure_model_config(
                deployment_name="gpt-4.1-mini",
                endpoint="https://ally-frcentral.openai.azure.com/",
                logger=self.logger,
            )

        return self.create_agent(
            name="ai_knowledge_specialist",
            system_prompt=SystemPrompts.AI_KNOWLEDGE_SPECIALIST,
            tool_groups=tool_groups,  # type: ignore
            model=model,
            additional_instructions=additional_instructions,
            include_context_tools=include_context_tools,
            require_human_approval=require_human_approval,
            approval_callback=approval_callback,
            tool_replacements=tool_replacements,
            **agent_kwargs
        )

    def create_ally_config_admin(
        self,
        tool_groups: list[AllyConfigToolGroup] | None = None,
        model: str | ModelConfiguration | None = None,
        additional_instructions: str | None = None,
        include_context_tools: bool = True,
        require_human_approval: bool = False,
        approval_callback: Callable | None = None,
        tool_replacements: dict[str, Callable] | None = None,
        **agent_kwargs,
    ) -> Agent[OpenAPIToolDependencies]:
        """
        Create an Ally Config administrator agent.

        Args:
            tool_groups: Optional list of Ally Config tool groups (defaults to ALL)
            model: Model to use. If None, creates Azure GPT-4.1-mini model automatically
            additional_instructions: Optional additional instructions
            include_context_tools: Whether to include context management tools
            require_human_approval: Whether to require human approval for non-read-only operations
            approval_callback: Optional callback for human approval
            tool_replacements: Optional dict mapping operation IDs to mock functions for testing
            **agent_kwargs: Additional arguments for Agent

        Returns:
            Configured Ally Config administrator agent
        """
        if tool_groups is None:
            tool_groups = [AllyConfigToolGroup.ALL]

        # Auto-create Azure model config if no model specified
        if model is None:
            self.logger.info("No model specified, creating default Azure GPT-4.1-mini configuration")
            model = create_azure_model_config(
                deployment_name="gpt-4.1-mini",
                endpoint="https://ally-frcentral.openai.azure.com/",
                logger=self.logger,
            )

        return self.create_agent(
            name="ally_config_admin",
            system_prompt=SystemPrompts.ALLY_CONFIG_ADMIN,
            tool_groups=tool_groups,  # type: ignore
            model=model,
            additional_instructions=additional_instructions,
            include_context_tools=include_context_tools,
            require_human_approval=require_human_approval,
            approval_callback=approval_callback,
            tool_replacements=tool_replacements,
            **agent_kwargs
        )

    def create_hybrid_assistant(
        self,
        ai_knowledge_groups: list[AIKnowledgeToolGroup] | None = None,
        ally_config_groups: list[AllyConfigToolGroup] | None = None,
        model: str | ModelConfiguration | None = None,
        additional_instructions: str | None = None,
        include_context_tools: bool = True,
        require_human_approval: bool = False,
        approval_callback: Callable | None = None,
        tool_replacements: dict[str, Callable] | None = None,
        **agent_kwargs,
    ) -> Agent[OpenAPIToolDependencies]:
        """
        Create a hybrid agent with both AI Knowledge and Ally Config capabilities.

        Args:
            ai_knowledge_groups: Optional list of AI Knowledge tool groups (defaults to ALL)
            ally_config_groups: Optional list of Ally Config tool groups (defaults to ALL)
            model: Model to use. If None, creates Azure GPT-4.1-mini model automatically
            additional_instructions: Optional additional instructions
            include_context_tools: Whether to include context management tools
            require_human_approval: Whether to require human approval for non-read-only operations
            approval_callback: Optional callback for human approval
            tool_replacements: Optional dict mapping operation IDs to mock functions for testing
            **agent_kwargs: Additional arguments for Agent

        Returns:
            Configured hybrid agent
        """
        all_groups = []

        if ai_knowledge_groups:
            all_groups.extend(ai_knowledge_groups)
        if ally_config_groups:
            all_groups.extend(ally_config_groups)

        if not all_groups:
            all_groups = [AIKnowledgeToolGroup.ALL, AllyConfigToolGroup.ALL]

        # Auto-create Azure model config if no model specified
        if model is None:
            self.logger.info("No model specified, creating default Azure GPT-4.1-mini configuration")
            model = create_azure_model_config(
                deployment_name="gpt-4.1-mini",
                endpoint="https://ally-frcentral.openai.azure.com/",
                logger=self.logger,
            )

        return self.create_agent(
            name="hybrid_ai_assistant",
            system_prompt=SystemPrompts.HYBRID_AI_ASSISTANT,
            tool_groups=all_groups,
            model=model,
            additional_instructions=additional_instructions,
            include_context_tools=include_context_tools,
            require_human_approval=require_human_approval,
            approval_callback=approval_callback,
            tool_replacements=tool_replacements,
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

    def get_available_groups(self) -> dict[str, dict[str, list[str]]]:
        """
        Get information about available tool groups.

        Returns:
            Dictionary mapping tool group categories to their available groups
        """
        return self.tool_manager.get_available_groups()
