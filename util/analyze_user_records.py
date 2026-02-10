#!/usr/bin/env python3
"""
Analyze User Records from Meta Ally sessions.

Extracts and aggregates:
- Token counts (input/output) from LLM responses
- Turn response times (user prompt to final displayed response)
- Separate stats for single-agent vs multi-agent configurations
- For multi-agent: separate orchestrator vs specialist token counts
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

# Path configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
USER_RECORDS_DIR = PROJECT_ROOT / "Data" / "UserRecords"


def parse_timestamp(ts_str: str) -> datetime | None:
    """
    Parse ISO format timestamp string to datetime.

    Returns:
        datetime object if parsing succeeds, None otherwise.
    """
    if not ts_str:
        return None
    try:
        # Handle various ISO formats
        ts_str = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def extract_usage_from_message(message: dict) -> dict | None:
    """
    Extract usage stats from a response message.

    Returns:
        Dictionary with token counts and metadata, or None if not a response.
    """
    if message.get("kind") != "response":
        return None
    usage = message.get("usage")
    if not usage:
        return None
    return {
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "cache_read_tokens": usage.get("cache_read_tokens", 0),
        "cache_write_tokens": usage.get("cache_write_tokens", 0),
        "timestamp": parse_timestamp(message.get("timestamp")),
        "model_name": message.get("model_name"),
    }


def find_user_prompt_timestamp(entry: dict) -> datetime | None:
    """
    Find the timestamp of a user-prompt in an entry.

    Returns:
        datetime of user prompt, or None if not found.
    """
    # Check in data.parts for orchestrator_message entries
    data = entry.get("data", entry)
    parts = data.get("parts", [])
    for part in parts:
        if part.get("part_kind") == "user-prompt":
            return parse_timestamp(part.get("timestamp"))
    return None


def find_last_response_timestamp(entry: dict) -> datetime | None:
    """
    Find the timestamp of the last response in an entry.

    Returns:
        datetime of last response, or None if not found.
    """
    data = entry.get("data", entry)
    if data.get("kind") == "response":
        return parse_timestamp(data.get("timestamp"))
    return None


def _record_turn_if_complete(current_turn_start, last_response_ts, turn_times):
    """Record turn duration if both start and end timestamps exist."""
    if current_turn_start and last_response_ts:
        turn_duration = (last_response_ts - current_turn_start).total_seconds()
        if turn_duration > 0:
            turn_times.append(turn_duration)


def _process_user_prompt(part, current_turn_start, last_response_ts, turn_times):
    """
    Process a user prompt part and update turn tracking.

    Returns:
        Tuple of (current_turn_start, last_response_ts).
    """
    if part.get("part_kind") == "user-prompt":
        # If we had a previous turn, record its duration
        _record_turn_if_complete(current_turn_start, last_response_ts, turn_times)
        # Start new turn
        return parse_timestamp(part.get("timestamp")), None
    return current_turn_start, last_response_ts


def process_single_agent_file(data: dict) -> dict:
    """
    Process a single-agent session file.

    Returns:
        Dictionary with token_records and turn_times.
    """
    timeline = data.get("conversation_timeline", [])
    token_records = []
    turn_times = []
    current_turn_start = None
    last_response_ts = None

    for entry in timeline:
        # Handle both wrapped and unwrapped message formats
        msg_data = entry.get("data", {}) if "entry_type" in entry else entry

        # Check for user prompt (start of turn)
        parts = msg_data.get("parts", [])
        for part in parts:
            current_turn_start, last_response_ts = _process_user_prompt(
                part, current_turn_start, last_response_ts, turn_times
            )
            if part.get("part_kind") == "user-prompt":
                break

        # Extract token usage from responses
        if msg_data.get("kind") == "response":
            usage = extract_usage_from_message(msg_data)
            if usage:
                token_records.append(usage)
                last_response_ts = usage["timestamp"]

    # Don't forget the last turn
    _record_turn_if_complete(current_turn_start, last_response_ts, turn_times)

    return {
        "token_records": token_records,
        "turn_times": turn_times,
    }


def _process_orchestrator_message(msg_data, current_turn_start, last_response_ts, turn_times, orchestrator_tokens):
    """
    Process an orchestrator message and extract token usage.

    Returns:
        Tuple of (current_turn_start, last_response_ts).
    """
    # Check for user prompt (start of turn)
    parts = msg_data.get("parts", [])
    for part in parts:
        current_turn_start, last_response_ts = _process_user_prompt(
            part, current_turn_start, last_response_ts, turn_times
        )
        if part.get("part_kind") == "user-prompt":
            break

    # Extract orchestrator token usage
    if msg_data.get("kind") == "response":
        usage = extract_usage_from_message(msg_data)
        if usage:
            orchestrator_tokens.append(usage)
            last_response_ts = usage["timestamp"]

    return current_turn_start, last_response_ts


def _process_specialist_run(spec_data, last_response_ts, specialist_tokens):
    """
    Process specialist run and extract token usage from messages.

    Returns:
        Updated last_response_ts.
    """
    new_messages = spec_data.get("new_messages", [])

    for msg in new_messages:
        if msg.get("kind") == "response":
            usage = extract_usage_from_message(msg)
            if usage and usage["timestamp"]:
                specialist_tokens.append(usage)
                # Specialist responses also count towards turn completion
                if last_response_ts:
                    last_response_ts = max(last_response_ts, usage["timestamp"])
                else:
                    last_response_ts = usage["timestamp"]

    return last_response_ts


def process_multi_agent_file(data: dict) -> dict:
    """
    Process a multi-agent session file.

    Returns:
        Dictionary with orchestrator_tokens, specialist_tokens, and turn_times.
    """
    timeline = data.get("conversation_timeline", [])
    orchestrator_tokens = []
    specialist_tokens = []
    turn_times = []
    current_turn_start = None
    last_response_ts = None

    for entry in timeline:
        entry_type = entry.get("entry_type", "")

        if entry_type == "orchestrator_message":
            msg_data = entry.get("data", {})
            current_turn_start, last_response_ts = _process_orchestrator_message(
                msg_data, current_turn_start, last_response_ts, turn_times, orchestrator_tokens
            )
        elif entry_type == "specialist_run":
            spec_data = entry.get("data", {})
            last_response_ts = _process_specialist_run(spec_data, last_response_ts, specialist_tokens)

    # Don't forget the last turn
    _record_turn_if_complete(current_turn_start, last_response_ts, turn_times)

    return {
        "orchestrator_tokens": orchestrator_tokens,
        "specialist_tokens": specialist_tokens,
        "turn_times": turn_times,
    }


def analyze_user_records(records_dir: Path = USER_RECORDS_DIR) -> dict:
    """
    Analyze all user record JSON files in the directory.

    Returns:
        Dictionary with single_agent and multi_agent results.
    """
    single_agent_results = []
    multi_agent_results = []

    json_files = list(records_dir.glob("*.json"))

    for json_file in json_files:
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not read {json_file.name}: {e}")
            continue

        metadata = data.get("metadata", {})
        config = metadata.get("config", {})
        is_multi_agent = config.get("use_multi_agent", False)

        file_info = {
            "filename": json_file.name,
            "name": metadata.get("name", "Unknown"),
            "timestamp": metadata.get("timestamp"),
            "model": config.get("model_deployment_name", "Unknown"),
            "sus_score": metadata.get("sus_score"),
        }

        if is_multi_agent:
            result = process_multi_agent_file(data)
            result.update(file_info)
            result["agent_type"] = "multi"
            multi_agent_results.append(result)
        else:
            result = process_single_agent_file(data)
            result.update(file_info)
            result["agent_type"] = "single"
            single_agent_results.append(result)

    return {
        "single_agent": single_agent_results,
        "multi_agent": multi_agent_results,
    }


def create_token_dataframe(token_records: list[dict]) -> pd.DataFrame:
    """
    Create a DataFrame from token records.

    Returns:
        DataFrame with token columns.
    """
    if not token_records:
        return pd.DataFrame(columns=["input_tokens", "output_tokens", "total_tokens"])

    df = pd.DataFrame(token_records)
    df["total_tokens"] = df["input_tokens"] + df["output_tokens"]
    return df


def _print_token_stats(df_tokens: pd.DataFrame, label: str) -> None:
    """Print token statistics for a dataframe."""
    print(f"\n{label} ({len(df_tokens)} LLM calls):")
    print("-" * 40)
    print(f"  Total input tokens:    {df_tokens['input_tokens'].sum():,}")
    print(f"  Total output tokens:   {df_tokens['output_tokens'].sum():,}")
    print(f"  Total tokens:          {df_tokens['total_tokens'].sum():,}")
    print(f"  Avg input per call:    {df_tokens['input_tokens'].mean():,.1f}")
    print(f"  Avg output per call:   {df_tokens['output_tokens'].mean():,.1f}")
    print(f"  Avg total per call:    {df_tokens['total_tokens'].mean():,.1f}")


def _print_turn_time_stats(turn_times: list[float]) -> None:
    """Print turn time statistics."""
    if not turn_times:
        return

    turn_series = pd.Series(turn_times)
    print(f"\nTurn Response Time ({len(turn_series)} turns):")
    print("-" * 40)
    print(f"  Average:    {turn_series.mean():.2f} seconds")
    print(f"  Median:     {turn_series.median():.2f} seconds")
    print(f"  Min:        {turn_series.min():.2f} seconds")
    print(f"  Max:        {turn_series.max():.2f} seconds")
    print(f"  Std Dev:    {turn_series.std():.2f} seconds")


def _print_single_agent_session_breakdown(sessions: list[dict]) -> None:
    """Print per-session breakdown for single-agent sessions."""
    print("\nPer-Session Breakdown:")
    print("-" * 40)
    for session in sessions:
        tokens = session.get("token_records", [])
        turns = session.get("turn_times", [])
        total_tokens = sum(t.get("input_tokens", 0) + t.get("output_tokens", 0) for t in tokens)
        avg_turn = sum(turns) / len(turns) if turns else 0
        name_short = session['name'][:40]
        print(
            f"  {name_short:<40} | {total_tokens:>8,} tokens | "
            f"{len(turns):>3} turns | {avg_turn:>6.1f}s avg"
        )


def _print_single_agent_stats(single_agent: list[dict]) -> None:
    """Print statistics for single-agent sessions."""
    print(f"\n{'=' * 40}")
    print("SINGLE-AGENT SESSIONS")
    print(f"{'=' * 40}")
    print(f"Total sessions: {len(single_agent)}")

    if not single_agent:
        return

    # Collect all token records and turn times
    all_tokens = []
    all_turn_times = []
    for session in single_agent:
        all_tokens.extend(session.get("token_records", []))
        all_turn_times.extend(session.get("turn_times", []))

    if all_tokens:
        df_tokens = create_token_dataframe(all_tokens)
        _print_token_stats(df_tokens, "Token Statistics")

    _print_turn_time_stats(all_turn_times)
    _print_single_agent_session_breakdown(single_agent)


def _print_multi_agent_session_breakdown(sessions: list[dict]) -> None:
    """Print per-session breakdown for multi-agent sessions."""
    print("\nPer-Session Breakdown:")
    print("-" * 40)
    for session in sessions:
        orch_tokens = session.get("orchestrator_tokens", [])
        spec_tokens = session.get("specialist_tokens", [])
        turns = session.get("turn_times", [])
        total_orch = sum(t.get("input_tokens", 0) + t.get("output_tokens", 0) for t in orch_tokens)
        total_spec = sum(t.get("input_tokens", 0) + t.get("output_tokens", 0) for t in spec_tokens)
        avg_turn = sum(turns) / len(turns) if turns else 0
        name_short = session['name'][:35]
        print(
            f"  {name_short:<35} | Orch: {total_orch:>8,} | "
            f"Spec: {total_spec:>8,} | {len(turns):>3} turns | {avg_turn:>6.1f}s avg"
        )


def _print_multi_agent_stats(multi_agent: list[dict]) -> None:
    """Print statistics for multi-agent sessions."""
    print(f"\n{'=' * 40}")
    print("MULTI-AGENT SESSIONS")
    print(f"{'=' * 40}")
    print(f"Total sessions: {len(multi_agent)}")

    if not multi_agent:
        return

    # Collect all token records and turn times
    all_orchestrator = []
    all_specialist = []
    all_turn_times = []
    for session in multi_agent:
        all_orchestrator.extend(session.get("orchestrator_tokens", []))
        all_specialist.extend(session.get("specialist_tokens", []))
        all_turn_times.extend(session.get("turn_times", []))

    # Orchestrator stats
    print("\n--- ORCHESTRATOR ---")
    if all_orchestrator:
        df_orch = create_token_dataframe(all_orchestrator)
        _print_token_stats(df_orch, "Token Statistics")
    else:
        print("  No orchestrator token data found.")

    # Specialist stats
    print("\n--- SPECIALISTS ---")
    if all_specialist:
        df_spec = create_token_dataframe(all_specialist)
        _print_token_stats(df_spec, "Token Statistics")
    else:
        print("  No specialist token data found.")

    # Combined multi-agent stats
    print("\n--- COMBINED (Orchestrator + Specialists) ---")
    all_multi_tokens = all_orchestrator + all_specialist
    if all_multi_tokens:
        df_combined = create_token_dataframe(all_multi_tokens)
        print(f"Token Statistics ({len(df_combined)} total LLM calls):")
        print("-" * 40)
        print(f"  Total input tokens:    {df_combined['input_tokens'].sum():,}")
        print(f"  Total output tokens:   {df_combined['output_tokens'].sum():,}")
        print(f"  Total tokens:          {df_combined['total_tokens'].sum():,}")

    _print_turn_time_stats(all_turn_times)
    _print_multi_agent_session_breakdown(multi_agent)


def _print_comparison(single_agent: list[dict], multi_agent: list[dict]) -> None:
    """Print comparison statistics between single and multi-agent sessions."""
    print(f"\n{'=' * 40}")
    print("COMPARISON: SINGLE vs MULTI-AGENT")
    print(f"{'=' * 40}")

    # Single agent totals
    single_tokens = []
    single_turns = []
    for s in single_agent:
        single_tokens.extend(s.get("token_records", []))
        single_turns.extend(s.get("turn_times", []))

    # Multi agent totals
    multi_tokens = []
    multi_turns = []
    for m in multi_agent:
        multi_tokens.extend(m.get("orchestrator_tokens", []))
        multi_tokens.extend(m.get("specialist_tokens", []))
        multi_turns.extend(m.get("turn_times", []))

    print(f"\n{'Metric':<30} | {'Single-Agent':>15} | {'Multi-Agent':>15}")
    print("-" * 65)

    single_total = sum(t.get("input_tokens", 0) + t.get("output_tokens", 0) for t in single_tokens)
    multi_total = sum(t.get("input_tokens", 0) + t.get("output_tokens", 0) for t in multi_tokens)
    print(f"{'Total tokens':<30} | {single_total:>15,} | {multi_total:>15,}")

    print(f"{'Number of LLM calls':<30} | {len(single_tokens):>15,} | {len(multi_tokens):>15,}")

    single_avg_turn = sum(single_turns) / len(single_turns) if single_turns else 0
    multi_avg_turn = sum(multi_turns) / len(multi_turns) if multi_turns else 0
    print(f"{'Avg turn response time (s)':<30} | {single_avg_turn:>15.2f} | {multi_avg_turn:>15.2f}")

    print(f"{'Number of turns':<30} | {len(single_turns):>15,} | {len(multi_turns):>15,}")
    print(f"{'Number of sessions':<30} | {len(single_agent):>15,} | {len(multi_agent):>15,}")


def print_summary_stats(results: dict) -> None:
    """Print summary statistics."""
    print("=" * 80)
    print("META ALLY USER RECORDS ANALYSIS")
    print("=" * 80)

    single_agent = results["single_agent"]
    multi_agent = results["multi_agent"]

    _print_single_agent_stats(single_agent)
    _print_multi_agent_stats(multi_agent)
    _print_comparison(single_agent, multi_agent)


def main():
    """Main entry point."""
    print(f"Analyzing user records in: {USER_RECORDS_DIR}")
    print()

    if not USER_RECORDS_DIR.exists():
        print(f"Error: Directory not found: {USER_RECORDS_DIR}")
        return

    results = analyze_user_records()
    print_summary_stats(results)


if __name__ == "__main__":
    main()
