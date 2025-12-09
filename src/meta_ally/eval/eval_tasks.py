"""Different evaluation tasks for language models."""

from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, UserPromptPart
from typing import List, Any, Callable
from .conversation_turns import ModelMessage


def create_agent_conversation_task(agent: Agent[Any,Any], deps: Any) -> Callable:
    """Create an evaluation task where the agent must handle a conversation."""

    def run_agent_conversation(
        input_messages: List[ModelMessage],
    ) -> List[ModelMessage]:
        """Run the agent through a conversation and return the message history."""
        # Create a copy to avoid mutating the original input_messages
        messages_copy = input_messages.copy()
        
        # Pop last message from input messages to kick off agent
        last_message = messages_copy.pop()
        
        # Extract user prompt text from the last message
        user_prompt = None
        if isinstance(last_message, ModelRequest):
            for part in last_message.parts:
                if isinstance(part, UserPromptPart):
                    user_prompt = part.content
                    break
        
        response = agent.run_sync(user_prompt, deps=deps, message_history=messages_copy)
        
        # Remove the first message (the user prompt we just sent) from new_messages
        # since it's already in the input_messages
        new_messages = response.new_messages()
        if new_messages:
            new_messages = new_messages[1:]  # Skip the first message
        
        return new_messages

    return run_agent_conversation
