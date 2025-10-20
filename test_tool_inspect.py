#!/usr/bin/env python3
"""
Quick script to inspect how tools are currently being created.
"""

import asyncio
from lib.openapi_to_tools import OpenAPIToolsLoader

async def main():
    # Initialize the loader
    loader = OpenAPIToolsLoader(
        openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        keycloak_url="https://keycloak.acc.iam-services.aws.inform-cloud.io/",
        realm_name="inform-ai",
        client_id="ally-portal-frontend-dev",
        models_filename="ally_config_api_models.py",
        regenerate_models=False
    )
    
    # Load tools
    tools = loader.load_tools()
    
    # Inspect the first few tools
    for i, tool in enumerate(tools[:3]):
        print(f"\n=== Tool {i+1}: {tool.name} ===")
        print(f"Function: {tool.function}")
        print(f"Description: {tool.description}")
        
        # Get the function and inspect its signature
        import inspect
        sig = inspect.signature(tool.function)
        print(f"Function signature: {sig}")
        
        # Check if there's parameter schema information
        if hasattr(tool.function, '__annotations__'):
            print(f"Function annotations: {tool.function.__annotations__}")
        
        # Check internal tool properties
        print(f"Tool dir: {[attr for attr in dir(tool) if not attr.startswith('_')]}")
        
        # Check the tool_def property
        if hasattr(tool, 'tool_def'):
            tool_def = tool.tool_def
            print(f"Tool def: {tool_def}")
            if hasattr(tool_def, 'parameters_json_schema'):
                print(f"Tool def parameters_json_schema: {tool_def.parameters_json_schema}")
        
        # Try to access the schema through various attributes
        for attr in ['parameters_json_schema', '_json_schema', 'json_schema', 'schema']:
            if hasattr(tool, attr):
                print(f"Tool {attr}: {getattr(tool, attr)}")
        
        # Check if it's using from_schema
        if hasattr(tool, '_json_schema'):
            print(f"JSON Schema found: {tool._json_schema}")
        elif hasattr(tool, 'parameters_json_schema'):
            print(f"Parameters JSON Schema: {tool.parameters_json_schema}")
        else:
            print("No JSON schema attributes found")

if __name__ == "__main__":
    asyncio.run(main())
