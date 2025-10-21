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
import subprocess
import os
from typing import Any, Dict, List, Optional, Callable, cast, Union
from pydantic_ai import Tool, RunContext
from pydantic import BaseModel, Field, create_model
import importlib
import sys
import inspect
from lib.auth_manager import AuthManager

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
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
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
        auth_manager: Optional[AuthManager] = None,
        keycloak_url: str = "https://keycloak.acc.iam-services.aws.inform-cloud.io/",
        realm_name: str = "inform-ai",
        client_id: str = "ally-portal-frontend-dev",
        models_filename: str = "api_models.py",
        regenerate_models: bool = False
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
            models_filename: Filename for the generated Pydantic models (default: ally_config_api_models.py)
            regenerate_models: Whether to regenerate the models file if it exists (default: False)
        """
        self.openapi_url = openapi_url
        self.base_url = base_url or openapi_url.rsplit('/', 1)[0]  # Remove /openapi.json
        self.spec: Optional[Dict[str, Any]] = None
        self.tools: List[Tool] = []
        self.models_filename = models_filename
        self.regenerate_models = regenerate_models
        
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
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
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
        parameters_schema: Dict[str, Any]
    ) -> Callable:
        """
        Create a function that will be wrapped as a Tool
        
        Args:
            operation_id: The operation ID from OpenAPI spec
            path: The API path
            method: HTTP method (get, post, etc.)
            operation: The operation definition from OpenAPI
            parameters_schema: JSON schema for parameters
        
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

    def _extract_parameters_schema(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and create a JSON schema from operation parameters
        
        Args:
            operation: The operation definition from OpenAPI
        
        Returns:
            A JSON schema dictionary for the tool parameters
        """
        schema = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        }
        
        # Handle path parameters
        parameters = operation.get("parameters", [])
        for param in parameters:
            param_name = param["name"]
            param_schema = param.get("schema", {})
            param_type = param_schema.get("type", "string")
            required = param.get("required", False)
            description = param.get("description", "")
            
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
        
        return schema
    
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
                
                # Extract parameters schema
                parameters_schema = self._extract_parameters_schema(operation)
                
                # Create the tool function
                tool_func = self._create_tool_function(
                    operation_id=operation_id,
                    path=path,
                    method=method,
                    operation=operation,
                    parameters_schema=parameters_schema
                )
                
                # Create the Tool using from_schema for proper parameter handling
                description = operation.get("description") or operation.get("summary", "")
                tool = Tool.from_schema(
                    function=tool_func,
                    name=operation_id,
                    description=description,
                    json_schema=parameters_schema,
                    takes_ctx=True
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


