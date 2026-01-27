"""
Example demonstrating the analytics_api_mock_service.py functionality and serving as a light weight test.

This example shows how to:
1. Create and use the AllyConfigMockService directly
2. Test the time-shifting capabilities
3. Use the convenience functions to create mock tool replacements
4. Integrate mock tools with AgentFactory
5. Optional terminal chat with replaced mock tools
"""

from datetime import UTC, datetime, timedelta

from rich.console import Console

from meta_ally.agents import AgentFactory
from meta_ally.agents.agent_presets import create_hybrid_assistant
from meta_ally.auth.auth_manager import AuthManager
from meta_ally.mock.analytics_api_mock_service import (
    create_ally_config_mock_tool_replacements,
    create_mock_service,
)
from meta_ally.tools.tool_group_manager import (
    AIKnowledgeToolGroup,
    AllyConfigToolGroup,
    ToolGroupManager,
)
from meta_ally.ui.terminal_chat import start_chat_session


def _test_ratings(mock_service, endpoint):
    """Test get_copilot_ratings endpoint."""
    print("\n--- Testing get_copilot_ratings ---")
    ratings = mock_service.get_copilot_ratings(endpoint)
    print(f"Ratings for endpoint '{endpoint}': {ratings}")


def _test_cost_data(mock_service, endpoint):
    """Test get_copilot_cost_daily with both tokens and euro."""
    # Test with tokens
    print("\n--- Testing get_copilot_cost_daily (tokens) ---")
    cost_tokens = mock_service.get_copilot_cost_daily(endpoint, "tokens")
    if cost_tokens:
        print(f"Found {len(cost_tokens)} days of token cost data")
        for _i, (date, values) in enumerate(list(cost_tokens.items())[:3]):
            print(f"  {date}: {values}")
    else:
        print("No token cost data available")

    # Test with euro
    print("\n--- Testing get_copilot_cost_daily (euro) ---")
    cost_euro = mock_service.get_copilot_cost_daily(endpoint, "euro")
    if cost_euro:
        print(f"Found {len(cost_euro)} days of euro cost data")
        for _i, (date, values) in enumerate(list(cost_euro.items())[:3]):
            print(f"  {date}: {values}")
    else:
        print("No euro cost data available")


def _test_sessions(mock_service, endpoint, start_time, end_time):
    """
    Test get_copilot_sessions endpoint.

    Returns:
        The sessions data returned from the mock service.
    """
    print("\n--- Testing get_copilot_sessions ---")
    sessions = mock_service.get_copilot_sessions(
        endpoint,
        start_time.isoformat(),
        end_time.isoformat()
    )

    print(f"Requested sessions from {start_time.date()} to {end_time.date()}")

    if isinstance(sessions, dict) and sessions.get("_truncated"):
        print("⚠ Response was truncated:")
        print(f"  Original size: {sessions['_original_size']} chars")
        print(f"  Truncated at: {sessions['_truncated_at']} chars")
        print(f"  Message: {sessions['_message']}")
    else:
        print(f"Found {len(sessions)} sessions")
        if sessions:
            first_session = sessions[0]
            print("\nFirst session:")
            print(f"  Session ID: {first_session['session_id']}")
            print(f"  Timestamp: {first_session['timestamp']}")
            print(f"  Messages: {len(first_session['messages'])}")
            if first_session['messages']:
                first_msg = first_session['messages'][0]
                print(f"  First message role: {first_msg['role']}")
                print(f"  First message content (truncated): {first_msg['content'][:100]}...")

    return sessions


def _test_sessions_summaries(mock_service, endpoint, start_time, end_time):
    """Test get_copilot_sessions_summaries endpoint."""
    print("\n--- Testing get_copilot_sessions_summaries ---")
    summaries = mock_service.get_copilot_sessions_summaries(
        endpoint,
        start_time.isoformat(),
        end_time.isoformat()
    )

    if isinstance(summaries, dict) and summaries.get("_truncated"):
        print("⚠ Response was truncated")
    else:
        print(f"Total count: {summaries.get('total_count', 0)}")
        print(f"Sessions returned: {len(summaries.get('sessions', []))}")
        if summaries.get('sessions'):
            first_summary = summaries['sessions'][0]
            print("\nFirst session summary:")
            print(f"  Session ID: {first_summary['session_id']}")
            print(f"  Timestamp: {first_summary['timestamp']}")
            print(f"  Message count: {first_summary['message_count']}")


def _test_single_session(mock_service, endpoint, sessions):
    """Test get_copilot_session for retrieving a single session."""
    print("\n--- Testing get_copilot_session ---")
    if sessions and not isinstance(sessions, dict):
        test_session_id = sessions[0]['session_id']
        print(f"Retrieving session: {test_session_id}")

        single_session = mock_service.get_copilot_session(test_session_id, endpoint)

        if isinstance(single_session, dict) and single_session.get("_truncated"):
            print("⚠ Response was truncated")
        else:
            print(f"Session ID: {single_session['session_id']}")
            print(f"Timestamp: {single_session['timestamp']}")
            print(f"Messages: {len(single_session['messages'])}")
    else:
        print("Skipping (no sessions available for testing)")


def _test_error_handling(mock_service):
    """Test error handling with invalid endpoint."""
    print("\n--- Testing error handling ---")
    try:
        invalid_endpoint = "invalid_endpoint"
        mock_service.get_copilot_ratings(invalid_endpoint)
        print("ERROR: Should have raised ModelRetry exception")
    except Exception as e:
        print(f"Correctly raised exception: {type(e).__name__}")
        print(f"Exception message: {e}")


def test_direct_mock_service():
    """Test the AllyConfigMockService directly."""
    print("=" * 80)
    print("TEST 1: Direct Mock Service Usage")
    print("=" * 80)

    mock_service = create_mock_service()
    endpoint = "website_analytics"

    print(f"\nCapture time: {mock_service.capture_time}")
    print(f"Original time range: {mock_service.original_start} to {mock_service.original_end}")

    # Run all test components
    _test_ratings(mock_service, endpoint)
    _test_cost_data(mock_service, endpoint)

    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(days=7)

    sessions = _test_sessions(mock_service, endpoint, start_time, end_time)
    _test_sessions_summaries(mock_service, endpoint, start_time, end_time)
    _test_single_session(mock_service, endpoint, sessions)
    _test_error_handling(mock_service)


def test_time_shifting():
    """Test that time shifting works correctly."""
    print("\n" + "=" * 80)
    print("TEST 2: Time Shifting Verification")
    print("=" * 80)

    mock_service = create_mock_service()

    # Get the time shift
    time_shift = mock_service._calculate_time_shift()  # noqa: SLF001
    print(f"\nTime shift from capture to now: {time_shift.days} days")

    # Verify that shifted dates are recent
    endpoint = "website_analytics"
    cost_data = mock_service.get_copilot_cost_daily(endpoint, "tokens")

    if cost_data:
        dates = [datetime.fromisoformat(date).replace(tzinfo=UTC) for date in cost_data]
        most_recent = max(dates)
        oldest = min(dates)

        print("\nShifted date range:")
        print(f"  Oldest: {oldest.date()}")
        print(f"  Most recent: {most_recent.date()}")
        print(f"  Days ago (oldest): {(datetime.now(UTC) - oldest).days}")
        print(f"  Days ago (most recent): {(datetime.now(UTC) - most_recent).days}")

        # Verify that data appears "fresh" (within last 30-40 days)
        days_ago_recent = (datetime.now(UTC) - most_recent).days
        if days_ago_recent <= 10:
            print("\n✓ Time shifting working correctly - data appears recent!")
        else:
            print(f"\n⚠ Warning: Most recent data is {days_ago_recent} days old")


def test_mock_tool_replacements():
    """Test creating mock tool replacements."""
    print("\n" + "=" * 80)
    print("TEST 3: Mock Tool Replacements")
    print("=" * 80)

    # Create mock tool replacements
    mock_tools = create_ally_config_mock_tool_replacements()

    print(f"\nCreated {len(mock_tools)} mock tool replacements:")
    for tool_name in mock_tools:
        print(f"  - {tool_name}")

    # Verify the tools are callable
    print("\nVerifying tools are callable...")
    for tool_name, tool_func in mock_tools.items():
        print(f"  {tool_name}: callable = {callable(tool_func)}")


async def _test_async_ratings(mock_tools, ctx, endpoint):
    """Test mock_get_copilot_ratings."""
    print("\n--- Testing mock_get_copilot_ratings ---")
    ratings_func = mock_tools["ally_config_get_copilot_ratings"]
    ratings = await ratings_func(ctx, endpoint)
    print(f"Result: {ratings}")


async def _test_async_cost(mock_tools, ctx, endpoint):
    """Test mock_get_copilot_cost_daily."""
    print("\n--- Testing mock_get_copilot_cost_daily ---")
    cost_func = mock_tools["ally_config_get_copilot_cost_daily"]
    cost_data = await cost_func(ctx, endpoint, "tokens")
    print(f"Found {len(cost_data)} days of data")


async def _test_async_sessions(mock_tools, ctx, endpoint):
    """
    Test mock_get_copilot_sessions.

    Returns:
        A tuple containing the sessions data, start_time, and end_time.
    """
    print("\n--- Testing mock_get_copilot_sessions ---")
    sessions_func = mock_tools["ally_config_get_copilot_sessions"]
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(days=7)

    sessions = await sessions_func(
        ctx,
        endpoint,
        start_time.isoformat(),
        end_time.isoformat()
    )
    if isinstance(sessions, dict) and sessions.get("_truncated"):
        print("Response was truncated")
    else:
        print(f"Found {len(sessions)} sessions")

    return sessions, start_time, end_time


async def _test_async_summaries(mock_tools, ctx, endpoint, start_time, end_time):
    """Test mock_get_copilot_sessions_summaries."""
    print("\n--- Testing mock_get_copilot_sessions_summaries ---")
    summaries_func = mock_tools["ally_config_get_copilot_sessions_summaries"]
    summaries = await summaries_func(
        ctx,
        endpoint,
        start_time.isoformat(),
        end_time.isoformat()
    )
    if isinstance(summaries, dict) and summaries.get("_truncated"):
        print("Response was truncated")
    else:
        print(f"Total count: {summaries.get('total_count', 0)}")


async def _test_async_single_session(mock_tools, ctx, endpoint, sessions):
    """Test mock_get_copilot_session."""
    print("\n--- Testing mock_get_copilot_session ---")
    session_func = mock_tools["ally_config_get_copilot_session"]
    if sessions and not isinstance(sessions, dict):
        test_session_id = sessions[0]['session_id']
        single_session = await session_func(ctx, test_session_id, endpoint)
        if isinstance(single_session, dict) and single_session.get("_truncated"):
            print("Response was truncated")
        else:
            print(f"Retrieved session: {single_session['session_id']}")
    else:
        print("Skipping (no sessions available)")


async def test_async_mock_tools():
    """Test that async mock tools work correctly."""
    print("\n" + "=" * 80)
    print("TEST 4: Async Mock Tools")
    print("=" * 80)

    # Create mock tool replacements
    mock_tools = create_ally_config_mock_tool_replacements()

    # Create a dummy context (tools expect this as first parameter)
    class DummyCtx:
        pass

    ctx = DummyCtx()
    endpoint = "website_analytics"

    # Test each mock tool
    await _test_async_ratings(mock_tools, ctx, endpoint)
    await _test_async_cost(mock_tools, ctx, endpoint)
    sessions, start_time, end_time = await _test_async_sessions(mock_tools, ctx, endpoint)
    await _test_async_summaries(mock_tools, ctx, endpoint, start_time, end_time)
    await _test_async_single_session(mock_tools, ctx, endpoint, sessions)


class DummyCtx:
    """Dummy context class for tool testing."""


def _setup_tool_manager():
    """
    Set up and configure tool manager with mock replacements.

    Returns:
        ToolGroupManager: Configured tool manager with mock replacements applied.
    """
    auth_manager = AuthManager()
    tool_manager = ToolGroupManager(auth_manager)

    print("\n--- Loading Ally Config tools ---")
    tool_manager.load_ally_config_tools(regenerate_models=True)

    logs_tools = tool_manager.get_tools_for_groups([AllyConfigToolGroup.LOGS])
    print(f"Loaded {len(logs_tools)} LOGS tools")

    print("\n--- Creating mock tool replacements ---")
    mock_tools = create_ally_config_mock_tool_replacements()
    print(f"Created {len(mock_tools)} mock tool replacements")

    print("\n--- Applying tool replacements ---")
    tool_manager.apply_tool_replacements(mock_tools)

    return tool_manager


def _get_test_tools(tool_manager):
    """
    Retrieve tools for testing.

    Returns:
        dict: Dictionary mapping tool names to tool objects.
    """
    all_tools = tool_manager.get_tools_for_groups([AllyConfigToolGroup.ALL])
    return {
        'ratings': next((t for t in all_tools if t.name == "ally_config_get_copilot_ratings"), None),
        'cost': next((t for t in all_tools if t.name == "ally_config_get_copilot_cost_daily"), None),
        'sessions': next((t for t in all_tools if t.name == "ally_config_get_copilot_sessions"), None),
        'session': next((t for t in all_tools if t.name == "ally_config_get_copilot_session"), None),
        'summaries': next((t for t in all_tools if t.name == "ally_config_get_copilot_sessions_summaries"), None),
    }


async def _test_ratings_tool(tool, ctx, endpoint):
    """Test the get_copilot_ratings tool."""
    if not tool:
        return
    print("\n• Testing get_copilot_ratings:")
    try:
        ratings = await tool.function(ctx, endpoint)
        print(f"  Ratings: {ratings}")
    except Exception as e:
        print(f"  Error: {e}")


async def _test_cost_tool(tool, ctx, endpoint):
    """Test the get_copilot_cost_daily tool."""
    if not tool:
        return
    print("\n• Testing get_copilot_cost_daily:")
    try:
        cost_data = await tool.function(ctx, endpoint, "tokens")
        print(f"  Found {len(cost_data)} days of cost data")
        if cost_data:
            for _i, (date, values) in enumerate(list(cost_data.items())[:2]):
                print(f"    {date}: {values}")
    except Exception as e:
        print(f"  Error: {e}")


async def _test_sessions_tool(tool, ctx, endpoint):
    """
    Test the get_copilot_sessions tool.

    Returns:
        list | None: List of sessions or None if error or tool not found.
    """
    if not tool:
        return None
    print("\n• Testing get_copilot_sessions:")
    try:
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=7)

        sessions = await tool.function(
            ctx,
            endpoint,
            start_time.isoformat(),
            end_time.isoformat()
        )
        if isinstance(sessions, dict) and sessions.get("_truncated"):
            print("  Response was truncated")
        else:
            print(f"  Found {len(sessions)} sessions")
            if sessions:
                first_session = sessions[0]
                print(f"    First session ID: {first_session['session_id']}")
                print(f"    Messages: {len(first_session['messages'])}")
        return sessions
    except Exception as e:
        print(f"  Error: {e}")
        return None


async def _test_summaries_tool(tool, ctx, endpoint, start_time, end_time):
    """Test the get_copilot_sessions_summaries tool."""
    if not tool:
        return
    print("\n• Testing get_copilot_sessions_summaries:")
    try:
        summaries = await tool.function(
            ctx,
            endpoint,
            start_time.isoformat(),
            end_time.isoformat()
        )
        if isinstance(summaries, dict) and summaries.get("_truncated"):
            print("  Response was truncated")
        else:
            print(f"  Total count: {summaries.get('total_count', 0)}")
            if summaries.get('sessions'):
                print(f"    First summary ID: {summaries['sessions'][0]['session_id']}")
                print(f"    Message count: {summaries['sessions'][0]['message_count']}")
    except Exception as e:
        print(f"  Error: {e}")


async def _test_session_tool(tool, ctx, endpoint, sessions):
    """Test the get_copilot_session tool."""
    if not tool or not sessions or isinstance(sessions, dict):
        return
    print("\n• Testing get_copilot_session:")
    try:
        test_session_id = sessions[0]['session_id']
        single_session = await tool.function(ctx, test_session_id, endpoint)
        if isinstance(single_session, dict) and single_session.get("_truncated"):
            print("  Response was truncated")
        else:
            print(f"  Retrieved session: {single_session['session_id']}")
            print(f"    Messages: {len(single_session['messages'])}")
    except Exception as e:
        print(f"  Error: {e}")


async def test_tool_group_manager_with_replacement():
    """
    Test replacing tools in a ToolGroupManager and calling them.

    Returns:
        ToolGroupManager: The configured tool manager for optional chat usage.
    """
    print("\n" + "=" * 80)
    print("TEST 5: ToolGroupManager with Tool Replacement")
    print("=" * 80)

    tool_manager = _setup_tool_manager()

    print("\n--- Testing replaced tools by calling them ---")

    tools = _get_test_tools(tool_manager)
    ctx = DummyCtx()
    endpoint = "website_analytics"

    await _test_ratings_tool(tools['ratings'], ctx, endpoint)
    await _test_cost_tool(tools['cost'], ctx, endpoint)

    sessions = await _test_sessions_tool(tools['sessions'], ctx, endpoint)

    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(days=7)
    await _test_summaries_tool(tools['summaries'], ctx, endpoint, start_time, end_time)
    await _test_session_tool(tools['session'], ctx, endpoint, sessions)

    print("\n✓ Tool replacement and execution test completed!")

    return tool_manager


def start_terminal_chat_with_mock_tools():
    """Start an interactive terminal chat with mock tools."""
    print("\n" + "=" * 80)
    print("TEST 6: Terminal Chat with Mock Tools")
    print("=" * 80)

    console = Console()

    # Initialize
    console.print("\n[dim]Setting up agent with mock tools...[/dim]")

    auth_manager = AuthManager()
    factory = AgentFactory(auth_manager=auth_manager)

    # Create and apply mock tool replacements
    mock_tools = create_ally_config_mock_tool_replacements()
    print(f"\nCreated {len(mock_tools)} mock tool replacements")

    # Create agent with the replaced tools
    agent = create_hybrid_assistant(
        factory=factory,
        ai_knowledge_groups=[AIKnowledgeToolGroup.ALL],
        ally_config_groups=[AllyConfigToolGroup.ALL],
        tool_replacements=mock_tools
    )

    # Create dependencies
    deps = factory.create_dependencies()

    console.print("[dim]✓ Agent initialized with mock tools[/dim]")
    console.print(f"[dim]Model: {agent.model}[/dim]")
    console.print("[dim]Replaced tools: get_copilot_ratings, get_copilot_cost_daily, get_copilot_sessions,[/dim]")
    console.print("[dim]                 get_copilot_session, get_copilot_sessions_summaries[/dim]")
    console.print("\n[yellow]Note: These tools will return mock data instead of making real API calls[/yellow]\n")

    # Start the chat session
    start_chat_session(agent, deps, console_width=200)


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Analytics API Mock Service Test" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")

    try:
        # Run synchronous tests
        test_direct_mock_service()
        test_time_shifting()
        test_mock_tool_replacements()

        # Run async tests
        import asyncio  # noqa: PLC0415
        asyncio.run(test_async_mock_tools())
        asyncio.run(test_tool_group_manager_with_replacement())

        print("\n" + "=" * 80)
        print("✓ All tests completed successfully!")
        print("=" * 80)

        # Optional: Start terminal chat with mock tools
        print("\n" + "=" * 80)
        user_input = input("Would you like to start a terminal chat with the mock tools? (y/n): ")
        if user_input.lower() in {'y', 'yes'}:
            asyncio.run(start_terminal_chat_with_mock_tools())
        else:
            print("Skipping terminal chat.")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nTo fix this:")
        print("1. Open capture_anonymize_api_data.ipynb")
        print("2. Run the notebook to capture API data")
        print("3. Run this example again")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback  # noqa: PLC0415
        traceback.print_exc()


if __name__ == "__main__":
    main()
