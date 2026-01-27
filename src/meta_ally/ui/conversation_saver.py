"""
Conversation saver for terminal chat sessions.

Provides functionality to save and load conversation timelines with metadata
including name, SUS score, and user notes. Also supports HTML export for visual
representation matching the terminal display style.
"""

import html
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# System Usability Scale (SUS) - 10 standard questions
SUS_QUESTIONS = [
    "I think that I would like to use this system frequently.",
    "I found the system unnecessarily complex.",
    "I thought the system was easy to use.",
    "I think that I would need the support of a technical person to be able to use this system.",
    "I found the various functions in this system were well integrated.",
    "I thought there was too much inconsistency in this system.",
    "I would imagine that most people would learn to use this system very quickly.",
    "I found the system very cumbersome to use.",
    "I felt very confident using the system.",
    "I needed to learn a lot of things before I could get going with this system."
]


def calculate_sus_score(responses: list[int]) -> float:
    """
    Calculate the System Usability Scale (SUS) score from responses.

    The SUS uses a 5-point Likert scale (1=Strongly Disagree, 5=Strongly Agree).
    Scoring: For odd items (1,3,5,7,9): subtract 1 from response.
             For even items (2,4,6,8,10): subtract response from 5.
             Sum all contributions and multiply by 2.5 for final score (0-100).

    Args:
        responses: List of 10 integers from 1-5 (Likert scale responses)

    Returns:
        SUS score from 0-100

    Raises:
        ValueError: If responses list is not exactly 10 items or values not 1-5
    """
    if len(responses) != 10:
        raise ValueError(f"SUS requires exactly 10 responses, got {len(responses)}")

    if not all(1 <= r <= 5 for r in responses):
        raise ValueError("All responses must be between 1 and 5")

    score = 0
    for i, response in enumerate(responses):
        if i % 2 == 0:  # Odd questions (0-indexed, so 0,2,4,6,8)
            score += response - 1
        else:  # Even questions (1,3,5,7,9)
            score += 5 - response

    return score * 2.5


def prompt_sus_questionnaire() -> tuple[bool, list[int] | None]:
    """
    Prompt user to complete the System Usability Scale (SUS) questionnaire.

    First asks if they want to complete it. If yes, presents all 10 questions.
    Uses a 5-point Likert scale: 1=Strongly Disagree, 5=Strongly Agree.

    Returns:
        Tuple of (completed: bool, responses: list[int] | None)
        - If user declines: (False, None)
        - If user completes: (True, [list of 10 responses])
    """
    # Ask if user wants to complete SUS
    print("\n" + "=" * 70)
    print("System Usability Scale (SUS) Questionnaire")
    print("=" * 70)
    print("\nWould you like to complete a brief 10-question usability survey?")
    print("This will help evaluate the system's usability (takes ~2 minutes).")

    while True:
        choice = input("\nComplete SUS questionnaire? (y/n): ").strip().lower()
        if choice in {'y', 'yes'}:
            break
        if choice in {'n', 'no'}:
            return False, None
        else:
            print("Please enter 'y' or 'n'.")

    # Collect responses
    print("\nPlease rate each statement on a scale of 1-5:")
    print("1 = Strongly Disagree | 2 = Disagree | 3 = Neutral | 4 = Agree | 5 = Strongly Agree\n")

    responses = []
    for i, question in enumerate(SUS_QUESTIONS, 1):
        while True:
            try:
                print(f"\nQuestion {i}/10: {question}")
                response = input("Your rating (1-5): ").strip()
                rating = int(response)
                if 1 <= rating <= 5:
                    responses.append(rating)
                    break
                print("Please enter a number between 1 and 5.")
            except ValueError:
                print("Invalid input. Please enter a number between 1 and 5.")

    return True, responses


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
    sus_score: float | None = None,
    sus_responses: list[int] | None = None,
    notes: str = "",
    save_dir: str | Path = "Data/UserRecords",
    config: dict[str, Any] | None = None
) -> Path:
    """
    Save a conversation timeline with metadata to a JSON file.

    Args:
        conversation_timeline: List of conversation entries to save
        name: Name/title for this conversation
        sus_score: Optional SUS score (0-100 scale)
        sus_responses: Optional list of 10 SUS questionnaire responses (1-5 scale)
        notes: Optional notes about the conversation
        save_dir: Directory to save the conversation (default: Data/UserRecords)
        config: Optional configuration dictionary to include in metadata

    Returns:
        Path to the saved file

    Raises:
        ValueError: If sus_score is provided and not between 0 and 100
    """
    if sus_score is not None and not 0 <= sus_score <= 100:
        raise ValueError("SUS score must be between 0 and 100")

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

    metadata = {
        "name": name,
        "notes": notes,
        "timestamp": datetime.now().isoformat(),
        "saved_at": timestamp
    }

    # Add SUS data if provided
    if sus_score is not None:
        metadata["sus_score"] = sus_score
    if sus_responses is not None:
        metadata["sus_responses"] = sus_responses
    
    # Add configuration if provided
    if config is not None:
        metadata["config"] = config

    data = {
        "metadata": metadata,
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


# HTML template for conversation visualization
_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --bg-color: #1e1e1e;
            --text-color: #d4d4d4;
            --user-border: #5c9fd6;
            --user-title: #5c9fd6;
            --assistant-border: #c678dd;
            --assistant-title: #c678dd;
            --orchestrator-border: #c678dd;
            --orchestrator-title: #c678dd;
            --specialist-border: #56b6c2;
            --specialist-title: #56b6c2;
            --specialist-response-border: #98c379;
            --specialist-response-title: #98c379;
            --tool-color: #e5c07b;
            --dim-color: #6b6b6b;
            --panel-bg: #252526;
            --divider-color: #3c3c3c;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
            line-height: 1.5;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            padding: 20px;
            border-bottom: 2px solid var(--assistant-border);
            margin-bottom: 30px;
        }}

        .header h1 {{
            color: var(--assistant-border);
            margin: 0 0 10px 0;
            font-size: 1.8em;
        }}

        .metadata {{
            background-color: var(--panel-bg);
            border: 1px solid var(--divider-color);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 30px;
        }}

        .metadata-item {{
            display: inline-block;
            margin-right: 30px;
            color: var(--dim-color);
        }}

        .metadata-item strong {{
            color: var(--text-color);
        }}

        .metadata-notes {{
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid var(--divider-color);
            color: var(--dim-color);
        }}

        .metadata-config {{
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid var(--divider-color);
            color: var(--dim-color);
        }}

        .metadata-config ul {{
            margin: 5px 0 0 0;
            padding-left: 20px;
            list-style-type: none;
        }}

        .metadata-config li {{
            margin: 3px 0;
        }}

        .conversation {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}

        .message {{
            max-width: 70%;
            border-radius: 8px;
            border: 2px solid;
            background-color: var(--panel-bg);
            overflow: hidden;
        }}

        .message-title {{
            padding: 8px 15px;
            font-weight: bold;
            border-bottom: 1px solid var(--divider-color);
        }}

        .message-content {{
            padding: 15px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        /* User messages - left aligned, blue */
        .message.user {{
            align-self: flex-start;
            border-color: var(--user-border);
        }}

        .message.user .message-title {{
            color: var(--user-title);
        }}

        /* Assistant/Orchestrator messages - right aligned, purple */
        .message.assistant, .message.orchestrator {{
            align-self: flex-end;
            border-color: var(--assistant-border);
        }}

        .message.assistant .message-title, .message.orchestrator .message-title {{
            color: var(--assistant-title);
        }}

        /* Specialist section */
        .specialist-section {{
            margin: 20px 0;
            padding: 15px;
            border: 2px solid var(--specialist-border);
            border-radius: 8px;
            background-color: rgba(86, 182, 194, 0.05);
        }}

        .specialist-header {{
            color: var(--specialist-title);
            font-weight: bold;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--specialist-border);
            margin-bottom: 15px;
        }}

        .specialist-task {{
            color: var(--dim-color);
            font-size: 0.9em;
            margin-bottom: 15px;
        }}

        .specialist-messages {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding-left: 20px;
        }}

        /* Specialist internal messages */
        .message.specialist-request {{
            align-self: flex-start;
            border-color: var(--orchestrator-border);
            max-width: 90%;
        }}

        .message.specialist-request .message-title {{
            color: var(--orchestrator-title);
        }}

        .message.specialist-response {{
            align-self: flex-end;
            border-color: var(--specialist-response-border);
            max-width: 90%;
        }}

        .message.specialist-response .message-title {{
            color: var(--specialist-response-title);
        }}

        /* Tool calls */
        .tool-call {{
            color: var(--tool-color);
            background-color: rgba(229, 192, 123, 0.1);
            padding: 8px 12px;
            border-radius: 4px;
            margin: 5px 0;
        }}

        .tool-call .tool-name {{
            font-weight: bold;
        }}

        .tool-call .tool-args {{
            color: var(--dim-color);
            font-size: 0.9em;
            margin-top: 5px;
        }}

        .tool-return {{
            color: var(--tool-color);
            background-color: rgba(229, 192, 123, 0.05);
            padding: 8px 12px;
            border-radius: 4px;
            margin: 5px 0;
        }}

        /* Divider */
        .divider {{
            border-top: 1px solid var(--divider-color);
            margin: 20px 0;
        }}

        /* Part type labels */
        .part-type {{
            color: var(--dim-color);
            font-size: 0.85em;
        }}

        /* Grade badge */
        .grade-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}

        .grade-high {{ background-color: #98c379; color: #1e1e1e; }}
        .grade-medium {{ background-color: #e5c07b; color: #1e1e1e; }}
        .grade-low {{ background-color: #e06c75; color: #1e1e1e; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 {title}</h1>
        </div>
        {metadata_html}
        <div class="conversation">
            {conversation_html}
        </div>
    </div>
</body>
</html>
"""


def _format_parts_html(parts: list[dict[str, Any]]) -> str:
    """
    Format message parts to HTML.

    Args:
        parts: List of message part dictionaries

    Returns:
        HTML string representation of the parts
    """
    output = []
    for part in parts:
        part_type = part.get('part_kind', '')

        if 'content' in part:
            content = html.escape(str(part['content']))
            if part_type in {'user-prompt', 'system-prompt'}:
                output.append(f'<span class="part-type">{part_type}:</span>\n{content}')
            elif part_type == 'tool-return':
                output.append(f'<div class="tool-return">🔧 Tool Return:\n{content}</div>')
            else:
                output.append(content)
        elif part_type == 'tool-call' or 'tool_name' in part:
            tool_name = part.get('tool_name', 'unknown')
            args = part.get('args', {})
            args_str = html.escape(json.dumps(args, indent=2)) if args else ''
            args_div = f'<div class="tool-args">Args: <pre>{args_str}</pre></div>' if args_str else ""
            output.append(
                f'<div class="tool-call">'
                f'<span class="tool-name">🔧 Tool Call: {html.escape(tool_name)}</span>'
                f"{args_div}"
                f'</div>'
            )

    return '\n'.join(output)


def _get_message_class_and_title(
    msg: dict[str, Any],
    is_multi_agent: bool,
    agent_prefix: str | None = None
) -> tuple[str, str]:
    """
    Determine the CSS class and title for a message.

    Args:
        msg: The message dictionary
        is_multi_agent: Whether this is a multi-agent conversation
        agent_prefix: Optional agent name prefix for specialist messages

    Returns:
        Tuple of (css_class, title)
    """
    kind = msg.get('kind', '')

    if kind == 'request':
        if agent_prefix:
            return ('specialist-request', '🎯 Orchestrator')
        return ('user', '👤 User')
    elif kind == 'response':
        if agent_prefix:
            return ('specialist-response', f'🤖 {agent_prefix}')
        if is_multi_agent:
            return ('orchestrator', '🎯 Orchestrator')
        return ('assistant', '🤖 Assistant')

    return ('', '')


def _render_message_html(
    msg: dict[str, Any],
    is_multi_agent: bool = False,
    agent_prefix: str | None = None
) -> str:
    """
    Render a single message as HTML.

    Args:
        msg: The message dictionary
        is_multi_agent: Whether this is a multi-agent conversation
        agent_prefix: Optional agent name prefix

    Returns:
        HTML string for the message
    """
    css_class, title = _get_message_class_and_title(msg, is_multi_agent, agent_prefix)
    if not css_class:
        return ''

    parts = msg.get('parts', [])
    content = _format_parts_html(parts)

    return f"""
        <div class="message {css_class}">
            <div class="message-title">{title}</div>
            <div class="message-content">{content}</div>
        </div>
    """


def _render_specialist_run_html(specialist_run: dict[str, Any]) -> str:
    """
    Render a specialist run section as HTML.

    Args:
        specialist_run: The specialist run dictionary

    Returns:
        HTML string for the specialist run section
    """
    agent_name = specialist_run.get('agent_name', 'Unknown')
    display_name = agent_name.replace('_', ' ').title()
    task = specialist_run.get('task', '')
    task_preview = html.escape(task[:100]) + ('...' if len(task) > 100 else '')
    new_messages = specialist_run.get('new_messages', [])

    messages_html = ''
    for msg in new_messages:
        messages_html += _render_message_html(msg, is_multi_agent=True, agent_prefix=display_name)

    return f"""
        <div class="specialist-section">
            <div class="specialist-header">🔧 Specialist: {html.escape(display_name)}</div>
            <div class="specialist-task">Task: {task_preview}</div>
            <div class="specialist-messages">
                {messages_html}
            </div>
        </div>
    """


def _render_timeline_entry_html(entry: dict[str, Any]) -> str:
    """
    Render a timeline entry as HTML.

    Args:
        entry: The timeline entry dictionary

    Returns:
        HTML string for the entry
    """
    entry_type = entry.get('entry_type', '')
    data = entry.get('data', {})

    if entry_type == 'orchestrator_message':
        return _render_message_html(data, is_multi_agent=True)
    elif entry_type == 'specialist_run':
        return _render_specialist_run_html(data)

    return ''


def _detect_conversation_format(timeline: list[dict[str, Any]]) -> str:
    """
    Detect the format of the conversation timeline.

    Args:
        timeline: The conversation timeline

    Returns:
        One of: 'timeline_entries', 'messages', 'unknown'
    """
    if not timeline:
        return 'unknown'

    first = timeline[0]
    if 'entry_type' in first:
        return 'timeline_entries'
    elif 'kind' in first or 'parts' in first:
        return 'messages'

    return 'unknown'


def _render_conversation_html(timeline: list[dict[str, Any]]) -> str:
    """
    Render the full conversation timeline as HTML.

    Args:
        timeline: The conversation timeline (list of entries or messages)

    Returns:
        HTML string for the conversation
    """
    format_type = _detect_conversation_format(timeline)
    html_parts = []

    if format_type == 'timeline_entries':
        # Multi-agent timeline with entries
        for entry in timeline:
            html_parts.append(_render_timeline_entry_html(entry))
    elif format_type == 'messages':
        # Simple message list (single-agent)
        for msg in timeline:
            html_parts.append(_render_message_html(msg, is_multi_agent=False))
    else:
        # Unknown format - try to render as generic
        for item in timeline:
            if isinstance(item, dict):
                html_parts.append(f'<pre>{html.escape(json.dumps(item, indent=2))}</pre>')

    return '\n'.join(html_parts)


def _render_metadata_html(metadata: dict[str, Any]) -> str:
    """
    Render conversation metadata as HTML.

    Args:
        metadata: The metadata dictionary

    Returns:
        HTML string for the metadata section
    """
    name = html.escape(str(metadata.get('name', 'Conversation')))
    sus_score = metadata.get('sus_score')
    notes = html.escape(str(metadata.get('notes', '')))
    timestamp = metadata.get('timestamp', '')

    # Build score HTML if SUS score exists
    score_html = ''
    if sus_score is not None:
        # SUS score interpretation:
        # 80+ = Excellent (A), 68-79 = Good (B), 51-67 = OK (C), <51 = Poor (F)
        if sus_score >= 80:
            score_class = 'grade-high'
            interpretation = 'Excellent'
        elif sus_score >= 68:
            score_class = 'grade-high'
            interpretation = 'Good'
        elif sus_score >= 51:
            score_class = 'grade-medium'
            interpretation = 'OK'
        else:
            score_class = 'grade-low'
            interpretation = 'Poor'

        score_html = (
            f'<span class="metadata-item"><strong>SUS Score:</strong> '
            f'<span class="grade-badge {score_class}">{sus_score:.1f}/100 '
            f'({interpretation})</span></span>'
        )

    notes_html = f'<div class="metadata-notes"><strong>Notes:</strong> {notes}</div>' if notes else ''
    
    # Build configuration HTML if config exists
    config_html = ''
    if config := metadata.get('config'):
        config_items = []
        for key, value in config.items():
            # Format key as readable (e.g., use_multi_agent -> Use Multi Agent)
            readable_key = key.replace('_', ' ').title()
            config_items.append(f'<li><strong>{html.escape(readable_key)}:</strong> {html.escape(str(value))}</li>')
        config_html = f'<div class="metadata-config"><strong>Configuration:</strong><ul>{"".join(config_items)}</ul></div>'

    return f"""
        <div class="metadata">
            <span class="metadata-item"><strong>Name:</strong> {name}</span>
            {score_html}
            <span class="metadata-item"><strong>Date:</strong> {html.escape(str(timestamp))}</span>
            {notes_html}
            {config_html}
        </div>
    """


def save_conversation_html(
    conversation_timeline: list[dict[str, Any]],
    name: str,
    sus_score: float | None = None,
    sus_responses: list[int] | None = None,
    notes: str = "",
    save_dir: str | Path = "Data/UserRecords",
    config: dict[str, Any] | None = None
) -> Path:
    """
    Save a conversation timeline as an HTML file with visual styling matching the terminal display.

    The HTML output preserves the visual hierarchy:
    - User messages: Left-aligned, blue border
    - Assistant/Orchestrator messages: Right-aligned, purple border
    - Specialist runs: Cyan bordered sections with indented conversation
    - Tool calls: Yellow highlighted blocks

    Args:
        conversation_timeline: List of conversation entries to save
        name: Name/title for this conversation
        sus_score: Optional SUS score (0-100 scale)
        sus_responses: Optional list of 10 SUS questionnaire responses (1-5 scale)
        notes: Optional notes about the conversation
        save_dir: Directory to save the HTML file (default: Data/UserRecords)
        config: Optional configuration dictionary to include in metadata

    Returns:
        Path to the saved HTML file

    Raises:
        ValueError: If sus_score is provided and not between 0 and 100

    Example:
        ```python
        from meta_ally.util.conversation_saver import save_conversation_html

        # Save a conversation timeline as HTML
        html_path = save_conversation_html(
            conversation_timeline=deps.conversation_timeline,
            name="API Integration Discussion",
            sus_score=82.5,
            notes="Successful multi-agent conversation about data analytics"
        )
        print(f"HTML saved to: {html_path}")
        ```
    """
    if sus_score is not None and not 0 <= sus_score <= 100:
        raise ValueError("SUS score must be between 0 and 100")

    # Create save directory if it doesn't exist
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in {' ', '_', '-'} else '_' for c in name)
    safe_name = safe_name.replace(' ', '_')
    filename = f"{safe_name}_{timestamp}.html"
    file_path = save_path / filename

    # Convert timeline to serializable format if needed
    serializable_timeline = _to_serializable(conversation_timeline)

    # Build metadata
    metadata = {
        "name": name,
        "notes": notes,
        "timestamp": datetime.now().isoformat(),
    }

    # Add SUS data if provided
    if sus_score is not None:
        metadata["sus_score"] = sus_score
    if sus_responses is not None:
        metadata["sus_responses"] = sus_responses
    
    # Add configuration if provided
    if config is not None:
        metadata["config"] = config

    # Render HTML
    metadata_html = _render_metadata_html(metadata)
    conversation_html = _render_conversation_html(serializable_timeline)

    html_content = _HTML_TEMPLATE.format(
        title=html.escape(name),
        metadata_html=metadata_html,
        conversation_html=conversation_html,
    )

    # Write to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return file_path
