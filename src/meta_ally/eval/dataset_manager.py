"""
Manage the creation and serialization of pydantic ai datasets from MessageHistoryCase with variants.

This module provides utilities for:
1. Creating variants from existing MessageHistoryCase objects
2. Building datasets that include both original cases and their variants
3. Saving datasets to YAML/JSON files with proper serialization
4. Loading datasets from YAML/JSON files with proper deserialization
5. Managing multiple datasets, each with their own original case and variants
6. Saving and loading complete DatasetManager state with hook libraries
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union, Dict, Any, Callable
import json
from pydantic_evals import Dataset
from .case_factory import MessageHistoryCase, ExpectedOutput, create_case_variant
from .dataset_hooks import HookLibrary
from .dataset_config import SerializableDatasetConfig, DatasetConfig


class DatasetManager:
    """Manager for creating and managing multiple datasets with variants from MessageHistoryCase objects.
    
    This class supports managing multiple independent datasets, each with their own
    original case, variants, hooks, and metadata.
    
    Main public methods:
    - create_dataset_from_case(): Create a new dataset with variants
    - add_variants_to_dataset(): Add more variants to an existing dataset
    - set_dataset_hooks(): Assign hooks to a dataset
    - save(): Save the manager to a directory
    - load(): Load a manager from a directory (classmethod)
    - visualize_dataset_comparison(): Visualize a dataset and its variants
    - get_dataset_stats(): Get statistics for a dataset
    """

    def __init__(self, hook_library: Optional[HookLibrary] = None):
        """Initialize the DatasetManager.
        
        Args:
            hook_library: Optional HookLibrary for managing reusable hooks.
                         If None, a new empty DefaultHookLibrary is created.
        """
        self._datasets: Dict[str, DatasetConfig] = {}
        self.hook_library: Optional[HookLibrary] = hook_library
        
    def create_dataset_from_case(
        self,
        case: MessageHistoryCase,
        dataset_id: Optional[str] = None,
        num_variants: int = 2,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new dataset from a case with its variants.
        
        The dataset is automatically built and stored in the config.
        
        Args:
            case: The original MessageHistoryCase
            dataset_id: Unique identifier. If None, will use case.name as ID
            num_variants: Number of variants to generate
            name: Human-readable name. If None, uses case.name
            description: Optional description
            metadata: Additional metadata
            
        Returns:
            The dataset_id of the created dataset
            
        Raises:
            ValueError: If dataset_id already exists
        """
        # Generate ID if not provided
        if dataset_id is None:
            dataset_id = case.name
            
        # Check if ID already exists
        if dataset_id in self._datasets:
            raise ValueError(f"Dataset with ID '{dataset_id}' already exists")
            
        # Use case name as dataset name if not provided
        if name is None:
            name = case.name
            
        # Create the dataset config
        config = DatasetConfig(
            dataset_id=dataset_id,
            name=name,
            original_case=case,
            variants=[],
            description=description,
            metadata=metadata or {}
        )
        
        # Generate variants if requested
        if num_variants > 0:
            previous_variants = []
            for variant_num in range(1, num_variants + 1):
                variant_case = create_case_variant(
                    case,
                    previous_variants=previous_variants
                )
                variant_case.name = f"{case.name} - Variant {variant_num}"
                config.variants.append(variant_case)
                previous_variants.append(variant_case)
        
        # Store the dataset config
        self._datasets[dataset_id] = config
        
        # Build the dataset immediately
        self._build_dataset_for_config(
            dataset_id=dataset_id,
            include_original=True,
            include_variants=True
        )
        
        return dataset_id
    
    def add_dataset_config(self, config: DatasetConfig) -> None:
        """Add a pre-configured DatasetConfig.
        
        Args:
            config: The DatasetConfig to add
            
        Raises:
            ValueError: If dataset_id already exists
        """
        if config.dataset_id in self._datasets:
            raise ValueError(f"Dataset with ID '{config.dataset_id}' already exists")
        self._datasets[config.dataset_id] = config
    
    def get_dataset_config(self, dataset_id: str) -> DatasetConfig:
        """Get a dataset configuration by ID.
        
        Args:
            dataset_id: The dataset identifier
            
        Returns:
            The DatasetConfig object
            
        Raises:
            KeyError: If dataset_id not found
        """
        if dataset_id not in self._datasets:
            raise KeyError(f"Dataset with ID '{dataset_id}' not found")
        return self._datasets[dataset_id]
    
    def list_dataset_ids(self) -> List[str]:
        """Get list of all dataset IDs.
        
        Returns:
            List of dataset IDs
        """
        return list(self._datasets.keys())
    
    def get_all_datasets(self) -> Dict[str, DatasetConfig]:
        """Get all dataset configurations.
        
        Returns:
            Dictionary mapping dataset IDs to their configs
        """
        return self._datasets.copy()
    
    def remove_dataset(self, dataset_id: str) -> None:
        """Remove a dataset by ID.
        
        Args:
            dataset_id: The dataset identifier
            
        Raises:
            KeyError: If dataset_id not found
        """
        if dataset_id not in self._datasets:
            raise KeyError(f"Dataset with ID '{dataset_id}' not found")
        del self._datasets[dataset_id]
    
    def add_variants_to_dataset(
        self,
        dataset_id: str,
        num_variants: int = 1
    ) -> List[MessageHistoryCase]:
        """Add more variants to an existing dataset.
        
        The dataset is automatically rebuilt after adding variants.
        
        Args:
            dataset_id: The dataset identifier
            num_variants: Number of additional variants to create
            
        Returns:
            List of newly created variants
            
        Raises:
            KeyError: If dataset_id not found
        """
        config = self.get_dataset_config(dataset_id)
        
        # Use existing variants as previous variants
        previous_variants = config.variants.copy()
        new_variants = []
        
        start_num = len(config.variants) + 1
        for variant_num in range(start_num, start_num + num_variants):
            variant_case = create_case_variant(
                config.original_case,
                previous_variants=previous_variants
            )
            variant_case.name = f"{config.original_case.name} - Variant {variant_num}"
            config.variants.append(variant_case)
            new_variants.append(variant_case)
            previous_variants.append(variant_case)
        
        # Rebuild the dataset with the new variants
        self._build_dataset_for_config(
            dataset_id=dataset_id,
            include_original=True,
            include_variants=True
        )
            
        return new_variants
    
    def _build_dataset_for_config(
        self,
        dataset_id: str,
        include_original: bool = True,
        include_variants: bool = True
    ) -> Dataset:
        """Build a pydantic-eval Dataset for a specific dataset config.
        
        This is an internal method. Use save() to persist datasets.
        
        Args:
            dataset_id: The dataset identifier
            include_original: Whether to include the original case
            include_variants: Whether to include variant cases
            
        Returns:
            Dataset containing the requested cases
            
        Raises:
            KeyError: If dataset_id not found
            ValueError: If both include_original and include_variants are False
        """
        if not include_original and not include_variants:
            raise ValueError("At least one of include_original or include_variants must be True")
            
        config = self.get_dataset_config(dataset_id)
        cases = []
        
        if include_original:
            cases.append(config.original_case.to_case())
            
        if include_variants:
            cases.extend([variant.to_case() for variant in config.variants])
            
        config.dataset = Dataset(cases=cases, name=config.name)
        return config.dataset
    
    def _build_combined_dataset(
        self,
        name: str = "Combined Dataset",
        dataset_ids: Optional[List[str]] = None,
        include_originals: bool = True,
        include_variants: bool = True
    ) -> Dataset:
        """Build a combined Dataset from multiple dataset configs.
        
        Args:
            name: Name for the combined dataset
            dataset_ids: List of dataset IDs to include. If None, includes all.
            include_originals: Whether to include original cases
            include_variants: Whether to include variant cases
            
        Returns:
            Combined Dataset
            
        Raises:
            ValueError: If both include_originals and include_variants are False
        """
        if not include_originals and not include_variants:
            raise ValueError("At least one of include_originals or include_variants must be True")
            
        # Determine which datasets to include
        ids_to_use = dataset_ids if dataset_ids is not None else self.list_dataset_ids()
        
        cases = []
        for dataset_id in ids_to_use:
            config = self.get_dataset_config(dataset_id)
            
            if include_originals:
                cases.append(config.original_case.to_case())
                
            if include_variants:
                cases.extend([variant.to_case() for variant in config.variants])
                
        return Dataset(cases=cases, name=name)
    
    def _save_dataset_from_config(
        self,
        dataset_id: str,
        path: Union[Path, str],
        include_original: bool = True,
        include_variants: bool = True,
        fmt: Optional[str] = None,
        schema_path: Optional[Union[Path, str]] = None
    ) -> None:
        """Build and save a dataset from a specific config to a file.
        
        This is an internal method used by save(). Not intended for direct use.
        
        Args:
            dataset_id: The dataset identifier
            path: Path to save the dataset to
            include_original: Whether to include the original case
            include_variants: Whether to include variant cases
            fmt: Format to use ('yaml' or 'json'). If None, inferred from file extension
            schema_path: Optional path to save the JSON schema
            
        Raises:
            KeyError: If dataset_id not found
        """
        dataset = self._build_dataset_for_config(
            dataset_id,
            include_original=include_original,
            include_variants=include_variants
        )
        
        dataset.to_file(
            path=Path(path) if isinstance(path, str) else path,
            fmt=fmt,  # type: ignore
            schema_path=schema_path
        )
    
    def _save_all_datasets(
        self,
        output_dir: Union[Path, str],
        include_originals: bool = True,
        include_variants: bool = True,
        fmt: str = "json"
    ) -> Dict[str, Path]:
        """Save all datasets to separate files in a directory.
        
        This is an internal method used by save(). Not intended for direct use.
        
        Args:
            output_dir: Directory to save datasets to
            include_originals: Whether to include original cases
            include_variants: Whether to include variant cases
            fmt: Format to use ('yaml' or 'json')
            
        Returns:
            Dictionary mapping dataset IDs to their file paths
        """
        output_path = Path(output_dir) if isinstance(output_dir, str) else output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        for dataset_id in self.list_dataset_ids():
            # Create safe filename from dataset_id
            safe_filename = dataset_id.replace(" ", "_").replace("/", "_")
            file_path = output_path / f"{safe_filename}.{fmt}"
            
            self._save_dataset_from_config(
                dataset_id=dataset_id,
                path=file_path,
                include_original=include_originals,
                include_variants=include_variants,
                fmt=fmt
            )
            saved_files[dataset_id] = file_path
            
        return saved_files
    
    def set_dataset_hooks(
        self,
        dataset_id: str,
        pre_task_hook: Optional[Callable] = None,
        post_task_hook: Optional[Callable] = None,
        pre_task_hook_id: Optional[str] = None,
        post_task_hook_id: Optional[str] = None
    ) -> None:
        """Set pre and post task hooks for a specific dataset.
        
        Args:
            dataset_id: The dataset identifier
            pre_task_hook: Optional pre-task hook function (direct callable)
            post_task_hook: Optional post-task hook function (direct callable)
            pre_task_hook_id: Optional hook ID to look up in the hook library
            post_task_hook_id: Optional hook ID to look up in the hook library
            
        Note:
            If both callable and hook_id are provided, the callable takes precedence.
            
        Raises:
            KeyError: If dataset_id not found or hook_id not found in library
        """
        config = self.get_dataset_config(dataset_id)
        
        if pre_task_hook is not None:
            config.pre_task_hook = pre_task_hook
        elif pre_task_hook_id is not None:
            if self.hook_library is None:
                raise ValueError("Cannot use hook_id without a hook_library")
            config.pre_task_hook = self.hook_library.get_hook(pre_task_hook_id)
            
        if post_task_hook is not None:
            config.post_task_hook = post_task_hook
        elif post_task_hook_id is not None:
            if self.hook_library is None:
                raise ValueError("Cannot use hook_id without a hook_library")
            config.post_task_hook = self.hook_library.get_hook(post_task_hook_id)
    
    def get_dataset_stats(self, dataset_id: str) -> Dict[str, Any]:
        """Get statistics for a specific dataset.
        
        Args:
            dataset_id: The dataset identifier
            
        Returns:
            Dictionary with dataset statistics
            
        Raises:
            KeyError: If dataset_id not found
        """
        config = self.get_dataset_config(dataset_id)
        return {
            "dataset_id": dataset_id,
            "name": config.name,
            "original_case": config.original_case.name,
            "num_variants": len(config.variants),
            "total_cases": 1 + len(config.variants),
            "has_pre_hook": config.pre_task_hook is not None,
            "has_post_hook": config.post_task_hook is not None,
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all datasets.
        
        Returns:
            Dictionary mapping dataset IDs to their statistics
        """
        return {
            dataset_id: self.get_dataset_stats(dataset_id)
            for dataset_id in self.list_dataset_ids()
        }
    
    def save(
        self,
        directory: Union[Path, str],
        save_built_datasets: bool = True,
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """Save the complete DatasetManager to a directory.
        
        This creates a directory structure:
        - directory/
          - configs/
            - dataset_1.json
            - dataset_2.json
            ...
          - datasets/  (optional, if save_built_datasets=True)
            - dataset_1_built.json
            - dataset_2_built.json
            ...
          - metadata.json
        
        Args:
            directory: Directory to save to
            save_built_datasets: If True, also saves built Dataset objects using pydantic-evals
            overwrite: If True, removes existing directory before saving. Default: True
            
        Returns:
            Dictionary with information about saved files
            
        Example:
            ```python
            manager = DatasetManager()
            # ... create datasets ...
            info = manager.save("my_datasets/")
            ```
        """
        dir_path = Path(directory) if isinstance(directory, str) else directory
        
        # Remove existing directory if overwrite is True
        if overwrite and dir_path.exists():
            import shutil
            shutil.rmtree(dir_path)
        
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        configs_dir = dir_path / "configs"
        configs_dir.mkdir(exist_ok=True)
        
        datasets_dir = None
        if save_built_datasets:
            datasets_dir = dir_path / "datasets"
            datasets_dir.mkdir(exist_ok=True)
        
        saved_info = {
            "directory": str(dir_path),
            "num_datasets": len(self._datasets),
            "config_files": [],
            "dataset_files": [],
            "metadata_file": None
        }
        
        # Collect hook IDs that are actually used by datasets
        used_hook_ids = set()
        
        # Save each dataset config
        for dataset_id, config in self._datasets.items():
            # Create serializable config
            serializable = SerializableDatasetConfig.from_dataset_config(
                config,
                hook_library=self.hook_library
            )
            
            # Track used hook IDs
            if serializable.pre_task_hook_id:
                used_hook_ids.add(serializable.pre_task_hook_id)
            if serializable.post_task_hook_id:
                used_hook_ids.add(serializable.post_task_hook_id)
            
            # Save built dataset if requested and available
            if save_built_datasets and config.dataset is not None and datasets_dir is not None:
                safe_id = dataset_id.replace(" ", "_").replace("/", "_")
                dataset_file = datasets_dir / f"{safe_id}_built.json"
                config.dataset.to_file(dataset_file, fmt="json")
                serializable.dataset_path = str(dataset_file.relative_to(dir_path))
                saved_info["dataset_files"].append(str(dataset_file))
            
            # Save config
            safe_id = dataset_id.replace(" ", "_").replace("/", "_")
            config_file = configs_dir / f"{safe_id}.json"
            config_file.write_text(serializable.model_dump_json(indent=2))
            saved_info["config_files"].append(str(config_file))
        
        # Save metadata about the manager
        metadata = {
            "num_datasets": len(self._datasets),
            "dataset_ids": list(self._datasets.keys()),
            "saved_with_built_datasets": save_built_datasets,
            "hook_ids_used": list(used_hook_ids)
        }
        metadata_file = dir_path / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))
        saved_info["metadata_file"] = str(metadata_file)
        
        return saved_info
    
    @classmethod
    def load(
        cls,
        directory: Union[Path, str],
        hook_library: Optional[HookLibrary] = None
    ) -> DatasetManager:
        """Load a DatasetManager from a directory.
        
        Args:
            directory: Directory containing the saved manager
            hook_library: Optional HookLibrary with registered hooks.
                         If None, hooks will not be restored (datasets will have None hooks).
                         If provided, hooks will be looked up by ID.
            
        Returns:
            DatasetManager instance with loaded state
            
        Example:
            ```python
            # Create and register hooks
            library = HookLibrary()
            library.register_hook("my_pre_hook", my_pre_hook_fn, "My Pre Hook")
            
            # Load manager with hooks
            manager = DatasetManager.load("my_datasets/", hook_library=library)
            ```
        """
        dir_path = Path(directory) if isinstance(directory, str) else directory
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        configs_dir = dir_path / "configs"
        if not configs_dir.exists():
            raise FileNotFoundError(f"Configs directory not found: {configs_dir}")
        
        # Create manager with the provided hook library
        manager = cls(hook_library=hook_library)
        
        # Load each config file
        for config_file in configs_dir.glob("*.json"):
            # Load serializable config
            config_data = json.loads(config_file.read_text())
            serializable = SerializableDatasetConfig.model_validate(config_data)
            
            # Convert to DatasetConfig (hooks will be restored from library if available)
            config = serializable.to_dataset_config(hook_library=manager.hook_library)
            
            # Load built dataset if path is specified
            if serializable.dataset_path:
                dataset_file = dir_path / serializable.dataset_path
                if dataset_file.exists():
                    config.dataset = DatasetManager.load_dataset(dataset_file)
            
            # Add to manager
            manager._datasets[config.dataset_id] = config
        
        return manager
    
    def visualize_dataset(
        self,
        dataset_id: str,
        show_details: bool = True,
        max_cases: Optional[int] = None,
        include_original: bool = True,
        include_variants: bool = True,
        console_instance: Optional[Any] = None
    ) -> None:
        """Visualize a specific dataset.
        
        Args:
            dataset_id: The dataset identifier
            show_details: If True, show detailed view of each case
            max_cases: Optional limit on number of cases to visualize in detail
            include_original: Whether to include the original case
            include_variants: Whether to include variant cases
            console_instance: Optional Console instance to use for output
            
        Raises:
            KeyError: If dataset_id not found
        """
        from ..util.visualization import visualize_dataset_from_config
        
        config = self.get_dataset_config(dataset_id)
        visualize_dataset_from_config(
            config,
            show_details=show_details,
            max_cases=max_cases,
            include_original=include_original,
            include_variants=include_variants,
            console_instance=console_instance
        )
    
    def visualize_dataset_comparison(
        self,
        dataset_id: str,
        console_instance: Optional[Any] = None
    ) -> None:
        """Visualize a specific dataset's original case and all its variants for comparison.
        
        Args:
            dataset_id: The dataset identifier
            console_instance: Optional Console instance to use for output
            
        Raises:
            KeyError: If dataset_id not found
        """
        from ..util.visualization import visualize_dataset_comparison as viz_comparison
        
        config = self.get_dataset_config(dataset_id)
        viz_comparison(config, console_instance=console_instance)
    
    def visualize_all_datasets(
        self,
        show_details: bool = False,
        console_instance: Optional[Any] = None
    ) -> None:
        """Visualize summary of all datasets.
        
        Args:
            show_details: If True, show detailed stats for each dataset
            console_instance: Optional Console instance to use for output
        """
        from ..util.visualization import visualize_all_datasets_summary
        
        visualize_all_datasets_summary(
            self._datasets,
            show_details=show_details,
            console_instance=console_instance
        )
    
    def wrap_task_for_dataset(
        self,
        dataset_id: str,
        task: Callable[[Any], Any]
    ) -> Callable[[Any], Any]:
        """Wrap a task function with the hooks from a specific dataset.
        
        Args:
            dataset_id: The dataset identifier
            task: The task function to wrap
            
        Returns:
            Wrapped task function
            
        Raises:
            KeyError: If dataset_id not found
        """
        config = self.get_dataset_config(dataset_id)
        import asyncio
        
        # Check if task is async
        is_async = asyncio.iscoroutinefunction(task)
        
        if is_async:
            async def async_wrapper(inputs: Any) -> Any:
                # Pre-task hook
                if config.pre_task_hook is not None:
                    if asyncio.iscoroutinefunction(config.pre_task_hook):
                        await config.pre_task_hook(inputs)
                    else:
                        config.pre_task_hook(inputs)
                
                # Execute task
                output = await task(inputs)
                
                # Post-task hook
                if config.post_task_hook is not None:
                    if asyncio.iscoroutinefunction(config.post_task_hook):
                        await config.post_task_hook(inputs, output)
                    else:
                        config.post_task_hook(inputs, output)
                
                return output
            
            return async_wrapper
        else:
            def sync_wrapper(inputs: Any) -> Any:
                # Pre-task hook
                if config.pre_task_hook is not None:
                    config.pre_task_hook(inputs)
                
                # Execute task
                output = task(inputs)
                
                # Post-task hook
                if config.post_task_hook is not None:
                    config.post_task_hook(inputs, output)
                
                return output
            
            return sync_wrapper


    @staticmethod
    def load_dataset(path: Union[Path, str]) -> Dataset:
        """Load a dataset from a YAML or JSON file.

        Args:
            path: Path to load the dataset from

        Returns:
            Loaded Dataset object

        Note:
            This uses Dataset.from_file() which properly deserializes
            the message history and expected outputs.
        """
        # Import types for proper deserialization
        from pydantic_ai.messages import ModelMessage

        # Load with proper type hints
        return Dataset[List[ModelMessage], ExpectedOutput, Dict[str, Any]].from_file(
            Path(path) if isinstance(path, str) else path
        )
    
    # Backward compatibility aliases
    def save_manager_state(self, *args, **kwargs):
        """Deprecated: Use save() instead."""
        import warnings
        warnings.warn("save_manager_state() is deprecated, use save() instead", DeprecationWarning, stacklevel=2)
        return self.save(*args, **kwargs)
    
    @classmethod
    def load_manager_state(cls, *args, **kwargs):
        """Deprecated: Use load() instead."""
        import warnings
        warnings.warn("load_manager_state() is deprecated, use load() instead", DeprecationWarning, stacklevel=2)
        return cls.load(*args, **kwargs)


