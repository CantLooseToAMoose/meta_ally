from pprint import pprint
from pathlib import Path
import uvicorn
import logfire

# Now import from meta_ally
from meta_ally.agents import AgentFactory
from meta_ally.util.tool_group_manager import AIKnowledgeToolGroup, AllyConfigToolGroup


def main():
        
    logfire.configure()
    logfire.instrument_pydantic_ai()
    # Create a single factory instance and reuse it
    factory = AgentFactory()

    # Create agent - tools and model config are loaded automatically!
    agent = factory.create_hybrid_assistant(
        ai_knowledge_groups=[AIKnowledgeToolGroup.ALL],
        ally_config_groups=[AllyConfigToolGroup.ALL],
    )

    # Create dependencies for the agent
    deps = factory.create_dependencies()
    app = agent.to_ag_ui(deps=deps)
    uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
    main()
