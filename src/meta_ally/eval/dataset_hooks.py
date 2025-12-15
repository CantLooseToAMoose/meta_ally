"""
Hook management system for dataset evaluation.

This module provides classes for managing reusable hooks with unique identifiers
that can be used for pre-task and post-task processing in dataset evaluation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from pydantic import BaseModel, Field


class HookConfig(BaseModel):
    """
    Configuration for a registered hook with a unique identifier.

    This allows hooks to be referenced by ID instead of serializing the callable directly.
    """

    hook_id: str = Field(description="Unique identifier for the hook")
    name: str = Field(description="Human-readable name for the hook")
    description: str | None = Field(default=None, description="Description of what the hook does")
    hook_type: str = Field(description="Type of hook: 'pre' or 'post'")


class HookLibrary(ABC):
    """
    Abstract base class for managing reusable hooks with unique identifiers.

    This class provides a complete implementation for hook storage and retrieval.
    Subclasses only need to implement the `register_hooks()` method to define
    which hooks to register.

    Example:
        ```python
        class MyHookLibrary(HookLibrary):
            def register_hooks(self):
                self.register_hook(
                    "log_inputs",
                    my_log_function,
                    "Log Inputs",
                    description="Logs input messages"
                )
                self.register_hook(
                    "validate",
                    my_validate_function,
                    "Validate Outputs",
                    hook_type="post"
                )

        # Hooks are automatically registered on initialization
        library = MyHookLibrary()
        ```
    """

    def __init__(self):
        """
        Initialize the hook library and register hooks.

        Calls register_hooks() automatically to set up the library.
        """
        self._hooks: dict[str, Callable] = {}
        self._hook_configs: dict[str, HookConfig] = {}
        self.register_hooks()

    @abstractmethod
    def register_hooks(self) -> None:
        """
        Register all custom hooks for this library.

        Subclasses must implement this method to define which hooks to register.
        Use self.register_hook() to add hooks.

        Example:
            ```python
            def register_hooks(self):
                self.register_hook("my_hook", my_fn, "My Hook")
                self.register_hook("other_hook", other_fn, "Other Hook", hook_type="post")
            ```
        """
        ...

    def register_hook(
        self,
        hook_id: str,
        hook: Callable,
        name: str,
        description: str | None = None,
        hook_type: str = "pre"
    ) -> None:
        """
        Register a hook with a unique ID.

        Args:
            hook_id: Unique identifier for the hook
            hook: The callable hook function
            name: Human-readable name
            description: Optional description
            hook_type: Type of hook ('pre' or 'post')

        Raises:
            ValueError: If hook_id already exists
        """
        if hook_id in self._hooks:
            raise ValueError(f"Hook with ID '{hook_id}' already registered")

        self._hooks[hook_id] = hook
        self._hook_configs[hook_id] = HookConfig(
            hook_id=hook_id,
            name=name,
            description=description,
            hook_type=hook_type
        )

    def get_hook(self, hook_id: str) -> Callable:
        """
        Get a hook by its ID.

        Args:
            hook_id: The hook identifier

        Returns:
            The hook callable

        Raises:
            KeyError: If hook_id not found
        """
        if hook_id not in self._hooks:
            raise KeyError(f"Hook with ID '{hook_id}' not found in library")
        return self._hooks[hook_id]

    def get_hook_config(self, hook_id: str) -> HookConfig:
        """
        Get hook configuration by ID.

        Args:
            hook_id: The hook identifier

        Returns:
            The HookConfig object

        Raises:
            KeyError: If hook_id not found
        """
        if hook_id not in self._hook_configs:
            raise KeyError(f"Hook config with ID '{hook_id}' not found")
        return self._hook_configs[hook_id]

    def list_hooks(self) -> list[HookConfig]:
        """
        Get list of all registered hooks.

        Returns:
            List of HookConfig objects
        """
        return list(self._hook_configs.values())

    def has_hook(self, hook_id: str) -> bool:
        """
        Check if a hook is registered.

        Args:
            hook_id: The hook identifier

        Returns:
            True if hook exists, False otherwise
        """
        return hook_id in self._hooks

    def unregister_hook(self, hook_id: str) -> None:
        """
        Remove a hook from the library.

        Args:
            hook_id: The hook identifier

        Raises:
            KeyError: If hook_id not found
        """
        if hook_id not in self._hooks:
            raise KeyError(f"Hook with ID '{hook_id}' not found")
        del self._hooks[hook_id]
        del self._hook_configs[hook_id]

    def clear(self) -> None:
        """Clear all registered hooks."""
        self._hooks.clear()
        self._hook_configs.clear()
