"""Evaluation module for testing and validating agent performance."""

from .case_factory import (
    CaseFactory,
    MessageHistoryCase,
    ExpectedOutput,
    create_case_variant,
    create_tool_call_part,
)

from .dataset_manager import (
    DatasetManager,
    create_dataset_with_variants,
    save_dataset_with_variants,
    load_dataset_from_file,
)

from .evaluation_suite_manager import (
    EvaluationSuiteManager,
    EvaluationResult,
    SuiteEvaluationResults,
)

from .evaluators import ToolCallEvaluator

from .eval_tasks import create_agent_conversation_task

from .conversation_turns import ModelMessage

__all__ = [
    # Case factory
    "CaseFactory",
    "MessageHistoryCase",
    "ExpectedOutput",
    "create_case_variant",
    "create_tool_call_part",
    
    # Dataset manager
    "DatasetManager",
    "create_dataset_with_variants",
    "save_dataset_with_variants",
    "load_dataset_from_file",
    
    # Evaluation suite manager
    "EvaluationSuiteManager",
    "EvaluationResult",
    "SuiteEvaluationResults",
    
    # Evaluators
    "ToolCallEvaluator",
    
    # Tasks
    "create_agent_conversation_task",
    
    # Conversation
    "ModelMessage",
]
