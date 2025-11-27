#!/usr/bin/env python3
"""
Pytest tests for OpenAPIToolsLoader

This module contains pytest-compatible tests for the OpenAPIToolsLoader functionality.
"""

import os
import pytest
from typing import cast

from src.lib.openapi_to_tools import OpenAPIToolsLoader, OpenAPIToolDependencies
from pydantic_ai import RunContext


@pytest.mark.anyio
async def test_openapi_tools_loader_basic():
    """Test basic OpenAPIToolsLoader functionality"""
    # Initialize the loader with basic options
    loader = OpenAPIToolsLoader(
        openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        models_filename="ally_config_api_models.py",  # Custom filename for models
        regenerate_models=False  # Set to True to regenerate existing models file
    )
    
    # Load all tools
    tools = loader.load_tools()
    
    # Assertions
    assert tools is not None, "Tools should not be None"
    assert len(tools) > 0, "Should load at least one tool"
    assert isinstance(tools, list), "Tools should be a list"
    
    # Check that we can get a specific tool (using a current operation_id from the new API)
    example_tool = loader.get_tool_by_operation_id("list_models")
    assert example_tool is not None, "Should find the list_models tool"
    assert hasattr(example_tool, 'name'), "Tool should have a name attribute"
    assert hasattr(example_tool, 'function'), "Tool should have a function attribute"


@pytest.mark.anyio
async def test_openapi_tool_execution():
    """Test that we can execute a tool function"""
    loader = OpenAPIToolsLoader(
        openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        models_filename="ally_config_api_models.py",
        regenerate_models=False
    )
    
    # Load tools without using the tools variable
    loader.load_tools()
    example_tool = loader.get_tool_by_operation_id("list_models")
    
    assert example_tool is not None, "Should find the list_models tool"
    
    # Create dependencies and mock RunContext for the new pattern
    deps = loader.create_dependencies()
    
    class MockRunContext:
        def __init__(self, dependencies):
            self.deps = dependencies
    
    ctx = cast(RunContext[OpenAPIToolDependencies], MockRunContext(deps))
    
    # Execute the tool - let it fail if auth is not available
    result = await example_tool.function(ctx)
    assert result is not None, "Tool should return a result"
    # The result might be a dict or a list depending on the endpoint
    assert isinstance(result, (dict, list)), "Result should be a dictionary or list"


def test_openapi_tools_loader_initialization():
    """Test OpenAPIToolsLoader initialization with different parameters"""
    # Test basic initialization
    loader1 = OpenAPIToolsLoader(
        openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json"
    )
    assert loader1.openapi_url == "https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json"
    assert loader1.models_filename == "api_models.py"  # default
    assert not loader1.regenerate_models  # default
    
    # Test with custom parameters
    loader2 = OpenAPIToolsLoader(
        openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        models_filename="custom_models.py",
        regenerate_models=True
    )
    assert loader2.models_filename == "custom_models.py"
    assert loader2.regenerate_models


def test_model_generation():
    """Test the model generation functionality"""
    # Test: Generate models with a custom filename
    success = OpenAPIToolsLoader.generate_api_models(
        openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        output_filename="test_models.py",
        force_regenerate=True
    )
    
    assert success, "Model generation should succeed"
    
    # Verify file was created
    assert os.path.exists("test_models.py"), "Generated models file should exist"
    
    # Clean up test file
    if os.path.exists("test_models.py"):
        os.remove("test_models.py")


def test_model_generation_existing_file():
    """Test model generation behavior with existing files"""
    # Create a dummy file
    test_filename = "dummy_models.py"
    with open(test_filename, "w") as f:
        f.write("# dummy file\n")
    
    try:
        # Test that it doesn't overwrite by default
        success = OpenAPIToolsLoader.generate_api_models(
            openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
            output_filename=test_filename,
            force_regenerate=False
        )
        assert not success, "Should not overwrite existing file when force_regenerate=False"
        
        # Test that it does overwrite when forced
        success = OpenAPIToolsLoader.generate_api_models(
            openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
            output_filename=test_filename,
            force_regenerate=True
        )
        assert success, "Should overwrite existing file when force_regenerate=True"
        
    finally:
        # Clean up
        if os.path.exists(test_filename):
            os.remove(test_filename)


@pytest.mark.anyio
async def test_custom_models_filename():
    """Test OpenAPIToolsLoader with custom models filename"""
    custom_filename = "pytest_custom_models.py"
    
    try:
        loader = OpenAPIToolsLoader(
            openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
            models_filename=custom_filename,
            regenerate_models=True
        )
        
        tools = loader.load_tools()
        
        # Verify tools were loaded
        assert tools is not None, "Tools should be loaded"
        assert len(tools) > 0, "Should have at least one tool"
        
        # Verify custom models file was created
        assert os.path.exists(custom_filename), "Custom models file should be created"
        
    finally:
        # Clean up
        if os.path.exists(custom_filename):
            os.remove(custom_filename)
