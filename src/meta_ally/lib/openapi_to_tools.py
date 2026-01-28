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

import importlib
import json
import logging
import os
import shutil
import subprocess  # noqa: S404
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

import httpx
from pydantic import BaseModel
from pydantic_ai import ModelRetry, RunContext, Tool

from ..auth.auth_manager import AuthManager

logger = logging.getLogger(__name__)


class ApprovalResponse(BaseModel):
    """Response from an approval callback"""
    approved: bool
    reason: str | None = None


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
    geschaeftsbereich: str | None = None
    project_number: str | None = None
    endpoint_name: str | None = None


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

        Raises:
            FileNotFoundError: If datamodel-codegen is not found
        """
        # Check if file exists and force_regenerate is False
        if os.path.exists(output_filename) and not force_regenerate:
            print(f"Models file '{output_filename}' already exists. Use force_regenerate=True to overwrite.")
            return False

        try:
            # Run datamodel-codegen command
            # First try to find the datamodel-codegen executable
            codegen_path = shutil.which("datamodel-codegen")
            if not codegen_path:
                # Try in the virtual environment
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
            subprocess.run(cmd, capture_output=True, text=True, check=True)  # noqa: S603

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
        base_url: str | None = None,
        models_filename: str = "api_models.py",
        regenerate_models: bool = False,
        require_human_approval: bool = False,
        approval_callback: Callable[[str, str, dict], ApprovalResponse] | None = None,
        tool_name_prefix: str = "",
        max_response_chars: int | None = None
    ):
        """
        Initialize the loader with an OpenAPI spec URL

        Args:
            openapi_url: URL to fetch the OpenAPI JSON spec from
            base_url: Optional base URL for API calls (if different from openapi_url base)
            models_filename: Filename for the generated Pydantic models (default: api_models.py)
            regenerate_models: Whether to regenerate the models file if it exists (default: False)
            require_human_approval: Whether to require human approval for non-read-only operations (default: False)
            approval_callback: Optional callback for human approval. Receives (operation_id, method, params)
                and returns ApprovalResponse. Only called if require_human_approval is True.
            tool_name_prefix: Optional prefix to add to all tool names to avoid conflicts (default: "")
            max_response_chars: Maximum characters in API responses. If exceeded, response is truncated
                (default: None = no truncation)
        """
        self.openapi_url = openapi_url
        self.base_url = base_url or openapi_url.rsplit('/', maxsplit=1)[0]  # Remove /openapi.json
        self.spec: dict[str, Any] | None = None
        self.tools: list[Tool[OpenAPIToolDependencies]] = []
        self.models_filename = models_filename
        self.regenerate_models = regenerate_models
        self.require_human_approval = require_human_approval
        self.approval_callback = approval_callback
        self.tool_name_prefix = tool_name_prefix
        self.max_response_chars = max_response_chars
        self.tool_tags: dict[str, list[str]] = {}  # Maps tool names to their tags

    def fetch_spec(self) -> dict[str, Any]:
        """
        Fetch the OpenAPI specification from the URL

        Returns:
            The parsed OpenAPI specification as a dictionary

        Raises:
            ValueError: If the response is None after fetching
        """
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

        Raises:
            FileNotFoundError: If datamodel-codegen is not found
        """
        # Check if file exists and regenerate_models is False
        if os.path.exists(self.models_filename) and not self.regenerate_models:
            print(f"Models file '{self.models_filename}' already exists. Use regenerate_models=True to overwrite.")
            return False

        try:
            # Run datamodel-codegen command
            # First try to find the datamodel-codegen executable
            codegen_path = shutil.which("datamodel-codegen")
            if not codegen_path:
                # Try in the virtual environment
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
            subprocess.run(cmd, capture_output=True, text=True, check=True)  # noqa: S603

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

    def _truncate_response(self, response: Any) -> Any:
        """
        Truncate response if it exceeds max_response_chars

        Args:
            response: The API response (typically a dict)

        Returns:
            Truncated response with metadata about truncation, or original response if no truncation needed
        """
        if self.max_response_chars is None:
            return response

        # Convert to JSON string to measure size
        response_str = json.dumps(response, default=str)

        if len(response_str) <= self.max_response_chars:
            return response

        # Truncate and add metadata
        truncated_str = response_str[:self.max_response_chars]

        # Try to keep valid JSON by closing structures at a safe point
        try:
            # Find last comma to avoid breaking in the middle of a value
            last_comma = truncated_str.rfind(',')
            if last_comma > 0:
                truncated_str = truncated_str[:last_comma]
        except Exception as exc:
            logger.exception("Failed to truncate response at comma boundary: %s", exc)

        return {
            "_truncated": True,
            "_original_size": len(response_str),
            "_truncated_at": self.max_response_chars,
            "_message": f"Response truncated from {len(response_str)} to {self.max_response_chars} characters",
            "_partial_data": truncated_str
        }

    def _resolve_ref(self, ref: str) -> type[BaseModel] | None:
        """
        Resolve a $ref to a Pydantic model from ally_config_api_models

        Args:
            ref: Reference string like "#/components/schemas/EndpointConfigRequest"

        Returns:
            The Pydantic model class if found, None otherwise
        """
        if not ref.startswith("#/components/schemas/"):
            return None

        model_name = ref.rsplit("/", maxsplit=1)[-1]

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

    def _check_approval(
        self,
        operation_id: str,
        method: str,
        path: str,
        kwargs: dict[str, Any]
    ) -> None:
        """
        Check if human approval is required and request it

        Args:
            operation_id: The operation ID
            method: HTTP method
            path: API path
            kwargs: Request parameters

        Raises:
            ModelRetry: If approval is required but not granted
        """
        if not self.require_human_approval or self._is_read_only_operation(method):
            return

        if self.approval_callback is None:
            raise ModelRetry(
                f"Human approval required for {method.upper()} operation on {path}, "
                "but no approval callback configured"
            )

        approval_response = self.approval_callback(operation_id, method.upper(), kwargs)
        if not approval_response.approved:
            reason = approval_response.reason or "User denied approval"
            raise ModelRetry(f"Operation denied: {reason}")

    def _build_url_and_params(
        self,
        path: str,
        kwargs: dict[str, Any],
        query_param_names: list[str]
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """
        Build URL with path parameters and separate query/body parameters

        Args:
            path: API path template
            kwargs: All request parameters
            query_param_names: List of parameter names that should be query params

        Returns:
            Tuple of (final_url, query_params, body_params)
        """
        # Build the URL - replace path parameters
        final_path = path
        remaining_kwargs = kwargs.copy()

        # Extract and substitute path parameters
        for key, value in list(kwargs.items()):
            if f"{{{key}}}" in final_path:
                final_path = final_path.replace(f"{{{key}}}", str(value))
                remaining_kwargs.pop(key, None)

        # Separate query parameters from body parameters
        query_params = {k: v for k, v in remaining_kwargs.items() if k in query_param_names}
        body_params = {k: v for k, v in remaining_kwargs.items() if k not in query_param_names}

        return f"{self.base_url}{final_path}", query_params, body_params

    async def _execute_http_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        query_params: dict[str, Any],
        body_params: dict[str, Any],
        headers: dict[str, str]
    ) -> httpx.Response:
        """
        Execute the HTTP request based on the method

        Args:
            client: HTTP client
            method: HTTP method
            url: Request URL
            query_params: Query parameters
            body_params: Body parameters
            headers: Request headers

        Returns:
            HTTP response

        Raises:
            ValueError: If HTTP method is unsupported
        """
        method_lower = method.lower()
        if method_lower == "get":
            return await client.get(url, params=query_params, headers=headers)
        elif method_lower == "post":
            return await client.post(url, params=query_params, json=body_params, headers=headers)
        elif method_lower == "put":
            return await client.put(url, params=query_params, json=body_params, headers=headers)
        elif method_lower == "delete":
            return await client.delete(
                url, params=query_params, json=body_params if body_params else None, headers=headers
            )
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    def _handle_response(self, response: httpx.Response) -> dict[str, Any] | str:
        """
        Handle and parse the HTTP response

        Args:
            response: HTTP response

        Returns:
            Parsed response or success message
        """
        # Handle empty response bodies
        if not response.content or response.content.strip() == b"":
            return f"API request succeeded with status {response.status_code}"

        try:
            result = response.json()
            # Handle empty JSON responses
            if result is None or result in ("", {}, []):
                return f"API request succeeded with status {response.status_code} and response is empty"
            return self._truncate_response(result)
        except ValueError:
            # If response is not JSON but has content, return success message
            return f"API request succeeded with status {response.status_code}"

    def _create_tool_function(
        self,
        operation_id: str,
        path: str,
        method: str,
        operation: dict[str, Any],
        query_param_names: list[str]
    ) -> Callable:
        """
        Create a function that will be wrapped as a Tool

        Args:
            operation_id: The operation ID from OpenAPI spec
            path: The API path
            method: HTTP method (get, post, etc.)
            operation: The operation definition from OpenAPI
            query_param_names: List of parameter names that should be sent as query parameters

        Returns:
            A callable function that can be wrapped as a Tool
        """
        # Create the actual API call function
        async def api_call(ctx: RunContext[OpenAPIToolDependencies], **kwargs) -> dict[str, Any] | str:
            """
            Make an HTTP request to the API endpoint

            Args:
                ctx: The run context from pydantic-ai containing dependencies
                **kwargs: Parameters for the API call

            Returns:
                The JSON response from the API or success message

            Raises:
                ModelRetry: If the API request fails, approval is denied, or encounters an error
            """
            # Check if human approval is required
            self._check_approval(operation_id, method, path, kwargs)

            # Build URL and separate parameters
            url, query_params, body_params = self._build_url_and_params(path, kwargs, query_param_names)

            # Prepare headers with authorization
            headers = {"Content-Type": "application/json"}
            headers.update(ctx.deps.auth_manager.get_auth_header())

            # Configure timeout for slow API endpoints
            timeout = httpx.Timeout(60.0, connect=10.0, read=60.0)

            async with httpx.AsyncClient(timeout=timeout) as client:
                try:
                    response = await self._execute_http_request(
                        client, method, url, query_params, body_params, headers
                    )
                    response.raise_for_status()
                    return self._handle_response(response)
                except httpx.HTTPStatusError as e:
                    msg = f"API request failed with status {e.response.status_code}: {e.response.text}"
                    raise ModelRetry(msg) from e
                except httpx.RequestError as e:
                    error_details = f"{type(e).__name__}: {str(e) or repr(e)}"
                    if hasattr(e, 'request'):
                        error_details += f" (URL: {e.request.url})"
                    raise ModelRetry(f"Network error occurred: {error_details}") from e
                except Exception as e:
                    error_msg = (
                        f"Unexpected error during API call to {method.upper()} {path}: "
                        f"{type(e).__name__}: {e!s}"
                    )
                    raise ModelRetry(error_msg) from e

        # Set the function name and docstring
        api_call.__name__ = operation_id
        api_call.__doc__ = operation.get("description", operation.get("summary", f"Call {operation_id}"))

        return api_call

    def _resolve_ref(self, schema: dict[str, Any]) -> dict[str, Any] | None:
        """
        Resolve a single $ref reference

        Args:
            schema: Schema with a $ref

        Returns:
            Resolved schema or None if cannot be resolved
        """
        if not self.spec or "components" not in self.spec or "schemas" not in self.spec["components"]:
            return None

        ref_name = schema["$ref"].split("/")[-1]
        if ref_name not in self.spec["components"]["schemas"]:
            return None

        resolved_schema = self.spec["components"]["schemas"][ref_name].copy()
        # Preserve description if it exists in the original schema
        if "description" in schema:
            resolved_schema["description"] = schema["description"]
        return resolved_schema

    def _resolve_nested_properties(self, schema: dict[str, Any]) -> dict[str, Any]:
        """
        Resolve refs in properties and patternProperties

        Returns:
            Schema with resolved property references
        """
        if "properties" in schema:
            schema["properties"] = {
                prop_name: self._resolve_schema_refs(prop_schema)
                for prop_name, prop_schema in schema["properties"].items()
            }

        if "patternProperties" in schema:
            schema["patternProperties"] = {
                pattern: self._resolve_schema_refs(prop_schema)
                for pattern, prop_schema in schema["patternProperties"].items()
            }

        return schema

    def _resolve_composition_schemas(self, schema: dict[str, Any]) -> dict[str, Any]:
        """
        Resolve refs in anyOf, oneOf, allOf

        Returns:
            Schema with resolved composition references
        """
        for key in ["anyOf", "oneOf", "allOf"]:
            if key in schema:
                schema[key] = [self._resolve_schema_refs(item) for item in schema[key]]
        return schema

    def _resolve_discriminator_mapping(self, schema: dict[str, Any]) -> dict[str, Any]:
        """
        Resolve discriminator mapping references

        Returns:
            Schema with preserved discriminator mapping
        """
        if "discriminator" not in schema or "mapping" not in schema["discriminator"]:
            return schema

        # Keep original references for discriminator mapping
        # No actual resolution needed, just preserve the structure
        return schema

    def _resolve_schema_refs(self, schema: dict[str, Any]) -> dict[str, Any]:
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
            resolved = self._resolve_ref(schema)
            if resolved:
                return self._resolve_schema_refs(resolved)
            return schema

        # Recursively resolve refs in nested structures
        resolved_schema = schema.copy()

        # Resolve nested properties
        resolved_schema = self._resolve_nested_properties(resolved_schema)

        # Handle items (for arrays)
        if "items" in resolved_schema:
            resolved_schema["items"] = self._resolve_schema_refs(resolved_schema["items"])

        # Handle composition schemas (anyOf, oneOf, allOf)
        resolved_schema = self._resolve_composition_schemas(resolved_schema)

        # Handle discriminator mapping
        resolved_schema = self._resolve_discriminator_mapping(resolved_schema)

        return resolved_schema

    def _add_param_schema_constraints(self, param_schema_dict: dict[str, Any], param_schema: dict[str, Any]) -> None:
        """Add schema constraints like format, enum, default, min/max to parameter schema"""
        constraints = ["format", "enum", "default", "minimum", "maximum"]
        for constraint in constraints:
            if constraint in param_schema:
                param_schema_dict[constraint] = param_schema[constraint]

        # Handle array types - must include items property
        if param_schema.get("type") == "array" and "items" in param_schema:
            param_schema_dict["items"] = param_schema["items"]

    def _process_parameter(self, param: dict[str, Any], schema: dict[str, Any], query_param_names: list[str]) -> None:
        """Process a single parameter and add it to the schema"""
        param_name = param["name"]
        param_schema = param.get("schema", {})
        param_type = param_schema.get("type", "string")
        required = param.get("required", False)
        description = param.get("description", "")
        param_in = param.get("in", "query")

        # Track query parameters
        if param_in == "query":
            query_param_names.append(param_name)

        # Add to schema properties
        schema["properties"][param_name] = {
            "type": param_type,
            "description": description
        }

        # Add constraints
        self._add_param_schema_constraints(schema["properties"][param_name], param_schema)

        if required:
            schema["required"].append(param_name)

    def _extract_ref_schema_properties(self, ref_name: str) -> dict[str, Any] | None:
        """
        Extract properties from a referenced schema

        Args:
            ref_name: The name of the schema reference

        Returns:
            The referenced schema dictionary or None if not found
        """
        if not self.spec or "components" not in self.spec or "schemas" not in self.spec["components"]:
            return None

        if ref_name not in self.spec["components"]["schemas"]:
            return None

        return self.spec["components"]["schemas"][ref_name]

    def _process_body_schema_ref(self, body_schema: dict[str, Any], schema: dict[str, Any]) -> None:
        """Process a $ref in request body schema and add properties to schema"""
        ref_name = body_schema["$ref"].split("/")[-1]
        resolved_schema = self._extract_ref_schema_properties(ref_name)

        if resolved_schema and "properties" in resolved_schema:
            for prop_name, prop_schema in resolved_schema["properties"].items():
                resolved_prop_schema = self._resolve_schema_refs(prop_schema)
                schema["properties"][prop_name] = resolved_prop_schema

            if "required" in resolved_schema:
                schema["required"].extend(resolved_schema["required"])

    def _process_body_schema_properties(self, body_schema: dict[str, Any], schema: dict[str, Any]) -> None:
        """Process direct properties in request body schema"""
        for prop_name, prop_schema in body_schema["properties"].items():
            resolved_prop_schema = self._resolve_schema_refs(prop_schema)
            schema["properties"][prop_name] = resolved_prop_schema

        if "required" in body_schema:
            schema["required"].extend(body_schema["required"])

    def _process_request_body(self, request_body: dict[str, Any], schema: dict[str, Any]) -> None:
        """Process request body and add its properties to schema"""
        if not (request_body and "content" in request_body):
            return

        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        body_schema = json_content.get("schema", {})

        if "$ref" in body_schema:
            self._process_body_schema_ref(body_schema, schema)
        elif "properties" in body_schema:
            self._process_body_schema_properties(body_schema, schema)

    def _extract_parameters_schema(self, operation: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
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

        query_param_names: list[str] = []

        # Handle path and query parameters
        parameters = operation.get("parameters", [])
        for param in parameters:
            self._process_parameter(param, schema, query_param_names)

        # Handle request body parameters
        request_body = operation.get("requestBody")
        self._process_request_body(request_body, schema)

        return schema, query_param_names

    def load_tools(self) -> list[Tool[OpenAPIToolDependencies]]:
        """
        Load all operations from the OpenAPI spec and convert them to Tools

        Returns:
            A list of pydantic-ai Tool objects

        Raises:
            ValueError: If the OpenAPI spec fails to load
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
                if method not in {"get", "post", "put", "delete", "patch"}:
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
                    query_param_names=query_param_names
                )

                # Create the Tool - cast to proper type since Tool.from_schema doesn't infer it
                description = operation.get("description") or operation.get("summary", "")

                # Add prefix if configured
                prefixed_operation_id = (
                    f"{self.tool_name_prefix}{operation_id}" if self.tool_name_prefix else operation_id
                )

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
        auth_manager: AuthManager | None = None,
        keycloak_url: str = "https://keycloak.acc.iam-services.aws.inform-cloud.io/",
        realm_name: str = "inform-ai",
        client_id: str = "ai-cli-device"
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
        """
        Apply the same truncation logic used when creating tools

        Returns:
            Truncated tool name (max 64 characters)
        """
        if len(tool_name) <= 64:
            return tool_name

        # Try to preserve the important parts by removing redundant prefixes/suffixes
        truncated = tool_name

        # Remove common redundant parts
        redundant_patterns = ["_api_", "api_", "_post", "_get", "_put", "_delete"]
        for pattern in redundant_patterns:
            if pattern in truncated and len(truncated) > 64:
                replacement = "_" if (pattern.startswith("_") and pattern.endswith("_")) else ""
                truncated = truncated.replace(pattern, replacement, 1)

        # If still too long, truncate from the end
        if len(truncated) > 64:
            truncated = truncated[:64]

        return truncated

    def get_tool_by_operation_id(self, operation_id: str) -> Tool[OpenAPIToolDependencies] | None:
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
        """
        Get the dependencies type for type annotations

        Returns:
            The OpenAPIToolDependencies class type
        """
        return OpenAPIToolDependencies

    def get_tags_for_tool(self, tool_name: str) -> list[str]:
        """
        Get the tags associated with a specific tool

        Args:
            tool_name: The name of the tool (may include prefix)

        Returns:
            List of tags for the tool, or empty list if tool not found or has no tags
        """
        return self.tool_tags.get(tool_name, [])

    def get_all_tool_tags(self) -> dict[str, list[str]]:
        """
        Get all tool tags as a dictionary

        Returns:
            Dictionary mapping tool names to their tags
        """
        return self.tool_tags.copy()
