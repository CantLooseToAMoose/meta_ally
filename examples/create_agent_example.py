"""Example demonstrating how to create and use a hybrid assistant agent with meta_ally."""

from pydantic_ai import ModelRetry

from meta_ally.agents import AgentFactory
from meta_ally.agents.agent_presets import create_hybrid_assistant
from meta_ally.tools.tool_group_manager import (
    AIKnowledgeToolGroup,
    AllyConfigToolGroup,
)


def main():
    """Create and test a hybrid assistant agent with AI Knowledge and Ally Config tools."""
    # Create a single factory instance and reuse it
    factory = AgentFactory()

    # Create agent - tools and model config are loaded automatically!
    # No need to call setup_ai_knowledge_tools(), setup_ally_config_tools(),
    # or create_azure_model_config() manually anymore
    agent = create_hybrid_assistant(
        factory=factory,
        ai_knowledge_groups=[AIKnowledgeToolGroup.ALL],
        ally_config_groups=[AllyConfigToolGroup.ALL],
    )

    # Create a custom tool to simulate an error
    @agent.tool_plain
    def call_dev_infos():
        """
        Call some developer info endpoints.

        Raises:
            ModelRetry: Simulates an HTTP error that can be retried.
        """
        # Create mock request and response for HTTPStatusError
        raise ModelRetry("HTTP error occurred. You can try again.")

    # Create dependencies for the agent
    deps = factory.create_dependencies()

    def print_agent_message_history(agent_response):
        for msg in agent_response.all_messages():
            print(f"-- Message Type: {type(msg)} --")
            for part in msg.parts:
                print(f"{part}\n")

    print(f"Created agent: {agent}")
    print(f"Agent model: {agent.model}")
    print("Testing Agent \n" + "=" * 40)
    question = "How can you assist me with AI Knowledge and Ally Config?"
    print(f"Ask agent: {question}")
    response = agent.run_sync(question, deps=deps)
    print_agent_message_history(response)
    print("\n" + "=" * 40 + "\n")
    question = "What tools are at your disposal?"
    print(f"Ask agent: {question}")
    response = agent.run_sync(
        question, deps=deps, message_history=response.all_messages()
    )
    print_agent_message_history(response)
    print("\n" + "=" * 40 + "\n")
    question = "Can you list all available models?"
    print(f"Ask agent: {question}")
    response = agent.run_sync(question, deps=deps)
    print_agent_message_history(response)

    print("\n" + "=" * 40 + "\n")
    question = "Can you provide developer information?"
    print(f"Ask agent: {question}")
    response = agent.run_sync(question, deps=deps)
    print_agent_message_history(response)
    print("\n" + "=" * 40 + "\n")


if __name__ == "__main__":
    main()
