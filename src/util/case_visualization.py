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
