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
- Uses dependency injection pattern with AuthManager in RunContext

Usage:
    # Create loader
    loader = OpenAPIToolsLoader("https://api.example.com/openapi.json")
    
    # Load tools
    tools = loader.load_tools()
    
    # Create dependencies with auth (base_url is handled internally)
    deps = loader.create_dependencies(auth_manager=my_auth_manager)
    
    # Use with agent
    agent = Agent(
        'openai:gpt-4',
        deps_type=OpenAPIToolDependencies,
        tools=tools
    )
    
    result = await agent.run("Make an API call", deps=deps)

"""

import httpx
import subprocess
import os
from typing import Any, Dict, List, Optional, Callable, cast
from pydantic_ai import Tool, RunContext, ModelRetry
from pydantic import BaseModel
import importlib
import sys
from dataclasses import dataclass
from .auth_manager import AuthManager


@dataclass
class OpenAPIToolDependencies:
    """
    Dependencies for OpenAPI tools that need authentication and context tracking.
    
    These dependencies track user context information that helps agents provide
    more personalized and relevant responses.
    
    Attributes:
        auth_manager: Manages authentication for API calls
        geschaeftsbereich: The user's business area (Geschäftsbereich) - None if not yet provided
        project_number: The project number the user is working with - None if not yet provided
        endpoint_name: The specific endpoint configuration being discussed - None if not yet provided
    """
    auth_manager: AuthManager
    geschaeftsbereich: Optional[str] = None
    project_number: Optional[str] = None
    endpoint_name: Optional[str] = None

# We'll dynamically import models as needed to avoid import errors
# from ally_config_api_models import *


class OpenAPIToolsLoader:
    """Loads OpenAPI operations and converts them into pydantic-ai Tools"""
    
    @staticmethod
    def generate_api_models(
        openapi_url: str, 
        output_filename: str = "ally_config_api_models.py",
        force_regenerate: bool = False
    ) -> bool:
        """
        Standalone function to generate Pydantic models from an OpenAPI spec
        
        Args:
            openapi_url: URL to the OpenAPI specification
            output_filename: Output filename for the generated models
            force_regenerate: Whether to overwrite existing files
        
        Returns:
            True if successful, False otherwise
        """
        # Check if file exists and force_regenerate is False
        if os.path.exists(output_filename) and not force_regenerate:
            print(f"Models file '{output_filename}' already exists. Use force_regenerate=True to overwrite.")
            return False
        
        try:
            # Run datamodel-codegen command
            # First try to find the datamodel-codegen executable
            import shutil
            codegen_path = shutil.which("datamodel-codegen")
            if not codegen_path:
                # Try in the virtual environment
                import sys
                venv_path = sys.prefix
                codegen_path = os.path.join(venv_path, "bin", "datamodel-codegen")
                if not os.path.exists(codegen_path):
                    raise FileNotFoundError("datamodel-codegen not found")
            
            cmd = [
                codegen_path,
                "--url", openapi_url,
                "--input-file-type", "openapi",
                "--output", output_filename
            ]
            
            print(f"Generating models file '{output_filename}' from {openapi_url}...")
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            print(f"Successfully generated '{output_filename}'")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error generating models file: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False
        except FileNotFoundError:
            print("Error: datamodel-codegen not found. Please install it with:")
            print("  pip install datamodel-code-generator")
            return False
    
    def __init__(
        self, 
        openapi_url: str, 
        base_url: Optional[str] = None,
        models_filename: str = "api_models.py",
        regenerate_models: bool = False,
        require_human_approval: bool = False,
        tool_name_prefix: str = ""
    ):
        """
        Initialize the loader with an OpenAPI spec URL
        
        Args:
            openapi_url: URL to fetch the OpenAPI JSON spec from
            base_url: Optional base URL for API calls (if different from openapi_url base)
            models_filename: Filename for the generated Pydantic models (default: api_models.py)
            regenerate_models: Whether to regenerate the models file if it exists (default: False)
            require_human_approval: Whether to require human approval for non-read-only operations (default: False)
            tool_name_prefix: Optional prefix to add to all tool names to avoid conflicts (default: "")
        """
        self.openapi_url = openapi_url
        self.base_url = base_url or openapi_url.rsplit('/', 1)[0]  # Remove /openapi.json
        self.spec: Optional[Dict[str, Any]] = None
        self.tools: List[Tool[OpenAPIToolDependencies]] = []
        self.models_filename = models_filename
        self.regenerate_models = regenerate_models
        self.require_human_approval = require_human_approval
        self.tool_name_prefix = tool_name_prefix
        self.tool_tags: Dict[str, List[str]] = {}  # Maps tool names to their tags
        
    def fetch_spec(self) -> Dict[str, Any]:
        """Fetch the OpenAPI specification from the URL"""
        response = httpx.get(self.openapi_url, timeout=30)
        response.raise_for_status()
        self.spec = response.json()
        if self.spec is None:
            raise ValueError("Failed to fetch OpenAPI spec: response is None")
        return self.spec
    
    def generate_models_file(self) -> bool:
        """
        Generate Pydantic models file from OpenAPI spec using datamodel-codegen
        
        Returns:
            True if the file was generated successfully, False otherwise
        """
        # Check if file exists and regenerate_models is False
        if os.path.exists(self.models_filename) and not self.regenerate_models:
            print(f"Models file '{self.models_filename}' already exists. Use regenerate_models=True to overwrite.")
            return False
        
        try:
            # Run datamodel-codegen command
            # First try to find the datamodel-codegen executable
            import shutil
            codegen_path = shutil.which("datamodel-codegen")
            if not codegen_path:
                # Try in the virtual environment
                import sys
                venv_path = sys.prefix
                codegen_path = os.path.join(venv_path, "bin", "datamodel-codegen")
                if not os.path.exists(codegen_path):
                    raise FileNotFoundError("datamodel-codegen not found")
            
            cmd = [
                codegen_path,
                "--url", self.openapi_url,
                "--input-file-type", "openapi",
                "--output", self.models_filename
            ]
            
            print(f"Generating models file '{self.models_filename}' from {self.openapi_url}...")
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            print(f"Successfully generated '{self.models_filename}'")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error generating models file: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False
        except FileNotFoundError:
            print("Error: datamodel-codegen not found. Please install it with:")
            print("  pip install datamodel-code-generator")
            return False
    
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
    
    def _is_read_only_operation(self, method: str) -> bool:
        """
        Determine if an HTTP method represents a read-only operation
        
        Args:
            method: HTTP method (get, post, put, delete, etc.)
            
        Returns:
            True if the operation is read-only, False otherwise
        """
        return method.lower() == "get"
    
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
        
        # Try to get the model from the models file
        try:
            # Get module name from filename (remove .py extension)
            module_name = self.models_filename.replace('.py', '')
            
            # Lazy import to avoid issues with const field
            if module_name in sys.modules:
                models_module = sys.modules[module_name]
            else:
                models_module = importlib.import_module(module_name)
            
            # Normalize the model name from OpenAPI format to Python class name
            normalized_name = self._normalize_model_name(model_name)
            
            return getattr(models_module, normalized_name, None)
        except Exception as e:
            print(f"Warning: Could not resolve model {model_name}: {e}")
            return None
    
    def _create_tool_function(
        self, 
        operation_id: str, 
        path: str, 
        method: str, 
        operation: Dict[str, Any],
        parameters_schema: Dict[str, Any],
        query_param_names: List[str]
    ) -> Callable:
        """
        Create a function that will be wrapped as a Tool
        
        Args:
            operation_id: The operation ID from OpenAPI spec
            path: The API path
            method: HTTP method (get, post, etc.)
            operation: The operation definition from OpenAPI
            parameters_schema: JSON schema for parameters
            query_param_names: List of parameter names that should be sent as query parameters
        
        Returns:
            A callable function that can be wrapped as a Tool
        """
        # Create the actual API call function
        async def api_call(ctx: RunContext[OpenAPIToolDependencies], **kwargs) -> Dict[str, Any]:
            """
            Make an HTTP request to the API endpoint
            
            Args:
                ctx: The run context from pydantic-ai containing dependencies
                **kwargs: Parameters for the API call
            
            Returns:
                The JSON response from the API
            """
            # Check if human approval is required for non-read-only operations
            if (self.require_human_approval and 
                not self._is_read_only_operation(method) and 
                not ctx.tool_call_approved):
                from pydantic_ai import ApprovalRequired
                raise ApprovalRequired(
                    f"Human approval required for {method.upper()} operation on {path}"
                )
            
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
            
            # Separate query parameters from body parameters
            query_params = {}
            body_params = {}
            
            for key, value in kwargs.items():
                if key in query_param_names:
                    query_params[key] = value
                else:
                    body_params[key] = value
            
            url = f"{self.base_url}{final_path}"
            
            # Prepare headers with authorization
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add authorization header from context dependencies
            auth_header = ctx.deps.auth_manager.get_auth_header()
            headers.update(auth_header)
            
            # Configure timeout: 20 seconds for each operation (connect, read, write, pool)
            timeout = httpx.Timeout(20.0, connect=10.0)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                try:
                    if method.lower() == "get":
                        response = await client.get(url, params=query_params, headers=headers)
                    elif method.lower() == "post":
                        # For POST, send query params as URL params and body params as JSON
                        response = await client.post(url, params=query_params, json=body_params, headers=headers)
                    elif method.lower() == "put":
                        response = await client.put(url, params=query_params, json=body_params, headers=headers)
                    elif method.lower() == "delete":
                        # DELETE typically doesn't have a body, use params instead
                        response = await client.delete(url, params=query_params, headers=headers)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                    
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPStatusError as e:
                    # Convert HTTPStatusError to ModelRetry so the LLM can try again
                    raise ModelRetry(f"API request failed with status {e.response.status_code}: {e.response.text}")
                except httpx.RequestError as e:
                    # Handle network/connection errors with detailed information
                    error_details = f"{type(e).__name__}: {str(e) or repr(e)}"
                    if hasattr(e, 'request'):
                        error_details += f" (URL: {e.request.url})"
                    raise ModelRetry(f"Network error occurred: {error_details}")
                except Exception as e:
                    # Catch any other exceptions and convert to ModelRetry
                    raise ModelRetry(f"Unexpected error during API call to {method.upper()} {path}: {type(e).__name__}: {str(e)}")
        
        # Set the function name and docstring
        api_call.__name__ = operation_id
        api_call.__doc__ = operation.get("description", operation.get("summary", f"Call {operation_id}"))
        
        return api_call
    
    def _resolve_schema_refs(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively resolve all $ref references in a schema
        
        Args:
            schema: The schema dictionary that may contain $ref references
        
        Returns:
            The schema with all $ref references resolved
        """
        if not isinstance(schema, dict):
            return schema
        
        # If this schema has a $ref, resolve it
        if "$ref" in schema:
            if self.spec and "components" in self.spec and "schemas" in self.spec["components"]:
                ref_name = schema["$ref"].split("/")[-1]
                if ref_name in self.spec["components"]["schemas"]:
                    resolved_schema = self.spec["components"]["schemas"][ref_name].copy()
                    # Preserve description if it exists in the original schema
                    if "description" in schema:
                        resolved_schema["description"] = schema["description"]
                    # Recursively resolve any refs in the resolved schema
                    return self._resolve_schema_refs(resolved_schema)
            # If we can't resolve it, return as-is
            return schema
        
        # Recursively resolve refs in nested structures
        resolved_schema = schema.copy()
        
        if "properties" in resolved_schema:
            resolved_properties = {}
            for prop_name, prop_schema in resolved_schema["properties"].items():
                resolved_properties[prop_name] = self._resolve_schema_refs(prop_schema)
            resolved_schema["properties"] = resolved_properties
        
        if "patternProperties" in resolved_schema:
            resolved_pattern_properties = {}
            for pattern, prop_schema in resolved_schema["patternProperties"].items():
                resolved_pattern_properties[pattern] = self._resolve_schema_refs(prop_schema)
            resolved_schema["patternProperties"] = resolved_pattern_properties
        
        if "items" in resolved_schema:
            resolved_schema["items"] = self._resolve_schema_refs(resolved_schema["items"])
        
        if "anyOf" in resolved_schema:
            resolved_schema["anyOf"] = [self._resolve_schema_refs(item) for item in resolved_schema["anyOf"]]
        
        if "oneOf" in resolved_schema:
            resolved_schema["oneOf"] = [self._resolve_schema_refs(item) for item in resolved_schema["oneOf"]]
        
        if "allOf" in resolved_schema:
            resolved_schema["allOf"] = [self._resolve_schema_refs(item) for item in resolved_schema["allOf"]]
        
        # Handle discriminator mapping in oneOf/anyOf
        if "discriminator" in resolved_schema and "mapping" in resolved_schema["discriminator"]:
            mapping = resolved_schema["discriminator"]["mapping"]
            resolved_mapping = {}
            for key, ref_value in mapping.items():
                if ref_value.startswith("#/components/schemas/"):
                    ref_name = ref_value.split("/")[-1]
                    if (self.spec and "components" in self.spec and 
                        "schemas" in self.spec["components"] and 
                        ref_name in self.spec["components"]["schemas"]):
                        # Keep the original reference for discriminator mapping
                        resolved_mapping[key] = ref_value
                    else:
                        resolved_mapping[key] = ref_value
                else:
                    resolved_mapping[key] = ref_value
            resolved_schema["discriminator"]["mapping"] = resolved_mapping
        
        return resolved_schema

    def _extract_parameters_schema(self, operation: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
        """
        Extract and create a JSON schema from operation parameters
        
        Args:
            operation: The operation definition from OpenAPI
        
        Returns:
            A tuple of (JSON schema dictionary for the tool parameters, list of query parameter names)
        """
        schema = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        }
        
        query_param_names = []
        
        # Handle path and query parameters
        parameters = operation.get("parameters", [])
        for param in parameters:
            param_name = param["name"]
            param_schema = param.get("schema", {})
            param_type = param_schema.get("type", "string")
            required = param.get("required", False)
            description = param.get("description", "")
            param_in = param.get("in", "query")  # "query", "path", "header", etc.
            
            # Track query parameters
            if param_in == "query":
                query_param_names.append(param_name)
            
            # Add to schema properties
            schema["properties"][param_name] = {
                "type": param_type,
                "description": description
            }
            
            # Handle additional schema properties
            if "format" in param_schema:
                schema["properties"][param_name]["format"] = param_schema["format"]
            if "enum" in param_schema:
                schema["properties"][param_name]["enum"] = param_schema["enum"]
            if "default" in param_schema:
                schema["properties"][param_name]["default"] = param_schema["default"]
            if "minimum" in param_schema:
                schema["properties"][param_name]["minimum"] = param_schema["minimum"]
            if "maximum" in param_schema:
                schema["properties"][param_name]["maximum"] = param_schema["maximum"]
            # CRITICAL: Handle array types - must include items property
            if param_type == "array" and "items" in param_schema:
                schema["properties"][param_name]["items"] = param_schema["items"]
            
            if required:
                schema["required"].append(param_name)
        
        # Handle request body parameters
        request_body = operation.get("requestBody")
        if request_body and "content" in request_body:
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            body_schema = json_content.get("schema", {})
            
            if "$ref" in body_schema:
                # Try to resolve the reference and extract properties
                if self.spec and "components" in self.spec and "schemas" in self.spec["components"]:
                    ref_name = body_schema["$ref"].split("/")[-1]
                    if ref_name in self.spec["components"]["schemas"]:
                        resolved_schema = self.spec["components"]["schemas"][ref_name]
                        if "properties" in resolved_schema:
                            for prop_name, prop_schema in resolved_schema["properties"].items():
                                # Recursively resolve any refs in the property schema
                                resolved_prop_schema = self._resolve_schema_refs(prop_schema)
                                schema["properties"][prop_name] = resolved_prop_schema
                            if "required" in resolved_schema:
                                schema["required"].extend(resolved_schema["required"])
            elif "properties" in body_schema:
                # Direct schema properties
                for prop_name, prop_schema in body_schema["properties"].items():
                    # Recursively resolve any refs in the property schema
                    resolved_prop_schema = self._resolve_schema_refs(prop_schema)
                    schema["properties"][prop_name] = resolved_prop_schema
                if "required" in body_schema:
                    schema["required"].extend(body_schema["required"])
        
        return schema, query_param_names
    
    def load_tools(self) -> List[Tool[OpenAPIToolDependencies]]:
        """
        Load all operations from the OpenAPI spec and convert them to Tools
        
        Returns:
            A list of pydantic-ai Tool objects
        """
        if self.spec is None:
            self.fetch_spec()
        
        if self.spec is None:
            raise ValueError("Failed to load OpenAPI spec")
        
        # Generate models file if needed
        if self.regenerate_models or not os.path.exists(self.models_filename):
            self.generate_models_file()
        
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
                
                # Extract tags from the operation
                tags = operation.get("tags", [])
                
                # Extract parameters schema and query parameter names
                parameters_schema, query_param_names = self._extract_parameters_schema(operation)
                
                # Create the tool function
                tool_func = self._create_tool_function(
                    operation_id=operation_id,
                    path=path,
                    method=method,
                    operation=operation,
                    parameters_schema=parameters_schema,
                    query_param_names=query_param_names
                )
                
                # Create the Tool - cast to proper type since Tool.from_schema doesn't infer it
                description = operation.get("description") or operation.get("summary", "")
                
                # Add prefix if configured
                prefixed_operation_id = f"{self.tool_name_prefix}{operation_id}" if self.tool_name_prefix else operation_id
                
                # Truncate operation_id to 64 characters to meet OpenAI requirements
                tool_name = self._truncate_tool_name(prefixed_operation_id)
                if tool_name != prefixed_operation_id:
                    print(f"Warning: Truncated tool name from '{prefixed_operation_id}' to '{tool_name}'")
                
                tool_untyped = Tool.from_schema(
                    function=tool_func,
                    name=tool_name,
                    description=description,
                    json_schema=parameters_schema,
                    takes_ctx=True
                )
                # Cast the tool to the proper type
                tool: Tool[OpenAPIToolDependencies] = cast(Tool[OpenAPIToolDependencies], tool_untyped)
                
                self.tools.append(tool)
                
                # Store the tags for this tool
                self.tool_tags[tool_name] = tags
                
                print(f"Created tool: {tool_name} [{method.upper()} {path}]")
        
        return self.tools
    
    def create_dependencies(
        self,
        auth_manager: Optional[AuthManager] = None,
        keycloak_url: str = "https://keycloak.acc.iam-services.aws.inform-cloud.io/",
        realm_name: str = "inform-ai",
        client_id: str = "ally-portal-frontend-dev"
    ) -> OpenAPIToolDependencies:
        """
        Create dependencies for the OpenAPI tools
        
        Args:
            auth_manager: Optional AuthManager instance for handling authorization
            keycloak_url: Keycloak URL for authentication (used if auth_manager not provided)
            realm_name: Keycloak realm name (used if auth_manager not provided)
            client_id: Client ID for authentication (used if auth_manager not provided)
        
        Returns:
            OpenAPIToolDependencies instance
        """
        if auth_manager is None:
            auth_manager = AuthManager(
                keycloak_url=keycloak_url,
                realm_name=realm_name,
                client_id=client_id
            )
        
        return OpenAPIToolDependencies(
            auth_manager=auth_manager
        )
    
    def _truncate_tool_name(self, tool_name: str) -> str:
        """Apply the same truncation logic used when creating tools"""
        if len(tool_name) <= 64:
            return tool_name
        
        # Try to preserve the important parts by removing redundant prefixes/suffixes
        truncated = tool_name
        
        # Remove common redundant parts
        redundant_patterns = ["_api_", "api_", "_post", "_get", "_put", "_delete"]
        for pattern in redundant_patterns:
            if pattern in truncated and len(truncated) > 64:
                truncated = truncated.replace(pattern, "_" if pattern.startswith("_") and pattern.endswith("_") else "", 1)
        
        # If still too long, truncate from the end
        if len(truncated) > 64:
            truncated = truncated[:64]
        
        return truncated
    
    def get_tool_by_operation_id(self, operation_id: str) -> Optional[Tool[OpenAPIToolDependencies]]:
        """
        Get a specific tool by its operation ID (supports both original and truncated names).
        Automatically handles the tool name prefix if one was configured.
        
        Args:
            operation_id: The operation ID without any prefix
            
        Returns:
            The tool if found, None otherwise
        """
        # Add prefix if configured
        prefixed_operation_id = f"{self.tool_name_prefix}{operation_id}" if self.tool_name_prefix else operation_id
        
        # First try exact match with prefix
        for tool in self.tools:
            if tool.name == prefixed_operation_id:
                return tool
        
        # If no exact match, try with truncation logic applied to the prefixed operation_id
        truncated_operation_id = self._truncate_tool_name(prefixed_operation_id)
        for tool in self.tools:
            if tool.name == truncated_operation_id:
                return tool
        
        return None
    
    @staticmethod
    def get_dependencies_type() -> type[OpenAPIToolDependencies]:
        """Get the dependencies type for type annotations"""
        return OpenAPIToolDependencies
    
    def get_tags_for_tool(self, tool_name: str) -> List[str]:
        """
        Get the tags associated with a specific tool
        
        Args:
            tool_name: The name of the tool (may include prefix)
            
        Returns:
            List of tags for the tool, or empty list if tool not found or has no tags
        """
        return self.tool_tags.get(tool_name, [])
    
    def get_all_tool_tags(self) -> Dict[str, List[str]]:
        """
        Get all tool tags as a dictionary
        
        Returns:
            Dictionary mapping tool names to their tags
        """
        return self.tool_tags.copy()



