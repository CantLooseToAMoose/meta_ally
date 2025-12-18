"""
Example usage of the analyze_reports utility.

This example demonstrates how to:
1. Load evaluation results from disk
2. Generate LaTeX tables for specific datasets
3. Generate LaTeX summary tables for entire runs
4. Convert evaluation reports to pandas DataFrames
5. Perform data analysis and filtering
6. Export results to various formats
"""

from meta_ally.util.analyze_reports import (
    create_dataset_table,
    create_run_summary_table,
    export_dataframe,
    load_evaluation_run,
    reports_to_dataframe,
    run_to_dataframe,
)


def main():  # noqa: PLR0915, C901, PLR0912, PLR0914
    """Run the analyze_reports example."""
    # Load a specific run
    print("Loading evaluation run...")
    run_data = load_evaluation_run(
        base_dir="evaluation_results",
        run_id="multi_dataset_eval_20251217_080318"
    )

    print(f"✓ Loaded run: {run_data['metadata']['run_id']}")
    print(f"  Task: {run_data['metadata']['task_name']}")
    print(f"  Datasets: {', '.join(run_data['metadata']['dataset_ids'])}")
    print()

    # ========================================================================
    # PART 1: LaTeX Table Generation
    # ========================================================================

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
    print("EXAMPLE 2: Dataset Table with Selected Scores")
    print("=" * 80)
    print()

    dataset_table_filtered = create_dataset_table(
        reports=run_data['reports'],
        dataset_id="addone_case_1",
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

    # ========================================================================
    # PART 2: DataFrame Analysis
    # ========================================================================

    # Example 5: Convert a single dataset to DataFrame
    print("=" * 80)
    print("EXAMPLE 5: Convert a single dataset to DataFrame")
    print("=" * 80)
    print()

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

    # Show input/output examples
    if 'inputs' in df_dataset.columns:
        print("\nExample: First case input/output structures:")
        first_case = df_dataset.iloc[0]

        # Access the complete input structure
        if first_case['inputs']:
            first_input = first_case['inputs'][0]
            if first_input.get('parts'):
                print(f"Input text: {first_input['parts'][0]['content'][:100]}...")

        # Access the complete output structure
        if first_case['output']:
            first_output = first_case['output'][0]
            if first_output.get('parts'):
                print(f"Output text: {first_output['parts'][0]['content'][:100]}...")

        # Access expected output
        if first_case['expected_output']:
            expected_msg = first_case['expected_output'].get('output_message', '')
            print(f"Expected: {expected_msg[:100]}...")
        print()

    # Example 6: Get all cases from entire run
    print("=" * 80)
    print("EXAMPLE 6: Get all cases from entire run")
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

    # Example 7: Aggregated statistics per dataset
    print("=" * 80)
    print("EXAMPLE 7: Aggregated statistics per dataset")
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

    # Example 8: Data analysis - Cost and performance metrics
    print("=" * 80)
    print("EXAMPLE 8: Data analysis - Cost and performance metrics")
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

    # Example 9: Export to various formats
    print("=" * 80)
    print("EXAMPLE 9: Export to various formats")
    print("=" * 80)
    print()

    # Export aggregated stats to CSV
    export_dataframe(df_agg, "evaluation_results/aggregated_stats.csv")
    print("✓ Exported aggregated stats to: evaluation_results/aggregated_stats.csv")

    # Export to JSON
    export_dataframe(df_agg, "evaluation_results/aggregated_stats.json")
    print("✓ Exported aggregated stats to: evaluation_results/aggregated_stats.json")
    print()

    # Example 10: Advanced filtering and grouping
    print("=" * 80)
    print("EXAMPLE 10: Advanced filtering and grouping")
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

    # Example 11: Analyzing input/output structures
    print("=" * 80)
    print("EXAMPLE 11: Analyzing input/output structures")
    print("=" * 80)
    print()

    if 'inputs' in df_all_cases.columns:
        # Helper function to extract text from inputs
        def get_input_text(inputs):
            if inputs and len(inputs) > 0 and inputs[0].get('parts'):
                return inputs[0]['parts'][0].get('content', '')
            return ''

        def get_output_text(output):
            if output and len(output) > 0 and output[0].get('parts'):
                return output[0]['parts'][0].get('content', '')
            return ''

        # Extract text for analysis
        df_all_cases['input_text'] = df_all_cases['inputs'].apply(get_input_text)
        df_all_cases['output_text'] = df_all_cases['output'].apply(get_output_text)

        # Calculate text lengths
        df_all_cases['input_length'] = df_all_cases['input_text'].str.len()
        df_all_cases['output_length'] = df_all_cases['output_text'].str.len()

        print("Text length statistics:")
        print(df_all_cases[['input_length', 'output_length']].describe())
        print()

        # Find cases with very long outputs
        if len(df_all_cases) > 0:
            longest_output = df_all_cases.nlargest(1, 'output_length').iloc[0]
            print(f"Longest output case: {longest_output['case_name']}")
            print(f"Output length: {longest_output['output_length']} characters")
            print()

        # You can also access the complete structures for detailed analysis
        print("Example: Accessing complete structures for first case")
        first_case = df_all_cases.iloc[0]
        print(f"  - Number of inputs: {len(first_case['inputs']) if first_case['inputs'] else 0}")
        print(f"  - Number of outputs: {len(first_case['output']) if first_case['output'] else 0}")
        if first_case['output'] and len(first_case['output']) > 0:
            print(f"  - Output model: {first_case['output'][0].get('model_name', 'N/A')}")
            print(f"  - Output timestamp: {first_case['output'][0].get('timestamp', 'N/A')}")
        print()
    else:
        print("Input/output structures not included in DataFrame.")
        print("Use include_io=True when calling reports_to_dataframe().")
        print()

    # ========================================================================
    print("=" * 80)
    print("Examples complete!")
    print("=" * 80)
    print()
    print("Key takeaways:")
    print()
    print("LaTeX Tables:")
    print("- Use create_dataset_table() for individual dataset tables")
    print("- Use create_run_summary_table() for aggregated run summaries")
    print("- Customize with score_names and include_metrics parameters")
    print()
    print("DataFrame Analysis:")
    print("- Use reports_to_dataframe() for single dataset analysis")
    print("- Use run_to_dataframe() to combine multiple datasets")
    print("- Use aggregate=True for summary statistics per dataset")
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
