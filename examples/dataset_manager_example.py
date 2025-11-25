"""Example demonstrating DatasetManager for creating and managing datasets with variants.

This example demonstrates:
1. Loading the ADD*ONE Sales Copilot dataset
2. Using DatasetManager to generate variants
3. Building datasets with different configurations
4. Saving datasets to YAML/JSON files
5. Loading datasets back from files
6. Dataset statistics and querying
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pathlib import Path
from case_factory_addone_example import example_addone_sales_copilot_creation
from src.eval.case_factory import MessageHistoryCase
from src.eval.dataset_manager import (
    DatasetManager,
    save_dataset_with_variants,
    load_dataset_from_file
)


def main():
    """Demonstrate DatasetManager functionality with ADD*ONE Sales Copilot dataset."""
    
    print("=" * 80)
    print("ADD*ONE Sales Copilot - DatasetManager Example")
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
    
    # Step 3: Get statistics
    print("\n3. Dataset statistics:")
    stats = manager.get_stats()
    print(f"   - Original cases: {stats['original_cases']}")
    print(f"   - Variant cases: {stats['variant_cases']}")
    print(f"   - Total cases: {stats['total_cases']}")
    
    # Step 4: Build different dataset configurations
    print("\n4. Building datasets with different configurations...")
    
    # Dataset with both originals and variants
    dataset_full = manager.build_dataset(
        name="Full Dataset with Variants",
        include_originals=True,
        include_variants=True
    )
    print(f"   ✓ Full dataset: {len(dataset_full.cases)} cases")
    
    # Dataset with only variants
    dataset_variants_only = manager.build_dataset(
        name="Variants Only Dataset",
        include_originals=False,
        include_variants=True
    )
    print(f"   ✓ Variants only: {len(dataset_variants_only.cases)} cases")
    
    # Dataset with only originals
    dataset_originals_only = manager.build_dataset(
        name="Originals Only Dataset",
        include_originals=True,
        include_variants=False
    )
    print(f"   ✓ Originals only: {len(dataset_originals_only.cases)} cases")
    
    # Step 5: Save datasets to files
    print("\n5. Saving datasets to files...")
    
    output_dir = Path("addone_datasets")
    output_dir.mkdir(exist_ok=True)
    
    # Save as YAML
    yaml_path = output_dir / "addone_sales_copilot_with_variants.yaml"
    manager.save_dataset(
        path=yaml_path,
        name="ADD*ONE Sales Copilot with Variants",
        include_originals=True,
        include_variants=True,
        fmt="yaml"
    )
    print(f"   ✓ Saved to YAML: {yaml_path}")
    
    # Save as JSON
    json_path = output_dir / "addone_sales_copilot_with_variants.json"
    manager.save_dataset(
        path=json_path,
        name="ADD*ONE Sales Copilot with Variants",
        include_originals=True,
        include_variants=True,
        fmt="json"
    )
    print(f"   ✓ Saved to JSON: {json_path}")
    
    # Step 6: Load dataset back from file
    print("\n6. Loading dataset from file...")
    loaded_dataset = load_dataset_from_file(yaml_path)
    print(f"   ✓ Loaded dataset: {loaded_dataset.name}")
    print(f"   ✓ Number of cases: {len(loaded_dataset.cases)}")
    
    # Step 7: Query specific variants
    print("\n7. Querying specific variants...")
    
    # Get variants for the first case
    first_case_name = original_cases[0].name
    case_variants = manager.get_variants(first_case_name)
    print(f"   ✓ Retrieved {len(case_variants)} variants for '{first_case_name}'")
    for i, variant in enumerate(case_variants, 1):
        print(f"     - {variant.name}")
    
    # Step 8: Demonstrate convenience function with a subset
    print("\n8. Using convenience function to save variants-only dataset...")
    
    # Save just variants (useful for testing variation quality)
    variants_only_path = output_dir / "addone_variants_only.yaml"
    
    # Use the convenience function with just one case for demonstration
    sample_cases = [original_cases[0]]
    save_dataset_with_variants(
        cases=sample_cases,
        path=variants_only_path,
        num_variants_per_case=3,
        name="ADD*ONE Sample Variants",
        include_originals=False,  # Only variants
        include_variants=True,
        fmt="yaml"
    )
    print(f"   ✓ Saved variants-only dataset: {variants_only_path}")
    
    # Load and verify
    loaded_variants = load_dataset_from_file(variants_only_path)
    print(f"   ✓ Verified: {len(loaded_variants.cases)} cases (3 variants, no originals)")
    
    print("\n" + "=" * 80)
    print("✓ ADD*ONE DatasetManager example completed successfully!")
    print("=" * 80)
    
    # Show what files were created
    print("\nGenerated files in addone_datasets/:")
    for file in sorted(output_dir.glob("*")):
        size = file.stat().st_size
        print(f"  - {file.name} ({size:,} bytes)")


if __name__ == "__main__":
    main()
