"""Evaluators for assessing model performance on conversation-based tasks."""

from dataclasses import dataclass

from pydantic_ai.messages import ToolCallPart
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from ..agents.dependencies import TimelineEntry, TimelineEntryType
from .case_factory import ExpectedOutput
from .conversation_turns import ModelMessage


@dataclass
class ToolCallEvaluator(Evaluator):
    """
    Evaluator to assess if the model made correct tool calls in a conversation.

    Returns a score between 0.0 and 1.0 based on how many expected tool calls were made correctly.
    By default, compares unique tool names (sets) to avoid duplicates skewing the score.

    Args:
        use_sets: If True (default), compare unique tool names. If False, count all occurrences.
    """

    use_sets: bool = True

    def evaluate(self, ctx: EvaluatorContext) -> float:
        """
        Evaluate the model's tool calls against expected tool calls.

        Supports both single-agent (list[ModelMessage]) and multi-agent (list[TimelineEntry]) outputs.

        Args:
            ctx: EvaluatorContext containing expected output and actual output

        Returns:
            Float between 0.0 and 1.0 representing tool call accuracy
        """
        expected: ExpectedOutput | None = ctx.expected_output
        actual_output = ctx.output

        # Handle case where expected_output is None
        if expected is None:
            return 0.0

        # Extract actual tool calls - handle both single-agent and multi-agent cases
        if actual_output and len(actual_output) > 0 and isinstance(actual_output[0], TimelineEntry):
            # Multi-agent case: output is list[TimelineEntry]
            actual_tool_calls = self._extract_tool_calls_from_timeline(actual_output)
        else:
            # Single-agent case: output is list[ModelMessage]
            actual_tool_calls = self._extract_tool_calls_from_messages(actual_output)

        # Get expected tool calls from either direct tool_calls or model_messages
        expected_tool_calls = self._get_expected_tool_calls(expected)

        if expected_tool_calls is None:
            # No tool calls expected - perfect score if none made, zero if any made
            return 1.0 if len(actual_tool_calls) == 0 else 0.0

        if len(expected_tool_calls) == 0:
            # Expected no tool calls - perfect score if none made, zero if any made
            return 1.0 if len(actual_tool_calls) == 0 else 0.0

        # Calculate accuracy based on tool names
        expected_tool_names = [tool.tool_name for tool in expected_tool_calls]
        actual_tool_names = [call.tool_name for call in actual_tool_calls]

        if self.use_sets:
            # Compare unique tool names (sets)
            expected_set = set(expected_tool_names)
            actual_set = set(actual_tool_names)
            matches = len(expected_set & actual_set)  # Intersection
            return matches / len(expected_set)
        else:
            # Count matches (handles multiple calls to same tool)
            matches = self._count_tool_name_matches(expected_tool_names, actual_tool_names)
            return matches / len(expected_tool_calls)

    def _extract_tool_calls_from_messages(self, messages: list[ModelMessage]) -> list[ToolCallPart]:
        """
        Extract all ToolCallPart objects from the given messages.

        Returns:
            List of ToolCallPart objects extracted from messages.
        """
        tool_calls = []
        for message in messages:
            if hasattr(message, 'parts'):
                for part in message.parts:
                    if isinstance(part, ToolCallPart):
                        tool_calls.append(part)
        return tool_calls

    def _extract_tool_calls_from_timeline(self, timeline: list[TimelineEntry]) -> list[ToolCallPart]:
        """
        Extract all ToolCallPart objects from timeline entries (multi-agent case).

        Args:
            timeline: List of TimelineEntry objects from multi-agent orchestrator

        Returns:
            List of ToolCallPart objects extracted from timeline entries.
        """
        tool_calls = []
        for entry in timeline:
            if entry.entry_type == TimelineEntryType.ORCHESTRATOR_MESSAGE:
                # Extract from orchestrator message
                message = entry.data
                if hasattr(message, 'parts'):
                    for part in message.parts:
                        if isinstance(part, ToolCallPart):
                            tool_calls.append(part)
            elif entry.entry_type == TimelineEntryType.SPECIALIST_RUN:
                # Extract from specialist run's new_messages
                specialist_run = entry.data
                if hasattr(specialist_run, 'new_messages'):
                    tool_calls.extend(self._extract_tool_calls_from_messages(specialist_run.new_messages))
        return tool_calls

    def _get_expected_tool_calls(self, expected: ExpectedOutput) -> list[ToolCallPart] | None:
        """
        Get expected tool calls from ExpectedOutput, prioritizing model_messages over tool_calls.

        Returns:
            List of expected ToolCallPart objects or None if no tool calls expected.
        """
        # Priority 1: Extract from model_messages if they exist
        if expected.model_messages and len(expected.model_messages) > 0:
            return self._extract_tool_calls_from_messages(expected.model_messages)

        # Priority 2: Use direct tool_calls if provided
        if expected.tool_calls:
            return expected.tool_calls

        # No expected tool calls
        return None

    def _count_tool_name_matches(self, expected_names: list[str], actual_names: list[str]) -> int:
        """
        Count how many expected tool names appear in actual tool names.

        This handles cases where:
        - Multiple calls to the same tool are expected
        - Order of calls might differ

        Returns:
            Number of matching tool name occurrences.
        """
        expected_counts = {}
        actual_counts = {}

        # Count occurrences of each tool name
        for name in expected_names:
            expected_counts[name] = expected_counts.get(name, 0) + 1

        for name in actual_names:
            actual_counts[name] = actual_counts.get(name, 0) + 1

        # Count matches (minimum of expected and actual for each tool)
        matches = 0
        for tool_name, expected_count in expected_counts.items():
            actual_count = actual_counts.get(tool_name, 0)
            matches += min(expected_count, actual_count)

        return matches
