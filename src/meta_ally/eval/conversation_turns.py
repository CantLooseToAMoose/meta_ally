"""Conversation turns builder for creating structured message histories."""

from typing import Any, List, Dict, Union
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
