"""
Mock API Service for Ally Config Analytics Endpoints.

This module provides time-shifted mock data for analytics endpoints based on
captured API data. It automatically adjusts timestamps so that data appears
"fresh" relative to when the API is called.
"""

import json
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic_ai import ModelRetry


class AllyConfigMockService:
    """Service for providing time-shifted mock data for Ally Config analytics."""

    def __init__(self, mock_data_path: str | Path):
        """
        Initialize the mock service with captured data.

        Args:
            mock_data_path: Path to the JSON file containing captured API data.
        """
        self.mock_data_path = Path(mock_data_path)
        self._load_data()

    def _load_data(self) -> None:
        """Load and parse the mock data from disk."""
        with open(self.mock_data_path, encoding="utf-8") as f:
            self.data = json.load(f)

        # Parse the capture timestamp
        self.capture_time = datetime.fromisoformat(
            self.data["metadata"]["capture_timestamp"]
        )

        # Parse the original time range
        self.original_start = datetime.fromisoformat(
            self.data["metadata"]["start_time"]
        )
        self.original_end = datetime.fromisoformat(
            self.data["metadata"]["end_time"]
        )

    def _calculate_time_shift(self) -> timedelta:
        """
        Calculate the time difference between capture time and now.

        Returns:
            The timedelta to shift all timestamps by.
        """
        return datetime.now() - self.capture_time

    def _validate_endpoint(self, endpoint: str) -> None:
        """
        Validate that the endpoint is supported.

        Args:
            endpoint: The endpoint identifier to validate.

        Raises:
            ModelRetry: If the endpoint does not contain 'website'.
        """
        if "website" not in endpoint.lower():
            raise ModelRetry(
                "Internal server error occurred while processing the request."
            )

    def get_copilot_ratings(
        self,
        endpoint: str,
        start_time: str | None = None,  # noqa: ARG002
        end_time: str | None = None,  # noqa: ARG002
    ) -> list:
        """
        Get copilot ratings (always returns empty list).

        Args:
            endpoint: The endpoint identifier for the Copilot.
            start_time: Optional start datetime (unused).
            end_time: Optional end datetime (unused).

        Returns:
            An empty list (no ratings in captured data).

        Raises:
            ModelRetry: If the endpoint does not contain 'website'.
        """
        self._validate_endpoint(endpoint)
        return []

    def get_copilot_cost_daily(
        self, endpoint: str, unit: str
    ) -> dict[str, list[float]]:
        """
        Get daily cost data with time-shifted dates.

        This adjusts all dates so they appear to be from the last 30 days
        relative to when this method is called.

        Args:
            endpoint: The endpoint identifier for the Copilot.
            unit: The unit of measurement ('tokens' or 'euro').

        Returns:
            A dictionary mapping date strings to lists of cost/token values,
            with dates shifted to appear current.

        Raises:
            ModelRetry: If the endpoint does not contain 'website'.
        """
        self._validate_endpoint(endpoint)

        # Get the appropriate cost data
        if unit == "tokens":
            cost_data = self.data.get("cost_tokens", {})
        elif unit == "euro":
            cost_data = self.data.get("cost_euro", {})
        else:
            return {}

        # Calculate time shift
        time_shift = self._calculate_time_shift()

        # Shift all dates
        shifted_data = {}
        for date_str, values in cost_data.items():
            # Parse the date
            original_date = datetime.fromisoformat(date_str).date()

            # Shift it
            shifted_date = original_date + timedelta(days=time_shift.days)

            # Convert back to string in same format
            shifted_data[shifted_date.isoformat()] = values

        return shifted_data

    def get_copilot_sessions(
        self, endpoint: str, start_time: str, end_time: str
    ) -> list[dict[str, Any]]:
        """
        Get session histories with time-shifted timestamps.

        This shifts all session and message timestamps so they align with the
        requested time range relative to when this method is called.

        Args:
            endpoint: The endpoint identifier for the Copilot.
            start_time: The start time (ISO 8601 format) for filtering.
            end_time: The end time (ISO 8601 format) for filtering.

        Returns:
            A list of session dictionaries with adjusted timestamps.

        Raises:
            ModelRetry: If the endpoint does not contain 'website'.
        """
        self._validate_endpoint(endpoint)

        # Parse the requested time range
        requested_start = datetime.fromisoformat(start_time)
        requested_end = datetime.fromisoformat(end_time)

        # Calculate time shift
        time_shift = self._calculate_time_shift()

        # Filter and shift sessions
        shifted_sessions = []
        for session in self.data.get("sessions", []):
            # Parse original session timestamp
            original_timestamp = datetime.fromisoformat(session["timestamp"])

            # Shift the timestamp
            shifted_timestamp = original_timestamp + time_shift

            # Check if this session falls within the requested range
            if requested_start <= shifted_timestamp <= requested_end:
                # Create shifted session
                shifted_session = {
                    "session_id": session["session_id"],
                    "timestamp": shifted_timestamp.isoformat(),
                    "messages": [],
                }

                # Shift all message timestamps
                for message in session.get("messages", []):
                    original_msg_time = datetime.fromisoformat(
                        message["timestamp"]
                    )
                    shifted_msg_time = original_msg_time + time_shift

                    shifted_session["messages"].append(
                        {
                            "role": message["role"],
                            "content": message["content"],
                            "timestamp": shifted_msg_time.isoformat(),
                        }
                    )

                shifted_sessions.append(shifted_session)

        return shifted_sessions

    def reload_data(self) -> None:
        """Reload data from disk (useful if the file has been updated)."""
        self._load_data()


# Convenience function to create a service instance
def create_mock_service(
    data_file: str = "anonymized_api_data_latest.json",
) -> AllyConfigMockService:
    """
    Create a mock service instance with the specified data file.

    Args:
        data_file: Name of the JSON file in Data/api_mock_data/ directory.

    Returns:
        An initialized AllyConfigMockService instance.

    Raises:
        FileNotFoundError: If the mock data file does not exist.
    """
    # Assume we're in src/meta_ally/util, go up to project root
    project_root = Path(__file__).parent.parent.parent.parent
    mock_data_path = project_root / "Data" / "api_mock_data" / data_file

    if not mock_data_path.exists():
        raise FileNotFoundError(
            f"Mock data file not found: {mock_data_path}\n"
            f"Make sure you've captured API data first using "
            f"capture_anonymize_api_data.ipynb"
        )

    return AllyConfigMockService(mock_data_path)


def create_ally_config_mock_tool_replacements(
    data_file: str = "anonymized_api_data_latest.json",
) -> dict[str, Callable]:
    """
    Create a dictionary of tool replacements for Ally Config analytics endpoints.

    This function creates async wrapper functions that match the pydantic-ai tool
    signature, with proper prefixed tool names for use with ToolGroupManager.

    Args:
        data_file: Name of the JSON file in Data/api_mock_data/ directory.

    Returns:
        Dictionary mapping prefixed tool names (e.g., "ally_config_get_copilot_ratings")
        to async mock functions that can be passed to AgentFactory's tool_replacements parameter.

    Raises:
        FileNotFoundError: If the mock data file does not exist.

    Example:
        ```python
        from meta_ally.agents import AgentFactory
        from meta_ally.util.api_mock_service import create_ally_config_mock_tool_replacements

        # Create mock replacements
        mock_replacements = create_ally_config_mock_tool_replacements()

        # Create agent with mock tools
        factory = AgentFactory()
        agent = factory.create_hybrid_assistant(
            tool_replacements=mock_replacements
        )

        # Now when the agent calls analytics tools, it will use mock data
        deps = factory.create_dependencies()
        result = agent.run_sync("Show me copilot cost data", deps=deps)
        ```
    """
    # Create the mock service instance
    mock_service = create_mock_service(data_file)

    # Create async wrappers for the mock service methods
    # These match the signature expected by pydantic-ai tools
    # Note: Functions must be async even though they don't await, to match tool signatures

    async def mock_get_copilot_ratings(ctx, endpoint: str, start_time: str | None = None, end_time: str | None = None):  # noqa: RUF029
        """Mock version of get_copilot_ratings using time-shifted data."""
        del ctx  # Context required by pydantic-ai but not used in mock
        return mock_service.get_copilot_ratings(endpoint, start_time, end_time)

    async def mock_get_copilot_cost_daily(ctx, endpoint: str, unit: str):  # noqa: RUF029
        """Mock version of get_copilot_cost_daily using time-shifted data."""
        del ctx  # Context required by pydantic-ai but not used in mock
        return mock_service.get_copilot_cost_daily(endpoint, unit)

    async def mock_get_copilot_sessions(ctx, endpoint: str, start_time: str, end_time: str):  # noqa: RUF029
        """Mock version of get_copilot_sessions using time-shifted data."""
        del ctx  # Context required by pydantic-ai but not used in mock
        return mock_service.get_copilot_sessions(endpoint, start_time, end_time)

    # Return the mapping with PREFIXED tool names
    # The prefix determines which tool list the replacement is applied to
    return {
        "ally_config_get_copilot_ratings": mock_get_copilot_ratings,
        "ally_config_get_copilot_cost_daily": mock_get_copilot_cost_daily,
        "ally_config_get_copilot_sessions": mock_get_copilot_sessions,
    }
