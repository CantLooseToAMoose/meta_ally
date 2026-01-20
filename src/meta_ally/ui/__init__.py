"""User interface components and utilities."""

from meta_ally.ui.conversation_saver import (
    list_saved_conversations,
    load_conversation,
    save_conversation,
    save_conversation_html,
)
from meta_ally.ui.human_approval_callback import create_human_approval_callback
from meta_ally.ui.terminal_chat import start_chat_session
from meta_ally.ui.visualization import (
    console,
    create_summary_table,
    display_chat_message,
    display_conversation_timeline,
    display_orchestrator_message,
    display_specialist_run,
    show_side_by_side_comparison,
    visualize_dataset,
    visualize_dataset_comparison,
    visualize_single_case,
)

__all__ = [
    "console",
    "create_human_approval_callback",
    "create_summary_table",
    "display_chat_message",
    "display_conversation_timeline",
    "display_orchestrator_message",
    "display_specialist_run",
    "list_saved_conversations",
    "load_conversation",
    "save_conversation",
    "save_conversation_html",
    "show_side_by_side_comparison",
    "start_chat_session",
    "visualize_dataset",
    "visualize_dataset_comparison",
    "visualize_single_case",
]
