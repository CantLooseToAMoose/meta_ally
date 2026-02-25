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
        query_param_names: list[str],
        path_param_names: list[str],
        array_body_param_name: str | None = None
    ) -> tuple[str, dict[str, Any], dict[str, Any] | list[Any]]:
        """
        Build URL with path parameters and separate query/body parameters.

        This method takes the raw parameters from the tool call and separates them
        into their appropriate locations for the HTTP request:

        1. Path parameters - Substituted directly into the URL path
           Example: /users/{user_id} + user_id=123 -> /users/123

        2. Query parameters - Added to URL query string
           Example: ?limit=10&offset=0

        3. Body parameters - Sent as JSON in the request body
           Can be either a dict (normal case) or a list (array body case)

        Args:
            path: API path template with {param} placeholders
            kwargs: All parameters passed to the tool by the LLM
            query_param_names: Names of params that should go in query string
            path_param_names: Names of params that should be substituted in the path
            array_body_param_name: If the request body is an array type, this is
                                   the parameter name containing the array data.
                                   When set, body_params will be the array itself,
                                   not a dict wrapper.

        Returns:
            Tuple of:
            - final_url: Complete URL with path params substituted
            - query_params: Dict of query string parameters
            - body_params: Either a dict or list depending on API requirements
        """
        # Start with the path template and make a copy of kwargs to modify
        final_path = path
        remaining_kwargs = kwargs.copy()

        # Step 1: Extract and substitute path parameters into the URL
        # e.g., /api/users/{user_id}/posts/{post_id} -> /api/users/123/posts/456
        for key, value in list(kwargs.items()):
            placeholder = f"{{{key}}}"
            if placeholder in final_path:
                final_path = final_path.replace(placeholder, str(value))
                remaining_kwargs.pop(key, None)  # Remove from remaining params

        # Step 2: Separate query parameters from body parameters
        # Query params go in the URL, body params go in the request body
        # Exclude both query params AND path params from body_params_dict
        query_params = {k: v for k, v in remaining_kwargs.items() if k in query_param_names}
        body_params_dict = {
            k: v for k, v in remaining_kwargs.items()
            if k not in query_param_names and k not in path_param_names
        }

        # Step 3: Handle array body type
        # If the API expects an array as the body (not an object), extract the array
        # from the wrapper parameter and return it directly
        #
        # Example: API expects body = [{"name": "test1"}, {"name": "test2"}]
        # Tool receives: items=[{"name": "test1"}, {"name": "test2"}]
        # We return the array itself, not {"items": [...]}
        body_params: dict[str, Any] | list[Any]
        if array_body_param_name and array_body_param_name in body_params_dict:
            # Return the array directly as the body (unwrap from the parameter)
            body_params = body_params_dict[array_body_param_name]
        else:
            # Normal case: body is a JSON object with the remaining params
            body_params = body_params_dict

        return f"{self.base_url}{final_path}", query_params, body_params

    async def _execute_http_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        query_params: dict[str, Any],
        body_params: dict[str, Any] | list[Any],
        headers: dict[str, str]
    ) -> httpx.Response:
        """
        Execute the HTTP request based on the method.

        Handles all common HTTP methods and properly serializes the body.
        The body_params can be either a dict (normal JSON object) or a list
        (when the API expects an array as the request body).

        Args:
            client: Async HTTP client for making requests
            method: HTTP method (get, post, put, delete)
            url: Fully constructed request URL
            query_params: Parameters to add to the URL query string
            body_params: Request body - can be dict or list depending on API spec
            headers: HTTP headers including auth and content-type

        Returns:
            The HTTP response object

        Raises:
            ValueError: If the HTTP method is not supported
        """
        method_lower = method.lower()
        if method_lower == "get":
            return await client.get(url, params=query_params, headers=headers)
        elif method_lower == "post":
            return await client.post(url, params=query_params, json=body_params, headers=headers)
        elif method_lower == "put":
            return await client.put(url, params=query_params, json=body_params, headers=headers)
        elif method_lower == "delete":
            # httpx's delete() method doesn't accept content/json parameters
            # Use request() directly when body is present to support DELETE with body
            if body_params is not None:
                return await client.request(
                    "DELETE",
                    url,
                    params=query_params,
                    json=body_params,
                    headers=headers
                )
            else:
                # No body for DELETE request - use the convenience method
                return await client.delete(url, params=query_params, headers=headers)
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
        query_param_names: list[str],
        path_param_names: list[str],
        array_body_param_name: str | None = None
    ) -> Callable:
        """
        Create a function that will be wrapped as a Tool.

        This method generates an async function that:
        1. Validates and processes the tool parameters
        2. Builds the HTTP request (URL, query params, body)
        3. Handles authentication via the auth_manager
        4. Makes the API call and processes the response

        The generated function is what pydantic-ai calls when the LLM decides
        to use this tool. It bridges the gap between LLM tool calls and actual
        HTTP API requests.

        Args:
            operation_id: The operation ID from OpenAPI spec (used as function name)
            path: The API path template (e.g., /users/{user_id})
            method: HTTP method (get, post, put, delete)
            operation: The full operation definition from OpenAPI spec
            query_param_names: Parameter names that go in the URL query string
            path_param_names: Parameter names that get substituted into the URL path
            array_body_param_name: If the request body is an array type, this is
                                   the name of the parameter containing the array.
                                   Used to correctly serialize array bodies.

        Returns:
            An async callable function that can be wrapped as a pydantic-ai Tool
        """
        # Create the actual API call function
        # Note: We capture variables from the outer scope (closure) so they're
        # available when the function is called later by the agent
        async def api_call(ctx: RunContext[OpenAPIToolDependencies], **kwargs) -> dict[str, Any] | str:
            """
            Make an HTTP request to the API endpoint.

            This function is called by pydantic-ai when the LLM uses this tool.
            It handles the complete request lifecycle:
            1. Optional human approval for write operations
            2. URL construction with path parameter substitution
            3. Parameter separation (query vs body)
            4. Authentication header injection
            5. HTTP request execution
            6. Response parsing and error handling

            Args:
                ctx: The run context from pydantic-ai containing dependencies
                     (auth_manager and optional context like geschaeftsbereich)
                **kwargs: Parameters passed by the LLM for this API call

            Returns:
                The JSON response from the API, or a success message for empty responses

            Raises:
                ModelRetry: If the API request fails, prompting the LLM to retry
                            with different parameters or handle the error gracefully
            """
            # Check if human approval is required for write operations
            self._check_approval(operation_id, method, path, kwargs)

            # Build URL and separate parameters into query string vs request body
            # The array_body_param_name, query_param_names, and path_param_names are captured from the outer scope
            url, query_params, body_params = self._build_url_and_params(
                path, kwargs, query_param_names, path_param_names, array_body_param_name
            )

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

    def _resolve_single_schema_ref(self, schema: dict[str, Any]) -> dict[str, Any] | None:
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
            resolved = self._resolve_single_schema_ref(schema)
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

    def _process_parameter(
        self,
        param: dict[str, Any],
        schema: dict[str, Any],
        query_param_names: list[str],
        path_param_names: list[str]
    ) -> None:
        """Process a single parameter and add it to the schema"""
        param_name = param["name"]
        param_schema = param.get("schema", {})
        param_type = param_schema.get("type", "string")
        required = param.get("required", False)
        description = param.get("description", "")
        param_in = param.get("in", "query")

        # Track query and path parameters
        if param_in == "query":
            query_param_names.append(param_name)
        elif param_in == "path":
            path_param_names.append(param_name)

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
        """
        Process a $ref in request body schema and add properties to the tool's schema.

        When the request body references another schema (e.g., {"$ref": "#/components/schemas/User"}),
        this method resolves that reference and extracts the properties from the referenced schema.
        Each property is then added to the tool's parameter schema.

        Example OpenAPI:
            requestBody:
              content:
                application/json:
                  schema:
                    $ref: "#/components/schemas/UserRequest"

        Args:
            body_schema: The body schema dict containing a $ref key
            schema: The tool's parameter schema to add properties to
        """
        ref_name = body_schema["$ref"].split("/")[-1]
        resolved_schema = self._extract_ref_schema_properties(ref_name)

        if resolved_schema and "properties" in resolved_schema:
            # Add each property from the referenced schema to the tool's parameters
            for prop_name, prop_schema in resolved_schema["properties"].items():
                resolved_prop_schema = self._resolve_schema_refs(prop_schema)
                schema["properties"][prop_name] = resolved_prop_schema

            # Preserve required field constraints from the referenced schema
            if "required" in resolved_schema:
                schema["required"].extend(resolved_schema["required"])

    def _process_body_schema_properties(self, body_schema: dict[str, Any], schema: dict[str, Any]) -> None:
        """
        Process direct properties in request body schema.

        When the request body defines properties inline (without a $ref),
        this method extracts those properties and adds them to the tool's schema.

        Example OpenAPI:
            requestBody:
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      name: {type: string}
                      age: {type: integer}

        Args:
            body_schema: The body schema dict containing a "properties" key
            schema: The tool's parameter schema to add properties to
        """
        for prop_name, prop_schema in body_schema["properties"].items():
            resolved_prop_schema = self._resolve_schema_refs(prop_schema)
            schema["properties"][prop_name] = resolved_prop_schema

        if "required" in body_schema:
            schema["required"].extend(body_schema["required"])

    def _process_body_schema_composition(  # noqa: C901
        self,
        body_schema: dict[str, Any],
        schema: dict[str, Any]
    ) -> None:
        """
        Process composition schemas (oneOf, anyOf, allOf) in request body.

        When the request body uses oneOf/anyOf/allOf to define multiple possible
        schemas, this method extracts properties from the first valid option.
        For allOf, it merges properties from all schemas.

        Example OpenAPI:
            requestBody:
              content:
                application/json:
                  schema:
                    oneOf:
                      - $ref: "#/components/schemas/EngineConfig-Input"
                      - $ref: "#/components/schemas/BogusEngineConfig"

        Args:
            body_schema: The body schema dict containing oneOf/anyOf/allOf
            schema: The tool's parameter schema to add properties to
        """
        # For allOf, merge all schemas
        if "allOf" in body_schema:
            for item in body_schema["allOf"]:
                resolved_item = self._resolve_schema_refs(item)
                if "properties" in resolved_item:
                    for prop_name, prop_schema in resolved_item["properties"].items():
                        schema["properties"][prop_name] = self._resolve_schema_refs(prop_schema)
                    if "required" in resolved_item:
                        schema["required"].extend(resolved_item["required"])

        # For oneOf/anyOf, use the first option that has properties
        # (LLM tools can't express "one of" so we pick the most complete option)
        for key in ["oneOf", "anyOf"]:
            if key in body_schema:
                for item in body_schema[key]:
                    resolved_item = self._resolve_schema_refs(item)
                    if "properties" in resolved_item:
                        for prop_name, prop_schema in resolved_item["properties"].items():
                            schema["properties"][prop_name] = self._resolve_schema_refs(prop_schema)
                        if "required" in resolved_item:
                            schema["required"].extend(resolved_item["required"])
                        # Use first option with properties
                        return

    def _process_body_schema_array(
        self,
        body_schema: dict[str, Any],
        schema: dict[str, Any],
        request_body: dict[str, Any]
    ) -> str | None:
        """
        Process array-type request body schemas.

        When the API expects the request body to be a JSON array (not an object),
        we need special handling. This creates a single parameter that will hold
        the entire array, rather than trying to extract object properties.

        Example OpenAPI:
            requestBody:
              content:
                application/json:
                  schema:
                    type: array
                    items:
                      $ref: "#/components/schemas/DialogTestCase"

        This would result in a tool parameter like:
            items: list[DialogTestCase]  # The entire array is passed as this param

        Args:
            body_schema: The body schema dict with type="array"
            schema: The tool's parameter schema to add the array parameter to
            request_body: The full requestBody definition (for extracting description)

        Returns:
            The name of the array body parameter (e.g., "items") if this is an array
            body schema, or None if not an array type.
        """
        if body_schema.get("type") != "array":
            return None

        # Determine the parameter name from the schema or use a default
        # OpenAPI may provide a title for the array, otherwise use "items"
        array_param_name = body_schema.get("title", "items")
        # Convert to snake_case for Python convention (e.g., "Test Cases" -> "test_cases")
        array_param_name = array_param_name.lower().replace(" ", "_")

        # Get description from the body schema or request body description
        description = body_schema.get(
            "description",
            request_body.get("description", "Array of items to send as the request body")
        )

        # Build the array parameter schema
        array_schema: dict[str, Any] = {
            "type": "array",
            "description": description
        }

        # Resolve the items schema (handles $ref in items)
        if "items" in body_schema:
            array_schema["items"] = self._resolve_schema_refs(body_schema["items"])

        # Add the array as a single parameter to the tool schema
        schema["properties"][array_param_name] = array_schema

        # Array body is required if the requestBody itself is required
        if request_body.get("required"):
            schema["required"].append(array_param_name)

        return array_param_name

    def _process_request_body(
        self,
        request_body: dict[str, Any],
        schema: dict[str, Any]
    ) -> str | None:
        """
        Process the request body and add its parameters to the tool schema.

        This method handles three types of request body schemas:
        1. $ref - References another schema (e.g., UserRequest model)
        2. properties - Inline object with properties defined directly
        3. array - The body itself is an array (e.g., list of test cases)

        For object-type bodies (cases 1 & 2), each property becomes a separate
        tool parameter. For array-type bodies (case 3), a single parameter is
        created to hold the entire array.

        Args:
            request_body: The requestBody definition from OpenAPI spec
            schema: The tool's parameter schema to populate

        Returns:
            The name of the array body parameter if the body is an array type,
            otherwise None. This is used later to correctly serialize the request.
        """
        if not (request_body and "content" in request_body):
            return None

        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        body_schema = json_content.get("schema", {})

        # Case 1: Body schema is a reference to another schema
        # e.g., $ref pointing to #/components/schemas/CreateUserRequest
        if "$ref" in body_schema:
            self._process_body_schema_ref(body_schema, schema)
            return None

        # Case 2: Body schema has inline properties
        # e.g., type=object with properties defining each field
        elif "properties" in body_schema:
            self._process_body_schema_properties(body_schema, schema)
            return None

        # Case 3: Body schema is an array type
        # e.g., type=array with items referencing a schema
        # The API expects a JSON array as the body, not an object
        elif body_schema.get("type") == "array":
            return self._process_body_schema_array(body_schema, schema, request_body)

        # Case 4: Body schema uses composition (oneOf, anyOf, allOf)
        # e.g., oneOf with multiple possible schema references
        elif any(key in body_schema for key in ["oneOf", "anyOf", "allOf"]):
            self._process_body_schema_composition(body_schema, schema)
            return None

        return None

    def _extract_parameters_schema(
        self,
        operation: dict[str, Any]
    ) -> tuple[dict[str, Any], list[str], list[str], str | None]:
        """
        Extract and create a JSON schema from operation parameters.

        This is a key method that converts OpenAPI operation parameters into a
        JSON schema that pydantic-ai can use for the tool. It handles:

        1. Path parameters - Variables in the URL path (e.g., /users/{user_id})
        2. Query parameters - URL query string params (e.g., ?limit=10&offset=0)
        3. Request body - JSON body for POST/PUT/PATCH requests

        The resulting schema defines what arguments the LLM can pass to the tool.

        Args:
            operation: The operation definition from OpenAPI spec, containing
                      'parameters' and optionally 'requestBody'

        Returns:
            A tuple containing:
            - JSON schema dict for tool parameters (what the LLM sees)
            - List of query parameter names (to separate from body params at runtime)
            - List of path parameter names (to exclude from body params at runtime)
            - Array body parameter name if the request body is an array type,
              otherwise None (needed to correctly serialize array bodies)
        """
        # Initialize the schema structure for the tool's parameters
        # This follows JSON Schema format which pydantic-ai uses
        schema = {
            "type": "object",
            "properties": {},       # Will hold each parameter definition
            "required": [],         # List of required parameter names
            "additionalProperties": False  # Strict: no extra params allowed
        }

        # Track which parameters are query params, path params, vs body params
        # This is needed later when building the actual HTTP request
        query_param_names: list[str] = []
        path_param_names: list[str] = []

        # Process path and query parameters from the 'parameters' array
        # These come from the URL path (e.g., {user_id}) and query string
        parameters = operation.get("parameters", [])
        for param in parameters:
            self._process_parameter(param, schema, query_param_names, path_param_names)

        # Process request body parameters
        # For POST/PUT/PATCH, the body may contain additional data
        # Returns the array param name if the body is an array type
        request_body = operation.get("requestBody")
        array_body_param_name = self._process_request_body(request_body, schema)

        return schema, query_param_names, path_param_names, array_body_param_name

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

                # Extract parameters schema, query parameter names, path parameter names, and array body info
                # - parameters_schema: JSON schema defining the tool's parameters
                # - query_param_names: Which params go in the URL query string
                # - path_param_names: Which params are substituted into the URL path
                # - array_body_param_name: If body is an array, the param name holding it
                (
                    parameters_schema,
                    query_param_names,
                    path_param_names,
                    array_body_param_name
                ) = self._extract_parameters_schema(operation)

                # Create the tool function that will make the actual API calls
                tool_func = self._create_tool_function(
                    operation_id=operation_id,
                    path=path,
                    method=method,
                    operation=operation,
                    query_param_names=query_param_names,
                    path_param_names=path_param_names,
                    array_body_param_name=array_body_param_name
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
