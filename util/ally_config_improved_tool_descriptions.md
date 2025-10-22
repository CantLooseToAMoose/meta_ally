# Improved Tool Docstrings

This document contains improved docstrings for tools generated from the Ally Portal OpenAPI specification.

---

## get_aws_logs_api_getAWSLogs_post

```
"""
Retrieve AWS log data from a specified log group within a given time range.

This function fetches log entries from an AWS log group, optionally filtering
the results by a specific session ID. It supports specifying start and end
times to limit the logs retrieved to a particular time window. The response
includes the list of log entries matching the criteria as well as a dictionary
mapping session IDs to their corresponding timestamps.

Args:
    log_group (str): The name of the AWS log group to query.
    session_id (str or None): Optional session ID to filter the logs. If None,
        logs from all sessions within the time range are returned.
    start_time (str): The ISO 8601 formatted start time for retrieving logs.
    end_time (str): The ISO 8601 formatted end time for retrieving logs.

Returns:
    dict: A response object containing:
        - 'logs' (list): List of log entries retrieved from the AWS log group.
        - 'session_ids' (dict): Dictionary mapping session IDs to their timestamps.

Raises:
    NoSuccess: If the specified log group does not exist or if there is an
        error retrieving the logs from AWS.
"""
```

---

## get_capabilities_api_capabilities_get

```
"""
Retrieves the current configuration capabilities of the Ally Portal.

This route provides essential configuration parameters required for integration and authentication purposes,
including details related to the Keycloak identity management server and Ally server environment.

Returns:
    CapabilitiesResponse: An object containing the following configuration details:
        - Keycloak server URL: The URL endpoint for Keycloak authentication.
        - Realm: The Keycloak security realm name.
        - Client ID: The client identifier registered with Keycloak.
        - Ally server domain: The domain where the Ally Portal is hosted.
        - AI knowledge host: The host URL serving AI knowledge resources.
"""
```

---

## get_active_config_api_getActiveConfig_post

```
"""
Retrieve the active or a historical Copilot configuration for a specified endpoint.

This function fetches the configuration data from the database for a given endpoint. If a specific configuration ID is provided, it returns the historical configuration corresponding to that ID; otherwise, it returns the currently active configuration. The configuration may be updated automatically if it uses an outdated data model version. Invalid configurations will still be returned, but will include a `validation_error` field describing the issues.

Args:
    endpoint (str): Name of the endpoint for which the configuration is requested.
    config_data (dict): Configuration details for the Copilot engine including:
        - dep_name (str): OpenAI model deployment name, e.g., 'gpt-4o-mini'.
        - temperature (float): Temperature setting for the language model. Defaults to 0. Use a negative value to apply the model’s default temperature.
        - history_reduction (dict or None): Settings for history reduction mechanism, including flags for old calls, bad calls, and large API responses.
        - instructions (str or None): Custom instructions for the language model; if empty, default instructions are used.
        - default_message (str or None): Predefined initial message sent to the user; falls back to default if empty.
        - initial_prompt_suggestions (list of str or None): Predefined suggestions for initial user prompts.
        - plugins (dict or None): Dictionary of plugin configurations keyed by plugin name, supporting AiKnowledge, ClientCalling, CodeExecution, and OpenAPI plugin types with their specific settings.
    config_id (str or None): Identifier of the specific configuration to retrieve; if None, fetches the active configuration.

Returns:
    dict: A LenientConfig-like response containing:
        - id (str): The ID of the returned configuration.
        - name (str): Timestamp string representing when the configuration was created.
        - engine_data (dict): The detailed configuration data used by the Copilot engine.
        - validation_error (str, optional): Error message if the configuration is invalid.

Raises:
    NonExistentEndpointError (404): If the requested endpoint does not exist.
    InvalidInput (200 + success=False): If the provided configuration ID is invalid.
    NoSuccess (200 + success=False): If the configuration could not be retrieved for any other reason.
    PermissionError (403): If the user lacks permission to view the configuration.
"""
```

---

## validate_config_api_validateConfig_post

```
"""
Validates the configuration data for a specified endpoint in the Ally Portal.

This function checks the provided configuration data against the Pydantic ConfigData model to ensure its validity.
It also verifies whether the selected AI model deployment is enabled and properly configured.

Args:
    endpoint (str): The name of the endpoint whose configuration is to be validated.
    config_data (dict, optional): A dictionary containing the configuration settings for the AI engine, including:
        - dep_name (str): Deployment name of the OpenAI model (e.g., 'gpt-4o-mini').
        - temperature (float, optional): Sampling temperature for the language model; default is 0. Use a negative value to apply the model's default temperature.
        - history_reduction (dict or None, optional): Settings related to history reduction mechanisms.
        - instructions (str or None, optional): Custom instructions for the language model; defaults used if empty.
        - default_message (str or None, optional): Predefined initial message sent to users; defaults used if empty.
        - initial_prompt_suggestions (list of str or None, optional): Suggested starting prompts for users.
        - plugins (dict or None, optional): Dictionary defining plugin configurations by name, each specifying parameters for AiKnowledge, ClientCalling, CodeExecution, or OpenAPI-based plugins.
    config_id (str or None, optional): Identifier of the specific configuration to validate. If None, validates the currently active configuration.

Returns:
    dict: A response object indicating whether the configuration is valid. If invalid, includes error messages detailing issues found during validation.

Raises:
    ValidationError: If the configuration data does not conform to required schema or contains invalid values.
"""
```

---

## set_config_api_setConfig_post

```
"""Set the configuration for a specified endpoint in the Ally Portal.

This function updates the Copilot configuration settings for the given endpoint with 
the provided engine and plugin configurations. It supports detailed customization 
of the language model parameters, history reduction mechanisms, initial user prompts, 
and integration of various plugins such as AiKnowledge, ClientCalling, CodeExecution, 
and OpenAPI plugins.

Args:
    endpoint (str): The name of the endpoint whose configuration is to be set.
    config_data (dict, optional): A dictionary containing the configuration settings 
        for the endpoint. This includes:
        - dep_name (str): The OpenAI model deployment name (e.g., 'gpt-4o-mini').
        - temperature (float, optional): Sampling temperature for the language model. 
          Defaults to 0. Negative values will use the model's default temperature.
        - history_reduction (dict or None, optional): Settings for history reduction 
          mechanisms, such as filtering old or bad calls and large API responses.
        - instructions (str or None, optional): Custom instructions for the language model.
        - default_message (str or None, optional): Predefined first message sent to users.
        - initial_prompt_suggestions (list[str] or None, optional): Suggested prompts 
          for initial user interactions.
        - plugins (dict or None, optional): Configuration for plugins keyed by plugin name.
          Supported plugin types include AiKnowledge, ClientCalling, CodeExecution, and OpenAPI.
    config_id (str or None, optional): The ID of the configuration to fetch or update. 
        If None, applies to the currently active configuration.

Returns:
    dict: A response object containing the ID of the newly set configuration.

Raises:
    NonExistentEndpointError: If the specified endpoint does not exist (HTTP 404).
    InvalidInput: If the selected model is not available or the input configuration is invalid.

"""
```

---

## get_config_history_api_getConfigHistory_post

```
"""Retrieve the configuration history for a specified active endpoint within the Ally Portal.

This function fetches a list of configuration history entries associated with a particular endpoint.
It returns only the names and IDs of the configurations, enabling users to review past setups 
without exposing full configuration details. This is useful for auditing, rollback, or comparison purposes.

Args:
    endpoint (str): The name of the endpoint for which to retrieve configuration history.
    config_data (dict, optional): Configuration details for the request, including:
        dep_name (str): OpenAI model deployment name, e.g., 'gpt-4o-mini'.
        temperature (float, optional): Temperature setting for the language model, default is 0. 
            Use negative value to apply model's default temperature.
        history_reduction (dict or None, optional): Settings to reduce history size based on criteria 
            like old calls, bad calls, or large API responses.
        instructions (str or None, optional): Custom instructions for the language model; if omitted, 
            default instructions are used.
        default_message (str or None, optional): Predefined initial message sent to the user; if omitted, 
            a default message is used.
        initial_prompt_suggestions (list[str] or None, optional): Suggested prompts to present initially to the user.
        plugins (dict or None, optional): Dictionary of plugin configurations keyed by plugin name.
    config_id (str or None, optional): Specific configuration ID to fetch history for. If None, uses the currently active configuration.

Returns:
    dict: A response object containing a list of configuration history items for the specified endpoint, 
        each item including name and ID only.
"""
```

---

## create_endpoint_api_createEndpoint_post

```
"""
Create a new endpoint with specified attributes and metadata.

This function registers a new endpoint in the Ally Portal, associating it with the given model and configuration details.
The endpoint name must be unique and must begin with a valid scope prefix.
Attributes such as the underlying model (dep_name), instructions, and a default message are provided to define the endpoint's behavior.
Optional metadata like a human-readable display name, description, and project number help manage and identify the endpoint.

Args:
    endpoint (str): The unique name of the endpoint to be created. Must begin with a valid scope prefix.
    endpoint_attributes (Optional[dict]): A dictionary containing attributes for the endpoint including:
        - dep_name (str): The model assigned to this endpoint.
        - instructions (Optional[str]): Optional instructions guiding the endpoint's behavior.
        - default_message (str): Default message used by the endpoint.
    endpoint_metadata (Optional[dict]): A dictionary containing metadata to manage the endpoint including:
        - display_name (Optional[str]): Human-readable name for easier identification.
        - description (Optional[str]): Description of the endpoint's purpose.
        - project_number (Optional[str]): Associated project number.

Returns:
    dict: A response indicating success or failure of the endpoint creation operation.

Raises:
    InvalidInput: If the endpoint name is invalid, already exists, or the specified model (dep_name) is not available.
"""
```

---

## get_endpoint_metadata_api_getEndpointMetadata_post

```
"""
Retrieve detailed metadata information for a specified API endpoint.

This function queries the Ally Portal backend to obtain metadata associated
with a given endpoint. The metadata may include configuration details, usage
statistics, access permissions, and other relevant information that helps
manage and analyze the endpoint within the Copilot configurations.

Args:
    endpoint (str): The API endpoint for which metadata is requested.

Returns:
    dict: A response object containing the metadata information for the 
    specified endpoint, including any relevant fields defined by the Ally 
    Portal API schema.
"""
```

---

## update_endpoint_metadata_api_updateEndpointMetadata_post

```
"""Update metadata for a specified endpoint within the Ally Portal.

This function allows updating the human-readable display name, detailed description,
and associated project number for a given API endpoint. It ensures that metadata
reflects the correct and current information that is used to manage Copilot configurations.

Args:
    endpoint (str): The identifier of the endpoint whose metadata is to be updated.
    metadata (dict): A dictionary containing the metadata fields to update. Supported keys:
        - display_name (str or None): A human-readable name for the endpoint.
        - description (str or None): A detailed description of what the endpoint does.
        - project_number (str or None): The project number associated with this endpoint.

Returns:
    dict: A response object indicating the success or failure of the metadata update operation.
"""
```

---

## delete_endpoint_api_deleteEndpoint_post

```
"""Delete an existing endpoint and all associated data from the Ally Portal.

This operation removes the specified endpoint identified by its name. The endpoint must exist
in the system, and the user invoking this action must have the necessary permissions to perform deletion.
If the endpoint does not exist or permissions are insufficient, an error will be raised.

Args:
    endpoint (str): The name of the endpoint to be deleted.

Returns:
    dict: A response object indicating whether the deletion was successful or if it failed,
    potentially including error messages.

Raises:
    InvalidInput: If the specified endpoint does not exist in the system.
    PermissionError: If the user does not have permission to delete the endpoint.
"""
```

---

## get_endpoints_api_getEndpoints_post

```
"""
Retrieve a list of API endpoints filtered by an optional prefix.

This function returns a list of endpoints that the authenticated user has permission to access. If a prefix is specified, only endpoints whose names start with the given prefix are returned. If no prefix or a root prefix ("/") is provided, the function lists endpoints across all scopes.

Args:
    prefix (str or None): Optional prefix string to filter the endpoints by their name. If None, endpoints from all scopes are listed.

Returns:
    dict: A response object containing a list of endpoint suffixes matching the prefix along with their associated metadata.
"""
```

---

## get_endpoint_authorization_api_endpoint_authorization_get

```
"""
Retrieve the authorization configuration for a specified API endpoint within the Ally Portal.

This function fetches the current authorization settings associated with a given endpoint name,
allowing the caller to understand the permissions and access controls configured for that endpoint.

Args:
    endpoint (str): The name of the API endpoint to retrieve authorization details for.
    userauth (object): The user authorization context used to verify if the requester has the 
        necessary permissions to access the endpoint's authorization configuration.

Returns:
    dict: A dictionary representing the authorization configuration of the specified endpoint,
        detailing roles, permissions, or other access control settings applied.
"""
```

---

## update_endpoint_authorization_api_endpoint_authorization_post

```
"""
Update the authorization configuration for a specified API endpoint within the Ally Portal.

This function modifies the authorization settings of the given endpoint to control access permissions. The update ensures that the endpoint's authorization configuration aligns with the desired security policies for managing Copilot configurations.

Args:
    endpoint (str): The name of the API endpoint whose authorization configuration is to be updated.
    auth_config (dict): The new authorization configuration settings to apply to the endpoint.
    userauth (object): A user authorization object used to verify that the invoking user has sufficient permissions to perform this update.

Raises:
    PermissionError: If the user does not have the required permissions to update the endpoint authorization.
    ValueError: If the provided authorization configuration is invalid.
"""
```

---

## delete_endpoint_authorization_api_endpoint_authorization_delete

```
"""Delete the authorization configuration for a specified API endpoint.

This action will remove any custom authorization settings applied to the 
given endpoint, causing it to revert to the default authorization configuration.

Args:
    endpoint (str): The name of the API endpoint whose authorization 
        configuration should be deleted.

Raises:
    AuthorizationError: If the user does not have permission to delete the 
        endpoint authorization.
    EndpointNotFoundError: If the specified endpoint does not exist.
"""
```

---

## execute_evaluation_suite_api_executeEvaluationSuite_post

```
"""
Executes an evaluation suite on a specified endpoint within the Ally Portal.

This function triggers the execution of a given test suite identified by its name
against a specific endpoint. It is used to run automated evaluations that help 
validate Copilot configurations and ensure they behave as expected.

Args:
    endpoint (str): The name of the endpoint where the evaluation should be executed.
    test_suite_name (str): The name of the test suite to be run for the evaluation.

Returns:
    dict: A response object containing the results of the evaluation, including
        success or failure statuses and detailed metrics.

Raises:
    NoSuccess: If the specified test suite does not exist or if the provided
        endpoint is invalid, indicating the evaluation could not be performed.
"""
```

---

## get_stored_evaluation_results_api_getStoredEvaluationResults_post

```
"""
Retrieve evaluation results for a specified test suite from a given endpoint.

This function queries the Ally Portal API to obtain the stored evaluation results 
associated with a particular test suite name at the specified endpoint. It is 
useful for accessing the outcomes of test suites that have been previously run 
to assess configuration performance or correctness.

Args:
    endpoint (str): The name of the API endpoint to query for evaluation results.
    test_suite_name (str): The exact name of the test suite whose results are to be retrieved.

Returns:
    dict: A response object containing the evaluation results data for the specified test suite.

Raises:
    NoSuccess: If the provided test suite name does not exist or the endpoint is invalid.
"""
```

---

## get_evaluation_suites_api_getEvaluationSuites_post

```
"""
Fetches the list of evaluation suite names from AWS based on the specified endpoint.

This function communicates with a given API endpoint to retrieve the names of evaluation suites available in the AWS environment. Evaluation suites are configurations or collections used to assess and validate different Copilot setups within the Ally Portal.

Args:
    endpoint (str): The name of the API endpoint to query for evaluation suites.

Returns:
    dict: A response object containing a list of evaluation suite names retrieved from AWS.
"""
```

---

## get_evaluation_suite_by_name_api_getEvaluationSuiteContentsByName_post

```
"""
Retrieve the contents of a specific evaluation test suite from AWS by its name.

This function fetches the detailed configuration and tests included in the specified evaluation suite 
hosted on an AWS endpoint, identified by the given endpoint name.

Args:
    endpoint (str): The name of the AWS endpoint where the evaluation suite is stored.
    test_suite_name (str): The exact name of the evaluation test suite to retrieve.

Returns:
    dict: A response object containing the stored test suite details such as test configurations and metadata.

Raises:
    NoSuccess: If the test suite with the specified name does not exist at the given endpoint or retrieval fails.
"""
```

---

## get_evaluation_suite_history_by_name_api_getEvaluationSuiteHistoryByName_post

```
"""Retrieve the version history of a specified evaluation test suite from AWS.

This function queries the AWS backend to obtain the previous versions of a given evaluation suite 
identified by its name and the specified endpoint within the Ally Portal environment.

Args:
    endpoint (str): The name of the API endpoint to target for fetching the evaluation suite history.
    test_suite_name (str): The exact name of the evaluation test suite whose version history is requested.

Returns:
    dict: A response object containing a list of all previous versions of the specified evaluation suite, 
          including relevant metadata such as version numbers and timestamps.

Raises:
    NoSuccess: If the specified test suite does not exist or the retrieval fails for any other reason.
"""
```

---

## create_evaluation_suite_api_createEvaluationSuite_post

```
"""
Creates a new evaluation suite in AWS for a specified endpoint.

This function registers a new test suite identified by `test_suite_name` under the given `endpoint`. 
The evaluation suite is used within the Ally Portal to organize and manage Copilot configuration tests.

Args:
    endpoint (str): The name of the endpoint under which the evaluation suite will be created.
    test_suite_name (str): The unique name of the test suite to be created. Must be valid and non-duplicate.

Returns:
    dict: A response object indicating the success or failure of the creation operation.

Raises:
    NoSuccess: If a test suite with the same name already exists for the given endpoint.
    ValueError: If the `test_suite_name` provided is invalid according to naming rules.
"""
```

---

## add_test_cases_to_evaluation_suite_api_addTestCasesToEvaluationSuite_post

```
"""
Add multiple test cases to a specified evaluation test suite within the Ally Portal.

This function allows you to augment an existing evaluation suite by providing a set of dialog test cases. Each test case represents a single interaction turn in a dialogue, including the user input, expected dialog engine response, and any expected API service calls. Multi-turn dialog sequences can be supported by linking test cases using the `continues` field, although this feature is not yet implemented.

Args:
    endpoint (str): The API endpoint related to the evaluation interactions.
    test_suite_name (str): The unique name of the evaluation test suite to which the test cases will be added.
    test_cases (list of dict): A list of dialog test case definitions, where each test case dictionary contains:
        - name (str): A unique identifier for the test case.
        - description (str, optional): An optional human-readable description of the test case.
        - user_input (str): The simulated user input text for this test case.
        - expected_actions (list, optional): A list of expected API calls or other actions triggered by the user input.
        - expected_response (str, optional): The expected dialog engine response corresponding to the user input.
        - continues (str, optional): The name of a preceding test case in a multi-turn dialog chain.

Returns:
    dict: A response object indicating the success or failure of adding the test cases to the evaluation suite.

Raises:
    NoSuccess: If the specified test suite does not exist or adding test cases fails.
"""
```

---

## save_evaluation_suite_api_saveEvaluationSuite_post

```
"""
Saves or updates an evaluation test suite in the Ally Portal for a specified endpoint.

This function allows you to create or modify a test suite used to evaluate the dialog engine's responses. The suite consists of multiple test cases, each representing a single interaction turn, where a user input is provided and the expected system actions and responses are defined.

Args:
    endpoint (str): The name of the endpoint associated with the evaluation suite.
    test_suite_name (str): The unique name of the test suite to save or update.
    test_cases (List[Dict]): A list of test case objects defining individual dialog turns. Each test case must include:
        - name (str): Unique identifier for the test case.
        - user_input (str): The user input text for this test case.
        - description (str, optional): Additional details about the test case (not used by the evaluation suite).
        - continues (str, optional): Name of the preceding test case if this is part of a multi-turn dialog chain (currently not implemented).
        - expected_actions (List[Any], optional): List of expected API calls or actions triggered by the dialog engine.
        - expected_response (str, optional): The expected textual response from the dialog engine for this input.

Returns:
    dict: A response object indicating the success or failure of saving the evaluation suite.

Raises:
    NoSuccess: If the specified test suite does not exist or the operation fails.
"""
```

---

## get_cost_graph_snapshot_api_getCostGraphSnapshot_post

```
"""
Fetches a snapshot image of token usage over the course of one week for a specified API endpoint.

This function retrieves a visual representation of token consumption, useful for analyzing usage patterns and cost management.

Args:
    endpoint (str): The name of the API endpoint for which to retrieve the token usage graph.
    month (int or None): The specific month for which data is requested. If None, defaults to the current month or available data.
    unit (str): The unit of measurement for the token usage, e.g., "tokens" or "euro".

Returns:
    dict: A response object containing a base64 encoded string of the graph image depicting token usage.

Raises:
    ValueError: If required parameters are missing or invalid.
"""
```

---

## get_cost_per_day_api_getCostPerDay_post

```
"""
Retrieve the daily token usage or cost for a specific API endpoint within a given month.

This function fetches usage data for the specified endpoint, aggregated by day, and returns it in the requested unit of measurement. It is designed to help monitor and analyze the consumption or cost patterns over time for better resource management.

Args:
    endpoint (str): The name of the API endpoint for which to retrieve usage data.
    month (int or None): The month (1-12) for which to retrieve data. If None, data for all available months may be returned.
    unit (str): The unit of measurement for the usage data (e.g., 'tokens' or 'euro').

Returns:
    dict: A dictionary where each key is a date (ISO 8601 format string) and the corresponding value is the token usage or cost for that day expressed in the specified unit.

Raises:
    InvalidInput: If the specified unit is not supported or if input parameters are invalid.
"""
```

---

## get_permissions_api__resource_type__permissions_get

```
"""
Retrieves all user-manageable permissions associated with a specific resource.

This API fetches a detailed list of roles assigned to the given resource, where each role includes the users associated with it and their respective permissions. The permissions returned are limited to those that users can manage directly.

If the specified resource has no permissions configured, the API responds with a 404 error.

Args:
    resource_type (str): The type or category of the resource (e.g., "document", "project").
    resource_name (str): The unique name or identifier of the resource for which permissions are requested.

Returns:
    dict: A dictionary containing the following keys:
        - success (bool): Indicates whether the API call was successful.
        - data (list): A list of roles for the resource; each role includes a list of users and their associated permissions.
"""
```

---

## add_role_api__resource_type__role_post

```
"""
Add a new role to a specified resource within the Ally Portal.

This function creates a new role associated with a given resource type and resource name. 
The new role is initialized without any users or permissions assigned.

Args:
    resource_type (str): The type/category of the resource to which the role will be added.
    resource_name (str): The name identifier of the resource to which the role belongs.
    role (str): The name of the new role to be created and added to the resource.

Raises:
    HTTPException: If a role with the specified name already exists for the resource, 
                   a 422 error is returned indicating a conflict.
"""
```

---

## remove_role_api__resource_type__role_delete

```
"""
Remove a role from a specified resource within the Copilot configuration.

This function removes the given role from the identified resource type and resource name. Note that the owner role is protected and cannot be removed; attempting to do so will result in an HTTP 422 error.

Args:
    resource_type (str): The type/category of the resource from which the role will be removed.
    resource_name (str): The unique name of the resource from which the role is to be removed.
    role (str): The name of the role that should be removed from the resource.

Raises:
    HTTPException: If an attempt is made to remove the owner role, an HTTP 422 error is raised indicating this operation is not permitted.
"""
```

---

## grant_permission_api__resource_type__role_permission_post

```
"""
Grant a specific permission to a role for a given resource within the Ally Portal.

This function enables assigning a permission identified by its ID to a specified role, scoped to a particular resource type and resource name. It updates the access controls by adding the permission to the role on the resource, facilitating fine-grained permission management in Copilot configurations.

Args:
    resource_type (str): The type/category of the resource to which the permission applies.
    resource_name (str): The name of the resource on which the role's permissions will be updated.
    role (str): The name of the role that will be granted the permission.
    permission (str): The unique identifier of the permission to add to the role.

Raises:
    HTTPException: If the permission is already granted to the role (status code 422), indicating that the operation is redundant.
"""
```

---

## revoke_permission_api__resource_type__role_permission_delete

```
"""
Revokes a specific permission from a given role on a designated resource.

This function removes an explicitly granted permission for a role related to a particular resource type and resource name within the Ally Portal. It ensures that the specified permission is no longer associated with the role for that resource.

Args:
    resource_type (str): The type/category of the resource from which the permission is to be revoked.
    resource_name (str): The name of the specific resource instance associated with the permission.
    role (str): The name of the role from which the permission will be revoked.
    permission (str): The identifier of the permission to be removed from the role.

Raises:
    HTTPException: Raised with status code 422 if the specified permission is not currently granted to the role on the resource.
"""
```

---

## add_user_api__resource_type__role_user_post

```
"""
Adds a user to a specific role within a given resource in the Ally Portal.

This function associates a specified user with a role assigned to a resource, enabling them to access or manage that resource according to the role's permissions. It is used to grant role-based access control to users for various resource types.

Args:
    resource_type (str): The type/category of the resource (e.g., project, team, application).
    resource_name (str): The name identifier of the resource to which the role belongs.
    role (str): The name of the role to which the user is being added.
    user (str): The username of the user to be added to the role.

Raises:
    HTTPException: Raised with status code 422 if the user is already a member of the specified role on the given resource.
"""
```

---

## remove_user_api__resource_type__role_user_delete

```
"""
Remove a user from a specific role on a given resource.

This function removes the specified user from the assigned role associated with the given resource type and resource name.
Note that a user is not allowed to remove themselves from the owner role to prevent accidental loss of ownership.

Args:
    resource_type (str): The type/category of the resource (e.g., project, repository).
    resource_name (str): The name of the resource from which the user role should be removed.
    role (str): The name of the role to update by removing the user.
    user (str): The username of the user to remove from the role.

Raises:
    HTTPException (422): If the specified user is not currently assigned to the role on this resource.
"""
```

---

## get_ratings_aws_api_getRatingsAWS_post

```
"""
Retrieves ratings data from AWS DynamoDB within a specified time range.

This method fetches ratings stored in AWS DynamoDB, optionally filtered by a given 
time interval defined by start and end timestamps. It can target a specific API 
endpoint if provided.

Args:
    endpoint (str or None): The AWS API endpoint to query. Defaults to None.
    start (str or None): The start datetime (ISO 8601 format) to filter ratings from. 
        If None, no lower time bound is applied.
    end (str or None): The end datetime (ISO 8601 format) to filter ratings up to. 
        If None, no upper time bound is applied.

Returns:
    list: A list of rating records retrieved from DynamoDB that match the criteria.

Raises:
    NoSuccess: If there is an error during the retrieval of ratings from AWS.
"""
```

---

## get_session_histories_api_getSessionHistories_post

```
"""
Retrieve session histories for a specified endpoint within a given time range.

Args:
    endpoint (str): The name of the endpoint for which session histories are requested.
    start_time (str): The start timestamp (in ISO 8601 format) marking the beginning of the desired session period.
    end_time (str): The end timestamp (in ISO 8601 format) marking the end of the desired session period.

Returns:
    Response: A response object containing a list of Conversation objects that represent the session histories
    recorded for the specified endpoint between the provided start and end times.

Raises:
    PermissionError: If the user authorization does not permit access to the requested session data.
    ValueError: If start_time or end_time are not valid datetime strings or if start_time > end_time.
"""
```

---

## get_available_AI_models_api_getAvailableAIModels_post

```
"""
Retrieve the list of available AI models from the model registry.

This endpoint fetches all AI models that are currently registered and available for use in endpoint configurations within the Ally Portal. It enables users to view which models can be selected and deployed as part of their Copilot configurations.

Returns:
    dict: A response object containing a list of available AI models, including relevant details for each model.
"""
```

---

## get_scopes_api_getScopes_post

```
"""
Retrieves all scopes available to the current user.

This function fetches and returns a comprehensive list of permission scopes
that the user has access to within the Ally Portal. Scopes define the 
specific permissions and access levels the user is granted for managing 
Copilot configurations.

Returns:
    dict: A response object containing a list of available scopes. Each 
          scope describes a particular permission or set of permissions 
          accessible to the user.
"""
```

---

## upload_file_to_S3_api_uploadToS3_post

```
"""
Uploads a file to an Amazon S3 bucket and returns the URI of the uploaded file.

This endpoint facilitates file storage by accepting a file upload request,
saving the file in an S3 bucket, and responding with the URI where the file is accessible.

Note:
    It is recommended to verify whether this route is actively used and necessary,
    as it may be subject to review or deprecation.

Returns:
    dict: A response object containing the URI of the uploaded file in the following format:
        {
            "file_uri": "<S3_file_URI>"
        }
"""
```

---

