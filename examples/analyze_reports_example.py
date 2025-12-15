"""
Example usage of the analyze_reports utility.

This example demonstrates how to:
1. Load evaluation results from disk
2. Generate LaTeX tables for specific datasets
3. Generate LaTeX summary tables for entire runs
"""

from meta_ally.util.analyze_reports import (
    create_dataset_table,
    create_run_summary_table,
    load_evaluation_run,
)


def main():
    """Run the analyze_reports example."""
    # Load a specific run
    print("Loading evaluation run...")
    run_data = load_evaluation_run(
        base_dir="evaluation_results",
        run_id="add_one_sales_copilot_eval_20251209_093432"
    )

    print(f"✓ Loaded run: {run_data['metadata']['run_id']}")
    print(f"  Task: {run_data['metadata']['task_name']}")
    print(f"  Datasets: {', '.join(run_data['metadata']['dataset_ids'])}")
    print()

    # Example 1: Generate a table for a specific dataset
    print("=" * 80)
    print("EXAMPLE 1: Dataset Table (addone_case_1)")
    print("=" * 80)
    print()

    dataset_table = create_dataset_table(
        reports=run_data['reports'],
        dataset_id="addone_case_1",
        include_metrics=True
    )
    print(dataset_table)
    print()

    # Example 2: Generate a table with specific scores only
    print("=" * 80)
    print("EXAMPLE 2: Dataset Table with Selected Scores (addone_case_2)")
    print("=" * 80)
    print()

    dataset_table_filtered = create_dataset_table(
        reports=run_data['reports'],
        dataset_id="addone_case_2",
        score_names=["ToolCallEvaluator"],  # Only show specific scores
        include_metrics=False  # Don't include token/cost metrics
    )
    print(dataset_table_filtered)
    print()

    # Example 3: Generate a summary table for the entire run
    print("=" * 80)
    print("EXAMPLE 3: Run Summary Table")
    print("=" * 80)
    print()

    summary_table = create_run_summary_table(
        run_data=run_data,
        include_metrics=True
    )
    print(summary_table)
    print()

    # Example 4: Summary table without metrics
    print("=" * 80)
    print("EXAMPLE 4: Run Summary Table (Scores Only)")
    print("=" * 80)
    print()

    summary_table_simple = create_run_summary_table(
        run_data=run_data,
        score_names=["ToolCallEvaluator", "Helpfulness and accuracy"],
        include_metrics=False
    )
    print(summary_table_simple)
    print()

    print("=" * 80)
    print("Examples complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
