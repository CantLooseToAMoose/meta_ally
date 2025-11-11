"""Evaluators for assessing model performance on conversation-based tasks."""

from dataclasses import dataclass
from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from .case_factory import ExpectedOutput
from .conversation_turns import ModelMessage
from typing import List, Optional
from pydantic_ai.messages import ToolCallPart


@dataclass
class ToolCallEvaluator(Evaluator):
    """Evaluator to assess if the model made correct tool calls in a conversation.
    
    Returns a score between 0.0 and 1.0 based on how many expected tool calls were made correctly.
    """

    def evaluate(self, ctx: EvaluatorContext) -> float:
        """Evaluate the model's tool calls against expected tool calls.
        
        Args:
            ctx: EvaluatorContext containing expected output and actual output
            
        Returns:
            Float between 0.0 and 1.0 representing tool call accuracy
        """
        expected: Optional[ExpectedOutput] = ctx.expected_output
        actual_messages: List[ModelMessage] = ctx.output

        # Handle case where expected_output is None
        if expected is None:
            return 0.0
        
        # Extract actual tool calls from model messages
        actual_tool_calls = self._extract_tool_calls_from_messages(actual_messages)
        
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
        
        # Count matches (handles multiple calls to same tool)
        matches = self._count_tool_name_matches(expected_tool_names, actual_tool_names)
        
        return matches / len(expected_tool_calls)
    
    def _extract_tool_calls_from_messages(self, messages: List[ModelMessage]) -> List[ToolCallPart]:
        """Extract all ToolCallPart objects from the given messages."""
        tool_calls = []
        for message in messages:
            if hasattr(message, 'parts'):
                for part in message.parts:
                    if isinstance(part, ToolCallPart):
                        tool_calls.append(part)
        return tool_calls
    
    def _get_expected_tool_calls(self, expected: ExpectedOutput) -> Optional[List[ToolCallPart]]:
        """Get expected tool calls from ExpectedOutput, prioritizing model_messages over tool_calls."""
        # Priority 1: Extract from model_messages if they exist
        if expected.model_messages and len(expected.model_messages) > 0:
            return self._extract_tool_calls_from_messages(expected.model_messages)
        
        # Priority 2: Use direct tool_calls if provided
        if expected.tool_calls:
            return expected.tool_calls
        
        # No expected tool calls
        return None
    
    def _count_tool_name_matches(self, expected_names: List[str], actual_names: List[str]) -> int:
        """Count how many expected tool names appear in actual tool names.
        
        This handles cases where:
        - Multiple calls to the same tool are expected
        - Order of calls might differ
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
