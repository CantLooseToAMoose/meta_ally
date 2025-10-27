from pprint import pprint
import sys
from pathlib import Path

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
    factory.setup_ai_knowledge_tools()
    print("Setting up Ally Config tools...")
    factory.setup_ally_config_tools()
    
    model_config = factory.create_azure_model_config()

    agent = factory.create_hybrid_assistant(
        model=model_config,
        ai_knowledge_groups=[AIKnowledgeToolGroup.ALL],
        ally_config_groups=[AllyConfigToolGroup.ALL]
    )
    
    # Create dependencies for the agent
    deps = factory.create_dependencies()
    deps.auth_manager._refresh_token()
    
    print(f"Created agent: {agent}")
    print(f"Agent model: {agent.model}")
    # print("Testing Agent \n"+"-" * 40)
    # question = "How can you assist me with AI Knowledge and Ally Config?"
    # print(f"Ask agent: {question}")
    # response = agent.run_sync(question, deps=deps)
    # print("Agent response:")
    # pprint(response)
    # print("\n" + "=" * 40 + "\n")
    # question = "What tools are at your disposal?"
    # print(f"Ask agent: {question}")
    # response = agent.run_sync(question, deps=deps)
    # print("Agent response:")
    # pprint(response)
    # print("\n" + "=" * 40 + "\n")
    question = "Can you list all available models?"
    print(f"Ask agent: {question}")
    response = agent.run_sync(question, deps=deps)
    print("Agent response:")
    pprint(response.all_messages())




if __name__ == "__main__":
    main()
