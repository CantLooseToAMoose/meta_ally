"""Evaluation module for testing and validating agent performance."""

from .case_factory import (
    CaseFactory,
    MessageHistoryCase,
    ExpectedOutput,
    create_case_variant,
    create_tool_call_part,
)

from .dataset_manager import DatasetManager

from .dataset_hooks import HookLibrary, HookConfig

from .dataset_config import DatasetConfig, SerializableDatasetConfig

from .evaluators import ToolCallEvaluator

from .eval_tasks import create_agent_conversation_task

from .conversation_turns import ModelMessage

from .evaluation_suite import (
    EvaluationSuite
)

__all__ = [
    # Case factory
    "CaseFactory",
    "MessageHistoryCase",
    "ExpectedOutput",
    "create_case_variant",
    "create_tool_call_part",
    
    # Dataset manager
    "DatasetManager",
    
    # Dataset hooks
    "HookLibrary",
    "HookConfig",
    
    # Dataset config
    "DatasetConfig",
    "SerializableDatasetConfig",
    
    # Evaluators
    "ToolCallEvaluator",
    
    # Tasks
    "create_agent_conversation_task",
    
    # Conversation
    "ModelMessage",
    
    # Evaluation suite
    "EvaluationSuite"
]
