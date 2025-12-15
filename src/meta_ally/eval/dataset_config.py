"""
Configuration models for dataset management.

This module provides configuration classes for managing datasets with their cases,
variants, and associated hooks.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field
from pydantic_evals import Dataset

from .case_factory import MessageHistoryCase
from .dataset_hooks import HookLibrary


class SerializableDatasetConfig(BaseModel):
    """
    Serializable version of DatasetConfig for saving/loading.

    This model excludes non-serializable fields (callables, Dataset objects)
    and uses hook IDs instead of the actual callables.
    """

    dataset_id: str
    name: str
    original_case: MessageHistoryCase
    variants: list[MessageHistoryCase]
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    pre_task_hook_id: str | None = None
    post_task_hook_id: str | None = None
    dataset_path: str | None = None  # Path to saved dataset file (if built and saved)

    @classmethod
    def from_dataset_config(
        cls,
        config: DatasetConfig,
        hook_library: HookLibrary | None = None,
    ) -> SerializableDatasetConfig:
        """
        Create a serializable config from a DatasetConfig.

        Args:
            config: The DatasetConfig to serialize
            hook_library: Optional HookLibrary to look up hook IDs

        Returns:
            SerializableDatasetConfig
        """
        # Try to find hook IDs if library provided
        pre_hook_id = None
        post_hook_id = None

        if hook_library:
            # Search for matching hooks in library
            for hook_config in hook_library.list_hooks():
                try:
                    hook_callable = hook_library.get_hook(hook_config.hook_id)
                    if config.pre_task_hook is hook_callable:
                        pre_hook_id = hook_config.hook_id
                    if config.post_task_hook is hook_callable:
                        post_hook_id = hook_config.hook_id
                except KeyError:
                    pass

        return cls(
            dataset_id=config.dataset_id,
            name=config.name,
            original_case=config.original_case,
            variants=config.variants,
            description=config.description,
            metadata=config.metadata,
            pre_task_hook_id=pre_hook_id,
            post_task_hook_id=post_hook_id,
            dataset_path=None,
        )

    def to_dataset_config(
        self,
        hook_library: HookLibrary | None = None,
    ) -> DatasetConfig:
        """
        Convert back to a DatasetConfig.

        Args:
            hook_library: Optional HookLibrary to resolve hook IDs

        Returns:
            DatasetConfig with hooks restored from library
        """
        pre_hook = None
        post_hook = None

        if hook_library:
            if self.pre_task_hook_id and hook_library.has_hook(self.pre_task_hook_id):
                pre_hook = hook_library.get_hook(self.pre_task_hook_id)
            if self.post_task_hook_id and hook_library.has_hook(self.post_task_hook_id):
                post_hook = hook_library.get_hook(self.post_task_hook_id)

        return DatasetConfig(
            dataset_id=self.dataset_id,
            name=self.name,
            original_case=self.original_case,
            variants=self.variants,
            description=self.description,
            metadata=self.metadata,
            pre_task_hook=pre_hook,
            post_task_hook=post_hook,
            dataset=None,
        )


class DatasetConfig(BaseModel):
    """
    Configuration for a single dataset with its case, variants, and hooks.

    This model holds all the information needed to manage a dataset including:
    - The original case
    - All generated variants
    - Pre and post task hooks
    - Dataset metadata like name and description
    - The built Dataset object (if created)
    """

    dataset_id: str = Field(description="Unique identifier for this dataset")
    name: str = Field(description="Human-readable name for the dataset")
    original_case: MessageHistoryCase = Field(description="The original test case")
    variants: list[MessageHistoryCase] = Field(default_factory=list, description="List of variant cases")
    description: str | None = Field(default=None, description="Description of the dataset")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    pre_task_hook: Callable | None = Field(default=None, exclude=True, description="Pre-task hook function")
    post_task_hook: Callable | None = Field(default=None, exclude=True, description="Post-task hook function")
    dataset: Dataset | None = Field(default=None, exclude=True, description="The built pydantic-evals Dataset")
