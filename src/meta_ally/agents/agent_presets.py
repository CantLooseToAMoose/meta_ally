#!/usr/bin/env python3
"""
Default Agent Presets

Pre-configured agent creation functions for common use cases.
These functions use the AgentFactory to create agents with standard configurations.
"""

from __future__ import annotations

from collections.abc import Callable

from pydantic_ai import Agent

from ..lib.openapi_to_tools import OpenAPIToolDependencies
from ..prompts.system_prompts import SystemPrompts
from ..tools.tool_group_manager import (
    AIKnowledgeToolGroup,
    AllyConfigToolGroup,
)
from .agent_factory import AgentFactory
from .dependencies import MultiAgentDependencies
from .model_config import ModelConfiguration


def create_ai_knowledge_specialist(
    factory: AgentFactory,
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
        factory: AgentFactory instance to use for agent creation
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
        model = factory._get_default_model()

    return factory.create_agent(
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
    factory: AgentFactory,
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
        factory: AgentFactory instance to use for agent creation
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
        model = factory._get_default_model()

    return factory.create_agent(
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
    factory: AgentFactory,
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
        factory: AgentFactory instance to use for agent creation
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
        model = factory._get_default_model()

    return factory.create_agent(
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


def create_default_multi_agent_system(
    factory: AgentFactory,
    orchestrator_model: str | ModelConfiguration | None = None,
    specialist_model: str | ModelConfiguration | None = None,
    include_context_tools: bool = True,
    require_human_approval: bool = False,
    approval_callback: Callable | None = None,
    tool_replacements: dict[str, Callable] | None = None,
    **agent_kwargs,
) -> Agent[MultiAgentDependencies]:
    """
    Create a default multi-agent system with AI Knowledge and Ally Config specialists.

    This is a convenience function that sets up a complete multi-agent system with:
    - An AI Knowledge specialist for knowledge management
    - An Ally Config specialist for Copilot configuration
    - An orchestrator that delegates to these specialists

    Args:
        factory: AgentFactory instance to use for agent creation
        orchestrator_model: Model for the orchestrator. If None, uses Azure GPT-4.1-mini.
        specialist_model: Model for specialists. If None, uses Azure GPT-4.1-mini.
        include_context_tools: Whether to include context management tools.
        require_human_approval: Whether specialists require human approval for operations.
        approval_callback: Optional callback for human approval.
        tool_replacements: Optional dict mapping operation IDs to mock functions (applied to specialists).
        **agent_kwargs: Additional arguments for orchestrator agent only.

    Returns:
        Orchestrator Agent configured with AI Knowledge and Ally Config specialists.

    Example:
        ```python
        from meta_ally.agents import AgentFactory
        from meta_ally.agents.agent_presets import create_default_multi_agent_system

        factory = AgentFactory()
        orchestrator = create_default_multi_agent_system(factory)

        deps = factory.create_multi_agent_dependencies()
        deps.auth_manager._refresh_token()

        result = orchestrator.run_sync("Help me set up a SharePoint source", deps=deps)
        ```
    """
    # Extend specialist instructions
    specialist_extension = SystemPrompts.SPECIALIST_INSTRUCTION_EXTENSION

    # Create AI Knowledge specialist with extended instructions
    ai_knowledge = create_ai_knowledge_specialist(
        factory=factory,
        model=specialist_model,
        additional_instructions=specialist_extension,
        include_context_tools=True,
        require_human_approval=require_human_approval,
        approval_callback=approval_callback,
        tool_replacements=tool_replacements,
    )

    # Create Ally Config specialist with extended instructions
    ally_config = create_ally_config_admin(
        factory=factory,
        model=specialist_model,
        additional_instructions=specialist_extension,
        include_context_tools=True,
        require_human_approval=require_human_approval,
        approval_callback=approval_callback,
        tool_replacements=tool_replacements,
    )

    # Define specialists with descriptions
    specialists = {
        "ai_knowledge_specialist": (
            ai_knowledge,
            "Expert in AI Knowledge management. Call or ask this specialist for tasks involving: "
            "creating and managing knowledge sources (document upload, websites, SharePoint, OneDrive, S3, GitHub),"
            "building and configuring collections, setting up indexing and search, "
            "and managing document metadata. Use for any knowledge-related queries."
        ),
        "ally_config_admin": (
            ally_config,
            "Expert in Ally Config and Copilot management. Call or ask this specialist for tasks involving: "
            "creating and configuring AI Copilot endpoints, managing model deployments, "
            "setting up plugins (including AI Knowledge plugin), running evaluations, "
            "monitoring costs and usage, and managing permissions. Use for any Copilot configuration queries."
        ),
    }

    # Create orchestrator (note: orchestrators don't use tool_replacements, only specialists do)
    return factory.create_orchestrator_with_specialists(
        specialists=specialists,
        orchestrator_model=orchestrator_model,
        include_context_tools=include_context_tools,
        **agent_kwargs,
    )
