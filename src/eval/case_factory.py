"""Factory for creating test cases with message history inputs and outputs."""

from typing import Any, Optional, List, Dict, Union
from dataclasses import dataclass
from pydantic_evals import Case, Dataset
from pydantic_ai.messages import (
    ModelRequest, 
    ModelResponse, 
    UserPromptPart, 
    TextPart,
    SystemPromptPart,
    ToolCallPart,
    ToolReturnPart
)

# Union type for message history (matching pydantic-ai's ModelMessage)
ModelMessage = Union[ModelRequest, ModelResponse]


@dataclass
class MessageHistoryCase:
    """A test case that holds message history as input and expected output.
    
    This is a convenient wrapper around pydantic-eval's Case type specifically
    designed for testing conversational AI systems with message histories.
    """
    
    name: str
    input_messages: List[ModelMessage]
    expected_output_messages: Optional[List[ModelMessage]] = None
    metadata: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    
    def to_case(self) -> Case[List[ModelMessage], List[ModelMessage], Dict[str, Any]]:
        """Convert this message history case to a pydantic-eval Case."""
        return Case(
            name=self.name,
            inputs=self.input_messages,
            expected_output=self.expected_output_messages,
            metadata=self.metadata
        )


class CaseFactory:
    """Factory for creating test cases with message histories."""
    
    def __init__(self):
        self._cases: List[MessageHistoryCase] = []
    
    def create_simple_case(
        self,
        name: str,
        user_input: str,
        expected_response: Optional[str] = None,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageHistoryCase:
        """Create a simple case with a single user input and optional expected response.
        
        Args:
            name: Name of the test case
            user_input: The user's input message
            expected_response: Expected response from the agent (optional)
            system_prompt: System prompt to include (optional)
            description: Description of the test case
            metadata: Additional metadata for the case
            
        Returns:
            MessageHistoryCase ready to be used in evaluations
        """
        # Build input messages
        input_parts = []
        if system_prompt:
            input_parts.append(SystemPromptPart(content=system_prompt))
        input_parts.append(UserPromptPart(content=user_input))
        
        input_messages = [ModelRequest(parts=input_parts)]
        
        # Build expected output messages if provided
        expected_output_messages = None
        if expected_response:
            expected_output_messages = [
                ModelResponse(parts=[TextPart(content=expected_response)])
            ]
        
        case = MessageHistoryCase(
            name=name,
            input_messages=list(input_messages),  # Cast to List[ModelMessage]
            expected_output_messages=list(expected_output_messages) if expected_output_messages else None,
            metadata=metadata,
            description=description
        )
        
        self._cases.append(case)
        return case
    
    def create_conversation_case(
        self,
        name: str,
        conversation_turns: List[Dict[str, Any]],
        expected_final_response: Optional[str] = None,
        expected_final_tool_calls: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageHistoryCase:
        """Create a case with multiple conversation turns, including tool calls.
        
        Args:
            name: Name of the test case
            conversation_turns: List of dicts with keys:
                - 'user': User message content (optional)
                - 'assistant': Assistant response content (optional)
                - 'tool_calls': List of tool calls made by assistant (optional)
                  Format: [{"id": "call_1", "name": "tool_name", "args": {"param": "value"}}]
                - 'tool_results': List of tool results (optional)
                  Format: [{"call_id": "call_1", "tool_name": "tool_name", "content": "result"}]
            expected_final_response: Expected final response from the agent
            expected_final_tool_calls: Expected tool calls in the final response
            system_prompt: System prompt to include at the start
            description: Description of the test case
            metadata: Additional metadata for the case
            
        Returns:
            MessageHistoryCase with full conversation history including tools
        """
        input_messages = []
        
        # Add system prompt as the first message if provided
        if system_prompt:
            input_messages.append(ModelRequest(parts=[
                SystemPromptPart(content=system_prompt)
            ]))
        
        # Process all conversation turns
        for turn in conversation_turns:
            # Handle user message
            if 'user' in turn:
                input_messages.append(ModelRequest(parts=[
                    UserPromptPart(content=turn['user'])
                ]))
            
            # Handle assistant response with potential tool calls
            assistant_parts = []
            if 'assistant' in turn:
                assistant_parts.append(TextPart(content=turn['assistant']))
            
            if 'tool_calls' in turn:
                for tool_call in turn['tool_calls']:
                    assistant_parts.append(ToolCallPart(
                        tool_name=tool_call["name"],
                        args=tool_call["args"],
                        tool_call_id=tool_call["id"]
                    ))
            
            if assistant_parts:
                input_messages.append(ModelResponse(parts=assistant_parts))
            
            # Handle tool results
            if 'tool_results' in turn:
                for tool_result in turn['tool_results']:
                    input_messages.append(ModelRequest(parts=[
                        ToolReturnPart(
                            tool_name=tool_result.get("tool_name", "unknown"),
                            tool_call_id=tool_result["call_id"],
                            content=tool_result["content"]
                        )
                    ]))
        
        # Build expected output if provided
        expected_output_messages = None
        if expected_final_response or expected_final_tool_calls:
            response_parts = []
            
            if expected_final_response:
                response_parts.append(TextPart(content=expected_final_response))
            
            if expected_final_tool_calls:
                for tool_call in expected_final_tool_calls:
                    response_parts.append(ToolCallPart(
                        tool_name=tool_call["name"],
                        args=tool_call["args"],
                        tool_call_id=tool_call["id"]
                    ))
            
            if response_parts:
                expected_output_messages = [ModelResponse(parts=response_parts)]
        
        case = MessageHistoryCase(
            name=name,
            input_messages=list(input_messages),  # Cast to List[ModelMessage]
            expected_output_messages=list(expected_output_messages) if expected_output_messages else None,
            metadata=metadata,
            description=description
        )
        
        self._cases.append(case)
        return case
    
    def create_custom_case(
        self,
        name: str,
        input_messages: List[ModelMessage],
        expected_output_messages: Optional[List[ModelMessage]] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageHistoryCase:
        """Create a case with custom message history.
        
        Args:
            name: Name of the test case
            input_messages: List of ModelMessage objects for input
            expected_output_messages: Expected output messages (optional)
            description: Description of the test case
            metadata: Additional metadata for the case
            
        Returns:
            MessageHistoryCase with custom message history
        """
        case = MessageHistoryCase(
            name=name,
            input_messages=input_messages,
            expected_output_messages=expected_output_messages,
            metadata=metadata,
            description=description
        )
        
        self._cases.append(case)
        return case
    
    def build_dataset(self, name: str = "Message History Test Dataset") -> Dataset:
        """Build a pydantic-eval Dataset from all created cases.
        
        Args:
            name: Name for the dataset
            
        Returns:
            Dataset containing all created cases
        """
        cases = [case.to_case() for case in self._cases]
        return Dataset(cases=cases, name=name)
    
    def get_cases(self) -> List[MessageHistoryCase]:
        """Get all created cases."""
        return self._cases.copy()
    
    def clear_cases(self) -> None:
        """Clear all created cases."""
        self._cases.clear()
    
    def add_batch_simple_cases(
        self,
        test_data: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> List[MessageHistoryCase]:
        """Add multiple simple cases from a list of test data.
        
        Args:
            test_data: List of dicts containing 'name', 'user_input', and optionally
                      'expected_response', 'description', 'metadata'
            system_prompt: Optional system prompt to apply to all cases
            
        Returns:
            List of created MessageHistoryCase objects
        """
        created_cases = []
        
        for data in test_data:
            case = self.create_simple_case(
                name=data['name'],
                user_input=data['user_input'],
                expected_response=data.get('expected_response'),
                system_prompt=system_prompt,
                description=data.get('description'),
                metadata=data.get('metadata')
            )
            created_cases.append(case)
        
        return created_cases


# Convenience function for quick case creation
def create_simple_case(
    name: str,
    user_input: str,
    expected_response: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> Case:
    """Convenience function to create a simple case without using the factory.
    
    Returns the pydantic-eval Case directly for immediate use.
    """
    factory = CaseFactory()
    message_case = factory.create_simple_case(
        name=name,
        user_input=user_input,
        expected_response=expected_response,
        system_prompt=system_prompt
    )
    return message_case.to_case()
