#!/usr/bin/env python3
"""
Human Approval Example for OpenAPI Tools

This example demonstrates how to enable human approval for non-read-only API operations.
Non-read-only operations (POST, PUT, DELETE) will require approval before execution.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import from src
from src.agents import AgentFactory
from src.util.tool_group_manager import AIKnowledgeToolGroup, AllyConfigToolGroup
from pydantic_ai import DeferredToolRequests, DeferredToolResults, ToolApproved, ToolDenied


def demonstrate_human_approval():
    """Demonstrates the human approval functionality"""
    
    # Create a single factory instance and reuse it
    factory = AgentFactory()

    # Setup the tools with human approval enabled for non-read-only operations
    print("Setting up AI Knowledge tools with human approval...")
    factory.setup_ai_knowledge_tools(require_human_approval=True)
    
    print("Setting up Ally Config tools with human approval...")
    factory.setup_ally_config_tools(require_human_approval=True)

    model_config = factory.create_azure_model_config()

    # Get tools with human approval enabled
    tools = factory.tool_manager.get_tools_for_groups([
        AIKnowledgeToolGroup.ALL,
        AllyConfigToolGroup.ALL
    ])

    # Create agent directly with proper output type for handling approvals
    from pydantic_ai import Agent
    agent = Agent(
        model_config.create_model(),
        deps_type=factory.tool_manager.create_dependencies().__class__,
        system_prompt="""You are a helpful assistant that can manage AI Knowledge and Ally Config APIs.
        When you need to make changes to the system, explain what you're about to do before calling the tools.
        Some operations may require human approval before proceeding.""",
        tools=tools,
        output_type=[str, DeferredToolRequests]  # Support both regular responses and approval requests
    )

    # Create dependencies for the agent
    deps = factory.create_dependencies()
    deps.auth_manager._refresh_token()

    endpoint_path="/test/clothes_advisor"

    print("Testing Agent with Human Approval Functionality\n Creating a Copilot Endpoint\n" + "=" * 50)

    #Delete endpoint if it exists from previous runs
    result = factory.tool_manager.execute_tool_safely("delete_endpoint_api_deleteEndpoint_post",endpoint=endpoint_path)
    
    # Example 1: Try to make a non-read-only operation (will require approval)
    question = f"I want to create a chatbot that helps me decide what to wear. Can you create an Endpoint for me?" \
    f"The Endpoint name should be \"{endpoint_path}\". I want to use \"gpt-4.1-nano\" as a model and you should figure the rest out yourself."
    print(f"Ask agent: {question}")
    
    # Initial run - this should result in DeferredToolRequests
    result = agent.run_sync(question, deps=deps)
    
    # Check if we got deferred tool requests (requiring approval)
    if isinstance(result.output, DeferredToolRequests):
        print("\n✋ Tool approval required!")
        print(f"Number of tools requiring approval: {len(result.output.approvals)}")
        
        # Show what tools need approval
        for approval_request in result.output.approvals:
            print(f"- Tool: {approval_request.tool_name}")
            print(f"  Arguments: {approval_request.args}")
            print(f"  Call ID: {approval_request.tool_call_id}")
        
        # Simulate user approval process
        print("\n🤔 Simulating user approval process...")
        approvals = {}
        
        for approval_request in result.output.approvals:
            # For this demo, we'll approve endpoint creation but deny other operations
            if "create" in approval_request.tool_name.lower() and "create_endpoint" in approval_request.tool_name.lower():
                approvals[approval_request.tool_call_id] = ToolApproved()
                print(f"✅ Approved: {approval_request.tool_name}")
            else:
                approvals[approval_request.tool_call_id] = ToolDenied("Operation not approved by user")
                print(f"❌ Denied: {approval_request.tool_name}")
        
        # Continue the agent run with approvals
        deferred_results = DeferredToolResults(approvals=approvals)
        
        print("\n🔄 Continuing with user approvals...")
        final_result = agent.run_sync(
            message_history=result.all_messages(),
            deferred_tool_results=deferred_results,
            deps=deps
        )
        
        print("\n✅ Final Result:")
        print(final_result.output)
        
    else:
        print(f"✅ No approval required. Result: {result.output}")
    
    print("\n" + "=" * 50)
    
    # Example 2: Try a read-only operation (should not require approval)
    question2 = "List all available collections"
    print(f"\nAsk agent: {question2}")
    
    result2 = agent.run_sync(question2, deps=deps)
    
    if isinstance(result2.output, DeferredToolRequests):
        print("⚠️ Unexpected: Read-only operation required approval")
    else:
        print("✅ Read-only operation executed without approval")
        print(f"Result: {result2.output}")


def main():
    """Main function"""
    try:
        demonstrate_human_approval()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Note: This example requires proper authentication and API access.")


if __name__ == "__main__":
    main()
