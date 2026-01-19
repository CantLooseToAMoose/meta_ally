"""
Terminal Chat Example with Multi-Agent and Human Approval Support

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
"""
import logfire
from rich.console import Console

from meta_ally.agents import AgentFactory
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
USE_MULTI_AGENT = True  # Set to True to use multi-agent orchestrator
REQUIRE_HUMAN_APPROVAL = True  # Set to True to require approval for non-read operations


def main():
    """Main function to set up and run the chat interface."""
    # Configure logging with logfire
    logfire.configure(scrubbing=False, console=False)
    logfire.instrument_pydantic_ai()
    # Initialize console for setup messages
    console = Console()

    # Display configuration
    console.print("[bold cyan]Terminal Chat Configuration:[/bold cyan]")
    console.print(f"  Multi-Agent Mode: {'[green]Enabled[/green]' if USE_MULTI_AGENT else '[dim]Disabled[/dim]'}")
    approval_status = '[green]Enabled[/green]' if REQUIRE_HUMAN_APPROVAL else '[dim]Disabled[/dim]'
    console.print(f"  Human Approval: {approval_status}\n")

    # Create agent factory
    console.print("[dim]Initializing agent...[/dim]")
    factory = AgentFactory()

    # Create approval callback if needed
    approval_callback = None
    if REQUIRE_HUMAN_APPROVAL:
        approval_callback = create_human_approval_callback(console_width=200)
        console.print("[yellow]Human approval enabled - non-read operations will require confirmation[/yellow]")

    # Create agent based on configuration
    if USE_MULTI_AGENT:
        console.print("[cyan]Creating multi-agent orchestrator with specialists...[/cyan]")
        agent = factory.create_default_multi_agent_system(
            require_human_approval=REQUIRE_HUMAN_APPROVAL,
            approval_callback=approval_callback,
        )
        deps = factory.create_multi_agent_dependencies()
        console.print("[green]✓ Multi-agent orchestrator initialized[/green]")
        console.print("[dim]  Specialists: AI Knowledge, Ally Config[/dim]")
    else:
        console.print("[cyan]Creating hybrid assistant agent...[/cyan]")
        agent = factory.create_hybrid_assistant(
            ai_knowledge_groups=[AIKnowledgeToolGroup.ALL],
            ally_config_groups=[AllyConfigToolGroup.ALL],
            require_human_approval=REQUIRE_HUMAN_APPROVAL,
            approval_callback=approval_callback,
        )
        deps = factory.create_dependencies()
        console.print("[green]✓ Hybrid assistant initialized[/green]")

    console.print(f"[dim]Model: {agent.model}[/dim]\n")

    # Start the chat session using the utility function
    start_chat_session(agent, deps, console_width=200)


if __name__ == "__main__":
    main()
