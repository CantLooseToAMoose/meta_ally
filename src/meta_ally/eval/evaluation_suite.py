"""Simplified evaluation suite for running and managing evaluation results.

This module provides the EvaluationSuite class which focuses on:
1. Running evaluations on DatasetManager datasets
2. Saving and loading EvaluationReport objects with metadata
3. Accessing and analyzing evaluation results across runs

The EvaluationSuite manages evaluation execution and stores the rich EvaluationReport
objects from pydantic_evals, along with minimal metadata for organization and tracking.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
import json
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic_evals.evaluators import Evaluator

from .dataset_manager import DatasetManager


class EvaluationMetadata(BaseModel):
    """Lightweight metadata record for a single evaluation run."""
    
    run_id: str = Field(description="Unique identifier for this run")
    timestamp: str = Field(description="ISO format timestamp of when run started")
    task_name: str = Field(description="Name of the evaluation task")
    dataset_manager_names: List[str] = Field(description="Names of dataset managers used")
    dataset_ids: List[str] = Field(description="List of dataset IDs evaluated")
    evaluator_names: List[str] = Field(description="Names of evaluators used")
    retry_config: Optional[Dict[str, Any]] = Field(default=None, description="Retry configuration used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional custom metadata")
    success: bool = Field(default=True, description="Whether the run completed successfully")
    error_message: Optional[str] = Field(default=None, description="Error message if run failed")


class EvaluationSuite:
    """Suite for running evaluations and managing EvaluationReport objects.
    
    This class:
    - Runs evaluations on one or multiple DatasetManager instances
    - Stores full EvaluationReport objects (from pydantic_evals)
    - Maintains lightweight metadata for organization
    - Saves/loads reports and metadata to/from disk
    - Provides access to rich evaluation results
    
    Main public methods:
    - add_dataset_manager(): Add a dataset manager to the suite
    - run_evaluation(): Execute evaluation and store reports with metadata
    - save_results(): Save reports and metadata to disk
    - load(): Load a suite with reports and metadata from disk (classmethod)
    - get_report(): Get EvaluationReport for a specific run
    - get_metadata(): Get metadata for a specific run
    - list_runs(): List all evaluation runs with metadata
    
    Example:
        ```python
        # Single dataset manager
        manager = DatasetManager.load("Data/add_one")
        suite = EvaluationSuite(manager)
        
        # Or multiple dataset managers
        manager1 = DatasetManager.load("Data/add_one")
        manager2 = DatasetManager.load("Data/conversation")
        suite = EvaluationSuite([manager1, manager2])
        
        # Or add managers later
        suite = EvaluationSuite()
        suite.add_dataset_manager(manager1, name="add_one")
        suite.add_dataset_manager(manager2, name="conversation")
        
        # Run evaluation - returns dict of EvaluationReport objects
        reports = suite.run_evaluation(
            task=my_task,
            evaluators=[evaluator1, evaluator2],
            task_name="conversation_evaluation"
        )
        
        # Access a report
        for dataset_id, report in reports.items():
            report.print()  # Use pydantic_evals built-in printing
            avg = report.averages()  # Use built-in aggregation
        
        # Save results
        suite.save_results("evaluation_results")
        
        # Load suite later
        loaded_suite = EvaluationSuite.load(
            "evaluation_results",
            dataset_managers=[manager1, manager2]
        )
        
        # Access stored reports
        report = loaded_suite.get_report("my_run_id", "dataset_1")
        ```
    """
    
    def __init__(
        self, 
        dataset_managers: Optional[Union[DatasetManager, List[DatasetManager]]] = None
    ):
        """Initialize an EvaluationSuite.
        
        Args:
            dataset_managers: Single DatasetManager, list of DatasetManagers, or None.
                            If None, managers can be added later with add_dataset_manager().
        """
        self._dataset_managers: Dict[str, DatasetManager] = {}
        self._metadata: List[EvaluationMetadata] = []
        self._reports: Dict[str, Dict[str, Any]] = {}  # run_id -> {dataset_id -> EvaluationReport}
        
        # Add initial dataset managers
        if dataset_managers is not None:
            if isinstance(dataset_managers, list):
                for i, manager in enumerate(dataset_managers):
                    self.add_dataset_manager(manager, name=f"manager_{i}")
            else:
                self.add_dataset_manager(dataset_managers, name="default")
    
    def add_dataset_manager(
        self, 
        dataset_manager: DatasetManager, 
        name: Optional[str] = None
    ) -> str:
        """Add a dataset manager to the suite.
        
        Args:
            dataset_manager: DatasetManager instance to add
            name: Optional name for the manager. If None, uses "manager_{n}"
            
        Returns:
            The name assigned to the manager
        """
        if name is None:
            name = f"manager_{len(self._dataset_managers)}"
        
        if name in self._dataset_managers:
            raise ValueError(f"Dataset manager with name '{name}' already exists")
        
        self._dataset_managers[name] = dataset_manager
        return name
    
    def get_dataset_manager(self, name: str) -> Optional[DatasetManager]:
        """Get a dataset manager by name.
        
        Args:
            name: Name of the dataset manager
            
        Returns:
            DatasetManager or None if not found
        """
        return self._dataset_managers.get(name)
    
    def list_dataset_managers(self) -> List[str]:
        """List all dataset manager names.
        
        Returns:
            List of dataset manager names
        """
        return list(self._dataset_managers.keys())
    
    def list_all_datasets(self) -> Dict[str, List[str]]:
        """List all datasets across all managers.
        
        Returns:
            Dictionary mapping manager names to their dataset IDs
        """
        return {
            name: manager.list_dataset_ids()
            for name, manager in self._dataset_managers.items()
        }
    
    def run_evaluation(
        self,
        task: Callable,
        evaluators: Optional[List[Evaluator]] = None,
        task_name: str = "evaluation",
        dataset_manager_names: Optional[List[str]] = None,
        dataset_ids: Optional[List[str]] = None,
        retry_config: Optional[Dict[str, Any]] = None,
        wrap_with_hooks: bool = True,
        use_async: bool = False,
        run_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run evaluation on datasets and store reports with metadata.
        
        Args:
            task: The evaluation task function
            evaluators: List of evaluators to use
            task_name: Name for this evaluation task
            dataset_manager_names: Specific managers to use (None = all managers)
            dataset_ids: Specific datasets to evaluate (None = all datasets from selected managers)
            retry_config: Retry configuration for tenacity
            wrap_with_hooks: Whether to wrap tasks with dataset hooks
            use_async: Whether to use async evaluation
            run_metadata: Additional custom metadata for this run
            
        Returns:
            Dictionary mapping dataset IDs to their EvaluationReport objects
        """
        if not self._dataset_managers:
            raise ValueError("No dataset managers available. Add at least one with add_dataset_manager().")
        
        # Determine which managers to use
        manager_names = dataset_manager_names or list(self._dataset_managers.keys())
        
        # Collect all dataset IDs if not specified
        all_dataset_ids = []
        for name in manager_names:
            if name not in self._dataset_managers:
                raise ValueError(f"Dataset manager '{name}' not found")
            all_dataset_ids.extend(self._dataset_managers[name].list_dataset_ids())
        
        # Generate run ID
        timestamp = datetime.now()
        run_id = f"{task_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Create metadata record
        metadata = EvaluationMetadata(
            run_id=run_id,
            timestamp=timestamp.isoformat(),
            task_name=task_name,
            dataset_manager_names=manager_names,
            dataset_ids=dataset_ids or all_dataset_ids,
            evaluator_names=[type(e).__name__ for e in evaluators] if evaluators else [],
            retry_config=retry_config,
            metadata=run_metadata or {}
        )
        
        try:
            # Run evaluation
            print(f"\n{'='*80}")
            print(f"Starting Evaluation: {run_id}")
            print(f"Task: {task_name}")
            print(f"Dataset Managers: {', '.join(manager_names)}")
            print(f"Datasets: {len(metadata.dataset_ids)}")
            if evaluators:
                print(f"Evaluators: {', '.join(metadata.evaluator_names)}")
            print('='*80)
            
            # Run evaluation on each selected manager
            reports = {}
            for manager_name in manager_names:
                manager = self._dataset_managers[manager_name]
                
                # Filter dataset_ids for this manager if specified
                manager_dataset_ids = None
                if dataset_ids:
                    available_ids = manager.list_dataset_ids()
                    manager_dataset_ids = [did for did in dataset_ids if did in available_ids]
                    if not manager_dataset_ids:
                        continue  # Skip this manager if no matching datasets
                
                print(f"\n--- Evaluating with manager: {manager_name} ---")
                
                manager_reports = manager.evaluate_all_datasets(
                    task=task,
                    evaluators=evaluators,
                    retry_config=retry_config,
                    wrap_with_hooks=wrap_with_hooks,
                    use_async=use_async,
                    dataset_ids=manager_dataset_ids
                )
                
                reports.update(manager_reports)
            
            metadata.success = True
            
            # Store reports
            self._reports[run_id] = reports
            
            print(f"\n{'='*80}")
            print(f"✓ Evaluation Completed: {run_id}")
            print(f"  Total reports: {len(reports)}")
            print('='*80)
            
        except Exception as e:
            print(f"\n{'='*80}")
            print(f"✗ Evaluation Failed: {run_id}")
            print(f"Error: {e}")
            print('='*80)
            
            metadata.success = False
            metadata.error_message = str(e)
            reports = {"error": str(e)}
            self._reports[run_id] = reports
        
        # Store metadata
        self._metadata.append(metadata)
        
        return reports
    
    def save_results(
        self,
        directory: Union[Path, str],
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """Save evaluation reports and metadata to disk.
        
        Creates directory structure:
        - directory/
          - metadata.json (all EvaluationMetadata records)
          - reports/
            - {run_id}/
              - {dataset_id}.json (each EvaluationReport serialized)
        
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
            "metadata_file": None,
            "num_runs": len(self._metadata),
            "report_files": []
        }
        
        # Save metadata
        metadata_file = dir_path / "metadata.json"
        metadata_data = [m.model_dump() for m in self._metadata]
        metadata_file.write_text(json.dumps(metadata_data, indent=2))
        saved_info["metadata_file"] = str(metadata_file)
        
        # Save reports
        reports_dir = dir_path / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        for run_id, dataset_reports in self._reports.items():
            run_dir = reports_dir / run_id
            run_dir.mkdir(exist_ok=True)
            
            for dataset_id, report in dataset_reports.items():
                report_file = run_dir / f"{dataset_id}.json"
                
                # Serialize the report
                if hasattr(report, 'model_dump'):
                    # It's a Pydantic model (EvaluationReport)
                    report_data = report.model_dump(mode='json')
                elif isinstance(report, dict):
                    # It's an error dict or already serialized
                    report_data = report
                else:
                    # Try to convert to dict
                    report_data = {"__type__": type(report).__name__, "data": str(report)}
                
                report_file.write_text(json.dumps(report_data, indent=2))
                saved_info["report_files"].append(str(report_file))
        
        print(f"\n✓ Evaluation results saved to: {dir_path}")
        print("  - Metadata: metadata.json")
        print(f"  - Total runs: {len(self._metadata)}")
        print(f"  - Total reports: {len(saved_info['report_files'])}")
        
        return saved_info
    
    @classmethod
    def load(
        cls,
        directory: Union[Path, str],
        dataset_managers: Optional[Union[DatasetManager, List[DatasetManager], Dict[str, DatasetManager]]] = None
    ) -> EvaluationSuite:
        """Load an EvaluationSuite with reports and metadata from disk.
        
        Args:
            directory: Directory containing saved results
            dataset_managers: DatasetManager(s) to use. Can be:
                - Single DatasetManager (will be named "default")
                - List of DatasetManagers (will be named "manager_0", "manager_1", ...)
                - Dict mapping names to DatasetManagers
                - None (suite will be created without managers, can add later)
            
        Returns:
            EvaluationSuite with loaded reports and metadata
            
        Raises:
            FileNotFoundError: If metadata file not found
        """
        dir_path = Path(directory) if isinstance(directory, str) else directory
        metadata_file = dir_path / "metadata.json"
        
        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")
        
        # Create suite instance with managers
        if isinstance(dataset_managers, dict):
            suite = cls()
            for name, manager in dataset_managers.items():
                suite.add_dataset_manager(manager, name=name)
        else:
            suite = cls(dataset_managers)
        
        # Load metadata
        metadata_data = json.loads(metadata_file.read_text())
        suite._metadata = [EvaluationMetadata(**m) for m in metadata_data]
        
        # Load reports
        reports_dir = dir_path / "reports"
        if reports_dir.exists():
            for run_dir in reports_dir.iterdir():
                if run_dir.is_dir():
                    run_id = run_dir.name
                    suite._reports[run_id] = {}
                    
                    for report_file in run_dir.glob("*.json"):
                        dataset_id = report_file.stem
                        report_data = json.loads(report_file.read_text())
                        # Store as dict - user can convert back to EvaluationReport if needed
                        suite._reports[run_id][dataset_id] = report_data
        
        print(f"\n✓ Loaded {len(suite._metadata)} evaluation runs from: {dir_path}")
        print(f"  - Total reports: {sum(len(r) for r in suite._reports.values())}")
        
        return suite
    
    def get_report(self, run_id: str, dataset_id: str) -> Optional[Any]:
        """Get an EvaluationReport for a specific run and dataset.
        
        Args:
            run_id: The run identifier
            dataset_id: The dataset identifier
            
        Returns:
            EvaluationReport (or dict if loaded from disk) or None if not found
        """
        if run_id in self._reports:
            return self._reports[run_id].get(dataset_id)
        return None
    
    def get_all_reports(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get all EvaluationReports for a specific run.
        
        Args:
            run_id: The run identifier
            
        Returns:
            Dictionary mapping dataset IDs to reports, or None if run not found
        """
        return self._reports.get(run_id)
    
    def get_metadata(self, run_id: str) -> Optional[EvaluationMetadata]:
        """Get metadata for a specific evaluation run.
        
        Args:
            run_id: The run identifier
            
        Returns:
            EvaluationMetadata or None if not found
        """
        for metadata in self._metadata:
            if metadata.run_id == run_id:
                return metadata
        return None
    
    def list_runs(
        self,
        successful_only: bool = False,
        task_name: Optional[str] = None
    ) -> List[EvaluationMetadata]:
        """Get list of all evaluation runs.
        
        Args:
            successful_only: If True, only return successful runs
            task_name: If provided, only return runs with this task name
            
        Returns:
            List of EvaluationMetadata objects
        """
        runs = self._metadata
        
        if successful_only:
            runs = [r for r in runs if r.success]
        
        if task_name:
            runs = [r for r in runs if r.task_name == task_name]
        
        return runs
    
    def print_run_summary(self, run_id: str) -> None:
        """Print a summary of a specific evaluation run.
        
        Args:
            run_id: The run identifier
        """
        metadata = self.get_metadata(run_id)
        if not metadata:
            print(f"Run not found: {run_id}")
            return
        
        reports = self.get_all_reports(run_id)
        
        print(f"\n{'='*80}")
        print(f"Evaluation Run: {run_id}")
        print('='*80)
        print(f"Task: {metadata.task_name}")
        print(f"Timestamp: {metadata.timestamp}")
        print(f"Status: {'✓ Success' if metadata.success else '✗ Failed'}")
        
        if metadata.error_message:
            print(f"Error: {metadata.error_message}")
        
        if metadata.evaluator_names:
            print(f"Evaluators: {', '.join(metadata.evaluator_names)}")
        
        print(f"\nDatasets ({len(metadata.dataset_ids)}):")
        for dataset_id in metadata.dataset_ids:
            print(f"  - {dataset_id}")
        
        if reports and metadata.success:
            print(f"\nReports available: {len(reports)}")
            
            # Show brief summary of each report if it's an EvaluationReport
            for dataset_id, report in reports.items():
                if isinstance(report, dict) and "error" not in report:
                    if "cases" in report:
                        num_cases = len(report["cases"])
                        print(f"  - {dataset_id}: {num_cases} cases")
                    else:
                        print(f"  - {dataset_id}: Report available")
        
        print('='*80)
    
    def visualize_results(self) -> None:
        """Print a summary of all evaluation runs."""
        print(f"\n{'='*80}")
        print("Evaluation Suite Summary")
        print('='*80)
        
        # Dataset managers info
        print(f"\nDataset Managers: {len(self._dataset_managers)}")
        total_datasets = sum(
            len(manager.list_dataset_ids()) 
            for manager in self._dataset_managers.values()
        )
        print(f"Total Datasets: {total_datasets}")
        
        if self._dataset_managers:
            print("\nManagers:")
            for name, manager in self._dataset_managers.items():
                print(f"  - {name}: {len(manager.list_dataset_ids())} datasets")
        
        # Runs summary
        print(f"\nEvaluation Runs: {len(self._metadata)}")
        successful = len([m for m in self._metadata if m.success])
        failed = len(self._metadata) - successful
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        
        if self._metadata:
            print("\nRecent Runs:")
            for metadata in self._metadata[-5:]:  # Show last 5 runs
                status = "✓" if metadata.success else "✗"
                print(f"  {status} {metadata.run_id}")
                print(f"     Task: {metadata.task_name}")
                print(f"     Time: {metadata.timestamp}")
                print(f"     Managers: {', '.join(metadata.dataset_manager_names)}")
                print(f"     Datasets: {len(metadata.dataset_ids)}")
        
        print('='*80)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the evaluation runs.
        
        Returns:
            Dictionary with statistics
        """
        all_datasets = self.list_all_datasets()
        total_datasets = sum(len(ds) for ds in all_datasets.values())
        
        stats = {
            "total_runs": len(self._metadata),
            "successful_runs": len([m for m in self._metadata if m.success]),
            "failed_runs": len([m for m in self._metadata if not m.success]),
            "unique_tasks": len(set(m.task_name for m in self._metadata)),
            "num_dataset_managers": len(self._dataset_managers),
            "dataset_managers": list(self._dataset_managers.keys()),
            "num_datasets": total_datasets,
            "datasets_by_manager": all_datasets
        }
        
        if self._metadata:
            stats["first_run"] = self._metadata[0].timestamp
            stats["last_run"] = self._metadata[-1].timestamp
        
        return stats
