"""Example demonstrating DatasetManager for creating a dataset with variants only.

This example demonstrates:
1. Loading the ADD*ONE Sales Copilot dataset
2. Using DatasetManager to generate variants
3. Visualizing the dataset
4. Saving the variants-only dataset as JSON to datasets/addone folder
5. Loading the saved dataset back
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pathlib import Path
from case_factory_addone_example import example_addone_sales_copilot_creation
from src.eval.case_factory import MessageHistoryCase
from src.eval.dataset_manager import DatasetManager


def main():
    """Create a variants-only dataset and save as JSON to datasets/addone folder."""
    
    print("=" * 80)
    print("ADD*ONE Sales Copilot - Dataset Variants Creation")
    print("=" * 80)
    
    # Step 1: Load the ADD*ONE Sales Copilot dataset
    print("\n1. Loading ADD*ONE Sales Copilot dataset...")
    dataset = example_addone_sales_copilot_creation()
    print(f"   ✓ Loaded {len(dataset.cases)} test cases from ADD*ONE dataset")
    
    # Convert cases to MessageHistoryCase objects
    original_cases = [MessageHistoryCase.from_case(case) for case in dataset.cases]
    
    # Show the original case names
    print("\n   Original test cases:")
    for i, case in enumerate(original_cases, 1):
        print(f"     {i}. {case.name}")
    
    # Step 2: Use DatasetManager to create variants
    print("\n2. Creating variants using DatasetManager...")
    manager = DatasetManager()
    manager.add_cases(original_cases)
    
    # Create 2 variants per case
    print("   Generating variants (this may take a moment)...")
    variants_mapping = manager.create_variants(num_variants_per_case=2)
    
    total_variants = sum(len(v) for v in variants_mapping.values())
    print(f"   ✓ Created {total_variants} variants across {len(variants_mapping)} cases")
    
    print("\n   Variants per case:")
    for case_name, variants in variants_mapping.items():
        print(f"     - {case_name}: {len(variants)} variants")
    
    # Step 3: Save variants-only dataset as JSON
    print("\n3. Visualizing the dataset...")
    
    # Show summary only
    print("\n   a) Summary view:")
    manager.visualize(show_details=False)
    
    # Step 4: Save variants-only dataset as JSON
    print("\n4. Saving variants-only dataset as JSON...")
    
    output_dir = Path("datasets/addone")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON with only variants (no originals)
    json_path = output_dir / "addone_sales_copilot_variants.json"
    manager.save_dataset(
        path=json_path,
        name="ADD*ONE Sales Copilot Variants",
        include_originals=False,  # Only variants
        include_variants=True,
        fmt="json"
    )
    print(f"   ✓ Saved to JSON: {json_path}")
    
    # Step 5: Load the saved dataset
    print("\n5. Loading the saved dataset...")
    loaded_dataset = DatasetManager.load_dataset(json_path)
    print(f"   ✓ Loaded {len(loaded_dataset.cases)} cases from {json_path}")
    print(f"   ✓ Dataset name: {loaded_dataset.name}")
    
    # Show loaded case names
    print("\n   Loaded test cases:")
    for i, case in enumerate(loaded_dataset.cases[:5], 1):  # Show first 5
        print(f"     {i}. {case.name}")
    if len(loaded_dataset.cases) > 5:
        print(f"     ... and {len(loaded_dataset.cases) - 5} more cases")
    
    # Step 6: Visualize a specific case with its variants
    print("\n6. Visualizing first case with its variants...")
    first_case_name = original_cases[0].name
    manager.visualize_variants_comparison(first_case_name)
    
    # Step 7: Show dataset statistics
    print("\n7. Dataset statistics:")
    stats = manager.get_stats()
    print(f"   - Original cases: {stats['original_cases']}")
    print(f"   - Variant cases: {stats['variant_cases']}")
    print(f"   - Total cases: {stats['total_cases']}")
    print(f"   - Cases saved: {stats['variant_cases']} (variants only)")
    
    print("\n" + "=" * 80)
    print("✓ Dataset with variants created successfully!")
    print("=" * 80)
    
    # Show file info
    size = json_path.stat().st_size
    print(f"\nGenerated file: {json_path} ({size:,} bytes)")


if __name__ == "__main__":
    main()
