"""Example for creating and visualizing case variants from the ADD*ONE Sales Copilot dataset.

This example demonstrates:
1. Loading an existing test dataset
2. Creating multiple variants for each test case
3. Visualizing differences between original and variants using rich (side-by-side)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from case_factory_addone_example import example_addone_sales_copilot_creation
from src.eval.case_factory import MessageHistoryCase, create_case_variant
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


console = Console(width=200)  # Increase console width for side-by-side display


def format_message_history(messages) -> str:
    """Format message history for better readability.
    
    Args:
        messages: List of messages to format
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


def show_side_by_side_comparison(original_case: MessageHistoryCase, 
                                   variant_case: MessageHistoryCase,
                                   variant_num: int):
    """Display original and variant side by side using rich panels.
    
    Args:
        original_case: The original test case
        variant_case: The variant test case
        variant_num: The variant number for labeling
    """
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
    console.print("\n")
    console.print(Columns([original_panel, variant_panel], equal=False, expand=False, padding=(0, 2)))
    console.print("\n")


def create_variants_for_dataset(dataset, num_variants: int = 2, 
                                show_visualizations: bool = True):
    """Create variants for all cases in a dataset and optionally visualize them.
    
    Args:
        dataset: The pydantic-eval Dataset to create variants for
        num_variants: Number of variants to create per case (default: 2)
        show_visualizations: Whether to show side-by-side comparisons (default: True)
    """
    console.print(f"\n[bold yellow]Creating {num_variants} variants for each of {len(dataset.cases)} test cases...[/bold yellow]\n")
    
    all_variants = {}
    
    for case_idx, case in enumerate(dataset.cases, 1):
        console.print(f"[bold]Processing Case {case_idx}/{len(dataset.cases)}:[/bold] {case.name}")
        
        # Convert to MessageHistoryCase
        original_case = MessageHistoryCase.from_case(case)
        variants = []
        
        # Create multiple variants
        for variant_num in range(1, num_variants + 1):
            console.print(f"  Generating variant {variant_num}/{num_variants}...")
            
            try:
                variant_case = create_case_variant(original_case)
                variant_case.name = f"{original_case.name} - Variant {variant_num}"
                variants.append(variant_case)
                
                # Show side-by-side comparison if requested
                if show_visualizations:
                    show_side_by_side_comparison(original_case, variant_case, variant_num)
                
            except Exception as e:
                console.print(f"  [red]✗[/red] Error creating variant {variant_num}: {e}")
                continue
        
        # Store variants for this case
        all_variants[case.name] = {
            'original': original_case,
            'variants': variants
        }
        
        console.print(f"  [green]✓[/green] Created {len(variants)} variants for this case\n")
    
    return all_variants


def create_summary_table(all_variants):
    """Create a summary table showing variant creation statistics.
    
    Args:
        all_variants: Dictionary mapping case names to their original and variants
    """
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
    
    console.print("\n")
    console.print(table)
    console.print("\n")


def main():
    """Main function to demonstrate variant creation and visualization."""
    
    # Configuration
    NUM_VARIANTS = 2  # Number of variants to create per case
    SHOW_VISUALIZATIONS = True  # Show side-by-side comparisons in console
    
    console.print("[bold blue]ADD*ONE Sales Copilot - Variant Generation & Visualization[/bold blue]")
    console.print("=" * 80 + "\n")
    
    # Load the original dataset
    console.print("Loading ADD*ONE Sales Copilot dataset...")
    dataset = example_addone_sales_copilot_creation()
    console.print(f"[green]✓[/green] Loaded {len(dataset.cases)} test cases\n")
    
    # Create variants and visualize
    all_variants = create_variants_for_dataset(
        dataset=dataset,
        num_variants=NUM_VARIANTS,
        show_visualizations=SHOW_VISUALIZATIONS
    )
    
    # Show summary
    create_summary_table(all_variants)
    
    # Final statistics
    total_variants = sum(len(data['variants']) for data in all_variants.values())
    console.print(f"[bold green]✓ Successfully created {total_variants} variants across {len(all_variants)} test cases[/bold green]")


if __name__ == "__main__":
    main()
