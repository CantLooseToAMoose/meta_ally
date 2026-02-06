"""
Conversation loader for resuming chat sessions.

Provides functionality to load previously saved conversations and resume them
with proper message history reconstruction for single-agent and multi-agent setups.
"""

import logging
from pathlib import Path
from typing import Any

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from .conversation_saver import list_saved_conversations, load_conversation

logger = logging.getLogger(__name__)


def load_conversation_for_single_agent(file_path: str | Path) -> tuple[list[ModelMessage], dict[str, Any]]:
    """
    Load a saved conversation for use with a single agent.

    This function loads a conversation from JSON and extracts the message history
    that can be passed to agent.run_sync(..., message_history=...).

    Args:
        file_path: Path to the saved conversation JSON file

    Returns:
        Tuple of (message_history, metadata)
        - message_history: List of ModelMessage objects ready for agent.run_sync()
        - metadata: Conversation metadata (name, notes, timestamp, etc.)

    Raises:
        FileNotFoundError: If the conversation file doesn't exist
        ValueError: If the conversation data is invalid or corrupted

    Example:
        ```python
        from meta_ally.ui.conversation_loader import load_conversation_for_single_agent

        # Load a previous conversation
        message_history, metadata = load_conversation_for_single_agent(
            "Data/UserRecords/my_chat_20260206_120000.json"
        )

        # Resume the conversation with an agent
        response = agent.run_sync(
            "Continue our previous discussion",
            deps=deps,
            message_history=message_history
        )
        ```
    """
    # Load the conversation data
    data = load_conversation(file_path)

    # Extract metadata and timeline
    metadata = data.get('metadata', {})
    conversation_timeline = data.get('conversation_timeline', [])

    if not conversation_timeline:
        raise ValueError("Conversation timeline is empty or missing")

    # Reconstruct message history from the timeline
    message_history = _reconstruct_message_history(conversation_timeline)

    return message_history, metadata


def _reconstruct_part(part_data: dict[str, Any]):
    """
    Reconstruct a message part from serialized data.

    Args:
        part_data: Serialized part dictionary

    Returns:
        Reconstructed part object

    Raises:
        ValueError: If part type is unknown
    """
    part_type = part_data.get('part_kind')

    if part_type == 'system-prompt':
        return SystemPromptPart(content=part_data['content'])
    elif part_type == 'user-prompt':
        return UserPromptPart(content=part_data['content'], timestamp=part_data.get('timestamp'))
    elif part_type == 'text':
        return TextPart(content=part_data['content'])
    elif part_type == 'tool-call':
        return ToolCallPart(
            tool_name=part_data['tool_name'],
            args=part_data['args'],
            tool_call_id=part_data.get('tool_call_id')
        )
    elif part_type == 'tool-return':
        return ToolReturnPart(
            tool_name=part_data['tool_name'],
            content=part_data['content'],
            tool_call_id=part_data.get('tool_call_id'),
            timestamp=part_data.get('timestamp')
        )
    else:
        raise ValueError(f"Unknown part type: {part_type}")


def _reconstruct_message_history(timeline: list[dict[str, Any]]) -> list[ModelMessage]:
    """
    Reconstruct message history from saved conversation timeline.

    The timeline contains serialized ModelRequest and ModelResponse objects
    that need to be reconstructed into proper pydantic-ai message objects.

    Args:
        timeline: List of serialized message dictionaries

    Returns:
        List of ModelMessage objects (ModelRequest | ModelResponse)

    Raises:
        ValueError: If message reconstruction fails
    """
    messages: list[ModelMessage] = []

    for entry in timeline:
        try:
            # Check the kind field to determine message type
            kind = entry.get('kind')

            if kind == 'request':
                # Reconstruct ModelRequest
                parts = [_reconstruct_part(p) for p in entry.get('parts', [])]
                messages.append(ModelRequest(parts=parts))

            elif kind == 'response':
                # Reconstruct ModelResponse
                parts = [_reconstruct_part(p) for p in entry.get('parts', [])]
                messages.append(ModelResponse(
                    parts=parts,
                    timestamp=entry.get('timestamp')
                ))
            else:
                # Skip unknown message types (might be specialist runs in multi-agent)
                continue

        except Exception as e:
            # Log but continue - partial history is better than failure
            logger.warning("Skipping message due to reconstruction error: %s", e)
            continue

    if not messages:
        raise ValueError("Failed to reconstruct any messages from conversation timeline")

    return messages


def list_loadable_conversations(save_dir: str | Path = "Data/UserRecords") -> list[dict[str, Any]]:
    """
    List all saved conversations with their metadata for selection.

    Args:
        save_dir: Directory containing saved conversations

    Returns:
        List of dictionaries with conversation info:
        - 'path': Path to the conversation file
        - 'name': Conversation name
        - 'timestamp': When it was saved
        - 'num_messages': Number of messages in the conversation
        - 'config': Configuration used (if available)

    Example:
        ```python
        from meta_ally.ui.conversation_loader import list_loadable_conversations

        # List all available conversations
        conversations = list_loadable_conversations()
        for i, conv in enumerate(conversations):
            print(f"{i+1}. {conv['name']} ({conv['timestamp']})")
            print(f"   Messages: {conv['num_messages']}")
        ```
    """
    conversation_files = list_saved_conversations(save_dir)
    conversations = []

    for file_path in conversation_files:
        try:
            data = load_conversation(file_path)
            metadata = data.get('metadata', {})
            timeline = data.get('conversation_timeline', [])

            conversations.append({
                'path': file_path,
                'name': metadata.get('name', 'Unnamed'),
                'timestamp': metadata.get('timestamp', 'Unknown'),
                'num_messages': len(timeline),
                'config': metadata.get('config', {}),
                'notes': metadata.get('notes', ''),
            })
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")
            continue

    return conversations
