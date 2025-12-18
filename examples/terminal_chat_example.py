"""
Example for chatting with an agent through the terminal.

This example demonstrates:
1. Creating a hybrid assistant agent
2. Interactive terminal chat interface using the terminal_chat utility
3. Side-by-side visualization of messages (ModelRequest on left, ModelResponse on right)
4. Conversation history management
"""

from rich.console import Console

from meta_ally.agents import AgentFactory
from meta_ally.util.terminal_chat import start_chat_session
from meta_ally.util.tool_group_manager import (
    AIKnowledgeToolGroup,
    AllyConfigToolGroup,
)


def main():
    """Main function to set up and run the chat interface."""
    # Initialize console for setup messages
    console = Console()

    # Create agent factory
    console.print("[dim]Initializing agent...[/dim]")
    factory = AgentFactory()

    # Create hybrid assistant with AI Knowledge and Ally Config tools
    agent = factory.create_hybrid_assistant(
        ai_knowledge_groups=[AIKnowledgeToolGroup.ALL],
        ally_config_groups=[AllyConfigToolGroup.ALL],
    )

    # Create dependencies
    deps = factory.create_dependencies()

    console.print("[dim]✓ Agent initialized successfully[/dim]")
    console.print(f"[dim]Model: {agent.model}[/dim]\n")

    # Start the chat session using the utility function
    start_chat_session(agent, deps, console_width=200)


if __name__ == "__main__":
    main()
