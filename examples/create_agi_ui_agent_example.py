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

    # Setup the tools first - this will trigger authentication if needed
    print("Setting up AI Knowledge tools...")
    factory.setup_ai_knowledge_tools()
    print("Setting up Ally Config tools...")
    factory.setup_ally_config_tools()

    model_config = factory.create_azure_model_config()

    agent = factory.create_hybrid_assistant(
        model=model_config,
        ai_knowledge_groups=[AIKnowledgeToolGroup.ALL],
        ally_config_groups=[AllyConfigToolGroup.ALL],
    )

    # Create dependencies for the agent
    deps = factory.create_dependencies()
    deps.auth_manager._refresh_token()
    app = agent.to_ag_ui(deps=deps)
    uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
    main()
