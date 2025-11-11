"""Different evaluation tasks for language models."""

from pydantic_ai import Agent, RunContext
from typing import List, Any, Callable
from .conversation_turns import ModelMessage


def create_agent_conversation_task(agent: Agent[Any,Any], deps: Any) -> Callable:
    """Create an evaluation task where the agent must handle a conversation."""

    def run_agent_conversation(
        input_messages: List[ModelMessage],
    ) -> List[ModelMessage]:
        """Run the agent through a conversation and return the message history."""
        response = agent.run_sync(None, deps=deps, message_history=input_messages)
        return response.new_messages()

    return run_agent_conversation
