"""
Terminal chat interface utilities for interactive agent conversations.

This module provides a clean terminal-based chat interface with:
- Side-by-side message display (ModelRequest on left, ModelResponse on right)
- Conversation history management
- Special commands (clear, history, exit)
- Rich formatting with panels and colors
- Multi-agent visualization with unified conversation timeline
"""

from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from rich.console import Console
from rich.prompt import IntPrompt, Prompt

from ..lib.dependencies import MultiAgentDependencies
from .conversation_saver import (
    save_conversation,
)
from .visualization import (
    display_chat_message,
    display_conversation_timeline,
)


def print_welcome_banner(console: Console):
    """
    Print the welcome banner for the chat interface.

    Args:
        console: Rich Console instance for output
    """
    console.print(f"\n[bold magenta]{'═' * 80}[/bold magenta]")
    console.print("[bold magenta]🤖 Meta Ally - Terminal Chat Interface[/bold magenta]")
    console.print(f"[bold magenta]{'═' * 80}[/bold magenta]\n")
    console.print("[dim]Type your message and press Enter. Type 'exit', 'quit', or 'q' to end the chat.[/dim]")
    console.print("[dim]Type 'clear' to clear the conversation history.[/dim]")
    console.print("[dim]Type 'history' to display all messages in the conversation.[/dim]")
    console.print("[dim]Type 'save' to save the current conversation.[/dim]\n")


def print_chat_divider(console: Console):
    """
    Print a divider between chat turns.

    Args:
        console: Rich Console instance for output
    """
    console.print(f"[dim]{'─' * 80}[/dim]\n")


def display_conversation_history(messages: list, panel_width: int, console: Console):
    """
    Display the entire conversation history.

    Args:
        messages: List of all messages in the conversation
        panel_width: Width of the panels
        console: Rich Console instance for output
    """
    console.print(f"\n[bold cyan]{'═' * 80}[/bold cyan]")
    console.print("[bold cyan]📜 Conversation History[/bold cyan]")
    console.print(f"[bold cyan]{'═' * 80}[/bold cyan]\n")

    for message in messages:
        display_chat_message(message, panel_width, console)

    console.print(f"[dim]{'─' * 80}[/dim]\n")


def handle_special_command(
    user_input: str,
    message_history: list,
    panel_width: int,
    console: Console,
    conversation_timeline: list | None = None
) -> tuple[bool, list, str]:
    """
    Handle special chat commands.

    Args:
        user_input: The user's input
        message_history: Current message history
        panel_width: Width of display panels
        console: Rich Console instance for output
        conversation_timeline: Optional conversation timeline for multi-agent mode

    Returns:
        Tuple of (should_continue, updated_message_history, command_type)
        should_continue is True if the chat should continue, False if it should exit
        command_type is 'save' if save command was used, empty string otherwise
    """
    if user_input.lower() in {'exit', 'quit', 'q'}:
        console.print("\n[green]Thank you for chatting! Goodbye![/green]\n")
        return (False, message_history, '')

    if user_input.lower() == 'clear':
        console.print("\n[yellow]✓ Conversation history cleared.[/yellow]\n")
        return (True, [], '')

    if user_input.lower() == 'history':
        if message_history:
            display_conversation_history(message_history, panel_width, console)
        else:
            console.print("\n[yellow]No conversation history yet.[/yellow]\n")
        return (True, message_history, '')

    if user_input.lower() == 'save':
        timeline_to_save = conversation_timeline if conversation_timeline else message_history
        if not timeline_to_save:
            console.print("\n[yellow]No conversation to save yet.[/yellow]\n")
            return (True, message_history, '')

        try:
            # Get metadata from user
            console.print("\n[cyan]💾 Save Conversation[/cyan]")
            name = Prompt.ask("  [cyan]Name[/cyan]")
            grade = IntPrompt.ask("  [cyan]Grade (1-10)[/cyan]", default=5)
            notes = Prompt.ask("  [cyan]Notes (optional)[/cyan]", default="")

            # Save in all three formats
            json_path = save_conversation(timeline_to_save, name, grade, notes)

            console.print("\n[green]✓ Conversation saved:[/green]")
            console.print(f"[green]  • JSON:  {json_path}[/green]")

        except ValueError as e:
            console.print(f"\n[red]❌ Error: {e}[/red]\n")
        except Exception as e:
            console.print(f"\n[red]❌ Failed to save: {e}[/red]\n")

        return (True, message_history, 'save')

    return (True, message_history, '')


def _handle_agent_response(
    agent,
    user_input: str,
    message_history: list,
    deps,
    is_multi_agent: bool,
    panel_width: int,
    console: Console,
) -> list:
    """
    Handle processing and displaying an agent response.

    Args:
        agent: The pydantic-ai agent
        user_input: User's input message
        message_history: Current message history
        deps: Agent dependencies
        is_multi_agent: Whether using multi-agent mode
        panel_width: Width of display panels
        console: Rich Console instance

    Returns:
        Updated message history
    """
    response = agent.run_sync(
        user_input,
        deps=deps,
        message_history=message_history if message_history else None
    )

    # Display messages based on agent type
    if is_multi_agent:
        # Add orchestrator's new messages to the timeline
        deps.add_orchestrator_messages(list(response.new_messages()))

        # Display only the undisplayed entries from the timeline
        undisplayed = deps.get_undisplayed_entries()
        display_conversation_timeline(undisplayed, panel_width, console)

        # Mark all entries as displayed (timeline is preserved)
        deps.mark_entries_as_displayed()
    else:
        # Standard single-agent display
        for message in response.new_messages():
            display_chat_message(message, panel_width, console)

    # Update message history with all messages
    return list(response.all_messages())


def start_chat_session(agent, deps, console_width: int = 200):
    """
    Start an interactive chat session with an agent.

    Supports both single-agent and multi-agent (orchestrator) modes.
    When using MultiAgentDependencies, specialist conversations are automatically
    visualized with appropriate prefixes.

    Args:
        agent: The pydantic-ai agent to chat with
        deps: Agent dependencies (OpenAPIToolDependencies or MultiAgentDependencies)
        console_width: Width of the console display (default: 200)

    Example (single agent):
        ```python
        from meta_ally.agents import AgentFactory
        from meta_ally.util.terminal_chat import start_chat_session

        factory = AgentFactory()
        agent = factory.create_hybrid_assistant()
        deps = factory.create_dependencies()

        start_chat_session(agent, deps)
        ```

    Example (multi-agent orchestrator):
        ```python
        from meta_ally.agents import AgentFactory
        from meta_ally.util.terminal_chat import start_chat_session

        factory = AgentFactory()
        orchestrator = factory.create_default_multi_agent_system()
        deps = factory.create_multi_agent_dependencies()

        start_chat_session(orchestrator, deps)
        ```
    """
    # Initialize console with specified width
    console = Console(width=console_width)

    # Check if this is a multi-agent setup
    is_multi_agent = isinstance(deps, MultiAgentDependencies)

    print_welcome_banner(console)

    if is_multi_agent:
        console.print(
            "[dim cyan]Multi-agent mode: Conversation timeline will show specialist interactions.[/dim cyan]\n"
        )

    # Calculate panel width (70% of console width)
    panel_width = int(console.width * 0.7)

    # Store message history
    message_history = []

    while True:
        # Get user input without echoing it back (we'll show it formatted)
        try:
            user_input = Prompt.ask("\n[bold blue]You[/bold blue]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Chat interrupted. Goodbye![/yellow]")
            break

        # Skip empty input
        if not user_input.strip():
            continue

        # Handle special commands
        timeline = deps.conversation_timeline if is_multi_agent else None
        should_continue, message_history, _command = handle_special_command(
            user_input, message_history, panel_width, console, timeline
        )
        if not should_continue:
            break

        # Check if command was handled
        if user_input.lower() in {'clear', 'history', 'save'}:
            # Also clear conversations and timeline if multi-agent
            if is_multi_agent and user_input.lower() == 'clear':
                deps.conversations.clear()
                deps.conversation_timeline.clear()
            continue

        try:
            message_history = _handle_agent_response(
                agent, user_input, message_history, deps, is_multi_agent, panel_width, console
            )
            print_chat_divider(console)

        except KeyboardInterrupt:
            console.print("\n[yellow]Response interrupted. Type 'exit' to quit.[/yellow]\n")
            continue
        except Exception as e:
            # Add user input and error response to message history so the agent has context
            error_message = f"Error occurred: {e!s}"
            user_request = ModelRequest(parts=[UserPromptPart(content=user_input)])
            error_response = ModelResponse(parts=[TextPart(content=error_message)])

            # Add to message history
            message_history.append(user_request)
            message_history.append(error_response)

            # Display the error to user
            console.print(f"\n[red]❌ Error: {e}[/red]\n")
            console.print("[dim]You can continue chatting or type 'exit' to quit.[/dim]\n")
            continue
