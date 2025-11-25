"""
Manage the creation and serialization of pydantic ai datasets from MessageHistoryCase with variants.

This module provides utilities for:
1. Creating variants from existing MessageHistoryCase objects
2. Building datasets that include both original cases and their variants
3. Saving datasets to YAML/JSON files with proper serialization
4. Loading datasets from YAML/JSON files with proper deserialization
"""

from pathlib import Path
from typing import List, Optional, Union, Dict, Any, Callable
from pydantic_evals import Dataset
from .case_factory import MessageHistoryCase, ExpectedOutput, create_case_variant


class DatasetManager:
    """Manager for creating datasets with variants from MessageHistoryCase objects."""

    def __init__(self):
        """Initialize the DatasetManager."""
        self._original_cases: List[MessageHistoryCase] = []
        self._variant_mapping: Dict[str, List[MessageHistoryCase]] = {}
        self.dataset: Optional[Dataset] = None
        self._pre_task_hook: Optional[Callable] = None
        self._post_task_hook: Optional[Callable] = None

    def add_case(self, case: MessageHistoryCase) -> None:
        """Add an original case to the manager.

        Args:
            case: The MessageHistoryCase to add
        """
        self._original_cases.append(case)

    def add_cases(self, cases: List[MessageHistoryCase]) -> None:
        """Add multiple original cases to the manager.

        Args:
            cases: List of MessageHistoryCase objects to add
        """
        self._original_cases.extend(cases)

    def create_variants(
        self,
        num_variants_per_case: int = 2,
        case_names: Optional[List[str]] = None
    ) -> Dict[str, List[MessageHistoryCase]]:
        """Create variants for all or specified cases.

        Args:
            num_variants_per_case: Number of variants to create for each case (default: 2)
            case_names: Optional list of case names to create variants for.
                       If None, creates variants for all cases.

        Returns:
            Dictionary mapping case names to lists of their variants

        Raises:
            ValueError: If specified case names are not found
        """
        cases_to_process = self._original_cases

        # Filter by case names if specified
        if case_names is not None:
            cases_to_process = [
                case for case in self._original_cases
                if case.name in case_names
            ]
            if len(cases_to_process) != len(case_names):
                found_names = {case.name for case in cases_to_process}
                missing = set(case_names) - found_names
                raise ValueError(f"Case names not found: {missing}")

        # Create variants for each case
        for original_case in cases_to_process:
            if original_case.name not in self._variant_mapping:
                self._variant_mapping[original_case.name] = []

            previous_variants = self._variant_mapping[original_case.name].copy()

            for variant_num in range(1, num_variants_per_case + 1):
                variant_case = create_case_variant(
                    original_case,
                    previous_variants=previous_variants
                )
                variant_case.name = f"{original_case.name} - Variant {variant_num}"
                self._variant_mapping[original_case.name].append(variant_case)
                previous_variants.append(variant_case)

        return self._variant_mapping

    def build_dataset(
        self,
        name: str = "Message History Dataset with Variants",
        include_originals: bool = True,
        include_variants: bool = True
    ) -> Dataset:
        """Build a pydantic-eval Dataset from all cases and variants.

        Args:
            name: Name for the dataset
            include_originals: Whether to include original cases (default: True)
            include_variants: Whether to include variant cases (default: True)

        Returns:
            Dataset containing the requested cases

        Raises:
            ValueError: If both include_originals and include_variants are False
        """
        if not include_originals and not include_variants:
            raise ValueError("At least one of include_originals or include_variants must be True")

        cases = []

        # Add original cases
        if include_originals:
            cases.extend([case.to_case() for case in self._original_cases])

        # Add variant cases
        if include_variants:
            for variants_list in self._variant_mapping.values():
                cases.extend([variant.to_case() for variant in variants_list])

        self.dataset = Dataset(cases=cases, name=name)
        return self.dataset

    def save_dataset(
        self,
        path: Union[Path, str],
        name: str = "Message History Dataset with Variants",
        include_originals: bool = True,
        include_variants: bool = True,
        fmt: Optional[str] = None,
        schema_path: Optional[Union[Path, str]] = None
    ) -> None:
        """Build and save a dataset to a file.

        Args:
            path: Path to save the dataset to
            name: Name for the dataset
            include_originals: Whether to include original cases (default: True)
            include_variants: Whether to include variant cases (default: True)
            fmt: Format to use ('yaml' or 'json'). If None, inferred from file extension
            schema_path: Optional path to save the JSON schema. Can use {stem} placeholder.

        Raises:
            ValueError: If both include_originals and include_variants are False
        """
        dataset = self.build_dataset(
            name=name,
            include_originals=include_originals,
            include_variants=include_variants
        )

        # Use Dataset.to_file() for proper serialization
        dataset.to_file(
            path=Path(path) if isinstance(path, str) else path,
            fmt=fmt,  # type: ignore
            schema_path=schema_path
        )

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

    def get_variants(self, case_name: str) -> List[MessageHistoryCase]:
        """Get all variants for a specific case.

        Args:
            case_name: Name of the original case

        Returns:
            List of variant MessageHistoryCase objects

        Raises:
            KeyError: If case name not found
        """
        if case_name not in self._variant_mapping:
            raise KeyError(f"No variants found for case: {case_name}")
        return self._variant_mapping[case_name].copy()

    def get_all_variants(self) -> Dict[str, List[MessageHistoryCase]]:
        """Get all variants for all cases.

        Returns:
            Dictionary mapping case names to their variant lists
        """
        return {name: variants.copy() for name, variants in self._variant_mapping.items()}

    def get_original_cases(self) -> List[MessageHistoryCase]:
        """Get all original cases.

        Returns:
            List of original MessageHistoryCase objects
        """
        return self._original_cases.copy()

    def clear(self) -> None:
        """Clear all cases and variants."""
        self._original_cases.clear()
        self._variant_mapping.clear()

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the dataset.

        Returns:
            Dictionary with counts of original cases, variants, and total cases
        """
        total_variants = sum(len(variants) for variants in self._variant_mapping.values())
        return {
            "original_cases": len(self._original_cases),
            "variant_cases": total_variants,
            "total_cases": len(self._original_cases) + total_variants
        }

    def set_pre_task_hook(self, hook: Callable[[Any], None]) -> None:
        """Set a pre-task hook that will be called before each task execution.

        The hook will receive the task inputs as its argument.

        Args:
            hook: A callable that takes the task inputs and returns None.
                  This will be called before the task is executed.

        Example:
            ```python
            def log_inputs(inputs):
                print(f"Running task with inputs: {inputs}")

            manager.set_pre_task_hook(log_inputs)
            ```
        """
        self._pre_task_hook = hook

    def set_post_task_hook(self, hook: Callable[[Any, Any], None]) -> None:
        """Set a post-task hook that will be called after each task execution.

        The hook will receive the task inputs and output as its arguments.

        Args:
            hook: A callable that takes the task inputs and output and returns None.
                  This will be called after the task is executed.

        Example:
            ```python
            def log_output(inputs, output):
                print(f"Task completed with output: {output}")

            manager.set_post_task_hook(log_output)
            ```
        """
        self._post_task_hook = hook

    def clear_hooks(self) -> None:
        """Clear both pre and post task hooks."""
        self._pre_task_hook = None
        self._post_task_hook = None

    def wrap_task(self, task: Callable[[Any], Any]) -> Callable[[Any], Any]:
        """Wrap a task function with pre and post hooks.

        This method creates a wrapper function that:
        1. Calls the pre-task hook (if set) before executing the task
        2. Executes the original task
        3. Calls the post-task hook (if set) after executing the task

        Args:
            task: The task function to wrap. Can be sync or async.

        Returns:
            A wrapped version of the task function that includes hook calls.

        Example:
            ```python
            def my_task(inputs):
                return process(inputs)

            manager.set_pre_task_hook(lambda inputs: print(f"Starting: {inputs}"))
            manager.set_post_task_hook(lambda inputs, output: print(f"Done: {output}"))

            wrapped_task = manager.wrap_task(my_task)
            result = wrapped_task(my_inputs)
            ```
        """
        import asyncio

        # Check if task is async
        is_async = asyncio.iscoroutinefunction(task)

        if is_async:
            async def async_wrapper(inputs: Any) -> Any:
                # Pre-task hook
                if self._pre_task_hook is not None:
                    if asyncio.iscoroutinefunction(self._pre_task_hook):
                        await self._pre_task_hook(inputs)
                    else:
                        self._pre_task_hook(inputs)

                # Execute task
                output = await task(inputs)

                # Post-task hook
                if self._post_task_hook is not None:
                    if asyncio.iscoroutinefunction(self._post_task_hook):
                        await self._post_task_hook(inputs, output)
                    else:
                        self._post_task_hook(inputs, output)

                return output

            return async_wrapper
        else:
            def sync_wrapper(inputs: Any) -> Any:
                # Pre-task hook
                if self._pre_task_hook is not None:
                    self._pre_task_hook(inputs)

                # Execute task
                output = task(inputs)

                # Post-task hook
                if self._post_task_hook is not None:
                    self._post_task_hook(inputs, output)

                return output

            return sync_wrapper

    async def run_evaluation(
        self,
        task: Callable[[Any], Any],
        name: Optional[str] = None,
        max_concurrency: Optional[int] = None,
        progress: bool = True,
        retry_task: Optional[Any] = None,
        retry_evaluators: Optional[Any] = None,
    ) -> Any:
        """Run evaluation on the dataset with optional pre/post hooks.

        This method wraps the task with any registered hooks before running the evaluation.

        Args:
            task: The task function to evaluate. Can be sync or async.
            name: The name of the task being evaluated. If omitted, uses the task function name.
            max_concurrency: The maximum number of concurrent evaluations. If None, all cases
                           will be evaluated concurrently.
            progress: Whether to show a progress bar. Defaults to True.
            retry_task: Optional retry configuration for the task execution.
            retry_evaluators: Optional retry configuration for evaluator execution.

        Returns:
            An EvaluationReport containing the results of the evaluation.

        Raises:
            ValueError: If no dataset has been built yet.

        Example:
            ```python
            # Build dataset
            manager.add_cases(cases)
            manager.create_variants(num_variants_per_case=2)
            manager.build_dataset()

            # Set hooks
            manager.set_pre_task_hook(lambda inputs: print(f"Processing: {inputs}"))
            manager.set_post_task_hook(lambda inputs, output: print(f"Result: {output}"))

            # Run evaluation
            report = await manager.run_evaluation(my_task)
            report.print()
            ```
        """
        if self.dataset is None:
            raise ValueError(
                "No dataset has been built. Call build_dataset() before running evaluation."
            )

        # Wrap the task with hooks if any are set
        wrapped_task = self.wrap_task(task)

        # Run evaluation using the dataset's evaluate method
        return await self.dataset.evaluate(
            wrapped_task,
            task_name=name,
            max_concurrency=max_concurrency,
            progress=progress,
            retry_task=retry_task,
            retry_evaluators=retry_evaluators,
        )

    def run_evaluation_sync(
        self,
        task: Callable[[Any], Any],
        name: Optional[str] = None,
        max_concurrency: Optional[int] = None,
        progress: bool = True,
        retry_task: Optional[Any] = None,
        retry_evaluators: Optional[Any] = None,
    ) -> Any:
        """Synchronous wrapper for run_evaluation.

        This is a convenience method that runs the async evaluation in a sync context.

        Args:
            task: The task function to evaluate. Can be sync or async.
            name: The name of the task being evaluated. If omitted, uses the task function name.
            max_concurrency: The maximum number of concurrent evaluations. If None, all cases
                           will be evaluated concurrently.
            progress: Whether to show a progress bar. Defaults to True.
            retry_task: Optional retry configuration for the task execution.
            retry_evaluators: Optional retry configuration for evaluator execution.

        Returns:
            An EvaluationReport containing the results of the evaluation.

        Raises:
            ValueError: If no dataset has been built yet.
        """
        import asyncio

        return asyncio.get_event_loop().run_until_complete(
            self.run_evaluation(
                task,
                name=name,
                max_concurrency=max_concurrency,
                progress=progress,
                retry_task=retry_task,
                retry_evaluators=retry_evaluators,
            )
        )


# Convenience functions

def create_dataset_with_variants(
    cases: List[MessageHistoryCase],
    num_variants_per_case: int = 2,
    name: str = "Message History Dataset with Variants",
    include_originals: bool = True,
    include_variants: bool = True
) -> Dataset:
    """Convenience function to create a dataset with variants in one call.

    Args:
        cases: List of original MessageHistoryCase objects
        num_variants_per_case: Number of variants to create for each case
        name: Name for the dataset
        include_originals: Whether to include original cases
        include_variants: Whether to include variant cases

    Returns:
        Dataset containing original cases and/or their variants
    """
    manager = DatasetManager()
    manager.add_cases(cases)
    manager.create_variants(num_variants_per_case=num_variants_per_case)
    return manager.build_dataset(
        name=name,
        include_originals=include_originals,
        include_variants=include_variants
    )


def save_dataset_with_variants(
    cases: List[MessageHistoryCase],
    path: Union[Path, str],
    num_variants_per_case: int = 2,
    name: str = "Message History Dataset with Variants",
    include_originals: bool = True,
    include_variants: bool = True,
    fmt: Optional[str] = None,
    schema_path: Optional[Union[Path, str]] = None
) -> None:
    """Convenience function to create and save a dataset with variants in one call.

    Args:
        cases: List of original MessageHistoryCase objects
        path: Path to save the dataset to
        num_variants_per_case: Number of variants to create for each case
        name: Name for the dataset
        include_originals: Whether to include original cases
        include_variants: Whether to include variant cases
        fmt: Format to use ('yaml' or 'json'). If None, inferred from file extension
        schema_path: Optional path to save the JSON schema
    """
    manager = DatasetManager()
    manager.add_cases(cases)
    manager.create_variants(num_variants_per_case=num_variants_per_case)
    manager.save_dataset(
        path=path,
        name=name,
        include_originals=include_originals,
        include_variants=include_variants,
        fmt=fmt,
        schema_path=schema_path
    )


def load_dataset_from_file(path: Union[Path, str]) -> Dataset:
    """Load a dataset from a YAML or JSON file.

    Args:
        path: Path to load the dataset from

    Returns:
        Loaded Dataset object
    """
    return DatasetManager.load_dataset(path)
