"""
Example usage of DataFrame-based report analysis.

This example demonstrates how to:
1. Convert evaluation reports to pandas DataFrames
2. Perform data analysis and filtering
3. Compare multiple evaluation runs
4. Export results to various formats
5. Create visualizations (basic examples)
"""

from meta_ally.util.analyze_reports import (
    export_dataframe,
    load_evaluation_run,
    reports_to_dataframe,
    run_to_dataframe,
)


def main():  # noqa: PLR0915
    """Run the DataFrame analysis examples."""
    print("=" * 80)
    print("EXAMPLE 1: Convert a single dataset to DataFrame")
    print("=" * 80)
    print()

    # Load a specific run
    run_data = load_evaluation_run(
        base_dir="evaluation_results",
        run_id="multi_dataset_eval_20251217_080318"
    )

    # Convert a single dataset to DataFrame
    df_dataset = reports_to_dataframe(
        reports=run_data['reports'],
        dataset_id="addone_case_1"
    )

    print("Dataset: addone_case_1")
    print(f"Shape: {df_dataset.shape}")
    print(f"\nColumns: {list(df_dataset.columns)}")
    print("\nFirst few rows:")
    print(df_dataset[['case_name', 'input_tokens', 'output_tokens', 'cost']].head())
    print()

    # ========================================================================
    print("=" * 80)
    print("EXAMPLE 2: Get all cases from entire run")
    print("=" * 80)
    print()

    df_all_cases = run_to_dataframe(run_data, aggregate=False)
    print(f"Total cases across all datasets: {len(df_all_cases)}")
    print(f"Datasets included: {df_all_cases['dataset_id'].unique()}")
    print()

    # Filter cases with high scores
    if 'score_Helpfulness_and_accuracy' in df_all_cases.columns:
        high_performers = df_all_cases[
            df_all_cases['score_Helpfulness_and_accuracy'] >= 0.9
        ]
        print(f"Cases with Helpfulness score >= 0.9: {len(high_performers)}")
    print()

    # ========================================================================
    print("=" * 80)
    print("EXAMPLE 3: Aggregated statistics per dataset")
    print("=" * 80)
    print()

    df_agg = run_to_dataframe(run_data, aggregate=True)
    print("Aggregated statistics:")
    print(df_agg[['dataset_id', 'num_cases', 'avg_cost', 'total_cost']].to_string())
    print()

    # Show average scores
    score_cols = [col for col in df_agg.columns if col.startswith('avg_score_')]
    if score_cols:
        print("\nAverage scores by dataset:")
        print(df_agg[['dataset_id', *score_cols]].to_string())
    print()

    # ========================================================================
    print("=" * 80)
    print("EXAMPLE 4: Data analysis - Cost and performance metrics")
    print("=" * 80)
    print()

    # Descriptive statistics
    print("Cost statistics across all cases:")
    print(df_all_cases['cost'].describe())
    print()

    # Calculate cost efficiency (cost per score point, if applicable)
    if 'score_Helpfulness_and_accuracy' in df_all_cases.columns:
        df_all_cases['cost_per_helpfulness_point'] = (
            df_all_cases['cost'] / df_all_cases['score_Helpfulness_and_accuracy']
        )
        print("Most cost-efficient cases (low cost per helpfulness point):")
        efficient = df_all_cases.nsmallest(3, 'cost_per_helpfulness_point')
        print(efficient[['case_name', 'cost', 'score_Helpfulness_and_accuracy',
                        'cost_per_helpfulness_point']].to_string())
    print()

    # ========================================================================
    print("=" * 80)
    print("EXAMPLE 5: Export to various formats")
    print("=" * 80)
    print()

    # Export aggregated stats to CSV
    export_dataframe(df_agg, "evaluation_results/aggregated_stats.csv")
    print("✓ Exported aggregated stats to: evaluation_results/aggregated_stats.csv")

    # Export all cases to Excel (if openpyxl is installed)
    try:
        export_dataframe(df_all_cases, "evaluation_results/all_cases.xlsx")
        print("✓ Exported all cases to: evaluation_results/all_cases.xlsx")
    except ImportError:
        print("⚠ Excel export requires openpyxl: pip install openpyxl")

    # Export to JSON
    export_dataframe(df_agg, "evaluation_results/aggregated_stats.json")
    print("✓ Exported aggregated stats to: evaluation_results/aggregated_stats.json")
    print()

    # ========================================================================
    print("=" * 80)
    print("EXAMPLE 6: Compare multiple runs (if available)")
    print("=" * 80)
    print()

    # This example assumes you have multiple runs
    # Uncomment and modify if you have multiple runs to compare:
    """
    try:
        df_comparison = compare_runs(
            base_dir="evaluation_results",
            run_ids=["run1_id", "run2_id"],
            aggregate=True
        )
        print("Comparison of multiple runs:")
        print(df_comparison[['run_id', 'dataset_id', 'avg_cost', 'avg_score_Helpfulness']].to_string())

        # Pivot table to compare runs side by side
        pivot = df_comparison.pivot_table(
            values='avg_cost',
            index='dataset_id',
            columns='run_id'
        )
        print("\nCost comparison (rows=datasets, columns=runs):")
        print(pivot)
    except ValueError as e:
        print(f"Could not compare runs: {e}")
    """
    print("(See commented code for multi-run comparison example)")
    print()

    # ========================================================================
    print("=" * 80)
    print("EXAMPLE 7: Advanced filtering and grouping")
    print("=" * 80)
    print()

    # Group by dataset and calculate statistics
    grouped = df_all_cases.groupby('dataset_id').agg({
        'cost': ['mean', 'sum', 'std'],
        'input_tokens': 'mean',
        'output_tokens': 'mean'
    })
    print("Statistics grouped by dataset:")
    print(grouped)
    print()

    # ========================================================================
    print("=" * 80)
    print("Examples complete!")
    print("=" * 80)
    print()
    print("Key takeaways:")
    print("- Use reports_to_dataframe() for single dataset analysis")
    print("- Use run_to_dataframe() to combine multiple datasets")
    print("- Use aggregate=True for summary statistics per dataset")
    print("- Use compare_runs() to analyze multiple evaluation runs")
    print("- Export results with export_dataframe() for sharing")
    print()
    print("DataFrames enable:")
    print("- Easy filtering: df[df['score'] > 0.8]")
    print("- Grouping: df.groupby('dataset_id').mean()")
    print("- Sorting: df.sort_values('cost')")
    print("- Statistical analysis: df.describe()")
    print("- Visualizations with matplotlib/seaborn")


if __name__ == "__main__":
    main()
