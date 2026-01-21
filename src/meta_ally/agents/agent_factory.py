#!/usr/bin/env python3
"""
Pydantic AI Agent Factory

A comprehensive factory for creating pydantic-ai agents with specific tool groups and system prompts.
Based on the tool categorization patterns found in the AI Knowledge and Ally Config notebooks.

Note: For pre-configured default agents, see agent_presets.py which provides convenience functions
for creating AI Knowledge specialists, Ally Config admins, hybrid assistants, and multi-agent systems.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.openai import OpenAIChatModel

from ..auth.auth_manager import AuthManager
from ..lib.openapi_to_tools import OpenAPIToolDependencies
from ..prompts.system_prompts import SystemPrompts
from ..tools.context_tools import get_context_tools
from ..tools.tool_group_manager import (
    AIKnowledgeToolGroup,
    AllyConfigToolGroup,
    ToolGroupManager,
    ToolGroupType,
)
from .dependencies import MultiAgentDependencies
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
        from meta_ally.agents import AgentFactory
        from meta_ally.agents.agent_presets import create_hybrid_assistant

        # Create factory
        factory = AgentFactory()

        # Create agent using preset (tools are loaded automatically)
        agent = create_hybrid_assistant(factory)

        # Create dependencies and refresh token for authentication
        deps = factory.create_dependencies()
        deps.auth_manager._refresh_token()  # IMPORTANT: Triggers browser auth flow

        # Run agent with dependencies
        result = agent.run_sync("Your question", deps=deps)
        ```

    Advanced usage (custom agents):
        ```python
        from meta_ally.agents import AgentFactory
        from meta_ally.tools.tool_group_manager import AIKnowledgeToolGroup

        factory = AgentFactory()

        # Create custom agent with specific tool groups
        agent = factory.create_agent(
            name="custom_assistant",
            system_prompt="You are a custom assistant...",
            tool_groups=[AIKnowledgeToolGroup.SOURCES],
            model="openai:gpt-4o"
        )
        ```

    """

    def __init__(
        self,
        auth_manager: AuthManager | None = None,
        keycloak_url: str = "https://keycloak.acc.iam-services.aws.inform-cloud.io/",
        realm_name: str = "inform-ai",
        client_id: str = "ai-cli-device",
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

    def _get_default_model(self) -> ModelConfiguration:
        """
        Get the default Azure GPT-4.1-mini model configuration.

        Returns
        -------
        ModelConfiguration
            Default Azure model configuration.
        """
        self.logger.info("No model specified, creating default Azure GPT-4.1-mini configuration")
        return create_azure_model_config(
            deployment_name="gpt-4.1-mini",
            endpoint="https://ally-frcentral.openai.azure.com/",
            logger=self.logger,
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

    def _get_datetime_instructions(self) -> str:
        """
        Get current date and time instructions for system prompts.

        Returns
        -------
        str
            Formatted date/time instructions.
        """
        now = datetime.now(ZoneInfo("Europe/Berlin"))
        return f"""

Current Date and Time:
- Date: {now.strftime('%A, %B %d, %Y')}
- Time: {now.strftime('%H:%M:%S')} (Europe/Berlin timezone)
- ISO Format: {now.isoformat()}

Use this information when the user asks about current dates, times, or when time-based context is relevant.
"""

    def _get_context_management_instructions(self, is_orchestrator: bool = False) -> str:
        """
        Get context management instructions for system prompts.

        Parameters
        ----------
        is_orchestrator : bool
            Whether this is for an orchestrator agent (affects instruction wording).

        Returns
        -------
        str
            Context management instructions.
        """
        base_instructions = """

        Context Management:
        You have access to tools for tracking user context information:
        - Business Area (Geschäftsbereich): The user's business domain or department
        - Project Number: The project the user is working on
        - Endpoint Name: The specific endpoint configuration being discussed

        When the user mentions any of these, use the appropriate set_* tool to remember it."""

        if is_orchestrator:
            return base_instructions + """
        Include relevant context when delegating to specialists.
        """
        return base_instructions + """
        Before performing operations that require this context, use the get_* tools to check
        if the information is available.
        If required information is missing, the get_* tool will return a message asking you
        to gather it from the user.
        """

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

        # Add context management instructions to system prompt
        if include_context_tools:
            complete_prompt += self._get_context_management_instructions(is_orchestrator=False)

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

        # Add dynamic datetime instructions that are evaluated at runtime
        @agent.instructions
        def add_current_datetime() -> str:
            """
            Add current date and time information dynamically at runtime.

            Returns:
                str: Formatted date and time instructions for the agent.
            """
            return self._get_datetime_instructions()

        self.logger.info("Created agent '%s' with %d tools", name, len(tools))

        return agent



    def create_dependencies(self) -> OpenAPIToolDependencies:
        """
        Create dependencies for running agents with OpenAPI tools.


        Example:
            ```python
            deps = factory.create_dependencies()
            result = agent.run_sync("question", deps=deps)
            ```

        Returns:
            OpenAPIToolDependencies instance with the configured AuthManager
        """
        return OpenAPIToolDependencies(auth_manager=self.auth_manager)

    def create_multi_agent_dependencies(self) -> MultiAgentDependencies:
        """
        Create dependencies for multi-agent systems with conversation tracking.

        Example:
            ```python
            deps = factory.create_multi_agent_dependencies()
            result = orchestrator.run_sync("question", deps=deps)
            ```

        Returns:
            MultiAgentDependencies instance with conversation tracking
        """
        return MultiAgentDependencies(auth_manager=self.auth_manager)

    def _create_specialist_tool(
        self,
        agent_name: str,
        agent: Agent[OpenAPIToolDependencies],
        description: str,
    ) -> Tool[MultiAgentDependencies]:
        """
        Create a tool that wraps a specialist agent for use by an orchestrator.

        Args:
            agent_name: Name identifier for the specialist
            agent: The specialist agent instance
            description: Description for the tool (used by orchestrator to decide when to call)

        Returns:
            A Tool that can be used by the orchestrator agent
        """
        # Create the tool function dynamically
        async def specialist_tool(
            ctx: RunContext[MultiAgentDependencies],
            task: str,
        ) -> str:
            """
            Dynamically created specialist tool function.

            Returns:
                The text response from the specialist agent.
            """
            # Get conversation history for this specialist
            message_history = ctx.deps.get_conversation(agent_name)

            # Run the specialist agent
            result = await agent.run(
                task,
                deps=ctx.deps,
                message_history=message_history if message_history else None,
            )

            # Get the response text
            response_text = result.output if isinstance(result.output, str) else str(result.output)

            # Update conversation history
            ctx.deps.update_conversation(agent_name, list(result.all_messages()))

            # Record the run to the timeline (before returning, so it appears in correct order)
            ctx.deps.add_specialist_run(
                agent_name=agent_name,
                task=task,
                response=response_text,
                new_messages=list(result.new_messages()),
                all_messages=list(result.all_messages()),
            )

            return response_text

        # Create the Tool with dynamic name and description
        tool = Tool(
            function=specialist_tool,
            name=f"call_{agent_name}",
            description=description,
        )

        return tool

    def create_orchestrator_with_specialists(
        self,
        specialists: dict[str, tuple[Agent[OpenAPIToolDependencies], str]],
        orchestrator_model: str | ModelConfiguration | None = None,
        orchestrator_instructions: str | None = None,
        include_context_tools: bool = True,
        max_retries: int = 3,
        **agent_kwargs,
    ) -> Agent[MultiAgentDependencies]:
        """
        Create an orchestrator agent with specialist agents registered as tools.

        The orchestrator can delegate tasks to specialists, and conversation history
        is maintained per specialist across multiple turns.

        Args:
            specialists: Dict mapping agent names to (agent, description) tuples.
                         The description is used as the tool description for the orchestrator.
            orchestrator_model: Model for the orchestrator. If None, creates Azure GPT-4.1-mini.
            orchestrator_instructions: Additional instructions for the orchestrator.
            include_context_tools: Whether to include context management tools.
            max_retries: Maximum retries for failed operations.
            **agent_kwargs: Additional arguments for the Agent.

        Returns:
            Orchestrator Agent configured with specialist tools.

        Example:
            ```python
            from meta_ally.agents.agent_presets import (
                create_ai_knowledge_specialist,
                create_ally_config_admin,
            )

            factory = AgentFactory()

            # Create specialist agents
            ai_knowledge = create_ai_knowledge_specialist(factory)
            ally_config = create_ally_config_admin(factory)

            # Create orchestrator with specialists as tools
            orchestrator = factory.create_orchestrator_with_specialists(
                specialists={
                    "ai_knowledge": (ai_knowledge, "Expert in knowledge management, sources, and collections"),
                    "ally_config": (ally_config, "Expert in Copilot configuration and endpoint management"),
                }
            )

            # Run with multi-agent dependencies
            deps = factory.create_multi_agent_dependencies()
            deps.auth_manager._refresh_token()
            result = orchestrator.run_sync("Set up a new knowledge source", deps=deps)
            ```
        """
        # Create specialist tools
        specialist_tools: list[Tool[MultiAgentDependencies]] = []
        for agent_name, (agent, description) in specialists.items():
            tool = self._create_specialist_tool(agent_name, agent, description)
            specialist_tools.append(tool)
            self.logger.info("Created specialist tool: call_%s", agent_name)

        # Build tools list
        tools: list[Any] = list(specialist_tools)

        # Add context management tools if requested
        if include_context_tools:
            context_tools = get_context_tools()
            tools.extend(context_tools)
            self.logger.info("Added %d context management tools to orchestrator", len(context_tools))

        # Build system prompt
        system_prompt = SystemPrompts.MULTI_AGENT_ORCHESTRATOR
        if orchestrator_instructions:
            system_prompt += f"\n\nAdditional Instructions:\n{orchestrator_instructions}"

        # Add context management instructions
        if include_context_tools:
            system_prompt += self._get_context_management_instructions(is_orchestrator=True)

        # Auto-create Azure model config if no model specified
        if orchestrator_model is None:
            orchestrator_model = self._get_default_model()

        # Resolve model configuration
        resolved_model = self._resolve_model(orchestrator_model)

        # Create orchestrator agent
        orchestrator = Agent(
            resolved_model,
            deps_type=MultiAgentDependencies,
            instructions=system_prompt,
            tools=tools,
            retries=max_retries,
            name="orchestrator",
            **agent_kwargs,
        )

        # Add dynamic datetime instructions that are evaluated at runtime
        @orchestrator.instructions
        def add_current_datetime() -> str:
            """
            Add current date and time information dynamically at runtime.

            Returns:
                str: Formatted date and time instructions for the agent.
            """
            return self._get_datetime_instructions()

        self.logger.info(
            "Created orchestrator with %d specialist tools and %d total tools",
            len(specialist_tools),
            len(tools),
        )

        return orchestrator



    def get_available_groups(self) -> dict[str, dict[str, list[str]]]:
        """
        Get information about available tool groups.

        Returns:
            Dictionary mapping tool group categories to their available groups
        """
        return self.tool_manager.get_available_groups()
