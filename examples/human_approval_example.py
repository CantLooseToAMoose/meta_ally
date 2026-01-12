#!/usr/bin/env python3
"""
Human Approval Example with Terminal Chat

This example demonstrates:
1. Creating an agent with human approval enabled for non-read-only operations
2. Using the terminal chat interface for interactive conversations
3. Automatic approval prompts when the agent attempts non-read-only operations (POST, PUT, DELETE)
4. Side-by-side visualization of messages

When the agent attempts to call a non-read-only API operation, you'll be prompted to approve or deny it.
"""

from rich.console import Console

from meta_ally.agents import AgentFactory
from meta_ally.util.human_approval_callback import (
    create_human_approval_callback,
)
from meta_ally.util.terminal_chat import start_chat_session
from meta_ally.util.tool_group_manager import (
    AIKnowledgeToolGroup,
    AllyConfigToolGroup,
)


def main():
    """Main function to set up and run the chat interface with human approval."""
    # Initialize console for setup messages
    console = Console()

    console.print("[bold cyan]Setting up agent with human approval...[/bold cyan]")

    # Create agent factory
    factory = AgentFactory()

    # Create human approval callback
    approval_callback = create_human_approval_callback(console_width=200)

    # Create hybrid assistant with human approval enabled
    agent = factory.create_hybrid_assistant(
        ai_knowledge_groups=[AIKnowledgeToolGroup.ALL],
        ally_config_groups=[AllyConfigToolGroup.ALL],
        require_human_approval=True,
        approval_callback=approval_callback
    )

    # Create dependencies
    deps = factory.create_dependencies()

    console.print("[green]✓ Agent initialized with human approval enabled[/green]")
    console.print(f"[dim]Model: {agent.model}[/dim]")
    console.print("[dim]Non-read-only operations (POST, PUT, DELETE) will require your approval.[/dim]\n")

    # Start the chat session
    start_chat_session(agent, deps, console_width=200)


if __name__ == "__main__":
    main()
