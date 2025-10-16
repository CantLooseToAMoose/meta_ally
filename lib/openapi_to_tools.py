"""
Dynamic OpenAPI to Pydantic AI Tools Converter

This module fetches an OpenAPI specification from a URL and dynamically converts
its operations into pydantic-ai Tool objects that can be used with agents.

Key Features:
- Automatically fetches and parses OpenAPI specs from URLs
- Converts all operations (GET, POST, PUT, DELETE) into pydantic-ai Tools
- Handles path parameters with automatic substitution
- Normalizes model names from OpenAPI format to Python class names
- Supports existing Pydantic models for request validation
- All operations are async by default

Example:
    loader = OpenAPIToolsLoader(
        openapi_url="https://api.example.com/openapi.json"
    )
    tools = loader.load_tools()
    agent = Agent('openai:gpt-4', tools=tools)
"""

import httpx
import json
from typing import Any, Dict, List, Optional, Callable, cast
from pydantic_ai import Tool, RunContext
from pydantic import BaseModel, Field, create_model
import importlib
import sys
import inspect
from auth_manager import AuthManager

# We'll dynamically import models as needed to avoid import errors
# from ally_config_api_models import *


class OpenAPIToolsLoader:
    """Loads OpenAPI operations and converts them into pydantic-ai Tools"""
    
    def __init__(
        self, 
        openapi_url: str, 
        base_url: Optional[str] = None,
        auth_manager: Optional[AuthManager] = None,
        keycloak_url: str = "https://keycloak.prod.iam-services.aws.inform-cloud.io/",
        realm_name: str = "inform-ai",
        client_id: str = "ally-portal-frontend-dev"
    ):
        """
        Initialize the loader with an OpenAPI spec URL
        
        Args:
            openapi_url: URL to fetch the OpenAPI JSON spec from
            base_url: Optional base URL for API calls (if different from openapi_url base)
            auth_manager: Optional AuthManager instance for handling authorization
            keycloak_url: Keycloak URL for authentication (used if auth_manager not provided)
            realm_name: Keycloak realm name (used if auth_manager not provided)
            client_id: Client ID for authentication (used if auth_manager not provided)
        """
        self.openapi_url = openapi_url
        self.base_url = base_url or openapi_url.rsplit('/', 1)[0]  # Remove /openapi.json
        self.spec: Optional[Dict[str, Any]] = None
        self.tools: List[Tool] = []
        
        # Initialize auth manager if not provided
        if auth_manager is None:
            self.auth_manager = AuthManager(
                keycloak_url=keycloak_url,
                realm_name=realm_name,
                client_id=client_id
            )
        else:
            self.auth_manager = auth_manager
        
    def fetch_spec(self) -> Dict[str, Any]:
        """Fetch the OpenAPI specification from the URL"""
        response = httpx.get(self.openapi_url, timeout=30)
        response.raise_for_status()
        self.spec = response.json()
        if self.spec is None:
            raise ValueError("Failed to fetch OpenAPI spec: response is None")
        return self.spec
    
    def _normalize_model_name(self, openapi_name: str) -> str:
        """
        Convert OpenAPI schema name to Python class name.
        
        Handles transformations like:
        - "EngineConfig-Input" → "EngineConfigInput"
        - "Response_str_" → "ResponseStr"
        - "Response_list_str__" → "ResponseListStr"
        - "Body_upload_file_to_S3_api_uploadToS3_post" → "BodyUploadFileToS3ApiUploadToS3Post"
        
        Args:
            openapi_name: The schema name from OpenAPI spec
            
        Returns:
            The normalized Python class name
        """
        # Remove hyphens (EngineConfig-Input → EngineConfigInput)
        normalized = openapi_name.replace('-', '')
        
        # Remove trailing underscores (Response_str_ → Response_str)
        normalized = normalized.rstrip('_')
        
        # Handle double underscores by treating them as word boundaries
        # Response_list_str__ → Response list str → ResponseListStr
        parts = normalized.split('_')
        
        # Capitalize each part and join (maintaining existing capitals)
        result = ''.join(part[0].upper() + part[1:] if part else '' for part in parts)
        
        return result
    
    def _resolve_ref(self, ref: str) -> Optional[type[BaseModel]]:
        """
        Resolve a $ref to a Pydantic model from ally_config_api_models
        
        Args:
            ref: Reference string like "#/components/schemas/EndpointConfigRequest"
        
        Returns:
            The Pydantic model class if found, None otherwise
        """
        if not ref.startswith("#/components/schemas/"):
            return None
        
        model_name = ref.split("/")[-1]
        
        # Try to get the model from ally_config_api_models
        try:
            # Lazy import to avoid issues with const field
            import ally_config_api_models
            
            # Normalize the model name from OpenAPI format to Python class name
            normalized_name = self._normalize_model_name(model_name)
            
            return getattr(ally_config_api_models, normalized_name, None)
        except Exception as e:
            print(f"Warning: Could not resolve model {model_name}: {e}")
            return None
    
    def _create_tool_function(
        self, 
        operation_id: str, 
        path: str, 
        method: str, 
        operation: Dict[str, Any],
        parameters: Optional[List[Dict[str, Any]]] = None
    ) -> Callable:
        """
        Create a function that will be wrapped as a Tool
        
        Args:
            operation_id: The operation ID from OpenAPI spec
            path: The API path
            method: HTTP method (get, post, etc.)
            operation: The operation definition from OpenAPI
            parameters: Optional list of parameter definitions
        
        Returns:
            A callable function that can be wrapped as a Tool
        """
        # Create the actual API call function
        async def api_call(ctx: RunContext[Any], **kwargs) -> Dict[str, Any]:
            """
            Make an HTTP request to the API endpoint
            
            Args:
                ctx: The run context from pydantic-ai
                **kwargs: Parameters for the API call
            
            Returns:
                The JSON response from the API
            """
            # Build the URL - replace path parameters
            final_path = path
            path_params = {}
            
            # Extract path parameters from kwargs
            for key, value in list(kwargs.items()):
                if f"{{{key}}}" in final_path:
                    final_path = final_path.replace(f"{{{key}}}", str(value))
                    path_params[key] = value
            
            # Remove path params from kwargs
            for key in path_params:
                kwargs.pop(key, None)
            
            url = f"{self.base_url}{final_path}"
            
            # Prepare headers with authorization
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add authorization header
            auth_header = self.auth_manager.get_auth_header()
            headers.update(auth_header)
            
            async with httpx.AsyncClient() as client:
                if method.lower() == "get":
                    response = await client.get(url, params=kwargs, headers=headers)
                elif method.lower() == "post":
                    response = await client.post(url, json=kwargs, headers=headers)
                elif method.lower() == "put":
                    response = await client.put(url, json=kwargs, headers=headers)
                elif method.lower() == "delete":
                    # DELETE typically doesn't have a body, use params instead
                    response = await client.delete(url, params=kwargs, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
        
        # Set the function name and docstring
        api_call.__name__ = operation_id
        api_call.__doc__ = operation.get("description", operation.get("summary", f"Call {operation_id}"))
        
        return api_call
    
    def _extract_parameters_schema(self, operation: Dict[str, Any]) -> Optional[type[BaseModel]]:
        """
        Extract and create a Pydantic model from operation parameters
        
        Args:
            operation: The operation definition from OpenAPI
        
        Returns:
            A dynamically created Pydantic model or None
        """
        # Check if there's a requestBody with a ref
        request_body = operation.get("requestBody")
        if request_body and "content" in request_body:
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})
            
            if "$ref" in schema:
                return self._resolve_ref(schema["$ref"])
        
        # Handle query parameters
        parameters = operation.get("parameters", [])
        if parameters:
            fields = {}
            for param in parameters:
                param_name = param["name"]
                param_schema = param.get("schema", {})
                param_type = param_schema.get("type", "string")
                required = param.get("required", False)
                description = param.get("description", "")
                
                # Map OpenAPI types to Python types
                type_mapping = {
                    "string": str,
                    "integer": int,
                    "number": float,
                    "boolean": bool,
                    "array": list,
                    "object": dict,
                }
                
                python_type = type_mapping.get(param_type, str)
                if not required:
                    python_type = Optional[python_type]
                
                fields[param_name] = (python_type, Field(description=description))
            
            if fields:
                return create_model(f"{operation['operationId']}_Params", **fields)
        
        return None
    
    def load_tools(self) -> List[Tool]:
        """
        Load all operations from the OpenAPI spec and convert them to Tools
        
        Returns:
            A list of pydantic-ai Tool objects
        """
        if self.spec is None:
            self.fetch_spec()
        
        if self.spec is None:
            raise ValueError("Failed to load OpenAPI spec")
        
        self.tools = []
        paths = self.spec.get("paths", {})
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                # Skip non-operation keys
                if method not in ["get", "post", "put", "delete", "patch"]:
                    continue
                
                operation_id = operation.get("operationId")
                if not operation_id:
                    continue
                
                # Extract parameters (query, path, etc.)
                parameters = operation.get("parameters", [])
                
                # Create the tool function
                tool_func = self._create_tool_function(
                    operation_id=operation_id,
                    path=path,
                    method=method,
                    operation=operation,
                    parameters=parameters
                )
                
                # Create the Tool
                tool = Tool(
                    tool_func,
                    name=operation_id,
                    description=operation.get("description") or operation.get("summary", "")
                )
                
                self.tools.append(tool)
                print(f"Created tool: {operation_id} [{method.upper()} {path}]")
        
        return self.tools
    
    def get_tool_by_operation_id(self, operation_id: str) -> Optional[Tool]:
        """Get a specific tool by its operation ID"""
        for tool in self.tools:
            if tool.name == operation_id:
                return tool
        return None


# Example usage
async def main():
    """Example of how to use the OpenAPIToolsLoader with authorization"""
    # Initialize the loader with authorization
    loader = OpenAPIToolsLoader(
        openapi_url="https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        keycloak_url="https://keycloak.prod.iam-services.aws.inform-cloud.io/",
        realm_name="inform-ai",
        client_id="ally-portal-frontend-dev"
    )
    
    # Load all tools
    tools = loader.load_tools()
    print(f"\nLoaded {len(tools)} tools from OpenAPI spec")
    
    # --- Minimal example: Call a tool function directly ---
    print("\n--- Example: Calling a tool function directly with authorization ---")
    
    if tools:
        # Get the first tool as an example
        example_tool = loader.get_tool_by_operation_id("get_available_AI_models_api_getAvailableAIModels_post")
        if example_tool is None:
            print("Example tool not found")
            return
        print(f"Calling tool: {example_tool.name}")
        print(f"Description: {example_tool.description}")
        print(f"Function signature: {inspect.signature(example_tool.function)}")
        print(f"Tool Definition: {example_tool.tool_def}")
        
        try:
            # Call the tool's function directly
            # The function is stored in tool.function
            # It expects a RunContext as first parameter, then any other parameters
            
            # Create a simple mock RunContext
            class MockRunContext:
                def __init__(self):
                    self.deps = None
            
            ctx = cast(RunContext[None], MockRunContext())
            
            # Call the function with the mock context
            # Add any required parameters based on your API endpoint
            # Example: result = await example_tool.function(ctx, param1='value', param2=123)
            result = await example_tool.function(ctx)
            
            print(f"Result: {result}")
            
        except Exception as e:
            print(f"Error calling tool: {e}")
            print(f"\nNote: The tool may require specific parameters.")
            print(f"Example with parameters:")
            print(f"  result = await example_tool.function(ctx, endpoint_id='some-id')")
    
    return tools


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
