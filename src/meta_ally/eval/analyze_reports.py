"""
Analyze evaluation reports and generate LaTeX tables and pandas DataFrames.

This script provides functions to:
1. Load evaluation reports from disk
2. Create LaTeX tables for specific datasets (rows = cases, columns = metrics)
3. Create LaTeX tables for runs (rows = datasets, columns = aggregated metrics)
4. Convert reports to pandas DataFrames for flexible analysis and visualization
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd


def load_evaluation_run(base_dir: str, run_id: str) -> dict[str, Any]:
    """
    Load all reports for a specific evaluation run.

    Args:
        base_dir: Base directory containing evaluation_results (e.g., "evaluation_results")
        run_id: The run_id to load (e.g., "add_one_sales_copilot_eval_20251209_093432")

    Returns:
        Dictionary with 'metadata' and 'reports' keys

    Raises:
        ValueError: If run directory or metadata file not found
    """
    base_path = Path(base_dir)
    run_dir = base_path / run_id

    if not run_dir.exists():
        raise ValueError(f"Run directory not found: {run_dir}")

    # Load metadata for this specific run
    metadata_path = run_dir / "metadata.json"
    if not metadata_path.exists():
        raise ValueError(f"Metadata file not found: {metadata_path}")

    with open(metadata_path, encoding="utf-8") as f:
        run_metadata = json.load(f)

    # Load all report files for this run
    reports_dir = run_dir / "reports"
    reports = {}

    if reports_dir.exists():
        for dataset_id in run_metadata['dataset_ids']:
            report_path = reports_dir / f"{dataset_id}.json"
            if report_path.exists():
                with open(report_path, encoding="utf-8") as f:
                    reports[dataset_id] = json.load(f)

    return {
        'metadata': run_metadata,
        'reports': reports
    }


def _format_number(value: float | Any, precision: int = 2) -> str:
    """
    Format a number for LaTeX table.

    Returns:
        Formatted string representation of the number
    """
    if isinstance(value, (int, float)):
        return f"{value:.{precision}f}"
    # Handle pandas scalars or other numeric types
    try:
        numeric_value = float(value)
        return f"{numeric_value:.{precision}f}"
    except (ValueError, TypeError):
        return str(value)


def _escape_latex(text: str) -> str:
    """
    Escape special LaTeX characters.

    Returns:
        Text with LaTeX special characters escaped
    """
    # Process backslash first to avoid double-escaping
    text = text.replace('\\', r'\textbackslash{}')

    # Then process other special characters
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def create_dataset_table(
    reports: dict[str, Any],
    dataset_id: str,
    score_names: list[str] | None = None,
    include_metrics: bool = True
) -> str:
    """
    Create a LaTeX table for a specific dataset.

    Each row represents a test case with columns:
    - Case name
    - Scores (specified by score_names, or all if None)
    - Metrics (input/output tokens, cost, etc.)

    Args:
        reports: Dictionary of report data (from load_evaluation_run)
        dataset_id: The dataset to create a table for
        score_names: List of score names to include (None = all scores)
        include_metrics: Whether to include metrics columns

    Returns:
        LaTeX table as a string

    Raises:
        ValueError: If dataset_id not found in reports
    """
    # Convert to DataFrame for easier data manipulation
    df = reports_to_dataframe(reports, dataset_id, flatten_scores=True)

    if df.empty:
        # Return empty table if no data
        return _create_empty_latex_table(dataset_id)

    # Get score columns
    score_cols = [col for col in df.columns if col.startswith('score_')
                  and not col.endswith('_reason')]

    # Filter to requested scores if specified
    if score_names:
        # Convert score names to column names
        requested_cols = [f"score_{name.replace(' ', '_').replace('-', '_')}"
                         for name in score_names]
        score_cols = [col for col in score_cols if col in requested_cols]

    # Build table header
    headers = ['Case Name']
    if include_metrics:
        headers.extend(['Input Tokens', 'Output Tokens', 'Cost'])
    headers.extend([col.replace('score_', '').replace('_', ' ') for col in score_cols])

    # Start building LaTeX table
    num_cols = len(headers)
    col_spec = 'l' + 'r' * (num_cols - 1)  # left-align first col, right-align rest

    latex = [
        r'\begin{table}[htbp]',
        r'\centering',
        f'\\begin{{tabular}}{{{col_spec}}}',
        r'\hline',
        ' & '.join(headers) + r' \\',
        r'\hline'
    ]

    # Add rows for each case
    for idx in range(len(df)):
        case_name = _escape_latex(str(df.iloc[idx]['case_name']))

        row = [case_name]

        # Add metrics if requested
        if include_metrics:
            row.append(_format_number(df.iloc[idx]['input_tokens'], 0))
            row.append(_format_number(df.iloc[idx]['output_tokens'], 0))
            row.append(_format_number(df.iloc[idx]['cost'], 4))

        # Add scores
        for score_col in score_cols:
            row.append(_format_number(df.iloc[idx][score_col], 2))

        latex.append(' & '.join(row) + r' \\')

    latex.extend([
        r'\hline',
        r'\end{tabular}',
        f'\\caption{{Evaluation results for dataset: {_escape_latex(dataset_id)}}}',
        f'\\label{{tab:{dataset_id}}}',
        r'\end{table}'
    ])

    return '\n'.join(latex)


def _create_empty_latex_table(dataset_id: str) -> str:
    """
    Create an empty LaTeX table for a dataset with no cases.

    Returns:
        LaTeX table string with no data message
    """
    return '\n'.join([
        r'\begin{table}[htbp]',
        r'\centering',
        r'\begin{tabular}{l}',
        r'\hline',
        'No data available \\\\',
        r'\hline',
        r'\end{tabular}',
        f'\\caption{{Evaluation results for dataset: {_escape_latex(dataset_id)}}}',
        f'\\label{{tab:{dataset_id}}}',
        r'\end{table}'
    ])


def create_run_summary_table(
    run_data: dict[str, Any],
    score_names: list[str] | None = None,
    include_metrics: bool = True
) -> str:
    """
    Create a LaTeX table summarizing a complete evaluation run.

    Each row represents a dataset with columns:
    - Dataset name
    - Average scores
    - Average metrics

    Args:
        run_data: Complete run data from load_evaluation_run()
        score_names: List of score names to include (None = all scores)
        include_metrics: Whether to include metrics columns

    Returns:
        LaTeX table as a string
    """
    # Convert to aggregated DataFrame
    df = run_to_dataframe(run_data, aggregate=True)

    if df.empty:
        return _create_empty_run_summary_table(run_data['metadata'])

    # Get score columns (avg_score_* columns)
    score_cols = [col for col in df.columns if col.startswith('avg_score_')]

    # Filter to requested scores if specified
    if score_names:
        # Convert score names to column names
        requested_cols = [f"avg_score_{name.replace(' ', '_').replace('-', '_')}"
                         for name in score_names]
        score_cols = [col for col in score_cols if col in requested_cols]

    # Build table header
    headers = ['Dataset']
    if include_metrics:
        headers.extend(['Avg Input Tokens', 'Avg Output Tokens', 'Avg Cost'])
    headers.extend([col.replace('avg_score_', '').replace('_', ' ')
                   for col in score_cols])

    # Start building LaTeX table
    num_cols = len(headers)
    col_spec = 'l' + 'r' * (num_cols - 1)

    latex = [
        r'\begin{table}[htbp]',
        r'\centering',
        f'\\begin{{tabular}}{{{col_spec}}}',
        r'\hline',
        ' & '.join(headers) + r' \\',
        r'\hline'
    ]

    # Add rows for each dataset
    for idx in range(len(df)):
        dataset_id = _escape_latex(str(df.iloc[idx]['dataset_id']))

        row = [dataset_id]

        # Add metrics if requested
        if include_metrics:
            row.append(_format_number(df.iloc[idx]['avg_input_tokens'], 0))
            row.append(_format_number(df.iloc[idx]['avg_output_tokens'], 0))
            row.append(_format_number(df.iloc[idx]['avg_cost'], 4))

        # Add scores
        for score_col in score_cols:
            row.append(_format_number(df.iloc[idx][score_col], 2))

        latex.append(' & '.join(row) + r' \\')

    metadata = run_data['metadata']
    latex.extend([
        r'\hline',
        r'\end{tabular}',
        f'\\caption{{Run summary: {_escape_latex(metadata["task_name"])}}}',
        f'\\label{{tab:run_{metadata["run_id"]}}}',
        r'\end{table}'
    ])

    return '\n'.join(latex)


def _create_empty_run_summary_table(metadata: dict[str, Any]) -> str:
    """
    Create an empty LaTeX table for a run with no data.

    Returns:
        LaTeX table string with no data message
    """
    return '\n'.join([
        r'\begin{table}[htbp]',
        r'\centering',
        r'\begin{tabular}{l}',
        r'\hline',
        'No data available \\\\',
        r'\hline',
        r'\end{tabular}',
        f'\\caption{{Run summary: {_escape_latex(metadata["task_name"])}}}',
        f'\\label{{tab:run_{metadata["run_id"]}}}',
        r'\end{table}'
    ])


# ============================================================================
# DataFrame conversion functions
# ============================================================================


def reports_to_dataframe(
    reports: dict[str, Any],
    dataset_id: str,
    flatten_scores: bool = True,
    include_io: bool = True
) -> pd.DataFrame:
    """
    Convert a single dataset's report to a pandas DataFrame.

    Args:
        reports: Dictionary of report data (from load_evaluation_run)
        dataset_id: The dataset to convert
        flatten_scores: If True, create separate columns for each score.
                       If False, keep scores as a dict in a single column.
        include_io: If True, include input, output, and expected_output columns.
                   If False, omit these columns (smaller DataFrame).

    Returns:
        DataFrame with one row per test case

    Raises:
        ValueError: If dataset_id not found in reports

    Example:
        >>> run_data = load_evaluation_run("evaluation_results", "my_run_id")
        >>> df = reports_to_dataframe(run_data['reports'], "addone_case_1")
        >>> df[['case_name', 'input_tokens', 'cost']].head()
    """
    if dataset_id not in reports:
        raise ValueError(f"Dataset '{dataset_id}' not found in reports")

    report = reports[dataset_id]
    cases = report['cases']

    if not cases:
        return pd.DataFrame()

    # Build list of dictionaries for DataFrame
    rows = []
    for case in cases:
        row = {
            'case_name': case['name'],
            'dataset_id': dataset_id,
        }

        # Add input/output/expected_output if requested
        if include_io:
            # Store complete structures as they are in the case
            row['inputs'] = case.get('inputs', None)
            row['output'] = case.get('output', None)
            row['expected_output'] = case.get('expected_output', None)

        # Add metrics
        metrics = case.get('metrics', {})
        row['input_tokens'] = metrics.get('input_tokens', 0)
        row['output_tokens'] = metrics.get('output_tokens', 0)
        row['requests'] = metrics.get('requests', 0)
        row['cost'] = metrics.get('cost', 0.0)

        # Add scores
        scores = case.get('scores', {})
        if flatten_scores:
            for score_name, score_data in scores.items():
                # Clean column name (replace spaces with underscores)
                col_name = score_name.replace(' ', '_').replace('-', '_')
                row[f'score_{col_name}'] = score_data.get('value', 0.0)
                row[f'score_{col_name}_reason'] = score_data.get('reason', None)
        else:
            row['scores'] = scores

        # Add assertions
        assertions = case.get('assertions', {})
        for assertion_name, assertion_data in assertions.items():
            col_name = assertion_name.replace(' ', '_').replace('-', '_')
            row[f'assertion_{col_name}'] = assertion_data.get('value', None)

        rows.append(row)

    return pd.DataFrame(rows)


def _aggregate_dataset_stats(
    dataset_id: str,
    cases: list[dict[str, Any]],
    metadata: dict[str, Any]
) -> dict[str, Any]:
    """
    Calculate aggregated statistics for a dataset.

    Returns:
        Dictionary with aggregated metrics and scores
    """
    row = {
        'dataset_id': dataset_id,
        'run_id': metadata['run_id'],
        'task_name': metadata['task_name'],
        'num_cases': len(cases),
    }

    # Calculate averages
    total_input_tokens = sum(c.get('metrics', {}).get('input_tokens', 0) for c in cases)
    total_output_tokens = sum(c.get('metrics', {}).get('output_tokens', 0) for c in cases)
    total_cost = sum(c.get('metrics', {}).get('cost', 0.0) for c in cases)
    total_requests = sum(c.get('metrics', {}).get('requests', 0) for c in cases)

    row['avg_input_tokens'] = total_input_tokens / len(cases)
    row['avg_output_tokens'] = total_output_tokens / len(cases)
    row['avg_cost'] = total_cost / len(cases)
    row['total_cost'] = total_cost
    row['total_requests'] = total_requests

    # Calculate average scores
    if cases and cases[0].get('scores'):
        score_names = list(cases[0]['scores'].keys())
        for score_name in score_names:
            col_name = score_name.replace(' ', '_').replace('-', '_')
            scores = [c.get('scores', {}).get(score_name, {}).get('value', 0.0)
                     for c in cases]
            row[f'avg_score_{col_name}'] = sum(scores) / len(scores)
            row[f'min_score_{col_name}'] = min(scores)
            row[f'max_score_{col_name}'] = max(scores)

    return row


def run_to_dataframe(
    run_data: dict[str, Any],
    flatten_scores: bool = True,
    aggregate: bool = False,
    include_io: bool = True
) -> pd.DataFrame:
    """
    Convert an entire evaluation run to a pandas DataFrame.

    Args:
        run_data: Complete run data from load_evaluation_run()
        flatten_scores: If True, create separate columns for each score
        aggregate: If True, aggregate by dataset (one row per dataset).
                  If False, include all individual cases.
        include_io: If True, include input, output, and expected_output columns.
                   Only applicable when aggregate=False.

    Returns:
        DataFrame with all cases across all datasets, or aggregated by dataset

    Example:
        >>> run_data = load_evaluation_run("evaluation_results", "my_run_id")
        >>> # Get all individual cases
        >>> df_cases = run_to_dataframe(run_data)
        >>> # Get aggregated stats per dataset
        >>> df_agg = run_to_dataframe(run_data, aggregate=True)
    """
    reports = run_data['reports']
    metadata = run_data['metadata']

    if aggregate:
        # Create aggregated DataFrame (one row per dataset)
        rows = []
        for dataset_id in metadata['dataset_ids']:
            if dataset_id not in reports:
                continue

            cases = reports[dataset_id]['cases']
            if not cases:
                continue

            row = _aggregate_dataset_stats(dataset_id, cases, metadata)
            rows.append(row)

        return pd.DataFrame(rows)

    # Combine all datasets into one DataFrame
    dfs = []
    for dataset_id in metadata['dataset_ids']:
        if dataset_id in reports:
            df = reports_to_dataframe(reports, dataset_id, flatten_scores, include_io)
            if not df.empty:
                df['run_id'] = metadata['run_id']
                df['task_name'] = metadata['task_name']
                dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)


def compare_runs(
    base_dir: str,
    run_ids: list[str],
    aggregate: bool = True,
    include_io: bool = False
) -> pd.DataFrame:
    """
    Compare multiple evaluation runs in a single DataFrame.

    Args:
        base_dir: Base directory containing evaluation_results
        run_ids: List of run IDs to compare
        aggregate: If True, show one row per dataset per run.
                  If False, show all individual cases.
        include_io: If True, include input/output/expected_output columns.
                   Only applicable when aggregate=False.

    Returns:
        DataFrame with data from all specified runs

    Raises:
        ValueError: If any run_id cannot be loaded

    Example:
        >>> df = compare_runs(
        ...     "evaluation_results",
        ...     ["run_20251201_120000", "run_20251215_150000"],
        ...     aggregate=True
        ... )
        >>> # Compare average scores across runs
        >>> df.pivot_table(
        ...     values='avg_score_Helpfulness',
        ...     index='dataset_id',
        ...     columns='run_id'
        ... )
    """
    dfs = []
    for run_id in run_ids:
        try:
            run_data = load_evaluation_run(base_dir, run_id)
            df = run_to_dataframe(run_data, aggregate=aggregate, include_io=include_io)
            if not df.empty:
                dfs.append(df)
        except ValueError as e:
            raise ValueError(f"Failed to load run '{run_id}': {e}") from e

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)


def export_dataframe(
    df: pd.DataFrame,
    output_path: str,
    file_format: str = "auto"
) -> None:
    """
    Export a DataFrame to various formats.

    Args:
        df: DataFrame to export
        output_path: Path to save the file
        file_format: Output format. Options: 'csv', 'excel', 'parquet', 'json', 'auto'
                     If 'auto', format is inferred from file extension.

    Raises:
        ValueError: If format is not supported or cannot be inferred

    Example:
        >>> df = run_to_dataframe(run_data, aggregate=True)
        >>> export_dataframe(df, "results.csv")
        >>> export_dataframe(df, "results.xlsx", file_format="excel")
    """
    path = Path(output_path)

    # Infer format from extension if auto
    if file_format == "auto":
        ext = path.suffix.lower()
        format_map = {
            '.csv': 'csv',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.parquet': 'parquet',
            '.json': 'json',
        }
        file_format = format_map.get(ext, '')
        if not file_format:
            raise ValueError(
                f"Cannot infer format from extension '{ext}'. "
                "Specify format explicitly."
            )

    # Export based on format
    if file_format == 'csv':
        df.to_csv(path, index=False)
    elif file_format == 'json':
        df.to_json(path, orient='records', indent=2)
    else:
        raise ValueError(
            f"Unsupported format '{file_format}'. "
            "Supported formats: 'csv', 'json'"
        )
