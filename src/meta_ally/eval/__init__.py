"""Evaluation module for testing and validating agent performance."""

from .case_factory import (
    CaseFactory,
    ExpectedOutput,
    MessageHistoryCase,
    create_case_variant,
    create_tool_call_part,
)
from .conversation_turns import ModelMessage
from .dataset_config import DatasetConfig, SerializableDatasetConfig
from .dataset_hooks import HookConfig, HookLibrary
from .dataset_manager import DatasetManager
from .eval_tasks import create_agent_conversation_task
from .evaluation_suite import EvaluationSuite
from .evaluators import ToolCallEvaluator

__all__ = [
    "CaseFactory",
    "DatasetConfig",
    "DatasetManager",
    "EvaluationSuite",
    "ExpectedOutput",
    "HookConfig",
    "HookLibrary",
    "MessageHistoryCase",
    "ModelMessage",
    "SerializableDatasetConfig",
    "ToolCallEvaluator",
    "create_agent_conversation_task",
    "create_case_variant",
    "create_tool_call_part",
]
