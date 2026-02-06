"""
Terminal chat interface utilities for interactive agent conversations.

This module provides a clean terminal-based chat interface with:
- Side-by-side message display (ModelRequest on left, ModelResponse on right)
- Conversation history management
- Special commands (clear, history, exit)
- Rich formatting with panels and colors
- Multi-agent visualization with unified conversation timeline
"""

import argparse
import logging
from typing import NamedTuple

import logfire
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from rich.console import Console
from rich.prompt import Prompt

from ..agents import AgentFactory
from ..agents.agent_presets import (
    create_default_multi_agent_system,
    create_hybrid_assistant,
)
from ..agents.dependencies import MultiAgentDependencies
from ..agents.model_config import create_azure_model_config
from ..mock.analytics_api_mock_service import (
    create_ally_config_mock_tool_replacements,
)
from ..tools.tool_group_manager import (
    AIKnowledgeToolGroup,
    AllyConfigToolGroup,
)
from .conversation_loader import load_conversation_for_single_agent
from .conversation_saver import (
    calculate_sus_score,
    prompt_sus_questionnaire,
    save_conversation,
    save_conversation_html,
)
from .human_approval_callback import create_human_approval_callback
from .visualization import (
    display_chat_message,
    display_conversation_timeline,
)


class AgentConfig(NamedTuple):
    """Configuration for agent creation."""
    use_multi_agent: bool
    require_approval: bool
    tool_replacements: dict | None
    ai_knowledge_descriptions_path: str | None
    ally_config_descriptions_path: str | None


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


def _handle_exit_command(console: Console, message_history: list) -> tuple[bool, list, str]:
    """
    Handle exit command and return signal to end chat.

    Returns:
        Tuple of (False, message_history, '') to signal chat should end.
    """
    console.print("\n[green]Thank you for chatting! Goodbye![/green]\n")
    return (False, message_history, '')


def _handle_clear_command(console: Console) -> tuple[bool, list, str]:
    """
    Handle clear command and return empty message history.

    Returns:
        Tuple of (True, [], '') with empty message history.
    """
    console.print("\n[yellow]✓ Conversation history cleared.[/yellow]\n")
    return (True, [], '')


def _handle_history_command(
    message_history: list,
    panel_width: int,
    console: Console
) -> tuple[bool, list, str]:
    """
    Handle history command and display conversation history.

    Returns:
        Tuple of (True, message_history, '') to continue chat.
    """
    if message_history:
        display_conversation_history(message_history, panel_width, console)
    else:
        console.print("\n[yellow]No conversation history yet.[/yellow]\n")
    return (True, message_history, '')


def _prompt_for_notes(console: Console) -> dict | str:
    """
    Prompt user for structured notes and return as dict or empty string.

    Returns:
        Dictionary with note fields if any provided, empty string otherwise.
    """
    console.print("\n[cyan]Notes (optional - press Enter to skip any field):[/cyan]")
    intention = Prompt.ask("  [cyan]What did you intend to do?[/cyan]", default="")
    achievement = Prompt.ask("  [cyan]What did you achieve?[/cyan]", default="")
    went_well = Prompt.ask("  [cyan]What went well?[/cyan]", default="")
    went_poorly = Prompt.ask("  [cyan]What went poorly?[/cyan]", default="")

    notes = {}
    if intention:
        notes['intention'] = intention
    if achievement:
        notes['achievement'] = achievement
    if went_well:
        notes['what_went_well'] = went_well
    if went_poorly:
        notes['what_went_poorly'] = went_poorly

    return notes if notes else ""


def _prompt_for_feedback(console: Console) -> str:
    """
    Prompt user for feedback and return as formatted string.

    Returns:
        Formatted feedback string or empty string if no feedback provided.
    """
    console.print("\n[cyan]Feedback (optional - press Enter to skip any field):[/cyan]")
    achievement_feedback = Prompt.ask(
        "  [cyan]Were you successful in achieving your goal? (yes/no)[/cyan]",
        default=""
    )
    improvement_feedback = Prompt.ask(
        "  [cyan]Is this an improvement from the classic Ally web portal? "
        "(yes/no/comments)[/cyan]",
        default=""
    )
    config_preference = Prompt.ask(
        "  [cyan]If you tried different configurations, which do you prefer?[/cyan]",
        default=""
    )

    feedback_parts = []
    if achievement_feedback:
        feedback_parts.append(f"Achievement: {achievement_feedback}")
    if improvement_feedback:
        feedback_parts.append(f"Portal comparison: {improvement_feedback}")
    if config_preference:
        feedback_parts.append(f"Configuration preference: {config_preference}")

    return " | ".join(feedback_parts) if feedback_parts else ""


def _handle_save_command(
    message_history: list,
    console: Console,
    conversation_timeline: list | None,
    config: dict | None
) -> tuple[bool, list, str]:
    """
    Handle save command and save conversation in JSON and HTML formats.

    Returns:
        Tuple of (True, message_history, 'save') to continue chat after saving.
    """
    timeline_to_save = conversation_timeline if conversation_timeline else message_history
    if not timeline_to_save:
        console.print("\n[yellow]No conversation to save yet.[/yellow]\n")
        return (True, message_history, '')

    try:
        # Get metadata from user
        console.print("\n[cyan]💾 Save Conversation[/cyan]")
        name = Prompt.ask("  [cyan]Name[/cyan]")

        # Prompt for SUS questionnaire
        completed, sus_responses = prompt_sus_questionnaire()
        sus_score = None
        if completed and sus_responses:
            sus_score = calculate_sus_score(sus_responses)
            console.print(f"\n[green]✓ SUS Score: {sus_score:.1f}/100[/green]")

        # Get notes and feedback
        notes = _prompt_for_notes(console)
        feedback = _prompt_for_feedback(console)

        # Save in JSON and HTML formats
        json_path = save_conversation(
            timeline_to_save, name, sus_score, sus_responses, notes, feedback, config=config
        )
        html_path = save_conversation_html(
            timeline_to_save, name, sus_score, sus_responses, notes, feedback, config=config
        )

        console.print("\n[green]✓ Conversation saved:[/green]")
        console.print(f"[green]  • JSON: {json_path}[/green]")
        console.print(f"[green]  • HTML: {html_path}[/green]")

    except ValueError as e:
        console.print(f"\n[red]❌ Error: {e}[/red]\n")
    except Exception as e:
        console.print(f"\n[red]❌ Failed to save: {e}[/red]\n")

    return (True, message_history, 'save')


def handle_special_command(
    user_input: str,
    message_history: list,
    panel_width: int,
    console: Console,
    conversation_timeline: list | None = None,
    config: dict | None = None
) -> tuple[bool, list, str]:
    """
    Handle special chat commands.

    Args:
        user_input: The user's input
        message_history: Current message history
        panel_width: Width of display panels
        console: Rich Console instance for output
        conversation_timeline: Optional conversation timeline for multi-agent mode
        config: Optional configuration dictionary to save with the conversation

    Returns:
        Tuple of (should_continue, updated_message_history, command_type)
        should_continue is True if the chat should continue, False if it should exit
        command_type is 'save' if save command was used, empty string otherwise
    """
    command = user_input.lower()

    if command in {'exit', 'quit', 'q'}:
        return _handle_exit_command(console, message_history)

    if command == 'clear':
        return _handle_clear_command(console)

    if command == 'history':
        return _handle_history_command(message_history, panel_width, console)

    if command == 'save':
        return _handle_save_command(message_history, console, conversation_timeline, config)

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


def _load_existing_conversation(
    console: Console,
    load_conversation_from: str,
    is_multi_agent: bool,
    panel_width: int
) -> tuple[list, dict | None]:
    """
    Load a conversation from file if path provided.

    Args:
        console: Rich Console instance
        load_conversation_from: Path to conversation JSON file
        is_multi_agent: Whether in multi-agent mode
        panel_width: Width of display panels

    Returns:
        Tuple of (message_history, loaded_metadata)
    """
    message_history = []
    loaded_metadata = None

    if is_multi_agent:
        console.print(
            "[yellow]⚠️  Warning: Conversation loading for multi-agent mode is not yet supported.[/yellow]"
        )
        console.print("[yellow]Starting with empty conversation.[/yellow]\n")
        return message_history, loaded_metadata

    console.print(f"[cyan]📂 Loading conversation from: {load_conversation_from}[/cyan]")
    message_history, loaded_metadata = load_conversation_for_single_agent(load_conversation_from)
    console.print(f"[green]✓ Loaded {len(message_history)} messages[/green]")

    if loaded_metadata:
        name = loaded_metadata.get('name', 'Unnamed')
        timestamp = loaded_metadata.get('timestamp', 'Unknown')
        console.print(f"[dim]  Name: {name}[/dim]")
        console.print(f"[dim]  Date: {timestamp}[/dim]")

        if notes := loaded_metadata.get('notes'):
            console.print(f"[dim]  Notes: {notes}[/dim]")

    console.print("\n[green]✓ Conversation loaded! You can continue from where you left off.[/green]\n")
    console.print("[cyan]Loaded conversation history:[/cyan]")
    display_conversation_history(message_history, panel_width, console)

    return message_history, loaded_metadata


def _initialize_chat(
    console: Console,
    is_multi_agent: bool,
    load_conversation_from: str | None,
    panel_width: int
) -> tuple[list, dict | None]:
    """
    Initialize chat session and optionally load conversation.

    Args:
        console: Rich Console instance
        is_multi_agent: Whether in multi-agent mode
        load_conversation_from: Optional path to conversation file
        panel_width: Width of display panels

    Returns:
        Tuple of (message_history, loaded_metadata)
    """
    print_welcome_banner(console)

    if is_multi_agent:
        console.print(
            "[dim cyan]Multi-agent mode: Conversation timeline will show specialist interactions.[/dim cyan]\n"
        )

    message_history = []
    loaded_metadata = None

    if load_conversation_from:
        try:
            message_history, loaded_metadata = _load_existing_conversation(
                console, load_conversation_from, is_multi_agent, panel_width
            )
        except FileNotFoundError:
            console.print(f"[red]❌ Conversation file not found: {load_conversation_from}[/red]")
            console.print("[yellow]Starting with empty conversation.[/yellow]\n")
        except Exception as e:
            console.print(f"[red]❌ Error loading conversation: {e}[/red]")
            console.print("[yellow]Starting with empty conversation.[/yellow]\n")

    return message_history, loaded_metadata


def _handle_error_in_response(
    console: Console,
    user_input: str,
    message_history: list,
    error: Exception
) -> list:
    """
    Handle an error that occurred during agent response.

    Args:
        console: Rich Console instance
        user_input: User's input that caused the error
        message_history: Current message history
        error: The exception that occurred

    Returns:
        Updated message history with error
    """
    error_message = f"Error occurred: {error!s}"
    user_request = ModelRequest(parts=[UserPromptPart(content=user_input)])
    error_response = ModelResponse(parts=[TextPart(content=error_message)])

    # Add to message history
    message_history.append(user_request)
    message_history.append(error_response)

    # Display the error to user
    console.print(f"\n[red]❌ Error: {error}[/red]\n")
    console.print("[dim]You can continue chatting or type 'exit' to quit.[/dim]\n")

    return message_history


def _process_user_input(
    user_input: str,
    message_history: list,
    agent,
    deps,
    is_multi_agent: bool,
    panel_width: int,
    console: Console
) -> list:
    """
    Process user input and get agent response.

    Args:
        user_input: User's input message
        message_history: Current message history
        agent: The pydantic-ai agent
        deps: Agent dependencies
        is_multi_agent: Whether in multi-agent mode
        panel_width: Width of display panels
        console: Rich Console instance

    Returns:
        Updated message history
    """
    # Handle clear command for multi-agent
    if is_multi_agent and user_input.lower() == 'clear':
        deps.conversations.clear()
        deps.conversation_timeline.clear()
        return message_history

    # Get agent response
    try:
        message_history = _handle_agent_response(
            agent, user_input, message_history, deps, is_multi_agent, panel_width, console
        )
        print_chat_divider(console)
    except KeyboardInterrupt:
        console.print("\n[yellow]Response interrupted. Type 'exit' to quit.[/yellow]\n")
    except Exception as e:
        message_history = _handle_error_in_response(console, user_input, message_history, e)

    return message_history


def start_chat_session(
    agent,
    deps,
    console_width: int = 200,
    config: dict | None = None,
    load_conversation_from: str | None = None
):
    """
    Start an interactive chat session with an agent.

    Supports both single-agent and multi-agent (orchestrator) modes.
    When using MultiAgentDependencies, specialist conversations are automatically
    visualized with appropriate prefixes.

    Args:
        agent: The pydantic-ai agent to chat with
        deps: Agent dependencies (OpenAPIToolDependencies or MultiAgentDependencies)
        console_width: Width of the console display (default: 200)
        config: Optional configuration dictionary to save with conversations
        load_conversation_from: Optional path to a saved conversation JSON file to resume

    Example (single agent):
        ```python
        from meta_ally.agents import AgentFactory
        from meta_ally.agents.agent_presets import create_hybrid_assistant
        from meta_ally.util.terminal_chat import start_chat_session

        factory = AgentFactory()
        agent = create_hybrid_assistant(factory)
        deps = factory.create_dependencies()

        start_chat_session(agent, deps)
        ```

    Example (multi-agent orchestrator):
        ```python
        from meta_ally.agents import AgentFactory
        from meta_ally.agents.agent_presets import create_default_multi_agent_system
        from meta_ally.util.terminal_chat import start_chat_session

        factory = AgentFactory()
        orchestrator = create_default_multi_agent_system(factory)
        deps = factory.create_multi_agent_dependencies()

        start_chat_session(orchestrator, deps)
        ```

    Example (resume conversation):
        ```python
        # Resume a previous conversation
        start_chat_session(
            agent, deps,
            load_conversation_from="Data/UserRecords/my_chat_20260206_120000.json"
        )
        ```
    """
    # Initialize console with specified width
    console = Console(width=console_width)

    # Check if this is a multi-agent setup
    is_multi_agent = isinstance(deps, MultiAgentDependencies)

    # Calculate panel width (70% of console width)
    panel_width = int(console.width * 0.7)

    # Initialize chat and load conversation if requested
    message_history, _loaded_metadata = _initialize_chat(
        console, is_multi_agent, load_conversation_from, panel_width
    )

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
            user_input, message_history, panel_width, console, timeline, config
        )
        if not should_continue:
            break

        # Check if command was handled
        if user_input.lower() in {'clear', 'history', 'save'}:
            message_history = _process_user_input(
                user_input, message_history, agent, deps, is_multi_agent, panel_width, console
            )
            continue

        # Process normal user input
        message_history = _process_user_input(
            user_input, message_history, agent, deps, is_multi_agent, panel_width, console
        )


def _create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the CLI.

    Returns:
        Configured ArgumentParser instance with all CLI options.
    """
    parser = argparse.ArgumentParser(
        description="Interactive terminal chat interface for Meta Ally agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with multi-agent orchestrator
  python -m meta_ally.ui.terminal_chat --multi-agent

  # Start with human approval and mock API
  python -m meta_ally.ui.terminal_chat --approval --mock-api

  # Use a specific model deployment
  python -m meta_ally.ui.terminal_chat --model gpt-4o

  # Load a previous conversation
  python -m meta_ally.ui.terminal_chat --load Data/UserRecords/chat_20260206.json

  # Single agent with improved descriptions
  python -m meta_ally.ui.terminal_chat --single-agent --improved-descriptions
        """
    )

    # Agent type
    agent_group = parser.add_mutually_exclusive_group()
    agent_group.add_argument(
        "--multi-agent",
        action="store_true",
        default=True,
        help="Use multi-agent orchestrator with specialists (default)"
    )
    agent_group.add_argument(
        "--single-agent",
        action="store_true",
        help="Use single hybrid assistant agent"
    )

    # Approval settings
    approval_group = parser.add_mutually_exclusive_group()
    approval_group.add_argument(
        "--approval",
        action="store_true",
        default=True,
        help="Require human approval for non-read operations (default)"
    )
    approval_group.add_argument(
        "--no-approval",
        action="store_true",
        help="Disable human approval requirement"
    )

    # API settings
    api_group = parser.add_mutually_exclusive_group()
    api_group.add_argument(
        "--mock-api",
        action="store_true",
        default=True,
        help="Use mock API data instead of real API calls (default)"
    )
    api_group.add_argument(
        "--real-api",
        action="store_true",
        help="Use real API calls instead of mock data"
    )

    # Model configuration
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4.1-mini",
        help="Azure OpenAI deployment name (default: gpt-4.1-mini)"
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default="https://ally-frcentral.openai.azure.com/",
        help="Azure OpenAI endpoint URL"
    )

    # Tool descriptions
    descriptions_group = parser.add_mutually_exclusive_group()
    descriptions_group.add_argument(
        "--improved-descriptions",
        action="store_true",
        default=True,
        help="Use improved tool descriptions (default)"
    )
    descriptions_group.add_argument(
        "--no-improved-descriptions",
        action="store_true",
        help="Disable improved tool descriptions"
    )

    # Conversation management
    parser.add_argument(
        "--load",
        type=str,
        metavar="FILE",
        help="Load a previous conversation from JSON file"
    )

    # Display settings
    parser.add_argument(
        "--console-width",
        type=int,
        default=200,
        help="Console width for display (default: 200)"
    )

    return parser


def _configure_logging():
    """Configure logging to suppress logfire output."""
    logging.basicConfig(level=logging.WARNING)
    logfire.configure(scrubbing=False, console=False)
    logfire.instrument_pydantic_ai()
    logging.getLogger("logfire._internal").setLevel(logging.ERROR)
    logging.getLogger("logfire").setLevel(logging.ERROR)


def _display_configuration(
    console: Console,
    use_multi_agent: bool,
    require_approval: bool,
    use_mock_api: bool,
    use_improved: bool,
    model: str,
    load_path: str | None
):
    """Display the current configuration to the console."""
    console.print("\n[bold cyan]═" * 40 + "[/bold cyan]")
    console.print("[bold cyan]Meta Ally Terminal Chat[/bold cyan]")
    console.print("[bold cyan]═" * 40 + "[/bold cyan]\n")
    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Agent Mode: {'[green]Multi-Agent[/green]' if use_multi_agent else '[cyan]Single Agent[/cyan]'}")
    console.print(f"  Human Approval: {'[green]Enabled[/green]' if require_approval else '[dim]Disabled[/dim]'}")
    console.print(f"  API Mode: {'[yellow]Mock[/yellow]' if use_mock_api else '[green]Real[/green]'}")
    console.print(f"  Improved Descriptions: {'[green]Enabled[/green]' if use_improved else '[dim]Disabled[/dim]'}")
    console.print(f"  Model: [cyan]{model}[/cyan]")
    if load_path:
        console.print(f"  Load Conversation: [cyan]{load_path}[/cyan]")
    console.print()


def _create_agent_and_deps(
    factory: AgentFactory,
    console: Console,
    model_config,
    agent_config: AgentConfig,
    approval_callback,
):
    """
    Create the agent and dependencies based on configuration.

    Args:
        factory: Agent factory instance
        console: Rich Console instance
        model_config: Model configuration
        agent_config: Agent configuration settings
        approval_callback: Callback function for human approval

    Returns:
        Tuple of (agent, dependencies) instances.
    """
    if agent_config.use_multi_agent:
        console.print("[cyan]Creating multi-agent orchestrator with specialists...[/cyan]")
        agent = create_default_multi_agent_system(
            factory=factory,
            orchestrator_model=model_config,
            specialist_model=model_config,
            require_human_approval=agent_config.require_approval,
            approval_callback=approval_callback,
            tool_replacements=agent_config.tool_replacements,
            ai_knowledge_descriptions_path=agent_config.ai_knowledge_descriptions_path,
            ally_config_descriptions_path=agent_config.ally_config_descriptions_path,
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
            require_human_approval=agent_config.require_approval,
            approval_callback=approval_callback,
            tool_replacements=agent_config.tool_replacements,
            ai_knowledge_descriptions_path=agent_config.ai_knowledge_descriptions_path,
            ally_config_descriptions_path=agent_config.ally_config_descriptions_path,
        )
        deps = factory.create_dependencies()
        console.print("[green]✓ Hybrid assistant initialized[/green]")

    console.print(f"[dim]Model: {agent.model}[/dim]\n")
    return agent, deps


def _setup_agent_configuration(
    console: Console,
    use_mock_api: bool,
    use_improved: bool
) -> tuple[dict | None, tuple[str | None, str | None]]:
    """
    Set up tool replacements and description paths.

    Args:
        console: Rich Console instance
        use_mock_api: Whether to use mock API
        use_improved: Whether to use improved descriptions

    Returns:
        Tuple of (tool_replacements, descriptions_paths)
    """
    tool_replacements = None
    if use_mock_api:
        console.print("[yellow]Creating mock API tool replacements...[/yellow]")
        tool_replacements = create_ally_config_mock_tool_replacements()
        console.print(f"[green]✓ Created {len(tool_replacements)} mock tool replacements[/green]")

    descriptions_paths = (
        (
            "Data/improved_tool_descriptions/ai_knowledge_improved_descriptions.json",
            "Data/improved_tool_descriptions/ally_config_improved_descriptions.json"
        )
        if use_improved else (None, None)
    )

    return tool_replacements, descriptions_paths


def main():
    """
    Command-line interface for Meta Ally terminal chat.

    Run with: python -m meta_ally.ui.terminal_chat [OPTIONS]
    """
    args = _create_argument_parser().parse_args()

    _configure_logging()

    # Resolve configuration
    use_multi_agent = not args.single_agent
    require_approval = not args.no_approval if args.no_approval else args.approval
    use_mock_api = not args.real_api if args.real_api else args.mock_api
    use_improved = not args.no_improved_descriptions if args.no_improved_descriptions else args.improved_descriptions

    # Initialize console
    console = Console(width=args.console_width)

    _display_configuration(
        console, use_multi_agent, require_approval, use_mock_api,
        use_improved, args.model, args.load
    )

    # Create agent factory
    console.print("[dim]Initializing agent...[/dim]")
    factory = AgentFactory()

    model_config = create_azure_model_config(
        deployment_name=args.model,
        endpoint=args.endpoint,
        logger=factory.logger,
    )

    # Create approval callback if needed
    approval_callback = create_human_approval_callback(args.console_width) if require_approval else None

    # Set up tool replacements and description paths
    tool_replacements, descriptions_paths = _setup_agent_configuration(
        console, use_mock_api, use_improved
    )

    agent_config = AgentConfig(
        use_multi_agent=use_multi_agent,
        require_approval=require_approval,
        tool_replacements=tool_replacements,
        ai_knowledge_descriptions_path=descriptions_paths[0],
        ally_config_descriptions_path=descriptions_paths[1]
    )

    agent, deps = _create_agent_and_deps(
        factory, console, model_config, agent_config, approval_callback
    )

    start_chat_session(
        agent, deps, args.console_width,
        config={
            "use_multi_agent": use_multi_agent,
            "require_human_approval": require_approval,
            "use_mock_api": use_mock_api,
            "use_improved_descriptions": use_improved,
            "model_deployment_name": args.model,
        },
        load_conversation_from=args.load
    )


if __name__ == "__main__":
    main()
