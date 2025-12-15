#!/usr/bin/env python3
"""
Test for verifying that OpenAPI tools have proper parameter schemas
"""

from meta_ally.lib.openapi_to_tools import OpenAPIToolsLoader


def test_tool_parameter_schemas():
    """Test that tools are created with proper parameter schemas"""
    loader = OpenAPIToolsLoader(
        openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        models_filename="ally_config_api_models.py",
        regenerate_models=False
    )

    tools = loader.load_tools()

    # Verify tools were created
    assert len(tools) > 0, "Should have created some tools"

    # Find specific tools to test
    list_copilots_tool = None
    create_copilot_tool = None
    get_copilot_config_tool = None

    for tool in tools:
        if tool.name == "list_copilots":
            list_copilots_tool = tool
        elif tool.name == "create_copilot":
            create_copilot_tool = tool
        elif tool.name == "get_copilot_config":
            get_copilot_config_tool = tool

    # Test tool with optional query parameter (GET)
    assert list_copilots_tool is not None, "Should find list_copilots tool"
    assert hasattr(list_copilots_tool, 'tool_def'), "Tool should have tool_def attribute"

    list_schema = list_copilots_tool.tool_def.parameters_json_schema
    assert list_schema['type'] == 'object', "Schema should be object type"
    assert 'properties' in list_schema, "Schema should have properties"
    # prefix parameter is optional
    if 'prefix' in list_schema['properties']:
        assert 'prefix' not in list_schema.get('required', []), "prefix should be optional"

    # Test tool with query parameter AND body (POST with mixed parameters)
    # This is the critical test case for the bug fix
    assert create_copilot_tool is not None, "Should find create_copilot tool"
    create_schema = create_copilot_tool.tool_def.parameters_json_schema
    assert create_schema['type'] == 'object', "Schema should be object type"
    assert 'properties' in create_schema, "Schema should have properties"

    # Should have endpoint as query parameter
    assert 'endpoint' in create_schema['properties'], "Should have endpoint parameter"
    assert 'endpoint' in create_schema['required'], "endpoint should be required"

    # Should have body parameters
    assert 'endpoint_attributes' in create_schema['properties'], "Should have endpoint_attributes parameter"
    assert 'endpoint_metadata' in create_schema['properties'], "Should have endpoint_metadata parameter"

    # Test tool with query parameters (GET with parameters)
    assert get_copilot_config_tool is not None, "Should find get_copilot_config tool"
    config_schema = get_copilot_config_tool.tool_def.parameters_json_schema
    assert config_schema['type'] == 'object', "Schema should be object type"
    assert 'endpoint' in config_schema['properties'], "Should have endpoint parameter"
    assert 'endpoint' in config_schema['required'], "endpoint should be required"

    print("All parameter schema tests passed!")


def test_schema_type_mappings():
    """Test that OpenAPI types are correctly mapped to JSON schema types"""
    loader = OpenAPIToolsLoader(
        openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        models_filename="ally_config_api_models.py",
        regenerate_models=False
    )

    # Mock operation to test type mappings
    operation = {
        "operationId": "test_operation",
        "parameters": [
            {
                "name": "string_param",
                "in": "query",
                "schema": {"type": "string"},
                "required": True,
                "description": "A string parameter"
            },
            {
                "name": "integer_param",
                "in": "query",
                "schema": {"type": "integer"},
                "required": False,
                "description": "An integer parameter"
            },
            {
                "name": "number_param",
                "in": "path",
                "schema": {"type": "number"},
                "required": True,
                "description": "A number parameter"
            },
            {
                "name": "boolean_param",
                "in": "query",
                "schema": {"type": "boolean"},
                "required": False,
                "description": "A boolean parameter"
            }
        ]
    }

    schema, query_param_names = loader._extract_parameters_schema(operation)

    # Check that all parameters are included
    assert 'string_param' in schema['properties']
    assert 'integer_param' in schema['properties']
    assert 'number_param' in schema['properties']
    assert 'boolean_param' in schema['properties']

    # Check types are preserved
    assert schema['properties']['string_param']['type'] == 'string'
    assert schema['properties']['integer_param']['type'] == 'integer'
    assert schema['properties']['number_param']['type'] == 'number'
    assert schema['properties']['boolean_param']['type'] == 'boolean'

    # Check required fields
    assert 'string_param' in schema['required']
    assert 'number_param' in schema['required']
    assert 'integer_param' not in schema['required']
    assert 'boolean_param' not in schema['required']

    # Check descriptions are included
    assert schema['properties']['string_param']['description'] == "A string parameter"
    assert schema['properties']['integer_param']['description'] == "An integer parameter"

    # Check query parameter tracking
    assert 'string_param' in query_param_names, "string_param should be tracked as query parameter"
    assert 'integer_param' in query_param_names, "integer_param should be tracked as query parameter"
    assert 'boolean_param' in query_param_names, "boolean_param should be tracked as query parameter"
    assert 'number_param' not in query_param_names, "number_param is a path parameter, not query"

    print("Type mapping tests passed!")


def test_query_and_body_parameter_separation():
    """Test that query parameters and body parameters are correctly separated"""
    loader = OpenAPIToolsLoader(
        openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        models_filename="ally_config_api_models.py",
        regenerate_models=False
    )

    # Mock operation with both query parameters and request body
    # This simulates the create_copilot endpoint structure
    operation = {
        "operationId": "create_test_endpoint",
        "parameters": [
            {
                "name": "endpoint",
                "in": "query",
                "schema": {"type": "string"},
                "required": True,
                "description": "The endpoint identifier"
            }
        ],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["name"]
                    }
                }
            }
        }
    }

    schema, query_param_names = loader._extract_parameters_schema(operation)

    # Check that both query and body parameters are in the schema
    assert 'endpoint' in schema['properties'], "Query parameter should be in schema"
    assert 'name' in schema['properties'], "Body parameter should be in schema"
    assert 'description' in schema['properties'], "Body parameter should be in schema"

    # Check required fields
    assert 'endpoint' in schema['required'], "Query parameter should be required"
    assert 'name' in schema['required'], "Body parameter should be required"
    assert 'description' not in schema['required'], "Optional body parameter should not be required"

    # Check that only query parameters are tracked
    assert 'endpoint' in query_param_names, "endpoint should be tracked as query parameter"
    assert 'name' not in query_param_names, "name should NOT be tracked as query parameter (it's in body)"
    assert 'description' not in query_param_names, "description should NOT be tracked as query parameter (it's in body)"

    print("Query and body parameter separation tests passed!")


if __name__ == "__main__":
    test_tool_parameter_schemas()
    test_schema_type_mappings()
    test_query_and_body_parameter_separation()
    print("All tests passed!")
