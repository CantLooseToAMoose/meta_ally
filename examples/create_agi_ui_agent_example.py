from pprint import pprint
import sys
from pathlib import Path
import uvicorn

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import from src
from src.agents import AgentFactory
from src.util.tool_group_manager import AIKnowledgeToolGroup, AllyConfigToolGroup


def main():
    # Create a single factory instance and reuse it
    factory = AgentFactory()

    # Setup the tools first - this will trigger authentication if needed
    print("Setting up AI Knowledge tools...")
    factory.setup_ai_knowledge_tools(require_human_approval=True)
    print("Setting up Ally Config tools...")
    factory.setup_ally_config_tools(require_human_approval=True)

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
