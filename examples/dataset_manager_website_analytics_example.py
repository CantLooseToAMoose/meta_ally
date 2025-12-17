"""
Example usage of DatasetManager with INFORM Webseite analytics cases.

This example demonstrates:
1. Creating a HookLibrary with API operation hooks for test resource management
2. Loading cases from case_factory_analytics_example
3. Creating datasets with 3 variants for each case
4. Assigning appropriate pre-task hooks to manage API resources (copilot endpoints)
5. Saving the manager to disk using save()
6. Loading the manager back from disk using load()
"""

from pathlib import Path

from examples.case_factory_website_analytics_example import example_inform_webseite_analytics

from meta_ally.eval import DatasetManager
from meta_ally.eval.api_test_hooks import APITestHookLibrary
from meta_ally.eval.case_factory import MessageHistoryCase
from meta_ally.lib.auth_manager import AuthManager


def main():
    """Main example: Create datasets, save manager state, and load it back."""
    print("=" * 80)
    print("INFORM Webseite Analytics DatasetManager Example - Save and Load Manager State")
    print("=" * 80)

    # Step 1: Load cases from case_factory_analytics_example
    print("\n[1] Loading cases from case_factory_analytics_example...")
    original_dataset = example_inform_webseite_analytics()
    print(f"    ✓ Loaded {len(original_dataset.cases)} cases")

    # Step 2: Create DatasetManager
    print("\n[2] Creating DatasetManager...")
    manager = DatasetManager()
    print("    ✓ DatasetManager created")

    # Step 3: Create datasets with variants for each case
    print("\n[3] Creating datasets with 3 variants for each case...")
    for i, case in enumerate(original_dataset.cases, 1):
        print(f"    [{i}/{len(original_dataset.cases)}] Processing: {case.name}")

        # Convert Case to MessageHistoryCase
        message_history_case = MessageHistoryCase.from_case(case)

        # Create dataset with 3 variants
        dataset_id = manager.create_dataset_from_case(
            case=message_history_case,
            dataset_id=f"analytics_case_{i}",
            num_variants=3,
            name=case.name,
            description=f"INFORM Webseite analytics test case {i} with variants"
        )

    # Step 4: Display statistics
    print("\n[4] Dataset Statistics:")
    print("-" * 80)
    all_stats = manager.get_all_stats()
    for dataset_id, stats in all_stats.items():
        print(f"  • {dataset_id}: {stats['num_variants']} variants, {stats['total_cases']} total cases")

    # Step 5: Save manager state
    output_dir = Path(__file__).parent.parent / "Data" / "analytics"
    print(f"\n[5] Saving manager state to: {output_dir}")

    save_info = manager.save(
        directory=output_dir,
        save_built_datasets=True,
        overwrite=True
    )

    print(f"    ✓ Saved {save_info['num_datasets']} datasets")
    print(f"    ✓ Config files: {len(save_info['config_files'])}")
    print(f"    ✓ Dataset files: {len(save_info['dataset_files'])}")

    # Step 6: Load manager state
    print(f"\n[6] Loading manager state from: {output_dir}")

    # Create a new hook library for loading (must have same hooks registered)
    new_auth_manager = AuthManager()
    new_hook_library = APITestHookLibrary(new_auth_manager)

    # Load the manager
    loaded_manager = DatasetManager.load(
        directory=output_dir,
        hook_library=new_hook_library
    )

    print(f"    ✓ Loaded {len(loaded_manager.list_dataset_ids())} datasets")

    # Step 7: Verify loaded data
    print("\n[7] Verifying loaded datasets:")
    print("-" * 80)
    loaded_stats = loaded_manager.get_all_stats()
    for dataset_id, stats in loaded_stats.items():
        print(f"  • {dataset_id}: {stats['num_variants']} variants, {stats['total_cases']} total cases")

    # Step 8: Show one dataset visualization as example
    print("\n[8] Visualizing first dataset as example:")
    print("-" * 80)
    first_dataset_id = loaded_manager.list_dataset_ids()[0]
    loaded_manager.visualize_dataset_comparison(first_dataset_id)

    print("\n" + "=" * 80)
    print("✨ Example completed successfully! ✨")
    print("=" * 80)
    print(f"\nAll datasets saved to: {output_dir}")
    print("  - configs/: Dataset configurations (cases + variants)")
    print("  - datasets/: Built pydantic-evals datasets")
    print("  - metadata.json: Manager metadata")


if __name__ == "__main__":
    main()
