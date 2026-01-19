"""
Example usage of DatasetManager with ADD*ONE sales copilot cases.

This example demonstrates:
1. Creating a HookLibrary with API operation hooks for test resource management
2. Loading cases from case_factory_addone_example
3. Creating datasets with 3 variants for each case
4. Assigning appropriate pre-task hooks to manage API resources (sources, collections, copilots)
5. Saving the manager to disk using save()
6. Loading the manager back from disk using load()
"""

from pathlib import Path

from case_factory_addone_example import example_addone_sales_copilot_creation

from meta_ally.auth.auth_manager import AuthManager
from meta_ally.eval import DatasetManager
from meta_ally.eval.api_test_hooks import APITestHookLibrary
from meta_ally.eval.case_factory import MessageHistoryCase


def main():  # noqa: PLR0915
    """Main example: Create datasets, save manager state, and load it back."""
    print("=" * 80)
    print("ADD*ONE DatasetManager Example - Save and Load Manager State")
    print("=" * 80)

    # Step 1: Load cases from case_factory_addone_example
    print("\n[1] Loading cases from case_factory_addone_example...")
    original_dataset = example_addone_sales_copilot_creation()
    print(f"    ✓ Loaded {len(original_dataset.cases)} cases")

    # Step 2: Create HookLibrary with API operation hooks and DatasetManager
    print("\n[2] Creating APITestHookLibrary with API operation hooks...")
    auth_manager = AuthManager()
    hook_library = APITestHookLibrary(auth_manager)
    hooks_list = hook_library.list_hooks()
    print(f"    ✓ Registered {len(hooks_list)} hooks:")
    for hook in hooks_list:
        print(f"      • {hook.hook_id}: {hook.name}")

    print("\n[3] Creating DatasetManager...")
    manager = DatasetManager(hook_library=hook_library)
    print("    ✓ DatasetManager created")

    # Step 3: Create datasets with variants for each case
    print("\n[4] Creating datasets with 3 variants for each case...")
    for i, case in enumerate(original_dataset.cases, 1):
        print(f"    [{i}/{len(original_dataset.cases)}] Processing: {case.name}")

        # Convert Case to MessageHistoryCase
        message_history_case = MessageHistoryCase.from_case(case)

        # Create dataset with 3 variants
        dataset_id = manager.create_dataset_from_case(
            case=message_history_case,
            dataset_id=f"addone_case_{i}",
            num_variants=3,
            name=case.name,
            description=f"ADD*ONE sales copilot test case {i} with variants"
        )

        # Set appropriate hooks based on the case
        # Case 4: Tests creating sources and collections - need to delete them first
        # Case 5: Tests creating copilot - need sources/collections to exist, copilot to not exist
        if i == 4:  # Case 4: Creating sources and collections
            manager.set_dataset_hooks(
                dataset_id=dataset_id,
                pre_task_hook_id="delete_addone_sources_and_collection"
            )
            print("        ✓ Created with 3 variants + cleanup hook (deletes sources/collections)")
        elif i == 5:  # Case 5: Creating copilot
            manager.set_dataset_hooks(
                dataset_id=dataset_id,
                pre_task_hook_id="cleanup_and_setup_addone_resources"
            )
            print("        ✓ Created with 3 variants + setup hook (ensures sources exist, copilot doesn't)")
        else:
            print("        ✓ Created with 3 variants (no hooks needed)")

    # Step 4: Display statistics
    print("\n[5] Dataset Statistics:")
    print("-" * 80)
    all_stats = manager.get_all_stats()
    for dataset_id, stats in all_stats.items():
        print(f"  • {dataset_id}: {stats['num_variants']} variants, {stats['total_cases']} total cases")

    # Step 5: Save manager state
    output_dir = Path(__file__).parent.parent / "Data" / "add_one"
    print(f"\n[6] Saving manager state to: {output_dir}")

    save_info = manager.save(
        directory=output_dir,
        save_built_datasets=True,
        overwrite=True
    )

    print(f"    ✓ Saved {save_info['num_datasets']} datasets")
    print(f"    ✓ Config files: {len(save_info['config_files'])}")
    print(f"    ✓ Dataset files: {len(save_info['dataset_files'])}")

    # Step 6: Load manager state
    print(f"\n[7] Loading manager state from: {output_dir}")

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
    print("\n[8] Verifying loaded datasets:")
    print("-" * 80)
    loaded_stats = loaded_manager.get_all_stats()
    for dataset_id, stats in loaded_stats.items():
        print(f"  • {dataset_id}: {stats['num_variants']} variants, {stats['total_cases']} total cases")

    # Step 8: Show one dataset visualization as example
    print("\n[9] Visualizing first dataset as example:")
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
