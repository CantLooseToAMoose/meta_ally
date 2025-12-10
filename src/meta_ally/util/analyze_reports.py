"""
Analyze evaluation reports and generate LaTeX tables.

This script provides functions to:
1. Load evaluation reports from disk
2. Create LaTeX tables for specific datasets (rows = cases, columns = metrics)
3. Create LaTeX tables for runs (rows = datasets, columns = aggregated metrics)
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import json


def load_evaluation_run(base_dir: str, run_id: str) -> Dict[str, Any]:
    """Load all reports for a specific evaluation run.
    
    Args:
        base_dir: Base directory containing evaluation_results (e.g., "evaluation_results")
        run_id: The run_id to load (e.g., "add_one_sales_copilot_eval_20251209_093432")
    
    Returns:
        Dictionary with 'metadata' and 'reports' keys
    """
    base_path = Path(base_dir)
    run_dir = base_path / run_id
    
    if not run_dir.exists():
        raise ValueError(f"Run directory not found: {run_dir}")
    
    # Load metadata for this specific run
    metadata_path = run_dir / "metadata.json"
    if not metadata_path.exists():
        raise ValueError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_path, 'r') as f:
        run_metadata = json.load(f)
    
    # Load all report files for this run
    reports_dir = run_dir / "reports"
    reports = {}
    
    if reports_dir.exists():
        for dataset_id in run_metadata['dataset_ids']:
            report_path = reports_dir / f"{dataset_id}.json"
            if report_path.exists():
                with open(report_path, 'r') as f:
                    reports[dataset_id] = json.load(f)
    
    return {
        'metadata': run_metadata,
        'reports': reports
    }


def _format_number(value: float, precision: int = 2) -> str:
    """Format a number for LaTeX table."""
    if isinstance(value, (int, float)):
        return f"{value:.{precision}f}"
    return str(value)


def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
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
    reports: Dict[str, Any],
    dataset_id: str,
    score_names: Optional[List[str]] = None,
    include_metrics: bool = True
) -> str:
    """Create a LaTeX table for a specific dataset.
    
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
    """
    if dataset_id not in reports:
        raise ValueError(f"Dataset '{dataset_id}' not found in reports")
    
    report = reports[dataset_id]
    cases = report['cases']
    
    # Determine which scores to include
    if cases:
        all_scores = list(cases[0].get('scores', {}).keys())
        scores_to_show = score_names if score_names else all_scores
    else:
        scores_to_show = []
    
    # Build table header
    headers = ['Case Name']
    if include_metrics:
        headers.extend(['Input Tokens', 'Output Tokens', 'Cost'])
    headers.extend(scores_to_show)
    
    # Start building LaTeX table
    num_cols = len(headers)
    col_spec = 'l' + 'r' * (num_cols - 1)  # left-align first col, right-align rest
    
    latex = []
    latex.append(r'\begin{table}[htbp]')
    latex.append(r'\centering')
    latex.append(f'\\begin{{tabular}}{{{col_spec}}}')
    latex.append(r'\hline')
    latex.append(' & '.join(headers) + r' \\')
    latex.append(r'\hline')
    
    # Add rows for each case
    for case in cases:
        case_name = _escape_latex(case['name'])
        
        row = [case_name]
        
        # Add metrics if requested
        if include_metrics:
            metrics = case.get('metrics', {})
            row.append(_format_number(metrics.get('input_tokens', 0), 0))
            row.append(_format_number(metrics.get('output_tokens', 0), 0))
            row.append(_format_number(metrics.get('cost', 0.0), 4))
        
        # Add scores
        scores = case.get('scores', {})
        for score_name in scores_to_show:
            score_value = scores.get(score_name, {}).get('value', 0.0)
            row.append(_format_number(score_value, 2))
        
        latex.append(' & '.join(row) + r' \\')
    
    latex.append(r'\hline')
    latex.append(r'\end{tabular}')
    latex.append(f'\\caption{{Evaluation results for dataset: {_escape_latex(dataset_id)}}}')
    latex.append(f'\\label{{tab:{dataset_id}}}')
    latex.append(r'\end{table}')
    
    return '\n'.join(latex)


def create_run_summary_table(
    run_data: Dict[str, Any],
    score_names: Optional[List[str]] = None,
    include_metrics: bool = True
) -> str:
    """Create a LaTeX table summarizing a complete evaluation run.
    
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
    reports = run_data['reports']
    metadata = run_data['metadata']
    
    # Determine which scores to include
    if reports:
        first_report = next(iter(reports.values()))
        if first_report['cases']:
            all_scores = list(first_report['cases'][0].get('scores', {}).keys())
            scores_to_show = score_names if score_names else all_scores
        else:
            scores_to_show = []
    else:
        scores_to_show = []
    
    # Build table header
    headers = ['Dataset']
    if include_metrics:
        headers.extend(['Avg Input Tokens', 'Avg Output Tokens', 'Avg Cost'])
    headers.extend([f'Avg {s}' for s in scores_to_show])
    
    # Start building LaTeX table
    num_cols = len(headers)
    col_spec = 'l' + 'r' * (num_cols - 1)
    
    latex = []
    latex.append(r'\begin{table}[htbp]')
    latex.append(r'\centering')
    latex.append(f'\\begin{{tabular}}{{{col_spec}}}')
    latex.append(r'\hline')
    latex.append(' & '.join(headers) + r' \\')
    latex.append(r'\hline')
    
    # Add rows for each dataset
    for dataset_id in metadata['dataset_ids']:
        if dataset_id not in reports:
            continue
        
        report = reports[dataset_id]
        cases = report['cases']
        
        if not cases:
            continue
        
        # Calculate averages
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0
        score_totals = {score_name: 0.0 for score_name in scores_to_show}
        
        for case in cases:
            # Sum metrics
            metrics = case.get('metrics', {})
            total_input_tokens += metrics.get('input_tokens', 0)
            total_output_tokens += metrics.get('output_tokens', 0)
            total_cost += metrics.get('cost', 0.0)
            
            # Sum scores
            scores = case.get('scores', {})
            for score_name in scores_to_show:
                score_value = scores.get(score_name, {}).get('value', 0.0)
                score_totals[score_name] += score_value
        
        num_cases = len(cases)
        avg_input_tokens = total_input_tokens / num_cases
        avg_output_tokens = total_output_tokens / num_cases
        avg_cost = total_cost / num_cases
        
        row = [_escape_latex(dataset_id)]
        
        if include_metrics:
            row.append(_format_number(avg_input_tokens, 0))
            row.append(_format_number(avg_output_tokens, 0))
            row.append(_format_number(avg_cost, 4))
        
        for score_name in scores_to_show:
            avg_score = score_totals[score_name] / num_cases
            row.append(_format_number(avg_score, 2))
        
        latex.append(' & '.join(row) + r' \\')
    
    latex.append(r'\hline')
    latex.append(r'\end{tabular}')
    latex.append(f'\\caption{{Run summary: {_escape_latex(metadata["task_name"])}}}')
    latex.append(f'\\label{{tab:run_{metadata["run_id"]}}}')
    latex.append(r'\end{table}')
    
    return '\n'.join(latex)
