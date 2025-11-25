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
from src.util.case_visualization import (
    console,
    show_side_by_side_comparison,
    create_summary_table
)


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
                # Pass previously created variants to avoid duplicates
                variant_case = create_case_variant(original_case, previous_variants=variants)
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
