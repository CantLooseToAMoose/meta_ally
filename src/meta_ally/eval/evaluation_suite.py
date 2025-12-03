"""Simplified evaluation suite for running and managing evaluation results.

This module provides the EvaluationSuite class which focuses on:
1. Running evaluations on DatasetManager datasets
2. Recording evaluation results with metadata
3. Saving and loading evaluation results
4. Aggregating and analyzing results across runs

The EvaluationSuite simplifies evaluation workflows by managing just the
evaluation execution and results, while DatasetManager handles dataset management.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
import json
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic_evals.evaluators import Evaluator

from .dataset_manager import DatasetManager


class EvaluationResult(BaseModel):
    """Record of a single evaluation run with metadata and results."""
    
    run_id: str = Field(description="Unique identifier for this run")
    timestamp: str = Field(description="ISO format timestamp of when run started")
    task_name: str = Field(description="Name of the evaluation task")
    dataset_ids: List[str] = Field(description="List of dataset IDs evaluated")
    evaluator_names: List[str] = Field(description="Names of evaluators used")
    retry_config: Optional[Dict[str, Any]] = Field(default=None, description="Retry configuration used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    success: bool = Field(default=True, description="Whether the run completed successfully")
    error_message: Optional[str] = Field(default=None, description="Error message if run failed")
    results_summary: Optional[Dict[str, Any]] = Field(default=None, description="Summary of results")


class EvaluationSuite:
    """Simplified suite for running evaluations and managing results.
    
    This class focuses on:
    - Running evaluations on DatasetManager datasets
    - Recording evaluation results with metadata
    - Saving and loading evaluation results
    - Aggregating results across runs
    
    Main public methods:
    - run_evaluation(): Execute evaluation on datasets and record results
    - save_results(): Save results to disk
    - load_results(): Load results from disk (classmethod)
    - get_result(): Get a specific evaluation result
    - list_results(): Get all evaluation results
    - aggregate_results(): Aggregate results across runs
    
    Example:
        ```python
        # Load dataset manager
        manager = DatasetManager.load("Data/add_one")
        
        # Create suite
        suite = EvaluationSuite(manager)
        
        # Run evaluation
        reports = suite.run_evaluation(
            task=my_task,
            evaluators=[evaluator1, evaluator2],
            task_name="conversation_evaluation"
        )
        
        # Save results
        suite.save_results("evaluation_results")
        
        # Load results later
        loaded_suite = EvaluationSuite.load_results(
            "evaluation_results",
            dataset_manager=manager
        )
        ```
    """
    
    def __init__(self, dataset_manager: DatasetManager):
        """Initialize an EvaluationSuite.
        
        Args:
            dataset_manager: DatasetManager instance with datasets to evaluate
        """
        self._dataset_manager = dataset_manager
        self._results: List[EvaluationResult] = []
    
    def run_evaluation(
        self,
        task: Callable,
        evaluators: Optional[List[Evaluator]] = None,
        task_name: str = "evaluation",
        dataset_ids: Optional[List[str]] = None,
        retry_config: Optional[Dict[str, Any]] = None,
        wrap_with_hooks: bool = True,
        use_async: bool = False,
        run_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run evaluation on datasets and record results.
        
        Args:
            task: The evaluation task function
            evaluators: List of evaluators to use
            task_name: Name for this evaluation task
            dataset_ids: Specific datasets to evaluate (None = all)
            retry_config: Retry configuration for tenacity
            wrap_with_hooks: Whether to wrap tasks with dataset hooks
            use_async: Whether to use async evaluation
            run_metadata: Additional metadata for this run
            
        Returns:
            Dictionary mapping dataset IDs to their evaluation reports
        """
        # Generate run ID
        timestamp = datetime.now()
        run_id = f"{task_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Create result record
        result = EvaluationResult(
            run_id=run_id,
            timestamp=timestamp.isoformat(),
            task_name=task_name,
            dataset_ids=dataset_ids or self._dataset_manager.list_dataset_ids(),
            evaluator_names=[type(e).__name__ for e in evaluators] if evaluators else [],
            retry_config=retry_config,
            metadata=run_metadata or {}
        )
        
        try:
            # Run evaluation
            print(f"\n{'='*80}")
            print(f"Starting Evaluation: {run_id}")
            print(f"Task: {task_name}")
            print(f"Datasets: {len(result.dataset_ids)}")
            if evaluators:
                print(f"Evaluators: {', '.join(result.evaluator_names)}")
            print('='*80)
            
            reports = self._dataset_manager.evaluate_all_datasets(
                task=task,
                evaluators=evaluators,
                retry_config=retry_config,
                wrap_with_hooks=wrap_with_hooks,
                use_async=use_async,
                dataset_ids=dataset_ids
            )
            
            result.success = True
            result.results_summary = self._extract_results_summary(reports)
            
            print(f"\n{'='*80}")
            print(f"✓ Evaluation Completed: {run_id}")
            print('='*80)
            
        except Exception as e:
            print(f"\n{'='*80}")
            print(f"✗ Evaluation Failed: {run_id}")
            print(f"Error: {e}")
            print('='*80)
            
            result.success = False
            result.error_message = str(e)
            reports = {"error": str(e)}
        
        # Record the result
        self._results.append(result)
        
        return reports
    
    def _extract_results_summary(self, reports: Dict[str, Any]) -> Dict[str, Any]:
        """Extract summary information from evaluation reports.
        
        Args:
            reports: Dictionary of reports from evaluation
            
        Returns:
            Dictionary with summary information
        """
        summary: Dict[str, Any] = {}
        
        for dataset_id, report in reports.items():
            if isinstance(report, dict) and "error" in report:
                summary[dataset_id] = report
            else:
                # Try to extract key metrics from the report
                try:
                    dataset_summary: Dict[str, Any] = {"report_type": type(report).__name__}
                    
                    # Extract common report attributes
                    if hasattr(report, 'results'):
                        dataset_summary['num_results'] = len(report.results)  # type: ignore
                    
                    if hasattr(report, 'scores'):
                        dataset_summary['scores'] = report.scores  # type: ignore
                    
                    if hasattr(report, 'aggregate_scores'):
                        dataset_summary['aggregate_scores'] = report.aggregate_scores  # type: ignore
                    
                    summary[dataset_id] = dataset_summary
                except Exception as e:
                    summary[dataset_id] = {"error": f"Failed to extract summary: {e}"}
        
        return summary
    
    def save_results(
        self,
        directory: Union[Path, str],
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """Save evaluation results to disk.
        
        Creates directory structure:
        - directory/
          - results.json (all EvaluationResult records)
          - reports/
            - run_1.json
            - run_2.json
            ...
        
        Args:
            directory: Directory to save results to
            overwrite: Whether to overwrite existing directory
            
        Returns:
            Dictionary with information about saved files
        """
        dir_path = Path(directory) if isinstance(directory, str) else directory
        
        # Create or clear directory
        if dir_path.exists() and overwrite:
            import shutil
            shutil.rmtree(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        saved_info = {
            "results_directory": str(dir_path),
            "results_file": None,
            "num_results": len(self._results)
        }
        
        # Save results metadata
        results_file = dir_path / "results.json"
        results_data = [r.model_dump() for r in self._results]
        results_file.write_text(json.dumps(results_data, indent=2))
        saved_info["results_file"] = str(results_file)
        
        print(f"\n✓ Evaluation results saved to: {dir_path}")
        print("  - Results metadata: results.json")
        print(f"  - Total runs: {len(self._results)}")
        
        return saved_info
    
    @classmethod
    def load_results(
        cls,
        directory: Union[Path, str],
        dataset_manager: DatasetManager
    ) -> EvaluationSuite:
        """Load evaluation results from disk.
        
        Args:
            directory: Directory containing saved results
            dataset_manager: DatasetManager instance to use
            
        Returns:
            EvaluationSuite with loaded results
            
        Raises:
            FileNotFoundError: If results file not found
        """
        dir_path = Path(directory) if isinstance(directory, str) else directory
        results_file = dir_path / "results.json"
        
        if not results_file.exists():
            raise FileNotFoundError(f"Results file not found: {results_file}")
        
        # Create suite instance
        suite = cls(dataset_manager)
        
        # Load results
        results_data = json.loads(results_file.read_text())
        suite._results = [EvaluationResult(**r) for r in results_data]
        
        print(f"\n✓ Loaded {len(suite._results)} evaluation results from: {dir_path}")
        
        return suite
    
    def get_result(self, run_id: str) -> Optional[EvaluationResult]:
        """Get a specific evaluation result by run ID.
        
        Args:
            run_id: The run identifier
            
        Returns:
            EvaluationResult or None if not found
        """
        for result in self._results:
            if result.run_id == run_id:
                return result
        return None
    
    def list_results(
        self,
        successful_only: bool = False,
        task_name: Optional[str] = None
    ) -> List[EvaluationResult]:
        """Get list of all evaluation results.
        
        Args:
            successful_only: If True, only return successful runs
            task_name: If provided, only return results with this task name
            
        Returns:
            List of EvaluationResult objects
        """
        results = self._results
        
        if successful_only:
            results = [r for r in results if r.success]
        
        if task_name:
            results = [r for r in results if r.task_name == task_name]
        
        return results
    
    def aggregate_results(
        self,
        run_ids: Optional[List[str]] = None,
        task_name: Optional[str] = None,
        aggregation_fn: Optional[Callable[[List[EvaluationResult]], Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Aggregate results across multiple runs.
        
        Args:
            run_ids: Specific run IDs to aggregate (None = all successful runs)
            task_name: Filter runs by task name
            aggregation_fn: Custom aggregation function. If None, uses default.
            
        Returns:
            Aggregated results dictionary
        """
        # Get results to aggregate
        if run_ids:
            found_results = [self.get_result(rid) for rid in run_ids]
            results = [r for r in found_results if r is not None]
        else:
            results = self.list_results(successful_only=True, task_name=task_name)
        
        if not results:
            return {"error": "No results found for aggregation"}
        
        # Apply aggregation function
        if aggregation_fn:
            return aggregation_fn(results)
        else:
            return self._default_aggregation(results)
    
    def _default_aggregation(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """Default aggregation strategy.
        
        Args:
            results: List of EvaluationResult objects
            
        Returns:
            Aggregated results
        """
        return {
            "num_runs": len(results),
            "run_ids": [r.run_id for r in results],
            "task_names": list(set(r.task_name for r in results)),
            "results": [
                {
                    "run_id": r.run_id,
                    "timestamp": r.timestamp,
                    "task_name": r.task_name,
                    "success": r.success,
                    "summary": r.results_summary
                }
                for r in results
            ]
        }
    
    def visualize_results(self) -> None:
        """Print a summary of all evaluation results."""
        print(f"\n{'='*80}")
        print("Evaluation Results Summary")
        print('='*80)
        
        # Dataset manager info
        print(f"\nDatasets: {len(self._dataset_manager.list_dataset_ids())}")
        
        # Results summary
        print(f"\nEvaluation Runs: {len(self._results)}")
        successful = len([r for r in self._results if r.success])
        failed = len(self._results) - successful
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        
        if self._results:
            print("\nRecent Runs:")
            for result in self._results[-5:]:  # Show last 5 runs
                status = "✓" if result.success else "✗"
                print(f"  {status} {result.run_id}")
                print(f"     Task: {result.task_name}")
                print(f"     Time: {result.timestamp}")
                print(f"     Datasets: {len(result.dataset_ids)}")
        
        print('='*80)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the evaluation results.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_runs": len(self._results),
            "successful_runs": len([r for r in self._results if r.success]),
            "failed_runs": len([r for r in self._results if not r.success]),
            "unique_tasks": len(set(r.task_name for r in self._results)),
            "num_datasets": len(self._dataset_manager.list_dataset_ids()),
            "dataset_ids": self._dataset_manager.list_dataset_ids()
        }
        
        if self._results:
            stats["first_run"] = self._results[0].timestamp
            stats["last_run"] = self._results[-1].timestamp
        
        return stats
