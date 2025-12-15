"""Tests for evaluators module."""

from datetime import datetime

import pytest
from pydantic_ai.messages import ModelResponse

from meta_ally.eval.case_factory import ExpectedOutput, create_tool_call_part
from meta_ally.eval.evaluators import ToolCallEvaluator


@pytest.fixture
def evaluator_sets():
    """Evaluator with set-based comparison."""
    return ToolCallEvaluator(use_sets=True)


@pytest.fixture
def evaluator_counts():
    """Evaluator with count-based comparison."""
    return ToolCallEvaluator(use_sets=False)


def create_response(tool_names: list[str]) -> ModelResponse:
    """Helper to create a ModelResponse with tool calls."""
    parts = [create_tool_call_part(name, {"arg": "value"}) for name in tool_names]
    return ModelResponse(parts=parts, timestamp=datetime.now())


def create_expected(tool_names: list[str]) -> ExpectedOutput:
    """Helper to create ExpectedOutput with tool calls."""
    return ExpectedOutput(
        tool_calls=[create_tool_call_part(name, {"arg": "value"}) for name in tool_names]
    )


class MockContext:
    """Mock EvaluatorContext for testing."""
    def __init__(self, expected_output, output):
        """Initialize mock context with expected and actual output."""
        self.expected_output = expected_output
        self.output = output


class TestToolCallEvaluatorSets:
    """Test set-based comparison (default)."""

    @pytest.mark.parametrize(("expected_tools", "actual_tools", "expected_score"), [
        (["get_user"], ["get_user"], 1.0),
        (["a", "b", "c"], ["a", "b", "c"], 1.0),
        (["a", "b", "c"], ["a", "b"], 2 / 3),
        (["a", "b"], ["c", "d"], 0.0),
        (["a"], ["a", "b", "c"], 1.0),  # Extra tools ignored
        (["a", "a", "a"], ["a"], 1.0),  # Duplicates ignored
    ])
    def test_tool_matching(self, evaluator_sets, expected_tools, actual_tools, expected_score):
        """Test various tool matching scenarios."""
        ctx = MockContext(
            expected_output=create_expected(expected_tools),
            output=[create_response(actual_tools)]
        )
        assert evaluator_sets.evaluate(ctx) == pytest.approx(expected_score)

    def test_no_tools_expected_or_actual(self, evaluator_sets):
        """Test when no tools are expected or called."""
        ctx = MockContext(
            expected_output=ExpectedOutput(tool_calls=[]),
            output=[ModelResponse(parts=[], timestamp=datetime.now())]
        )
        assert evaluator_sets.evaluate(ctx) == 1.0

    def test_no_tools_expected_but_called(self, evaluator_sets):
        """Test when no tools expected but some called."""
        ctx = MockContext(
            expected_output=ExpectedOutput(tool_calls=[]),
            output=[create_response(["unexpected"])]
        )
        assert evaluator_sets.evaluate(ctx) == 0.0

    def test_none_expected_output(self, evaluator_sets):
        """Test when expected_output is None."""
        ctx = MockContext(
            expected_output=None,
            output=[create_response(["tool"])]
        )
        assert evaluator_sets.evaluate(ctx) == 0.0

    def test_empty_actual_messages(self, evaluator_sets):
        """Test with empty actual messages."""
        ctx = MockContext(
            expected_output=create_expected(["tool"]),
            output=[]
        )
        assert evaluator_sets.evaluate(ctx) == 0.0

    def test_multiple_messages(self, evaluator_sets):
        """Test tools spread across multiple messages."""
        ctx = MockContext(
            expected_output=create_expected(["a", "b"]),
            output=[create_response(["a"]), create_response(["b"])]
        )
        assert evaluator_sets.evaluate(ctx) == 1.0

    def test_model_messages_priority(self, evaluator_sets):
        """Test that model_messages takes priority over tool_calls."""
        ctx = MockContext(
            expected_output=ExpectedOutput(
                model_messages=[create_response(["a"])],
                tool_calls=[create_tool_call_part("b", {})]
            ),
            output=[create_response(["a"])]
        )
        assert evaluator_sets.evaluate(ctx) == 1.0


class TestToolCallEvaluatorCounts:
    """Test count-based comparison."""

    @pytest.mark.parametrize(("expected_tools", "actual_tools", "expected_score"), [
        (["a", "a", "b"], ["a", "a", "b"], 1.0),
        (["a", "a", "a", "b"], ["a", "a", "b"], 0.75),  # 3/4 matched
        (["a"], ["a", "a", "a"], 1.0),  # Extra calls don't hurt
        (["a", "a", "b", "b", "b", "c"], ["a", "b", "b", "b"], 4 / 6),  # Mixed
    ])
    def test_count_matching(self, evaluator_counts, expected_tools, actual_tools, expected_score):
        """Test count-based matching scenarios."""
        ctx = MockContext(
            expected_output=create_expected(expected_tools),
            output=[create_response(actual_tools)]
        )
        assert evaluator_counts.evaluate(ctx) == pytest.approx(expected_score)


class TestEdgeCases:
    """Test edge cases."""

    def test_none_tool_calls_field(self, evaluator_sets):
        """Test when tool_calls field is None."""
        ctx = MockContext(
            expected_output=ExpectedOutput(tool_calls=None),
            output=[create_response(["tool"])]
        )
        assert evaluator_sets.evaluate(ctx) == 0.0

    def test_empty_model_messages(self, evaluator_sets):
        """Test when model_messages is empty."""
        ctx = MockContext(
            expected_output=ExpectedOutput(model_messages=[]),
            output=[]
        )
        assert evaluator_sets.evaluate(ctx) == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
