"""
Evaluation Suite Manager for running evaluations across multiple datasets.

This module provides a manager for coordinating evaluations across multiple
DatasetManager instances, allowing for comprehensive evaluation suites with
different datasets and evaluators.
"""

from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field
from pydantic_evals.evaluators import Evaluator
from .dataset_manager import DatasetManager


@dataclass
class EvaluationResult:
    """Results from evaluating a single dataset."""
    dataset_name: str
    report: Any  # EvaluationReport from pydantic_evals
    
    def print(self) -> None:
        """Print the evaluation report."""
        print(f"\n{'='*80}")
        print(f"Dataset: {self.dataset_name}")
        print(f"{'='*80}")
        self.report.print()


@dataclass
class SuiteEvaluationResults:
    """Results from evaluating an entire suite."""
    suite_name: str
    results: List[EvaluationResult] = field(default_factory=list)
    
    def print(self) -> None:
        """Print all evaluation reports in the suite."""
        print(f"\n{'#'*80}")
        print(f"# Evaluation Suite: {self.suite_name}")
        print(f"{'#'*80}\n")
        
        for result in self.results:
            result.print()
        
        print(f"\n{'#'*80}")
        print(f"# Summary: {len(self.results)} datasets evaluated")
        print(f"{'#'*80}\n")
    
    def get_result(self, dataset_name: str) -> Optional[EvaluationResult]:
        """Get results for a specific dataset by name."""
        for result in self.results:
            if result.dataset_name == dataset_name:
                return result
        return None


class EvaluationSuiteManager:
    """Manager for coordinating evaluations across multiple datasets.
    
    This class allows you to:
    1. Register multiple DatasetManager instances
    2. Add evaluators globally or per-dataset
    3. Run evaluation tasks across all or specific datasets
    4. Collect and aggregate results
    
    Example:
        ```python
        suite = EvaluationSuiteManager(name="My Evaluation Suite")
        
        # Add dataset managers
        suite.add_dataset_manager("dataset1", manager1)
        suite.add_dataset_manager("dataset2", manager2)
        
        # Add global evaluators (applied to all datasets)
        suite.add_global_evaluator(ToolCallEvaluator())
        
        # Add dataset-specific evaluators
        suite.add_evaluator("dataset1", custom_evaluator)
        
        # Run evaluations
        results = await suite.run_evaluation(task, deps)
        results.print()
        ```
    """
    
    def __init__(self, name: str = "Evaluation Suite"):
        """Initialize the EvaluationSuiteManager.
        
        Args:
            name: Name for this evaluation suite
        """
        self.name = name
        self._dataset_managers: Dict[str, DatasetManager] = {}
        self._global_evaluators: List[Evaluator] = []
        self._dataset_evaluators: Dict[str, List[Evaluator]] = {}
    
    def add_dataset_manager(
        self,
        name: str,
        manager: DatasetManager
    ) -> None:
        """Add a DatasetManager to the suite.
        
        Args:
            name: Unique name for this dataset
            manager: DatasetManager instance to add
            
        Raises:
            ValueError: If a dataset with this name already exists
        """
        if name in self._dataset_managers:
            raise ValueError(f"Dataset with name '{name}' already exists")
        
        self._dataset_managers[name] = manager
        self._dataset_evaluators[name] = []
    
    def remove_dataset_manager(self, name: str) -> None:
        """Remove a DatasetManager from the suite.
        
        Args:
            name: Name of the dataset to remove
            
        Raises:
            KeyError: If no dataset with this name exists
        """
        if name not in self._dataset_managers:
            raise KeyError(f"No dataset with name '{name}' found")
        
        del self._dataset_managers[name]
        del self._dataset_evaluators[name]
    
    def get_dataset_manager(self, name: str) -> DatasetManager:
        """Get a specific DatasetManager by name.
        
        Args:
            name: Name of the dataset
            
        Returns:
            The DatasetManager instance
            
        Raises:
            KeyError: If no dataset with this name exists
        """
        if name not in self._dataset_managers:
            raise KeyError(f"No dataset with name '{name}' found")
        
        return self._dataset_managers[name]
    
    def list_datasets(self) -> List[str]:
        """Get list of all dataset names in the suite.
        
        Returns:
            List of dataset names
        """
        return list(self._dataset_managers.keys())
    
    def add_global_evaluator(self, evaluator: Evaluator) -> None:
        """Add an evaluator that will be applied to all datasets.
        
        Args:
            evaluator: Evaluator instance to add
        """
        self._global_evaluators.append(evaluator)
    
    def add_evaluator(self, dataset_name: str, evaluator: Evaluator) -> None:
        """Add an evaluator for a specific dataset.
        
        Args:
            dataset_name: Name of the dataset to add the evaluator to
            evaluator: Evaluator instance to add
            
        Raises:
            KeyError: If no dataset with this name exists
        """
        if dataset_name not in self._dataset_managers:
            raise KeyError(f"No dataset with name '{dataset_name}' found")
        
        self._dataset_evaluators[dataset_name].append(evaluator)
    
    def clear_global_evaluators(self) -> None:
        """Clear all global evaluators."""
        self._global_evaluators.clear()
    
    def clear_dataset_evaluators(self, dataset_name: str) -> None:
        """Clear evaluators for a specific dataset.
        
        Args:
            dataset_name: Name of the dataset
            
        Raises:
            KeyError: If no dataset with this name exists
        """
        if dataset_name not in self._dataset_managers:
            raise KeyError(f"No dataset with name '{dataset_name}' found")
        
        self._dataset_evaluators[dataset_name].clear()
    
    def _apply_evaluators(self, dataset_name: str, manager: DatasetManager) -> None:
        """Apply global and dataset-specific evaluators to a dataset.
        
        Args:
            dataset_name: Name of the dataset
            manager: DatasetManager instance
        """
        if manager.dataset is None:
            raise ValueError(
                f"Dataset '{dataset_name}' has not been built. "
                "Call build_dataset() on the manager before running evaluation."
            )
        
        # Add global evaluators
        for evaluator in self._global_evaluators:
            manager.dataset.add_evaluator(evaluator)
        
        # Add dataset-specific evaluators
        for evaluator in self._dataset_evaluators[dataset_name]:
            manager.dataset.add_evaluator(evaluator)
    
    async def run_evaluation(
        self,
        task: Callable[[Any], Any],
        dataset_names: Optional[List[str]] = None,
        max_concurrency: Optional[int] = None,
        progress: bool = True,
        retry_task: Optional[Any] = None,
        retry_evaluators: Optional[Any] = None,
    ) -> SuiteEvaluationResults:
        """Run evaluation task across all or specified datasets.
        
        Args:
            task: The task function to evaluate
            dataset_names: Optional list of dataset names to evaluate. If None, evaluates all.
            max_concurrency: Maximum number of concurrent evaluations per dataset
            progress: Whether to show progress bars
            retry_task: Optional retry configuration for task execution
            retry_evaluators: Optional retry configuration for evaluator execution
            
        Returns:
            SuiteEvaluationResults containing all evaluation results
            
        Raises:
            ValueError: If specified dataset names don't exist or datasets aren't built
        """
        # Determine which datasets to evaluate
        datasets_to_evaluate = dataset_names if dataset_names else list(self._dataset_managers.keys())
        
        # Validate dataset names
        for name in datasets_to_evaluate:
            if name not in self._dataset_managers:
                raise ValueError(f"Dataset '{name}' not found in suite")
        
        results = []
        
        for dataset_name in datasets_to_evaluate:
            manager = self._dataset_managers[dataset_name]
            
            # Apply evaluators
            self._apply_evaluators(dataset_name, manager)
            
            # Run evaluation
            report = await manager.run_evaluation(
                task=task,
                name=f"{self.name} - {dataset_name}",
                max_concurrency=max_concurrency,
                progress=progress,
                retry_task=retry_task,
                retry_evaluators=retry_evaluators,
            )
            
            results.append(EvaluationResult(
                dataset_name=dataset_name,
                report=report
            ))
        
        return SuiteEvaluationResults(
            suite_name=self.name,
            results=results
        )
    
    def run_evaluation_sync(
        self,
        task: Callable[[Any], Any],
        dataset_names: Optional[List[str]] = None,
        max_concurrency: Optional[int] = None,
        progress: bool = True,
        retry_task: Optional[Any] = None,
        retry_evaluators: Optional[Any] = None,
    ) -> SuiteEvaluationResults:
        """Synchronous wrapper for run_evaluation.
        
        Args:
            task: The task function to evaluate
            dataset_names: Optional list of dataset names to evaluate. If None, evaluates all.
            max_concurrency: Maximum number of concurrent evaluations per dataset
            progress: Whether to show progress bars
            retry_task: Optional retry configuration for task execution
            retry_evaluators: Optional retry configuration for evaluator execution
            
        Returns:
            SuiteEvaluationResults containing all evaluation results
        """
        import asyncio
        
        return asyncio.get_event_loop().run_until_complete(
            self.run_evaluation(
                task=task,
                dataset_names=dataset_names,
                max_concurrency=max_concurrency,
                progress=progress,
                retry_task=retry_task,
                retry_evaluators=retry_evaluators,
            )
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about all datasets in the suite.
        
        Returns:
            Dictionary with dataset statistics
        """
        stats = {
            "suite_name": self.name,
            "num_datasets": len(self._dataset_managers),
            "global_evaluators": len(self._global_evaluators),
            "datasets": {}
        }
        
        for name, manager in self._dataset_managers.items():
            dataset_stats = manager.get_stats()
            dataset_stats["dataset_evaluators"] = len(self._dataset_evaluators[name])
            stats["datasets"][name] = dataset_stats
        
        return stats
    
    def print_stats(self) -> None:
        """Print statistics about the evaluation suite."""
        stats = self.get_stats()
        
        print(f"\n{'='*80}")
        print(f"Evaluation Suite: {stats['suite_name']}")
        print(f"{'='*80}")
        print(f"Number of datasets: {stats['num_datasets']}")
        print(f"Global evaluators: {stats['global_evaluators']}")
        print()
        
        for dataset_name, dataset_stats in stats["datasets"].items():
            print(f"  Dataset: {dataset_name}")
            print(f"    Original cases: {dataset_stats['original_cases']}")
            print(f"    Variant cases: {dataset_stats['variant_cases']}")
            print(f"    Total cases: {dataset_stats['total_cases']}")
            print(f"    Dataset-specific evaluators: {dataset_stats['dataset_evaluators']}")
            print()
        
        print(f"{'='*80}\n")
