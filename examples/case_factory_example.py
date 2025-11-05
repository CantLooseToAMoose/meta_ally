"""Example usage of the CaseFactory for testing a meta agent that creates copilots."""

from src.eval.case_factory import CaseFactory

# Example 1: Meta Agent Copilot Creation Factory
def example_meta_agent_copilot_factory():
    """Demonstrate test cases for a meta agent that creates copilots using Ally Config and AI Knowledge APIs."""
    
    factory = CaseFactory()
    
    # Test case 1: Simple copilot creation request
    factory.create_simple_case(
        name="Simple Copilot Creation",
        user_input="Create a customer support copilot for handling billing inquiries",
        expected_response="I'll create a customer support copilot specialized in billing inquiries. Let me set up the configuration and knowledge base for you.",
        system_prompt="You are a meta agent that helps users create specialized copilots using the Ally Config API and AI Knowledge system. You can create endpoints, configure models, set up knowledge collections, and deploy copilots.",
        description="Test basic copilot creation request",
        metadata={"category": "copilot_creation", "complexity": "simple"}
    )
    
    # Test case 2: Copilot creation with tool usage
    factory.create_conversation_case(
        name="Copilot Creation with Knowledge Setup",
        conversation_turns=[
            {"user": "I need a technical documentation copilot for our API guides"},
            {"assistant": "I'll create a technical documentation copilot for you. First, let me check what collections are available and then set up the configuration."},
            {
                "tool_calls": [
                    {"id": "list_collections_1", "name": "list_collections", "args": {}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "list_collections_1", "tool_name": "list_collections", "content": "Available collections: api-docs, user-guides, troubleshooting"}
                ]
            },
            {"assistant": "Great! I found an 'api-docs' collection that would be perfect. Now let me create an endpoint configuration for your copilot."},
            {
                "tool_calls": [
                    {"id": "create_endpoint_1", "name": "create_endpoint", "args": {"endpoint": "tech-docs-copilot", "endpoint_attributes": {"dep_name": "gpt-4o", "instructions": "You are a technical documentation assistant", "default_message": "How can I help you with our API documentation?"}}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "create_endpoint_1", "tool_name": "create_endpoint", "content": "Endpoint 'tech-docs-copilot' created successfully"}
                ]
            }
        ],
        expected_final_response="Perfect! I've successfully created your technical documentation copilot with access to the API documentation collection. The copilot is now available at the 'tech-docs-copilot' endpoint.",
        system_prompt="You are a meta agent that creates specialized copilots using Ally Config and AI Knowledge APIs.",
        description="Test copilot creation with knowledge base setup and endpoint configuration"
    )
    
    # Test case 3: Complex multi-step copilot deployment
    factory.create_conversation_case(
        name="Enterprise Copilot Deployment",
        conversation_turns=[
            {"user": "Deploy an enterprise sales copilot with access to product specs, pricing, and customer data"},
            {"assistant": "I'll deploy a comprehensive enterprise sales copilot. This requires setting up multiple knowledge sources, configuring permissions, and creating evaluation metrics."},
            {
                "tool_calls": [
                    {"id": "check_models_1", "name": "get_available_AI_models", "args": {}},
                    {"id": "list_collections_2", "name": "list_collections", "args": {}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "check_models_1", "tool_name": "get_available_AI_models", "content": "Available models: gpt-4o, gpt-4-turbo, claude-3-opus"},
                    {"call_id": "list_collections_2", "tool_name": "list_collections", "content": "Collections: product-specs, pricing-data, customer-profiles"}
                ]
            },
            {"assistant": "Excellent! I have all the required resources. Let me create the endpoint with enterprise-grade configuration."},
            {
                "tool_calls": [
                    {"id": "create_endpoint_2", "name": "create_endpoint", "args": {"endpoint": "enterprise-sales-copilot", "endpoint_attributes": {"dep_name": "gpt-4o", "instructions": "You are an enterprise sales assistant with access to product specifications, pricing information, and customer profiles. Provide accurate, professional sales support.", "default_message": "Hello! I'm your sales assistant. How can I help you with product information, pricing, or customer insights?"}}},
                    {"id": "setup_permissions_1", "name": "create_permission_role_request", "args": {"resource_name": "enterprise-sales-copilot", "role": "sales-team", "permissions": ["read", "query"]}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "create_endpoint_2", "tool_name": "create_endpoint", "content": "Enterprise sales copilot endpoint created successfully"},
                    {"call_id": "setup_permissions_1", "tool_name": "create_permission_role_request", "content": "Permissions configured for sales team access"}
                ]
            },
            {"user": "Can you also set up evaluation metrics to monitor performance?"}
        ],
        expected_final_response="Absolutely! I'll set up comprehensive evaluation metrics for your enterprise sales copilot to monitor response quality, accuracy, and customer satisfaction.",
        expected_final_tool_calls=[
            {"id": "create_eval_1", "name": "create_evaluation_suite", "args": {"suite_name": "enterprise-sales-eval", "endpoint": "enterprise-sales-copilot", "test_cases": ["accuracy", "helpfulness", "sales_effectiveness"]}}
        ],
        system_prompt="You are a meta agent specialized in deploying enterprise-grade copilots with comprehensive configuration, security, and monitoring.",
        description="Test complex enterprise copilot deployment with permissions and evaluation setup",
        metadata={"category": "enterprise_deployment", "complexity": "high", "tools_used": ["ally_config", "ai_knowledge", "permissions", "evaluations"]}
    )
    
    # Test case 4: Copilot customization and optimization
    factory.create_conversation_case(
        name="Copilot Performance Optimization",
        conversation_turns=[
            {"user": "My customer service copilot is responding too slowly. Can you optimize it?"},
            {"assistant": "I'll analyze your copilot's performance and optimize its configuration. Let me check the current setup first."},
            {
                "tool_calls": [
                    {"id": "get_endpoint_1", "name": "get_endpoint_metadata", "args": {"endpoint": "customer-service-copilot"}},
                    {"id": "get_costs_1", "name": "get_cost_per_day", "args": {"endpoint": "customer-service-copilot"}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "get_endpoint_1", "tool_name": "get_endpoint_metadata", "content": "Current model: gpt-4o, average response time: 3.5s, token usage: high"},
                    {"call_id": "get_costs_1", "tool_name": "get_cost_per_day", "content": "Daily cost: $45.60, trend: increasing"}
                ]
            },
            {"assistant": "I see the issue. You're using GPT-4o which is slower and more expensive. For customer service, GPT-4-turbo would be more efficient. Let me also optimize the knowledge retrieval."},
            {
                "tool_calls": [
                    {"id": "update_config_1", "name": "update_endpoint_metadata", "args": {"endpoint": "customer-service-copilot", "metadata": {"dep_name": "gpt-4-turbo", "max_tokens": 1000, "temperature": 0.3}}},
                    {"id": "optimize_retrieval_1", "name": "update_collection_settings", "args": {"collection_id": "customer-support-kb", "retrieval_count": 5, "similarity_threshold": 0.8}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "update_config_1", "tool_name": "update_endpoint_metadata", "content": "Endpoint configuration updated to use GPT-4-turbo"},
                    {"call_id": "optimize_retrieval_1", "tool_name": "update_collection_settings", "content": "Knowledge retrieval optimized for faster responses"}
                ]
            }
        ],
        expected_final_response="Perfect! I've optimized your customer service copilot by switching to GPT-4-turbo for faster responses and tuning the knowledge retrieval settings. This should reduce response time by ~40% and costs by ~30%.",
        system_prompt="You are a meta agent that specializes in optimizing copilot performance, reducing costs, and improving response times.",
        description="Test copilot performance optimization and cost reduction",
        metadata={"category": "optimization", "focus": ["performance", "cost_reduction"], "apis_used": ["ally_config", "cost_analysis"]}
    )
    
    # Build the dataset
    dataset = factory.build_dataset("Meta Agent Copilot Creation Test Suite")
    
    print(f"Created meta agent test dataset with {len(dataset.cases)} test cases:")
    for case in dataset.cases:
        print(f"- {case.name}")
        if case.metadata:
            print(f"  Category: {case.metadata.get('category', 'N/A')}")
            if 'tools_used' in case.metadata:
                print(f"  Tools: {', '.join(case.metadata['tools_used'])}")
    
    return dataset

# Example 2: Knowledge Base Management Tests
def example_knowledge_management():
    """Test cases for knowledge base management functionality."""
    
    factory = CaseFactory()
    
    # Test knowledge source creation
    factory.create_conversation_case(
        name="Knowledge Source Setup",
        conversation_turns=[
            {"user": "Help me set up a knowledge base for our product documentation"},
            {"assistant": "I'll help you create a knowledge base for your product docs. Let me start by creating a collection and setting up a source."},
            {
                "tool_calls": [
                    {"id": "create_collection_1", "name": "create_collection", "args": {"name": "product-documentation", "description": "Product documentation knowledge base"}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "create_collection_1", "tool_name": "create_collection", "content": "Collection 'product-documentation' created successfully with ID: coll_123"}
                ]
            },
            {"assistant": "Great! Now let me set up a source for your documentation files."},
            {
                "tool_calls": [
                    {"id": "create_source_1", "name": "create_source", "args": {"collection_id": "coll_123", "source_type": "s3", "source_config": {"bucket": "docs-bucket", "prefix": "product-docs/"}}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "create_source_1", "tool_name": "create_source", "content": "S3 source created and indexing started"}
                ]
            }
        ],
        expected_final_response="Perfect! Your product documentation knowledge base is now set up. The system is indexing your S3 documents and they'll be available for search shortly.",
        system_prompt="You are a meta agent that helps users set up and manage AI knowledge bases using the AI Knowledge API.",
        description="Test knowledge base creation and source setup",
        metadata={"category": "knowledge_management", "apis_used": ["ai_knowledge"]}
    )
    
    # Test document querying and retrieval
    factory.create_conversation_case(
        name="Knowledge Retrieval Testing",
        conversation_turns=[
            {"user": "Search our product docs for information about API rate limits"},
            {
                "tool_calls": [
                    {"id": "search_docs_1", "name": "query_collection", "args": {"collection_id": "coll_123", "query": "API rate limits", "limit": 5}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "search_docs_1", "tool_name": "query_collection", "content": "Found 3 relevant documents: 1) API Reference - Rate Limiting (score: 0.95), 2) Best Practices Guide (score: 0.87), 3) Troubleshooting Common Issues (score: 0.82)"}
                ]
            },
            {"user": "Can you get the specific content from the API Reference document?"}
        ],
        expected_final_response="I'll retrieve the specific content about rate limits from the API Reference document for you.",
        expected_final_tool_calls=[
            {"id": "get_doc_1", "name": "get_document_content", "args": {"document_id": "api-reference-rate-limiting", "fragment_ids": ["rate_limits_section"]}}
        ],
        system_prompt="You are a meta agent that helps users search and retrieve information from AI knowledge bases.",
        description="Test knowledge retrieval and document content access"
    )
    
    dataset = factory.build_dataset("Knowledge Management Test Suite")
    return dataset

# Example 3: Copilot Configuration and Testing
def example_copilot_configuration():
    """Test cases for copilot configuration management."""
    
    factory = CaseFactory()
    
    # Test configuration validation
    factory.create_conversation_case(
        name="Configuration Validation",
        conversation_turns=[
            {"user": "Validate the configuration for my HR copilot before deployment"},
            {"assistant": "I'll validate your HR copilot configuration. Let me check the endpoint settings and run some tests."},
            {
                "tool_calls": [
                    {"id": "get_config_1", "name": "get_endpoint_config", "args": {"endpoint": "hr-copilot"}},
                    {"id": "validate_config_1", "name": "validate_endpoint_config", "args": {"endpoint": "hr-copilot"}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "get_config_1", "tool_name": "get_endpoint_config", "content": "Configuration loaded: model=gpt-4o, instructions=HR assistant, knowledge_sources=[hr-policies, employee-handbook]"},
                    {"call_id": "validate_config_1", "tool_name": "validate_endpoint_config", "content": "Validation passed: All required fields present, knowledge sources accessible"}
                ]
            },
            {"assistant": "Configuration looks good! Now let me run a test evaluation to ensure quality."},
            {
                "tool_calls": [
                    {"id": "run_eval_1", "name": "run_evaluation_suite", "args": {"endpoint": "hr-copilot", "suite_name": "hr-validation-tests"}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "run_eval_1", "tool_name": "run_evaluation_suite", "content": "Evaluation completed: 8/10 test cases passed, average response quality: 4.2/5"}
                ]
            }
        ],
        expected_final_response="Your HR copilot configuration is validated and ready for deployment! The evaluation shows strong performance with 8/10 test cases passing and good response quality.",
        system_prompt="You are a meta agent that validates and tests copilot configurations before deployment.",
        description="Test configuration validation and quality assessment",
        metadata={"category": "validation", "tools_used": ["ally_config", "evaluations"]}
    )
    
    dataset = factory.build_dataset("Copilot Configuration Test Suite")
    return dataset

# Example 4: Tool call test cases using conversation format
def example_tool_cases():
    """Demonstrate creating cases with tool calls and results using conversation format."""
    
    factory = CaseFactory()
    
    # Simple tool case using conversation format
    factory.create_conversation_case(
        name="Model Inventory Check",
        conversation_turns=[
            {"user": "What AI models are available for my new copilot?"},
            {
                "tool_calls": [
                    {"id": "models_1", "name": "get_available_AI_models", "args": {}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "models_1", "tool_name": "get_available_AI_models", "content": "Available models: gpt-4o (fast, general), gpt-4-turbo (balanced), claude-3-opus (analytical), claude-3-sonnet (creative)"}
                ]
            }
        ],
        expected_final_response="You have several excellent AI models available: GPT-4o for fast general tasks, GPT-4-turbo for balanced performance, Claude-3-opus for analytical work, and Claude-3-sonnet for creative tasks. Which type of copilot are you planning to create?",
        system_prompt="You are a helpful meta agent that assists with AI model selection and copilot creation."
    )
    
    # Multiple tool calls case for comprehensive copilot setup
    factory.create_conversation_case(
        name="Comprehensive Copilot Setup",
        conversation_turns=[
            {"user": "Set up a complete legal research copilot with all necessary components"},
            {
                "tool_calls": [
                    {"id": "check_caps_1", "name": "get_capabilities", "args": {}},
                    {"id": "list_colls_1", "name": "list_collections", "args": {}},
                    {"id": "check_models_1", "name": "get_available_AI_models", "args": {}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "check_caps_1", "tool_name": "get_capabilities", "content": "Capabilities: document_search, semantic_retrieval, citation_extraction, legal_analysis"},
                    {"call_id": "list_colls_1", "tool_name": "list_collections", "content": "Collections: legal-cases, statutes, regulations, legal-forms"},
                    {"call_id": "check_models_1", "tool_name": "get_available_AI_models", "content": "Models: gpt-4o, claude-3-opus (recommended for legal analysis)"}
                ]
            },
            {"assistant": "Perfect! I have all the components needed for a comprehensive legal research copilot. I'll use Claude-3-opus for its analytical capabilities and connect it to your legal knowledge bases."},
            {
                "tool_calls": [
                    {"id": "create_endpoint_1", "name": "create_endpoint", "args": {"endpoint": "legal-research-copilot", "endpoint_attributes": {"dep_name": "claude-3-opus", "instructions": "You are a legal research assistant. Provide accurate legal information with proper citations.", "default_message": "How can I assist with your legal research today?"}}},
                    {"id": "setup_permissions_1", "name": "setup_endpoint_permissions", "args": {"endpoint": "legal-research-copilot", "collections": ["legal-cases", "statutes", "regulations", "legal-forms"], "access_level": "read"}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "create_endpoint_1", "tool_name": "create_endpoint", "content": "Legal research copilot endpoint created successfully"},
                    {"call_id": "setup_permissions_1", "tool_name": "setup_endpoint_permissions", "content": "Permissions configured for access to all legal collections"}
                ]
            }
        ],
        expected_final_response="Excellent! Your legal research copilot is now fully configured with Claude-3-opus for analytical capabilities and access to all your legal knowledge bases including cases, statutes, regulations, and forms. The copilot is ready for use.",
        system_prompt="You are a meta agent specializing in setting up domain-specific copilots with appropriate model selection and knowledge base integration.",
        description="Test comprehensive copilot setup with multiple API integrations",
        metadata={"category": "full_setup", "domain": "legal", "complexity": "high"}
    )
    
    dataset = factory.build_dataset("Tool Integration Test Cases")
    
    print(f"Created tool test dataset with {len(dataset.cases)} cases:")
    for case in dataset.cases:
        print(f"- {case.name}")
        # Count tool calls in the case
        tool_calls = 0
        for msg in case.inputs:
            if hasattr(msg, 'parts'):
                for part in msg.parts:
                    if hasattr(part, 'tool_name') and hasattr(part, 'tool_call_id'):
                        tool_calls += 1
        print(f"  Tool calls: {tool_calls}")
    
    return dataset

# Example 5: Real-world conversation based on actual user interaction
def example_real_world_conversation():
    """Test case based on actual meta agent conversation for creating GB80 office accessories advisor."""
    
    factory = CaseFactory()
    
    # Test case based on real conversation: Creating an office accessories advisor
    factory.create_conversation_case(
        name="GB80 Office Accessories Advisor Creation - Real World",
        conversation_turns=[
            {"user": "who are you?"},
            {"assistant": "I am your comprehensive AI assistant. I can help you with managing knowledge bases, configuring AI models and endpoints, monitoring performance, optimizing costs, and managing permissions and access. How can I assist you today?"},
            {"user": "can you help me create an endpoint?"},
            {"assistant": "Yes, I can help you create an endpoint. To proceed, I need some details about the endpoint you want to create:\n\n1. The unique name of the endpoint (must begin with a valid scope prefix).\n2. The model deployment name to be used for the endpoint (e.g., 'gpt-4o-mini').\n3. Optional instructions for the endpoint behavior.\n4. A default message for the endpoint.\n5. Optional metadata such as a human-readable display name, description, and project number.\n\nPlease provide these details so I can assist you in creating the endpoint."},
            {"user": "I want to create a chatbot for the gb80, that can help me choose accessories in the office. please give me advice."},
            {"assistant": "To create a chatbot endpoint for the gb80 business unit that helps with choosing office accessories, here are some recommendations and steps:\n\n1. Endpoint Name: Use a name starting with the scope prefix \"gb80\". For example, \"gb80_office_accessories_bot\".\n\n2. Model Deployment: Choose a suitable language model deployment for the chatbot. For example, \"gpt-4o-mini\" is a capable model for conversational tasks.\n\n3. Instructions: Provide clear instructions to the model about the chatbot's purpose. For example, \"You are a helpful assistant that helps users choose office accessories based on their needs and preferences.\"\n\n4. Default Message: Set a welcoming default message for users when they start interacting with the chatbot. For example, \"Hello! I am here to help you choose the best office accessories. How can I assist you today?\"\n\n5. Metadata: Optionally, add a display name like \"GB80 Office Accessories Chatbot\", a description, and a project number if applicable.\n\n6. Permissions: Ensure appropriate permissions are set for users who will access this endpoint.\n\nWould you like me to proceed with creating this endpoint using these recommendations? If yes, please provide any specific instructions or default message you want to include, or I can use the examples above."},
            {"user": "yes but i think the endpoint name needs to be something like this /gb80/office_accessories_bot"},
            {"assistant": "The endpoint name should be a unique identifier starting with the scope prefix but typically does not include slashes (\"/\"). Instead, it is usually a single string like \"gb80_office_accessories_bot\" without slashes.\n\nIf you want the endpoint to be recognized as part of the gb80 scope, the prefix \"gb80\" at the start of the name is sufficient.\n\nSo, the recommended endpoint name would be: gb80_office_accessories_bot\n\nWould you like me to create the endpoint with this name and the example instructions and default message I provided earlier? Or do you want to customize the instructions and default message?"},
            {"user": "no i want you to think of something. dont rely on the defaults"},
            {"assistant": "Understood. Here's a tailored suggestion for your chatbot endpoint:\n\nEndpoint Name: gb80_office_accessory_advisor\n\nInstructions for the chatbot:\n\"You are an expert office accessories advisor for the GB80 business unit. Your role is to assist users in selecting the most suitable office accessories based on their specific needs, preferences, and office environment. Provide clear, concise, and helpful recommendations, considering factors like ergonomics, functionality, and style. Always maintain a friendly and professional tone.\"\n\nDefault Message:\n\"Welcome to the GB80 Office Accessory Advisor! I'm here to help you find the perfect office accessories to enhance your workspace. What kind of accessories are you interested in today?\"\n\nMetadata:\nDisplay Name: GB80 Office Accessory Advisor\nDescription: A chatbot designed to help GB80 employees choose the best office accessories tailored to their needs.\nProject Number: (If you have a project number, please provide it; otherwise, I can leave it blank or use a default.)\n\nWould you like me to proceed with creating this endpoint using these details? If you want to provide a project number or any other customization, please let me know."},
            {"user": "yes"},
            {
                "tool_calls": [
                    {"id": "call_HdlOFhK8xqVpGePriWsyCN3s", "name": "create_endpoint_api_createEndpoint_post", "args": {"endpoint": "gb80_office_accessory_advisor", "endpoint_attributes": {"dep_name": "gpt-4o-mini", "instructions": "You are an expert office accessories advisor for the GB80 business unit. Your role is to assist users in selecting the most suitable office accessories based on their specific needs, preferences, and office environment. Provide clear, concise, and helpful recommendations, considering factors like ergonomics, functionality, and style. Always maintain a friendly and professional tone.", "default_message": "Welcome to the GB80 Office Accessory Advisor! I'm here to help you find the perfect office accessories to enhance your workspace. What kind of accessories are you interested in today?"}, "endpoint_metadata": {"display_name": "GB80 Office Accessory Advisor", "description": "A chatbot designed to help GB80 employees choose the best office accessories tailored to their needs."}}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "call_HdlOFhK8xqVpGePriWsyCN3s", "tool_name": "create_endpoint_api_createEndpoint_post", "content": "{\"success\":false,\"error_msg\":\"Endpoint name 'gb80_office_accessory_advisor' is not valid\"}"}
                ]
            },
            {"assistant": "The endpoint name \"gb80_office_accessory_advisor\" is not valid. It seems the naming convention requires a different format.\n\nCould you please confirm if the endpoint name should include slashes like \"/gb80/office_accessories_bot\" or if there are any specific rules for the endpoint name format? This will help me create the endpoint correctly."},
            {"user": "it should include slashes like i showed you"},
            {"assistant": "Thank you for the clarification. The endpoint name should include slashes, for example: /gb80/office_accessories_bot.\n\nI will proceed to create the endpoint with the name \"/gb80/office_accessory_advisor\" and the previously suggested instructions and default message."},
            {
                "tool_calls": [
                    {"id": "call_YLXyi6cXzDbDfvVDLtOyS70Y", "name": "create_endpoint_api_createEndpoint_post", "args": {"endpoint": "/gb80/office_accessory_advisor", "endpoint_attributes": {"dep_name": "gpt-4o-mini", "instructions": "You are an expert office accessories advisor for the GB80 business unit. Your role is to assist users in selecting the most suitable office accessories based on their specific needs, preferences, and office environment. Provide clear, concise, and helpful recommendations, considering factors like ergonomics, functionality, and style. Always maintain a friendly and professional tone.", "default_message": "Welcome to the GB80 Office Accessory Advisor! I'm here to help you find the perfect office accessories to enhance your workspace. What kind of accessories are you interested in today?"}, "endpoint_metadata": {"display_name": "GB80 Office Accessory Advisor", "description": "A chatbot designed to help GB80 employees choose the best office accessories tailored to their needs."}}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "call_YLXyi6cXzDbDfvVDLtOyS70Y", "tool_name": "create_endpoint_api_createEndpoint_post", "content": "{\"success\":false,\"error_msg\":\"Model gpt-4o-mini is not available\"}"}
                ]
            },
            {"assistant": "The model \"gpt-4o-mini\" is currently not available for use. I can help you select an available model for the endpoint.\n\nLet me check the list of available AI models for you."},
            {
                "tool_calls": [
                    {"id": "call_HonkXkOuhugoWneDnUPX5wGF", "name": "get_available_AI_models_api_getAvailableAIModels_post", "args": {}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "call_HonkXkOuhugoWneDnUPX5wGF", "tool_name": "get_available_AI_models_api_getAvailableAIModels_post", "content": "{\"success\":true,\"error_msg\":null,\"data\":[{\"label\":\"gpt-4o-latest\",\"name\":\"ChatGPT 4o\",\"description\":\"ChatGPT 4o (€€€€€)\",\"enabled\":true},{\"label\":\"gpt-4.1-nano\",\"name\":\"GPT 4.1 nano\",\"description\":\"GPT 4.1 nano (€)\",\"enabled\":true},{\"label\":\"gpt-4.1-mini\",\"name\":\"GPT 4.1 mini\",\"description\":\"GPT 4.1 mini (€€)\",\"enabled\":true},{\"label\":\"claude-4-sonnet\",\"name\":\"Claude 4 Sonnet\",\"description\":\"Claude 4 Sonnet (€€€€€)\",\"enabled\":true}]}"}
                ]
            },
            {"assistant": "The following AI models are available for creating your endpoint:\n\n- gpt-4o-latest (ChatGPT 4o)\n- gpt-4.1-nano (GPT 4.1 nano)\n- gpt-4.1-mini (GPT 4.1 mini)\n- claude-4-sonnet (Claude 4 Sonnet)\n\nWhich model would you like to use for your GB80 office accessory advisor chatbot? If you want, I can recommend one based on your needs."},
            {"user": "recommend one"},
            {"assistant": "For your GB80 office accessory advisor chatbot, I recommend using the \"gpt-4o-latest\" model. It is a powerful and versatile model suitable for conversational tasks, providing high-quality responses with good understanding and generation capabilities.\n\nWould you like me to proceed with creating the endpoint using the \"gpt-4o-latest\" model?"},
            {"user": "yes"},
            {
                "tool_calls": [
                    {"id": "call_ZDfL7idHhRSCbzAIhpX2NpCw", "name": "create_endpoint_api_createEndpoint_post", "args": {"endpoint": "/gb80/office_accessory_advisor", "endpoint_attributes": {"dep_name": "gpt-4o-latest", "instructions": "You are an expert office accessories advisor for the GB80 business unit. Your role is to assist users in selecting the most suitable office accessories based on their specific needs, preferences, and office environment. Provide clear, concise, and helpful recommendations, considering factors like ergonomics, functionality, and style. Always maintain a friendly and professional tone.", "default_message": "Welcome to the GB80 Office Accessory Advisor! I'm here to help you find the perfect office accessories to enhance your workspace. What kind of accessories are you interested in today?"}, "endpoint_metadata": {"display_name": "GB80 Office Accessory Advisor", "description": "A chatbot designed to help GB80 employees choose the best office accessories tailored to their needs."}}}
                ]
            },
            {
                "tool_results": [
                    {"call_id": "call_ZDfL7idHhRSCbzAIhpX2NpCw", "tool_name": "create_endpoint_api_createEndpoint_post", "content": "{\"success\":true,\"error_msg\":null,\"data\":null}"}
                ]
            }
        ],
        expected_final_response="The endpoint \"/gb80/office_accessory_advisor\" has been successfully created using the \"gpt-4o-latest\" model. It is configured to assist GB80 employees in choosing the best office accessories tailored to their needs.\n\nIf you need any further assistance with configuring, managing, or using this endpoint, please let me know!",
        system_prompt="You are a comprehensive AI assistant that helps with managing knowledge bases, configuring AI models and endpoints, monitoring performance, optimizing costs, and managing permissions and access. You provide detailed guidance and execute API calls to create and configure endpoints based on user requirements.",
        description="Real-world test case based on actual user interaction: Creating a domain-specific chatbot endpoint with error handling, model selection, and successful completion",
        metadata={
            "category": "real_world_endpoint_creation", 
            "complexity": "high", 
            "domain": "office_accessories", 
            "business_unit": "gb80", 
            "error_recovery": True,
            "conversation_length": "long",
            "tool_calls": 4,
            "errors_handled": 2,
            "final_success": True
        }
    )
    
    dataset = factory.build_dataset("Real World Meta Agent Conversation")
    
    print(f"Created real-world conversation dataset with {len(dataset.cases)} cases:")
    for case in dataset.cases:
        print(f"- {case.name}")
        # Count conversation turns and tool calls
        turn_count = len(case.inputs) if hasattr(case, 'inputs') else 0
        tool_calls = 0
        tool_errors = 0
        for msg in case.inputs:
            if hasattr(msg, 'parts'):
                for part in msg.parts:
                    if hasattr(part, 'tool_name') and hasattr(part, 'tool_call_id'):
                        tool_calls += 1
                    elif hasattr(part, 'content') and 'error_msg' in str(part.content):
                        tool_errors += 1
        print(f"  Conversation turns: {turn_count}, Tool calls: {tool_calls}, Tool errors handled: {tool_errors}")
    
    return dataset

if __name__ == "__main__":
    print("=== Example 1: Meta Agent Copilot Factory ===")
    dataset1 = example_meta_agent_copilot_factory()
    print()
    
    print("=== Example 2: Knowledge Management ===")
    dataset2 = example_knowledge_management()
    print()
    
    print("=== Example 3: Copilot Configuration ===")
    dataset3 = example_copilot_configuration()
    print()
    
    print("=== Example 4: Tool Call Cases ===")
    dataset4 = example_tool_cases()
    print()
    
    print("=== Example 5: Real World Conversation ===")
    dataset5 = example_real_world_conversation()
    print()
    
    print("Done! You now have test cases ready for evaluation with pydantic-eval.")
    print("These examples demonstrate creating copilots, managing knowledge bases,")
    print("validating configurations, testing tool integrations, and real-world scenarios.")
