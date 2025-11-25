"""Utilities for visualizing test cases and their variants.

This module provides functions for displaying case comparisons using rich formatting.
"""

from typing import List, Optional
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


# Default console with wider width for side-by-side display
console = Console(width=200)


def format_message_parts(parts: List) -> str:
    """Format message parts for display.
    
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
            if part_type in ['UserPromptPart', 'SystemPromptPart']:
                output.append(f"[dim]{part_type}:[/dim]\n{content}")
            else:
                output.append(f"[dim]{part_type}:[/dim] {content}")
        elif hasattr(part, 'tool_name'):
            # ToolCallPart
            output.append(f"[bold yellow]🔧 Tool Call:[/bold yellow] {part.tool_name}")
            output.append(f"[dim]Args:[/dim] {part.args}")
    return "\n".join(output)


def visualize_single_case(case, 
                          title: Optional[str] = None,
                          console_instance: Optional[Console] = None):
    """Visualize a single test case in a chat-like format.
    
    Args:
        case: The test case to visualize (MessageHistoryCase or similar)
        title: Optional custom title for the panel (defaults to case name)
        console_instance: Optional Console instance to use (defaults to module console)
    """
    _console = console_instance or console
    
    # Calculate panel width as 70% of console width
    panel_width = int(_console.width * 0.7)
    
    # Print title
    panel_title = title or getattr(case, 'name', 'Test Case')
    _console.print(f"\n[bold cyan]{'=' * 80}[/bold cyan]")
    _console.print(f"[bold cyan]{panel_title}[/bold cyan]")
    _console.print(f"[bold cyan]{'=' * 80}[/bold cyan]\n")
    
    # Add description if available
    if hasattr(case, 'description') and case.description:
        desc_panel = Panel(
            case.description,
            title="[bold]Description[/bold]",
            border_style="dim",
            padding=(0, 1)
        )
        _console.print(desc_panel)
        _console.print()
    
    # Display messages in chat format
    for i, msg in enumerate(case.input_messages):
        msg_type = type(msg).__name__
        
        # Format the message content
        content = format_message_parts(msg.parts)
        
        if msg_type == "ModelRequest":
            # User messages - aligned left with blue border
            panel = Panel(
                content,
                title="[bold blue]👤 User[/bold blue]",
                border_style="blue",
                padding=(1, 2),
                width=panel_width
            )
            _console.print(panel)
            
        elif msg_type == "ModelResponse":
            # Model responses - aligned right with green border
            from rich.padding import Padding
            panel = Panel(
                content,
                title="[bold green]🤖 Assistant[/bold green]",
                border_style="green",
                padding=(1, 2),
                width=panel_width
            )
            # Calculate left padding to align to the right
            left_padding = _console.width - panel_width
            padded_panel = Padding(panel, (0, 0, 0, left_padding))
            _console.print(padded_panel)
    
    # Add expected output if available
    if hasattr(case, 'expected_output') and case.expected_output:
        _console.print(f"\n[bold magenta]{'─' * 80}[/bold magenta]")
        expected = case.expected_output
        expected_text = ""
        
        # Show output message if present
        if hasattr(expected, 'output_message') and expected.output_message:
            expected_text += "[bold cyan]Expected Message:[/bold cyan]\n"
            expected_text += f"{expected.output_message}\n\n"
        
        # Show tool calls if present
        if hasattr(expected, 'tool_calls') and expected.tool_calls:
            expected_text += "[bold green]Expected Tool Calls:[/bold green]\n"
            for i, tool_call in enumerate(expected.tool_calls, 1):
                expected_text += f"  {i}. [yellow]🔧 {tool_call.tool_name}[/yellow]\n"
                expected_text += f"     Args: {tool_call.args}\n"
                expected_text += f"     ID: {tool_call.tool_call_id}\n"
            expected_text += "\n"
        
        # Show model messages if present
        if hasattr(expected, 'model_messages') and expected.model_messages:
            expected_text += "[bold yellow]Expected Model Messages:[/bold yellow]\n"
            expected_text += format_message_history(expected.model_messages)
        
        if expected_text:
            expected_panel = Panel(
                expected_text.strip(),
                title="[bold magenta]Expected Output[/bold magenta]",
                border_style="magenta",
                padding=(1, 2)
            )
            _console.print(expected_panel)
    
    # Add metadata if available
    if hasattr(case, 'metadata') and case.metadata:
        metadata_text = ""
        for key, value in case.metadata.items():
            metadata_text += f"[cyan]{key}:[/cyan] {value}\n"
        
        metadata_panel = Panel(
            metadata_text.strip(),
            title="[bold]Metadata[/bold]",
            border_style="dim",
            padding=(0, 1)
        )
        _console.print(metadata_panel)
    
    _console.print()


def format_message_history(messages: List) -> str:
    """Format message history for better readability.
    
    Args:
        messages: List of messages to format
        
    Returns:
        Formatted string representation of the message history
    """
    output = []
    for i, msg in enumerate(messages):
        output.append(f"[bold]Message {i+1}:[/bold]")
        for part in msg.parts:
            if hasattr(part, 'content'):
                # UserPromptPart, SystemPromptPart, or ToolReturnPart
                part_type = type(part).__name__
                content = part.content if isinstance(part.content, str) else str(part.content)
                output.append(f"  [{part_type}]")
                output.append(f"  {content}")
            elif hasattr(part, 'tool_name'):
                # ToolCallPart
                output.append(f"  [ToolCall] {part.tool_name}")
                output.append(f"  Args: {part.args}")
        output.append("")
    return "\n".join(output)


def show_side_by_side_comparison(original_case, 
                                   variant_case,
                                   variant_num: int,
                                   console_instance: Optional[Console] = None):
    """Display original and variant side by side using rich panels.
    
    Args:
        original_case: The original test case (MessageHistoryCase)
        variant_case: The variant test case (MessageHistoryCase)
        variant_num: The variant number for labeling
        console_instance: Optional Console instance to use (defaults to module console)
    """
    _console = console_instance or console
    
    # Format the message histories
    original_text = format_message_history(original_case.input_messages)
    variant_text = format_message_history(variant_case.input_messages)
    
    # Create panels with fixed width
    original_panel = Panel(
        original_text,
        title="[bold cyan]Original[/bold cyan]",
        border_style="cyan",
        padding=(1, 1),
        width=95
    )
    
    variant_panel = Panel(
        variant_text,
        title=f"[bold green]Variant {variant_num}[/bold green]",
        border_style="green",
        padding=(1, 1),
        width=95
    )
    
    # Display side by side with explicit configuration
    _console.print("\n")
    _console.print(Columns([original_panel, variant_panel], equal=False, expand=False, padding=(0, 2)))
    _console.print("\n")


def create_summary_table(all_variants: dict, console_instance: Optional[Console] = None):
    """Create a summary table showing variant creation statistics.
    
    Args:
        all_variants: Dictionary mapping case names to their original and variants.
                     Expected structure: {case_name: {'original': case, 'variants': [...]}}
        console_instance: Optional Console instance to use (defaults to module console)
    """
    _console = console_instance or console
    
    table = Table(title="Variant Creation Summary", show_header=True, header_style="bold magenta")
    table.add_column("Case #", style="cyan", width=8)
    table.add_column("Case Name", style="white")
    table.add_column("Variants Created", justify="center", style="green")
    table.add_column("Status", justify="center")
    
    for idx, (case_name, data) in enumerate(all_variants.items(), 1):
        num_variants = len(data['variants'])
        status = "✓" if num_variants > 0 else "✗"
        status_style = "green" if num_variants > 0 else "red"
        
        table.add_row(
            str(idx),
            case_name,
            str(num_variants),
            Text(status, style=status_style)
        )
    
    _console.print("\n")
    _console.print(table)
    _console.print("\n")
