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
        case: The test case to visualize (MessageHistoryCase, Case, or similar)
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
    
    # Get input messages - handle both Case (with .inputs) and MessageHistoryCase (with .input_messages)
    input_messages = getattr(case, 'input_messages', None) or getattr(case, 'inputs', [])
    
    # Display messages in chat format
    for i, msg in enumerate(input_messages):
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


def visualize_dataset(dataset,
                      show_details: bool = True,
                      max_cases: Optional[int] = None,
                      console_instance: Optional[Console] = None):
    """Visualize all cases in a dataset with an overview table and optional detailed views.
    
    Args:
        dataset: The dataset to visualize (pydantic_evals.Dataset or similar with .cases attribute)
        show_details: If True, show detailed view of each case. If False, only show summary table.
        max_cases: Optional limit on number of cases to visualize in detail (useful for large datasets)
        console_instance: Optional Console instance to use (defaults to module console)
    """
    _console = console_instance or console
    
    # Get cases from dataset
    cases = dataset.cases if hasattr(dataset, 'cases') else []
    
    if not cases:
        _console.print("[yellow]⚠️  Dataset is empty - no cases to visualize[/yellow]")
        return
    
    # Print dataset header
    dataset_name = getattr(dataset, 'name', 'Unnamed Dataset')
    _console.print(f"\n[bold magenta]{'═' * 80}[/bold magenta]")
    _console.print(f"[bold magenta]📊 Dataset: {dataset_name}[/bold magenta]")
    _console.print(f"[bold magenta]{'═' * 80}[/bold magenta]\n")
    
    # Create summary table
    table = Table(title="Dataset Overview", show_header=True, header_style="bold cyan")
    table.add_column("Case #", style="cyan", width=8, justify="right")
    table.add_column("Case Name", style="white", no_wrap=False)
    table.add_column("Messages", justify="center", style="green", width=10)
    table.add_column("Has Expected", justify="center", style="yellow", width=12)
    table.add_column("Type", style="magenta", width=12)
    
    # Analyze cases and populate table
    for idx, case in enumerate(cases, 1):
        case_name = getattr(case, 'name', f'Case {idx}')
        
        # Count messages - handle both Case (with .inputs) and MessageHistoryCase (with .input_messages)
        input_messages = getattr(case, 'input_messages', None) or getattr(case, 'inputs', [])
        num_messages = len(input_messages) if input_messages else 0
        
        # Check for expected output
        has_expected = "✓" if (hasattr(case, 'expected_output') and case.expected_output) else "✗"
        expected_style = "green" if has_expected == "✓" else "dim"
        
        # Determine case type (original vs variant)
        case_type = "Variant" if "variant" in case_name.lower() else "Original"
        
        table.add_row(
            str(idx),
            case_name,
            str(num_messages),
            Text(has_expected, style=expected_style),
            case_type
        )
    
    _console.print(table)
    
    # Print statistics
    _console.print(f"\n[bold]Statistics:[/bold]")
    _console.print(f"  • Total cases: [cyan]{len(cases)}[/cyan]")
    
    originals = sum(1 for c in cases if "variant" not in getattr(c, 'name', '').lower())
    variants = len(cases) - originals
    _console.print(f"  • Original cases: [cyan]{originals}[/cyan]")
    _console.print(f"  • Variant cases: [cyan]{variants}[/cyan]")
    
    # Calculate total messages - handle both Case and MessageHistoryCase
    total_messages = 0
    for c in cases:
        input_messages = getattr(c, 'input_messages', None) or getattr(c, 'inputs', [])
        total_messages += len(input_messages) if input_messages else 0
    _console.print(f"  • Total messages: [cyan]{total_messages}[/cyan]")
    
    # Show detailed views if requested
    if show_details:
        _console.print(f"\n[bold cyan]{'─' * 80}[/bold cyan]")
        _console.print(f"[bold cyan]Detailed Case Views[/bold cyan]")
        _console.print(f"[bold cyan]{'─' * 80}[/bold cyan]")
        
        # Limit number of cases if specified
        cases_to_show = cases[:max_cases] if max_cases else cases
        
        if max_cases and len(cases) > max_cases:
            _console.print(f"\n[dim]Showing first {max_cases} of {len(cases)} cases...[/dim]\n")
        
        for idx, case in enumerate(cases_to_show, 1):
            visualize_single_case(case, console_instance=_console)
            
            # Add separator between cases (except after last one)
            if idx < len(cases_to_show):
                _console.print(f"[dim]{'─' * 80}[/dim]\n")
        
        if max_cases and len(cases) > max_cases:
            _console.print(f"\n[dim]... and {len(cases) - max_cases} more cases[/dim]")
    else:
        _console.print(f"\n[dim]💡 Tip: Set show_details=True to see detailed case views[/dim]")
    
    _console.print()


def visualize_dataset_from_config(
    config,
    show_details: bool = True,
    max_cases: Optional[int] = None,
    include_original: bool = True,
    include_variants: bool = True,
    console_instance: Optional[Console] = None
) -> None:
    """Visualize a dataset built from a DatasetConfig.
    
    This function builds a dataset from the config and visualizes it.
    
    Args:
        config: DatasetConfig object containing the original case and variants
        show_details: If True, show detailed view of each case
        max_cases: Optional limit on number of cases to visualize in detail
        include_original: Whether to include the original case
        include_variants: Whether to include variant cases
        console_instance: Optional Console instance to use for output
    """
    from pydantic_evals import Dataset
    
    # Build cases list
    cases = []
    if include_original:
        cases.append(config.original_case)
    if include_variants:
        cases.extend(config.variants)
    
    # Create dataset without metadata (Dataset doesn't accept it)
    dataset = Dataset(
        name=config.name,
        cases=cases
    )
    
    # Visualize using existing function
    visualize_dataset(
        dataset,
        show_details=show_details,
        max_cases=max_cases,
        console_instance=console_instance
    )


def visualize_dataset_comparison(
    config,
    console_instance: Optional[Console] = None
) -> None:
    """Visualize a dataset's original case and all its variants for comparison.
    
    Args:
        config: DatasetConfig object containing the original case and variants
        console_instance: Optional Console instance to use for output
    """
    _console = console_instance or console
    
    # Print header
    _console.print(f"\n[bold magenta]{'═' * 80}[/bold magenta]")
    _console.print(f"[bold magenta]🔍 Dataset: {config.name}[/bold magenta]")
    _console.print(f"[bold magenta]{'═' * 80}[/bold magenta]\n")
    
    # Show original
    _console.print("[bold cyan]Original Case:[/bold cyan]")
    visualize_single_case(config.original_case, console_instance=_console)
    
    # Show each variant
    if config.variants:
        _console.print(f"\n[bold green]{'─' * 80}[/bold green]")
        _console.print(f"[bold green]Variants ({len(config.variants)} total):[/bold green]")
        _console.print(f"[bold green]{'─' * 80}[/bold green]\n")
        
        for idx, variant in enumerate(config.variants, 1):
            visualize_single_case(
                variant,
                title=f"{variant.name}",
                console_instance=_console
            )
            if idx < len(config.variants):
                _console.print(f"[dim]{'─' * 80}[/dim]\n")
    else:
        _console.print("\n[yellow]No variants created for this dataset yet.[/yellow]")
    
    _console.print()


def visualize_all_datasets_summary(
    datasets_dict: dict,
    show_details: bool = False,
    console_instance: Optional[Console] = None
) -> None:
    """Visualize summary of all datasets.
    
    Args:
        datasets_dict: Dictionary mapping dataset_id to DatasetConfig objects
        show_details: If True, show detailed stats for each dataset
        console_instance: Optional Console instance to use for output
    """
    _console = console_instance or console
    
    if not datasets_dict:
        _console.print("[yellow]No datasets created yet.[/yellow]")
        return
    
    _console.print(f"\n[bold cyan]{'═' * 80}[/bold cyan]")
    _console.print("[bold cyan]📊 All Datasets Summary[/bold cyan]")
    _console.print(f"[bold cyan]{'═' * 80}[/bold cyan]\n")
    
    # Create summary table
    table = Table(title="Datasets Overview", show_header=True, header_style="bold magenta")
    table.add_column("Dataset ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Original Case", style="yellow")
    table.add_column("Variants", justify="right", style="blue")
    table.add_column("Total Cases", justify="right", style="bold")
    
    for dataset_id, config in datasets_dict.items():
        num_variants = len(config.variants)
        total_cases = 1 + num_variants  # original + variants
        
        table.add_row(
            dataset_id,
            config.name,
            config.original_case.name,
            str(num_variants),
            str(total_cases)
        )
    
    _console.print(table)
    _console.print()
    
    if show_details:
        _console.print("[bold]Detailed Statistics:[/bold]\n")
        for dataset_id, config in datasets_dict.items():
            has_pre_hook = config.pre_task_hook is not None
            has_post_hook = config.post_task_hook is not None
            
            _console.print(f"[cyan]{dataset_id}:[/cyan]")
            _console.print(f"  Name: {config.name}")
            _console.print(f"  Original: {config.original_case.name}")
            _console.print(f"  Variants: {len(config.variants)}")
            _console.print(f"  Total Cases: {1 + len(config.variants)}")
            _console.print(f"  Has Pre-Hook: {has_pre_hook}")
            _console.print(f"  Has Post-Hook: {has_post_hook}")
            _console.print()
