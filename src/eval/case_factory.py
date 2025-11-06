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


class ConversationTurns:
    """A class for building conversation turns with proper validation."""
    
    def __init__(self):
        """Initialize conversation turns with optional system prompt.
        
        Args:
            system_prompt: Optional system prompt to include at the start
        """
        self._messages: List[ModelMessage] = []
        self._current_turn_parts: List[Any] = []
        self._pending_tool_calls: List[Dict[str, Any]] = []
        
    
    def add_user_message(self, content: str) -> 'ConversationTurns':
        """Add a user message to the conversation.
        
        Args:
            content: The user message content
            
        Returns:
            Self for method chaining
        """
        self._finish_current_turn()
        self._current_turn_parts = [UserPromptPart(content=content)]
        return self
    
    def add_model_message(self, content: str) -> 'ConversationTurns':
        """Add a model response message to the conversation.
        
        Args:
            content: The model response content
            
        Returns:
            Self for method chaining
        """
        self._finish_current_turn()
        self._current_turn_parts = [TextPart(content=content)]
        return self
    
    def add_tool_call(self, tool_call_id: str, tool_name: str, args: Dict[str, Any]) -> 'ConversationTurns':
        """Add a tool call to the current model response.
        
        Note: Only one tool call is allowed per model response. If you need multiple tool calls,
        add them in separate model responses with intermediate tool responses.
        
        Args:
            tool_call_id: Unique ID for the tool call
            tool_name: Name of the tool being called
            args: Arguments for the tool call
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If attempting to add multiple tool calls to the same response
        """
        # Check if we already have a tool call in the current turn
        if (self._current_turn_parts and 
            any(isinstance(part, ToolCallPart) for part in self._current_turn_parts)):
            raise ValueError("Only one tool call is allowed per model response. "
                           "Add tool response first, then start a new model response for additional tool calls.")
        
        # If we don't have current parts, or they contain user/system/tool return parts,
        # we need to start a new model response turn
        if (not self._current_turn_parts or 
            any(isinstance(part, (UserPromptPart, SystemPromptPart, ToolReturnPart)) 
                for part in self._current_turn_parts)):
            self._finish_current_turn()
            self._current_turn_parts = []
        
        self._current_turn_parts.append(ToolCallPart(
            tool_name=tool_name,
            args=args,
            tool_call_id=tool_call_id
        ))
        
        # Track pending tool call for validation
        self._pending_tool_calls.append({
            "id": tool_call_id,
            "name": tool_name,
            "args": args
        })
        
        return self
    
    def add_tool_response(self, tool_call_id: str, tool_name: str, content: str) -> 'ConversationTurns':
        """Add a tool response to the conversation.
        
        Args:
            tool_call_id: ID of the tool call this response corresponds to
            tool_name: Name of the tool that was called
            content: The response content from the tool
            
        Returns:
            Self for method chaining
        """
        self._finish_current_turn()
        
        # Remove from pending tool calls
        self._pending_tool_calls = [
            call for call in self._pending_tool_calls 
            if call["id"] != tool_call_id
        ]
        
        self._current_turn_parts = [ToolReturnPart(
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            content=content
        )]
        return self
    
    def _finish_current_turn(self) -> None:
        """Finish the current turn by creating appropriate message."""
        if not self._current_turn_parts:
            return
        
        # Determine if this should be a ModelRequest or ModelResponse
        if any(isinstance(part, (UserPromptPart, SystemPromptPart, ToolReturnPart)) 
               for part in self._current_turn_parts):
            self._messages.append(ModelRequest(parts=self._current_turn_parts))
        else:
            # Must be model response parts (TextPart, ToolCallPart)
            self._messages.append(ModelResponse(parts=self._current_turn_parts))
        
        self._current_turn_parts = []
    
    def validate(self) -> List[str]:
        """Validate the conversation structure.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        # Finish any pending turn
        self._finish_current_turn()
        
        errors = []
        
        if not self._messages:
            errors.append("Conversation must have at least one message")
            return errors
        
        # Check if there are pending tool calls without responses
        if self._pending_tool_calls:
            tool_ids = [call["id"] for call in self._pending_tool_calls]
            errors.append(f"Tool calls without responses: {tool_ids}")
        
        # Check that conversation starts with ModelRequest
        if not isinstance(self._messages[0], ModelRequest):
            errors.append("Conversation must start with a ModelRequest")
        
        # Check that conversation ends with ModelRequest
        if not isinstance(self._messages[-1], ModelRequest):
            errors.append("Conversation must end with a ModelRequest")
        
        # Check alternating pattern and single tool call constraint
        for i in range(1, len(self._messages)):
            current = self._messages[i]
            previous = self._messages[i-1]
            
            # Check for multiple tool calls in single response
            if isinstance(current, ModelResponse):
                tool_call_parts = [part for part in current.parts if isinstance(part, ToolCallPart)]
                if len(tool_call_parts) > 1:
                    tool_names = [part.tool_name for part in tool_call_parts]
                    errors.append(f"Message {i+1}: Multiple tool calls in single response: {tool_names}. Only one tool call per response is allowed.")
            
            if isinstance(current, ModelRequest) and isinstance(previous, ModelRequest):
                # Two consecutive ModelRequests - check if valid
                # Valid cases: System + User, User + ToolReturn, ToolReturn + User
                current_parts = current.parts
                previous_parts = previous.parts
                
                # Check for valid transitions
                valid_transition = False
                
                # System + User at start is ok
                if (i == 1 and 
                    any(isinstance(p, SystemPromptPart) for p in previous_parts) and
                    any(isinstance(p, UserPromptPart) for p in current_parts)):
                    valid_transition = True
                
                # ToolReturn followed by User is ok
                if (any(isinstance(p, ToolReturnPart) for p in previous_parts) and
                    any(isinstance(p, UserPromptPart) for p in current_parts)):
                    valid_transition = True
                
                if not valid_transition:
                    errors.append(f"Invalid transition at message {i+1}: ModelRequest -> ModelRequest")
            
            elif isinstance(current, ModelResponse) and isinstance(previous, ModelResponse):
                errors.append(f"Invalid transition at message {i+1}: ModelResponse -> ModelResponse")
        
        return errors
    
    def to_messages(self) -> List[ModelMessage]:
        """Convert to list of ModelMessage objects.
        
        Returns:
            List of ModelMessage objects representing the conversation
        """
        # Finish any pending turn
        self._finish_current_turn()
        return self._messages.copy()
    
    def get_message_count(self) -> int:
        """Get the number of messages in the conversation."""
        self._finish_current_turn()
        return len(self._messages)
    
    def preview_messages(self) -> List[str]:
        """Get a preview of the conversation messages for debugging.
        
        Returns:
            List of string representations of each message
        """
        self._finish_current_turn()
        previews = []
        for i, msg in enumerate(self._messages):
            if isinstance(msg, ModelRequest):
                parts_desc = []
                for part in msg.parts:
                    if isinstance(part, SystemPromptPart):
                        parts_desc.append(f"SystemPrompt: {part.content[:50]}...")
                    elif isinstance(part, UserPromptPart):
                        parts_desc.append(f"UserPrompt: {part.content[:50]}...")
                    elif isinstance(part, ToolReturnPart):
                        parts_desc.append(f"ToolReturn[{part.tool_name}]: {part.content[:30]}...")
                previews.append(f"{i+1}. ModelRequest({', '.join(parts_desc)})")
            elif isinstance(msg, ModelResponse):
                parts_desc = []
                for part in msg.parts:
                    if isinstance(part, TextPart):
                        parts_desc.append(f"Text: {part.content[:50]}...")
                    elif isinstance(part, ToolCallPart):
                        parts_desc.append(f"ToolCall[{part.tool_name}]")
                previews.append(f"{i+1}. ModelResponse({', '.join(parts_desc)})")
        return previews


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
        conversation_turns: ConversationTurns,
        expected_final_response: Optional[str] = None,
        expected_final_tool_calls: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageHistoryCase:
        """Create a case with multiple conversation turns, including tool calls.
        
        Args:
            name: Name of the test case
            conversation_turns: ConversationTurns object containing the conversation
            expected_final_response: Expected final response from the agent
            expected_final_tool_calls: Expected tool calls in the final response
            description: Description of the test case
            metadata: Additional metadata for the case
            
        Returns:
            MessageHistoryCase with full conversation history including tools
        """
        # Validate the conversation
        validation_errors = conversation_turns.validate()
        if validation_errors:
            raise ValueError(f"Invalid conversation turns: {'; '.join(validation_errors)}")
        
        # Get the input messages
        input_messages = conversation_turns.to_messages()
        
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
    
    def create_conversation_turns(self) -> ConversationTurns:
        """Create a new ConversationTurns object for building conversations.
        
        Args:
            system_prompt: Optional system prompt to include at the start
            
        Returns:
            ConversationTurns object for building the conversation
        """
        return ConversationTurns()

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
