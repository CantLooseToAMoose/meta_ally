#!/usr/bin/env python3
"""
Test for verifying that OpenAPI tools have proper parameter schemas
"""

import pytest
from lib.openapi_to_tools import OpenAPIToolsLoader


def test_tool_parameter_schemas():
    """Test that tools are created with proper parameter schemas"""
    loader = OpenAPIToolsLoader(
        openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        keycloak_url="https://keycloak.acc.iam-services.aws.inform-cloud.io/",
        realm_name="inform-ai",
        client_id="ally-portal-frontend-dev",
        models_filename="ally_config_api_models.py",
        regenerate_models=False
    )
    
    tools = loader.load_tools()
    
    # Verify tools were created
    assert len(tools) > 0, "Should have created some tools"
    
    # Find a specific tool to test
    aws_logs_tool = None
    capabilities_tool = None
    active_config_tool = None
    
    for tool in tools:
        if tool.name == "get_aws_logs_api_getAWSLogs_post":
            aws_logs_tool = tool
        elif tool.name == "get_capabilities_api_capabilities_get":
            capabilities_tool = tool
        elif tool.name == "get_active_config_api_getActiveConfig_post":
            active_config_tool = tool
    
    # Test tool with parameters (POST with request body)
    assert aws_logs_tool is not None, "Should find AWS logs tool"
    assert hasattr(aws_logs_tool, 'tool_def'), "Tool should have tool_def attribute"
    
    aws_schema = aws_logs_tool.tool_def.parameters_json_schema
    assert aws_schema['type'] == 'object', "Schema should be object type"
    assert 'properties' in aws_schema, "Schema should have properties"
    assert 'log_group' in aws_schema['properties'], "Should have log_group parameter"
    assert 'start_time' in aws_schema['properties'], "Should have start_time parameter"
    assert 'end_time' in aws_schema['properties'], "Should have end_time parameter"
    assert 'required' in aws_schema, "Schema should have required fields"
    assert 'log_group' in aws_schema['required'], "log_group should be required"
    
    # Test tool with no parameters (GET endpoint)
    assert capabilities_tool is not None, "Should find capabilities tool"
    cap_schema = capabilities_tool.tool_def.parameters_json_schema
    assert cap_schema['type'] == 'object', "Schema should be object type"
    assert len(cap_schema['properties']) == 0, "GET endpoint should have no parameters"
    assert len(cap_schema['required']) == 0, "GET endpoint should have no required parameters"
    
    # Test tool with mixed parameters (POST with both path and body parameters)
    assert active_config_tool is not None, "Should find active config tool"
    config_schema = active_config_tool.tool_def.parameters_json_schema
    assert config_schema['type'] == 'object', "Schema should be object type"
    assert 'endpoint' in config_schema['properties'], "Should have endpoint parameter"
    assert 'endpoint' in config_schema['required'], "endpoint should be required"
    
    print("All parameter schema tests passed!")


def test_schema_type_mappings():
    """Test that OpenAPI types are correctly mapped to JSON schema types"""
    loader = OpenAPIToolsLoader(
        openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        keycloak_url="https://keycloak.acc.iam-services.aws.inform-cloud.io/",
        realm_name="inform-ai",
        client_id="ally-portal-frontend-dev",
        models_filename="ally_config_api_models.py",
        regenerate_models=False
    )
    
    # Mock operation to test type mappings
    operation = {
        "operationId": "test_operation",
        "parameters": [
            {
                "name": "string_param",
                "schema": {"type": "string"},
                "required": True,
                "description": "A string parameter"
            },
            {
                "name": "integer_param", 
                "schema": {"type": "integer"},
                "required": False,
                "description": "An integer parameter"
            },
            {
                "name": "number_param",
                "schema": {"type": "number"},
                "required": True,
                "description": "A number parameter"
            },
            {
                "name": "boolean_param",
                "schema": {"type": "boolean"},
                "required": False,
                "description": "A boolean parameter"
            }
        ]
    }
    
    schema = loader._extract_parameters_schema(operation)
    
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
    
    print("Type mapping tests passed!")


if __name__ == "__main__":
    test_tool_parameter_schemas()
    test_schema_type_mappings()
    print("All tests passed!")
