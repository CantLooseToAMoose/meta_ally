"""
Terminal chat interface utilities for interactive agent conversations.

This module provides a clean terminal-based chat interface with:
- Side-by-side message display (ModelRequest on left, ModelResponse on right)
- Conversation history management
- Special commands (clear, history, exit)
- Rich formatting with panels and colors
"""

from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.prompt import Prompt


def format_message_parts(parts: list) -> str:
    """
    Format message parts for display.

    Args:
        parts: List of message parts to format

    Returns:
        Formatted string representation of the parts
    """
    output = []
    for part in parts:
        if hasattr(part, 'content'):
            # UserPromptPart, SystemPromptPart, TextPart, or ToolReturnPart
            part_type = type(part).__name__
            content = part.content if isinstance(part.content, str) else str(part.content)
            if part_type in {'UserPromptPart', 'SystemPromptPart'}:
                output.append(f"[dim]{part_type}:[/dim]\n{content}")
            elif part_type == 'ToolReturnPart':
                output.append(f"[dim cyan]🔧 Tool Return:[/dim cyan]\n{content}")
            else:
                output.append(f"[dim]{part_type}:[/dim] {content}")
        elif hasattr(part, 'tool_name'):
            # ToolCallPart
            output.append(f"[bold yellow]🔧 Tool Call:[/bold yellow] {part.tool_name}")
            if hasattr(part, 'args') and part.args:
                output.append(f"[dim]Args:[/dim] {part.args}")
    return "\n".join(output)


def display_chat_message(message, panel_width: int, console: Console):
    """
    Display a single chat message in the appropriate style.

    Args:
        message: The message to display (ModelRequest or ModelResponse)
        panel_width: Width of the panel
        console: Rich Console instance for output
    """
    content = format_message_parts(message.parts)
    msg_type = type(message).__name__

    if msg_type == "ModelRequest":
        # User messages on the left (blue)
        panel = Panel(
            content,
            title="[bold blue]👤 User[/bold blue]",
            border_style="blue",
            padding=(1, 2),
            width=panel_width
        )
        console.print(panel)
    elif msg_type == "ModelResponse":
        # Assistant messages on the right (green)
        panel = Panel(
            content,
            title="[bold green]🤖 Assistant[/bold green]",
            border_style="green",
            padding=(1, 2),
            width=panel_width
        )
        left_padding = console.width - panel_width
        padded_panel = Padding(panel, (0, 0, 0, left_padding))
        console.print(padded_panel)


def print_welcome_banner(console: Console):
    """
    Print the welcome banner for the chat interface.

    Args:
        console: Rich Console instance for output
    """
    console.print("\n[bold magenta]{'═' * 80}[/bold magenta]")
    console.print("[bold magenta]🤖 Meta Ally - Terminal Chat Interface[/bold magenta]")
    console.print("[bold magenta]{'═' * 80}[/bold magenta]\n")
    console.print("[dim]Type your message and press Enter. Type 'exit', 'quit', or 'q' to end the chat.[/dim]")
    console.print("[dim]Type 'clear' to clear the conversation history.[/dim]")
    console.print("[dim]Type 'history' to display all messages in the conversation.[/dim]\n")


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
    console.print("\n[bold cyan]{'═' * 80}[/bold cyan]")
    console.print("[bold cyan]📜 Conversation History[/bold cyan]")
    console.print("[bold cyan]{'═' * 80}[/bold cyan]\n")

    for message in messages:
        display_chat_message(message, panel_width, console)

    console.print(f"[dim]{'─' * 80}[/dim]\n")


def handle_special_command(
    user_input: str, message_history: list, panel_width: int, console: Console
) -> tuple[bool, list]:
    """
    Handle special chat commands.

    Args:
        user_input: The user's input
        message_history: Current message history
        panel_width: Width of display panels
        console: Rich Console instance for output

    Returns:
        Tuple of (should_continue, updated_message_history)
        should_continue is True if the chat should continue, False if it should exit
    """
    if user_input.lower() in {'exit', 'quit', 'q'}:
        console.print("\n[green]Thank you for chatting! Goodbye![/green]\n")
        return (False, message_history)

    if user_input.lower() == 'clear':
        console.print("\n[yellow]✓ Conversation history cleared.[/yellow]\n")
        return (True, [])

    if user_input.lower() == 'history':
        if message_history:
            display_conversation_history(message_history, panel_width, console)
        else:
            console.print("\n[yellow]No conversation history yet.[/yellow]\n")
        return (True, message_history)

    return (True, message_history)


def start_chat_session(agent, deps, console_width: int = 200):
    """
    Start an interactive chat session with an agent.

    Args:
        agent: The pydantic-ai agent to chat with
        deps: Agent dependencies
        console_width: Width of the console display (default: 200)

    Example:
        ```python
        from meta_ally.agents import AgentFactory
        from meta_ally.util.terminal_chat import start_chat_session

        factory = AgentFactory()
        agent = factory.create_hybrid_assistant()
        deps = factory.create_dependencies()

        start_chat_session(agent, deps)
        ```
    """
    # Initialize console with specified width
    console = Console(width=console_width)

    print_welcome_banner(console)

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
        should_continue, message_history = handle_special_command(
            user_input, message_history, panel_width, console
        )
        if not should_continue:
            break

        # Check if command was handled
        if user_input.lower() in {'clear', 'history'}:
            continue

        try:
            # Run the agent with the user's input
            response = agent.run_sync(
                user_input,
                deps=deps,
                message_history=message_history if message_history else None
            )

            # Display only the new messages from this run (includes user's formatted message)
            for message in response.new_messages():
                display_chat_message(message, panel_width, console)

            # Update message history with all messages
            message_history = response.all_messages()

            print_chat_divider(console)

        except KeyboardInterrupt:
            console.print("\n[yellow]Response interrupted. Type 'exit' to quit.[/yellow]\n")
            continue
        except Exception as e:
            console.print(f"\n[red]❌ Error: {e}[/red]\n")
            console.print("[dim]You can continue chatting or type 'exit' to quit.[/dim]\n")
            continue
