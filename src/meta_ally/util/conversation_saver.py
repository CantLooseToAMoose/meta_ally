"""
Conversation saver for terminal chat sessions.

Provides functionality to save and load conversation timelines with metadata
including name, grade, and user notes.
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


def _to_serializable(obj: Any) -> Any:  # noqa: PLR0911
    """
    Recursively convert an object to a JSON-serializable form.
    Handles pydantic models, enums, dataclasses, and nested structures.
    """  # noqa: DOC201
    # Handle None
    if obj is None:
        return None

    # Handle primitives
    if isinstance(obj, (str, int, float, bool)):
        return obj

    # Handle enums
    if isinstance(obj, Enum):
        return obj.value

    # Handle datetime
    if isinstance(obj, datetime):
        return obj.isoformat()

    # Handle pydantic models (v2) - mode='json' handles nested enums/types
    if hasattr(obj, 'model_dump'):
        return obj.model_dump(mode='json')

    # Handle pydantic models (v1)
    if hasattr(obj, 'dict'):
        return _to_serializable(obj.dict())

    # Handle lists/tuples
    if isinstance(obj, (list, tuple)):
        return [_to_serializable(item) for item in obj]

    # Handle dicts
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}

    # Handle objects with __dict__
    if hasattr(obj, '__dict__'):
        return {k: _to_serializable(v) for k, v in obj.__dict__.items() if not k.startswith('_')}

    # Fallback: convert to string
    return str(obj)


def save_conversation(
    conversation_timeline: list[dict[str, Any]],
    name: str,
    grade: int,
    notes: str = "",
    save_dir: str | Path = "Data/UserRecords"
) -> Path:
    """
    Save a conversation timeline with metadata to a JSON file.

    Args:
        conversation_timeline: List of conversation entries to save
        name: Name/title for this conversation
        grade: Grade rating from 1-10
        notes: Optional notes about the conversation
        save_dir: Directory to save the conversation (default: Data/UserRecords)

    Returns:
        Path to the saved file

    Raises:
        ValueError: If grade is not between 1 and 10
    """
    if not 1 <= grade <= 10:
        raise ValueError("Grade must be between 1 and 10")

    # Create save directory if it doesn't exist
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in {' ', '_', '-'} else '_' for c in name)
    safe_name = safe_name.replace(' ', '_')
    filename = f"{safe_name}_{timestamp}.json"
    file_path = save_path / filename

    # Convert timeline to serializable format (handles nested objects, enums, etc.)
    serializable_timeline = _to_serializable(conversation_timeline)

    data = {
        "metadata": {
            "name": name,
            "grade": grade,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
            "saved_at": timestamp
        },
        "conversation_timeline": serializable_timeline
    }

    # Write to file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return file_path


def load_conversation(file_path: str | Path) -> dict[str, Any]:
    """
    Load a saved conversation from a JSON file.

    Args:
        file_path: Path to the saved conversation file

    Returns:
        Dictionary containing 'metadata' and 'conversation_timeline'

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Conversation file not found: {file_path}")

    with open(file_path, encoding='utf-8') as f:
        data = json.load(f)

    return data


def list_saved_conversations(save_dir: str | Path = "Data/UserRecords") -> list[Path]:
    """
    List all saved conversation files in the directory.

    Args:
        save_dir: Directory containing saved conversations

    Returns:
        List of Path objects for saved conversation files
    """
    save_path = Path(save_dir)

    if not save_path.exists():
        return []

    return sorted(save_path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)