"""
Terminal Chat Example with Multi-Agent and Human Approval Support

This example demonstrates the programmatic API for creating and configuring agents
with various options. Edit the configuration variables below to customize behavior.

⚡ Alternative: Use the command-line interface for easier configuration:
    python -m meta_ally.ui.terminal_chat --help

This example demonstrates:
1. Creating a hybrid assistant agent or multi-agent orchestrator
2. Interactive terminal chat interface using the terminal_chat utility
3. Side-by-side visualization of messages (ModelRequest on left, ModelResponse on right)
4. Conversation history management
5. Human approval for non-read-only operations (optional)
6. Multi-agent orchestration with specialist visualization (optional)

Configuration:
- Set USE_MULTI_AGENT to True to use a multi-agent orchestrator with specialists
- Set REQUIRE_HUMAN_APPROVAL to True to prompt for approval on non-read-only operations
- Set USE_MOCK_API to True to use mock API data instead of real API calls
- Set USE_IMPROVED_DESCRIPTIONS to True to use improved tool descriptions
- Set MODEL_DEPLOYMENT_NAME to specify the Azure OpenAI deployment name (e.g., "gpt-4o", "gpt-4.1-mini")
"""
import logging

import logfire
from rich.console import Console

from meta_ally.agents import AgentFactory
from meta_ally.agents.agent_presets import (
    create_default_multi_agent_system,
    create_hybrid_assistant,
)
from meta_ally.agents.model_config import create_azure_model_config
from meta_ally.mock.analytics_api_mock_service import (
    create_ally_config_mock_tool_replacements,
)
from meta_ally.tools.tool_group_manager import (
    AIKnowledgeToolGroup,
    AllyConfigToolGroup,
)
from meta_ally.ui.human_approval_callback import (
    create_human_approval_callback,
)
from meta_ally.ui.terminal_chat import start_chat_session

# ============================================================================
# CONFIGURATION - Change these to toggle features
# ============================================================================
USE_MULTI_AGENT = False  # Set to True to use multi-agent orchestrator
REQUIRE_HUMAN_APPROVAL = True  # Set to True to require approval for non-read operations
USE_MOCK_API = True  # Set to True to use mock API data instead of real API calls
USE_IMPROVED_DESCRIPTIONS = True  # Set to True to use improved tool descriptions
MODEL_DEPLOYMENT_NAME = "gpt-5-mini"  # Azure OpenAI deployment name (e.g., "gpt-4o", "gpt-4.1-mini")
LOAD_CONVERSATION_FROM = "Data/UserRecords/Philipp_Langen__2nd_run__20260206_142400.json"
# Path to conversation JSON file to load (e.g., "Data/UserRecords/chat_20260206.json")


def main():
    """Main function to set up and run the chat interface."""
    # Suppress logfire logging
    logfire.configure(scrubbing=False, console=False)
    logfire.instrument_pydantic_ai()
    logging.getLogger("logfire._internal").setLevel(logging.ERROR)
    logging.getLogger("logfire").setLevel(logging.ERROR)
    # Initialize console for setup messages
    console = Console()

    # Display configuration
    console.print("[bold cyan]Terminal Chat Configuration:[/bold cyan]")
    console.print(f"  Multi-Agent Mode: {'[green]Enabled[/green]' if USE_MULTI_AGENT else '[dim]Disabled[/dim]'}")
    approval_status = '[green]Enabled[/green]' if REQUIRE_HUMAN_APPROVAL else '[dim]Disabled[/dim]'
    console.print(f"  Human Approval: {approval_status}")
    mock_api_status = '[green]Enabled[/green]' if USE_MOCK_API else '[dim]Disabled[/dim]'
    console.print(f"  Mock API: {mock_api_status}")
    improved_desc_status = '[green]Enabled[/green]' if USE_IMPROVED_DESCRIPTIONS else '[dim]Disabled[/dim]'
    console.print(f"  Improved Descriptions: {improved_desc_status}")
    console.print(f"  Model Deployment: [cyan]{MODEL_DEPLOYMENT_NAME}[/cyan]\n")

    # Create agent factory
    console.print("[dim]Initializing agent...[/dim]")
    factory = AgentFactory()

    # Create model configuration
    model_config = create_azure_model_config(
        deployment_name=MODEL_DEPLOYMENT_NAME,
        endpoint="https://ally-frcentral.openai.azure.com/",
        logger=factory.logger,
    )

    # Create approval callback if needed
    approval_callback = None
    if REQUIRE_HUMAN_APPROVAL:
        approval_callback = create_human_approval_callback(console_width=200)
        console.print("[yellow]Human approval enabled - non-read operations will require confirmation[/yellow]")

    # Create mock tool replacements if needed
    tool_replacements = None
    if USE_MOCK_API:
        console.print("[yellow]Creating mock API tool replacements...[/yellow]")
        tool_replacements = create_ally_config_mock_tool_replacements()
        console.print(f"[green]✓ Created {len(tool_replacements)} mock tool replacements[/green]")

    # Set up improved descriptions paths if enabled
    ai_knowledge_descriptions_path = None
    ally_config_descriptions_path = None
    if USE_IMPROVED_DESCRIPTIONS:
        ai_knowledge_descriptions_path = "Data/improved_tool_descriptions/ai_knowledge_improved_descriptions.json"
        ally_config_descriptions_path = "Data/improved_tool_descriptions/ally_config_improved_descriptions.json"
        console.print("[yellow]Using improved tool descriptions[/yellow]")

    # Create agent based on configuration
    if USE_MULTI_AGENT:
        console.print("[cyan]Creating multi-agent orchestrator with specialists...[/cyan]")
        agent = create_default_multi_agent_system(
            factory=factory,
            orchestrator_model=model_config,
            specialist_model=model_config,
            require_human_approval=REQUIRE_HUMAN_APPROVAL,
            approval_callback=approval_callback,
            tool_replacements=tool_replacements,
            ai_knowledge_descriptions_path=ai_knowledge_descriptions_path,
            ally_config_descriptions_path=ally_config_descriptions_path,
        )
        deps = factory.create_multi_agent_dependencies()
        console.print("[green]✓ Multi-agent orchestrator initialized[/green]")
        console.print("[dim]  Specialists: AI Knowledge, Ally Config[/dim]")
    else:
        console.print("[cyan]Creating hybrid assistant agent...[/cyan]")
        agent = create_hybrid_assistant(
            factory=factory,
            ai_knowledge_groups=[AIKnowledgeToolGroup.ALL],
            ally_config_groups=[AllyConfigToolGroup.ALL],
            model=model_config,
            require_human_approval=REQUIRE_HUMAN_APPROVAL,
            approval_callback=approval_callback,
            tool_replacements=tool_replacements,
            ai_knowledge_descriptions_path=ai_knowledge_descriptions_path,
            ally_config_descriptions_path=ally_config_descriptions_path,
        )
        deps = factory.create_dependencies()
        console.print("[green]✓ Hybrid assistant initialized[/green]")

    console.print(f"[dim]Model: {agent.model}[/dim]\n")

    # Prepare configuration dictionary to save with conversations
    config = {
        "use_multi_agent": USE_MULTI_AGENT,
        "require_human_approval": REQUIRE_HUMAN_APPROVAL,
        "use_mock_api": USE_MOCK_API,
        "use_improved_descriptions": USE_IMPROVED_DESCRIPTIONS,
        "model_deployment_name": MODEL_DEPLOYMENT_NAME,
    }

    # Start the chat session using the utility function
    start_chat_session(
        agent,
        deps,
        console_width=200,
        config=config,
        load_conversation_from=LOAD_CONVERSATION_FROM
    )


if __name__ == "__main__":
    main()
