"""Example script demonstrating how to create an AGI UI agent with meta_ally."""

import logfire
import uvicorn

from meta_ally.agents import AgentFactory
from meta_ally.agents.agent_presets import create_hybrid_assistant
from meta_ally.tools.tool_group_manager import (
    AIKnowledgeToolGroup,
    AllyConfigToolGroup,
)


def main():
    """Create and run a hybrid assistant agent with AGI UI interface."""
    logfire.configure()
    logfire.instrument_pydantic_ai()
    # Create a single factory instance and reuse it
    factory = AgentFactory()

    # Create agent - tools and model config are loaded automatically!
    agent = create_hybrid_assistant(
        factory=factory,
        ai_knowledge_groups=[AIKnowledgeToolGroup.ALL],
        ally_config_groups=[AllyConfigToolGroup.ALL],
    )

    # Create dependencies for the agent
    deps = factory.create_dependencies()
    app = agent.to_ag_ui(deps=deps)
    uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
    main()
