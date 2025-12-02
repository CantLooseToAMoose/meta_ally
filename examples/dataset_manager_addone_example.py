"""Example usage of DatasetManager with ADD*ONE sales copilot cases.

This example demonstrates:
1. Creating a HookLibrary with debug hooks
2. Loading cases from case_factory_addone_example
3. Creating datasets with 3 variants for each case
4. Saving the manager to disk using save()
5. Loading the manager back from disk using load()
"""

from pathlib import Path
from case_factory_addone_example import example_addone_sales_copilot_creation
from meta_ally.eval.case_factory import MessageHistoryCase
from meta_ally.eval import DatasetManager, HookLibrary


class DebugHookLibrary(HookLibrary):
    """Custom hook library with simple debug print hooks for ADD*ONE example."""
    
    def register_hooks(self) -> None:
        """Register debug hooks that print information about task execution."""
        
        def debug_pre_hook(inputs):
            """Debug hook that prints before task execution."""
            print(f"\n[DEBUG PRE-HOOK] Starting task with {len(inputs)} input messages")
            if inputs:
                print(f"[DEBUG PRE-HOOK] First message type: {type(inputs[0])}")
            return inputs
        
        def debug_post_hook(result):
            """Debug hook that prints after task execution."""
            print("[DEBUG POST-HOOK] Task completed")
            print(f"[DEBUG POST-HOOK] Result type: {type(result)}")
            return result
        
        self.register_hook(
            hook_id="debug_pre",
            hook=debug_pre_hook,
            name="Debug Pre-Task Hook",
            description="Prints debug information before task execution",
            hook_type="pre"
        )
        
        self.register_hook(
            hook_id="debug_post",
            hook=debug_post_hook,
            name="Debug Post-Task Hook",
            description="Prints debug information after task execution",
            hook_type="post"
        )


def main():
    """Main example: Create datasets, save manager state, and load it back."""
    
    print("=" * 80)
    print("ADD*ONE DatasetManager Example - Save and Load Manager State")
    print("=" * 80)
    
    # Step 1: Load cases from case_factory_addone_example
    print("\n[1] Loading cases from case_factory_addone_example...")
    original_dataset = example_addone_sales_copilot_creation()
    print(f"    ✓ Loaded {len(original_dataset.cases)} cases")
    
    # Step 2: Create HookLibrary and DatasetManager
    print("\n[2] Creating HookLibrary with debug hooks...")
    hook_library = DebugHookLibrary()
    print(f"    ✓ Registered hooks: {[h.hook_id for h in hook_library.list_hooks()]}")
    
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
        
        # Set hooks for this dataset
        manager.set_dataset_hooks(
            dataset_id=dataset_id,
            pre_task_hook_id="debug_pre",
            post_task_hook_id="debug_post"
        )
        
        print("        ✓ Created with 3 variants")
    
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
    new_hook_library = DebugHookLibrary()
    
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
