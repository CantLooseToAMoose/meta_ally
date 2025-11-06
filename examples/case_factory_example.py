"""Example usage of the refactored CaseFactory with ConversationTurns for testing a meta agent that creates copilots."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.eval.case_factory import CaseFactory

def example_meta_agent_with_conversation_turns():
    """Demonstrate test cases using the new ConversationTurns approach for a meta agent that creates copilots."""
    
    factory = CaseFactory()
    
    # Test case 1: Simple copilot creation request
    factory.create_simple_case(
        name="Simple Copilot Creation",
        user_input="Create a customer support copilot for handling billing inquiries",
        expected_response="I'll create a customer support copilot specialized in billing inquiries. Let me set up the configuration and knowledge base for you.",
        description="Test basic copilot creation request",
        metadata={"category": "copilot_creation", "complexity": "simple"}
    )
    
    # Test case 2: Copilot creation with tool usage - using new ConversationTurns approach
    conversation = factory.create_conversation_turns()
    
    # Build the conversation step by step
    conversation.add_user_message("I need a technical documentation copilot for our API guides")
    conversation.add_model_message("I'll create a technical documentation copilot for you. First, let me check what collections are available and then set up the configuration.")
    
    # Add tool call and response
    conversation.add_tool_call(
        tool_call_id="list_collections_1", 
        tool_name="list_collections", 
        args={}
    )
    conversation.add_tool_response(
        tool_call_id="list_collections_1", 
        tool_name="list_collections", 
        content="Available collections: api-docs, user-guides, troubleshooting"
    )
    
    # Continue the conversation
    conversation.add_model_message("Great! I found an 'api-docs' collection that would be perfect. Now let me create an endpoint configuration for your copilot.")
    
    # Add another tool call with complex arguments
    conversation.add_tool_call(
        tool_call_id="create_endpoint_1", 
        tool_name="create_endpoint", 
        args={
            "endpoint": "tech-docs-copilot", 
            "endpoint_attributes": {
                "dep_name": "gpt-4o", 
                "instructions": "You are a technical documentation assistant", 
                "default_message": "How can I help you with our API documentation?"
            }
        }
    )
    conversation.add_tool_response(
        tool_call_id="create_endpoint_1", 
        tool_name="create_endpoint", 
        content="Endpoint 'tech-docs-copilot' created successfully"
    )
    
    # Create the test case from the conversation
    factory.create_conversation_case(
        name="Copilot Creation with Knowledge Setup",
        conversation_turns=conversation,
        expected_final_response="Perfect! I've successfully created your technical documentation copilot with access to the API documentation collection. The copilot is now available at the 'tech-docs-copilot' endpoint.",
        description="Test copilot creation with knowledge base setup and endpoint configuration"
    )
    
    # Test case 3: Complex multi-step conversation with multiple tool calls
    conversation2 = factory.create_conversation_turns()
    
    # Initial request
    conversation2.add_user_message("Deploy an enterprise sales copilot with access to product specs, pricing, and customer data")
    conversation2.add_model_message("I'll deploy a comprehensive enterprise sales copilot. This requires setting up multiple knowledge sources, configuring permissions, and creating evaluation metrics.")
    
    # Multiple tool calls need to be done sequentially, one per model response
    conversation2.add_tool_call(
        tool_call_id="check_models_1", 
        tool_name="get_available_AI_models", 
        args={}
    )
    conversation2.add_tool_response(
        tool_call_id="check_models_1", 
        tool_name="get_available_AI_models", 
        content="Available models: gpt-4o, gpt-4-turbo, claude-3-opus"
    )
    
    # Second tool call in a separate model response
    conversation2.add_model_message("Now let me check the available collections.")
    conversation2.add_tool_call(
        tool_call_id="list_collections_2", 
        tool_name="list_collections", 
        args={}
    )
    conversation2.add_tool_response(
        tool_call_id="list_collections_2", 
        tool_name="list_collections", 
        content="Collections: product-specs, pricing-data, customer-profiles"
    )
    
    # Continue with more complex operations
    conversation2.add_model_message("Excellent! I have all the required resources. Let me create the endpoint with enterprise-grade configuration.")
    
    # First tool call for endpoint creation
    conversation2.add_tool_call(
        tool_call_id="create_endpoint_2", 
        tool_name="create_endpoint", 
        args={
            "endpoint": "enterprise-sales-copilot", 
            "endpoint_attributes": {
                "dep_name": "gpt-4o", 
                "instructions": "You are an enterprise sales assistant with access to product specifications, pricing information, and customer profiles. Provide accurate, professional sales support.", 
                "default_message": "Hello! I'm your sales assistant. How can I help you with product information, pricing, or customer insights?"
            }
        }
    )
    conversation2.add_tool_response(
        tool_call_id="create_endpoint_2", 
        tool_name="create_endpoint", 
        content="Enterprise sales copilot endpoint created successfully"
    )
    
    # Second tool call for permissions in a separate model response
    conversation2.add_model_message("Now let me set up the proper permissions for the sales team.")
    conversation2.add_tool_call(
        tool_call_id="setup_permissions_1", 
        tool_name="create_permission_role_request", 
        args={
            "resource_name": "enterprise-sales-copilot", 
            "role": "sales-team", 
            "permissions": ["read", "query"]
        }
    )
    conversation2.add_tool_response(
        tool_call_id="setup_permissions_1", 
        tool_name="create_permission_role_request", 
        content="Permissions configured for sales team access"
    )
    
    # Final user interaction
    conversation2.add_user_message("Can you also set up evaluation metrics to monitor performance?")
    
    # Create the test case
    factory.create_conversation_case(
        name="Enterprise Copilot Deployment",
        conversation_turns=conversation2,
        expected_final_response="Absolutely! I'll set up comprehensive evaluation metrics for your enterprise sales copilot to monitor response quality, accuracy, and customer satisfaction.",
        expected_final_tool_calls=[
            {"id": "create_eval_1", "name": "create_evaluation_suite", "args": {"suite_name": "enterprise-sales-eval", "endpoint": "enterprise-sales-copilot", "test_cases": ["accuracy", "helpfulness", "sales_effectiveness"]}}
        ],
        description="Test complex enterprise copilot deployment with permissions and evaluation setup",
        metadata={"category": "enterprise_deployment", "complexity": "high", "tools_used": ["ally_config", "ai_knowledge", "permissions", "evaluations"]}
    )
    
    # Test case 4: Validation example
    conversation3 = factory.create_conversation_turns()
    
    # Try to create an invalid conversation (doesn't start with user message)
    conversation3.add_model_message("I'll start the conversation incorrectly")
    
    # Validation will catch this error
    try:
        factory.create_conversation_case(
            name="Invalid Conversation Test",
            conversation_turns=conversation3,
            description="This should fail validation"
        )
    except ValueError as e:
        print(f"Validation caught error as expected: {e}")
    
    # Build the dataset
    dataset = factory.build_dataset("Meta Agent Copilot Creation Test Suite (Updated)")
    
    print(f"Created meta agent test dataset with {len(dataset.cases)} test cases:")
    for case in dataset.cases:
        print(f"  - {case.name}")
    
    return dataset

def example_conversation_validation():
    """Demonstrate conversation validation features."""
    
    factory = CaseFactory()
    
    # Example 1: Valid conversation
    valid_conversation = factory.create_conversation_turns()
    valid_conversation.add_user_message("Hello")
    valid_conversation.add_model_message("Hi there!")
    valid_conversation.add_user_message("How are you?")
    
    errors = valid_conversation.validate()
    print(f"Valid conversation errors: {errors}")  # Should be empty
    
    # Example 2: Invalid conversation - doesn't end with user request
    invalid_conversation = factory.create_conversation_turns()
    invalid_conversation.add_user_message("Hello")
    invalid_conversation.add_model_message("Hi there!")
    # Missing final user message
    
    errors = invalid_conversation.validate()
    print(f"Invalid conversation errors: {errors}")  # Should show validation error
    
    # Example 3: Tool call without response
    incomplete_conversation = factory.create_conversation_turns()
    incomplete_conversation.add_user_message("Search for something")
    incomplete_conversation.add_tool_call("call_1", "search_tool", {"query": "test"})
    # Missing tool response
    
    errors = incomplete_conversation.validate()
    print(f"Incomplete conversation errors: {errors}")  # Should show tool call error


if __name__ == "__main__":
    # Run the updated examples
    dataset = example_meta_agent_with_conversation_turns()
    
    # Demonstrate validation
    print("\n--- Validation Examples ---")
    example_conversation_validation()
