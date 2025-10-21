# Improved Tool Docstrings

This document contains improved docstrings for tools generated from the Ally Portal OpenAPI specification.

---

## get_aws_logs_api_getAWSLogs_post

```
"""
Retrieve AWS log data from a specified CloudWatch log group within a given time range.

This function fetches log entries from the specified AWS log group, optionally filtered by a session ID.
It returns the relevant logs along with a dictionary mapping session IDs to their corresponding timestamps.

Parameters:
    log_group (str): The name of the AWS CloudWatch log group to query.
    session_id (str or None): Optional session ID to filter the log entries. Use None to include all sessions.
    start_time (str): The start time (ISO 8601 format or compatible) for the log retrieval period.
    end_time (str): The end time (ISO 8601 format or compatible) for the log retrieval period.

Returns:
    dict: A response containing the retrieved log entries and a dictionary of session IDs with timestamps.

Raises:
    NoSuccess: If the specified log group does not exist or if there is an error retrieving the logs.
"""
```

---

## get_capabilities_api_capabilities_get

```
"""
Retrieve the current configuration parameters of the Ally Portal.

This API endpoint provides essential capability details required for integrating
and managing Copilot configurations within the Ally Portal. It returns vital
information including the Keycloak authentication server URL, security realm,
client identifier, as well as the Ally server domain and AI knowledge host URL.

Returns:
    CapabilitiesResponse: An object containing the following configuration parameters:
        - Keycloak server URL: The base URL for the Keycloak authentication server.
        - Realm: The security realm used within Keycloak.
        - Client ID: The client identifier registered in Keycloak.
        - Ally server domain: The domain address of the Ally server.
        - AI knowledge host: The host URL for AI knowledge services.
"""
```

---

## get_active_config_api_getActiveConfig_post

```
"""
Retrieve the active or a specific historical configuration for a given endpoint.

This function fetches the configuration data associated with an endpoint from the database. If a configuration ID is provided, it returns the corresponding historical configuration; otherwise, it returns the currently active configuration. The configuration data may be updated if it uses an outdated data model version. If the configuration is invalid, it will still be returned along with a `validation_error` field describing the validation issues.

Args:
    endpoint (str): The name of the endpoint to retrieve the configuration for.
    config_id (Optional[str or None]): The ID of the configuration to fetch. If None or omitted, the currently active configuration is returned.
    config_data (EngineConfig-Input, optional): Configuration data input, used internally for updates or validation.

Returns:
    dict: A response object containing a LenientConfig with the following fields:
        - id (str): The ID of the configuration.
        - name (str): A timestamp string indicating when the configuration was created.
        - engine_data (dict): The configuration data.
        - validation_error (str, optional): Validation error message if the configuration is invalid.

Raises:
    NonExistentEndpointError (404): If the specified endpoint does not exist.
    InvalidInput (200 + success=False): If the provided configuration ID is invalid.
    NoSuccess (200 + success=False): If the configuration could not be retrieved for any other reason.
    PermissionError (403): If the user does not have permission to view the configuration.
"""
```

---

## validate_config_api_validateConfig_post

```
"""
Validate the configuration data for a specified active endpoint in the Ally Portal.

This function checks the validity of the provided configuration details against the predefined Pydantic `ConfigData` model to ensure correctness and compliance. It also verifies that the AI model selected in the configuration is currently enabled and supported.

Parameters:
    endpoint (str): The name of the endpoint to validate the configuration against. This identifies which endpoint's settings are being checked.
    config_data (EngineConfig-Input): The configuration data object containing all necessary settings and parameters to validate.
    config_id (Optional[str or None]): The identifier of a specific configuration to fetch and validate. If None, the validation applies to the currently active configuration.

Returns:
    dict: A response indicating the result of the validation process. If the configuration is valid, the response confirms success. If invalid, it includes descriptive error messages explaining the validation failures.

Note:
    Review and confirm if this validation endpoint is currently utilized within the Ally Portal workflows or if it can be deprecated.
"""
```

---

## set_config_api_setConfig_post

```
"""
Set or update the configuration for a specified endpoint in the Ally Portal.

This function allows setting a new configuration or updating an existing one for a given endpoint. If a configuration ID is provided, it updates that specific configuration; otherwise, it applies to the currently active configuration for the endpoint.

Args:
    endpoint (str): The name of the endpoint for which the configuration is to be set.
    config_data (dict): The configuration data to apply, following the EngineConfig schema.
    config_id (str or None): Optional. The ID of the configuration to update. If None, the currently active configuration is updated.

Returns:
    dict: A response containing the ID of the newly set or updated configuration.

Raises:
    NonExistentEndpointError: If the specified endpoint does not exist (HTTP 404).
    InvalidInput: If the provided configuration is invalid, such as selecting a model that is not available (indicated by a 200 response with success=false).
"""
```

---

## get_config_history_api_getConfigHistory_post

```
"""
Retrieves the configuration history for a specified endpoint in the Ally Portal.

This function fetches a list of configuration history entries for an active endpoint associated with the user. It returns metadata including the names and IDs of past configurations, enabling users to review or manage previous Copilot settings.

Parameters:
    endpoint (str): The name of the endpoint whose configuration history is to be retrieved.
    config_data (dict, optional): Configuration data following the EngineConfig-Input schema. This may be used to filter or influence the history retrieval.
    config_id (str or None, optional): The ID of a specific configuration to fetch. If None, the function fetches the history for the currently active configuration.

Returns:
    dict: A response object containing a list of configuration history items, each with its name and ID.
"""
```

---

## create_endpoint_api_createEndpoint_post

```
"""
Create a new endpoint with specified attributes and metadata.

This function registers a new endpoint in the Ally Portal, which is used to manage Copilot configurations. The endpoint name must be unique and start with a valid scope prefix to ensure proper categorization and access control. Optional attributes and metadata can be provided to define the endpoint's characteristics and additional information.

Parameters:
    endpoint (str): The unique name of the endpoint to be created. Must comply with naming conventions including a valid scope prefix.
    endpoint_attributes (EndpointAttributes or None): Optional dictionary of attributes describing the endpoint's configuration and behavior.
    endpoint_metadata (EndpointMetadata or None): Optional dictionary containing metadata such as description, tags, or other relevant details.

Returns:
    Response object indicating the success or failure of the endpoint creation operation.

Raises:
    InvalidInput: If the endpoint name is invalid (e.g., missing or improperly formatted) or if required models/resources for creation are unavailable.
"""
```

---

## get_endpoint_metadata_api_getEndpointMetadata_post

```
"""
Retrieve metadata information for a specified API endpoint.

This function fetches detailed metadata associated with a given endpoint within the Ally Portal, which is used to manage Copilot configurations. The metadata can include configuration options, supported operations, data schemas, and other relevant details necessary for understanding and interacting with the endpoint.

Parameters:
    endpoint (str): The API endpoint path or identifier for which metadata is requested.

Returns:
    dict: A response object containing the metadata details for the specified endpoint, including configuration settings and descriptive information that assist in managing Copilot configurations effectively.
"""
```

---

## update_endpoint_metadata_api_updateEndpointMetadata_post

```
"""
Update the metadata for a specified API endpoint within the Ally Portal.

This function allows modification of the configuration metadata tied to a given endpoint. It accepts the endpoint identifier and the new metadata details, then applies the updates to customize endpoint behavior or information.

Parameters:
    endpoint (str): The unique identifier or path of the API endpoint whose metadata is to be updated.
    metadata (dict): A dictionary containing the updated metadata fields and values conforming to the EndpointMetadata schema.

Returns:
    dict: A response object indicating the success or failure of the update operation, including any relevant status messages or error details.
"""
```

---

## delete_endpoint_api_deleteEndpoint_post

```
"""
Delete an existing endpoint and all its associated data.

This operation removes the specified endpoint from the system, including
any data linked to it. The endpoint to delete must already exist, and the
requesting user must have the appropriate permissions to perform this action.

Args:
    endpoint (str): The name of the endpoint to be deleted.

Returns:
    dict: A response object indicating the success or failure of the deletion.

Raises:
    InvalidInput: If the specified endpoint does not exist or the input is invalid.
    PermissionError: If the user lacks the necessary permissions to delete the endpoint.
"""
```

---

## get_endpoints_api_getEndpoints_post

```
"""
List API endpoints filtered by an optional prefix.

This function retrieves a list of API endpoints whose names start with the specified prefix.
Only the endpoints that the authenticated user has permission to view under the given scope will be included.
If no prefix is provided or if the prefix is "/", the function returns endpoints from all scopes.

Parameters:
    prefix (str or None): Optional prefix string to filter endpoints by their name.
                          If None or "/", all endpoints are returned.

Returns:
    dict: A response object containing a list of endpoint suffixes along with their associated metadata,
          representing the endpoints accessible to the user within the specified scope.
"""
```

---

## get_endpoint_authorization_api_endpoint_authorization_get

```
"""
Retrieve the authorization configuration for a specified API endpoint within the Ally Portal.

This function fetches the authorization settings that determine the access permissions for the given endpoint. It helps in understanding what level of authorization is required to interact with that endpoint.

Args:
    endpoint (str): The name of the API endpoint for which to retrieve the authorization configuration.

Returns:
    dict: The authorization configuration details for the specified endpoint, indicating required permissions and access control settings.
"""
```

---

## update_endpoint_authorization_api_endpoint_authorization_post

```
"""
Update the authorization settings for a specified API endpoint within the Ally Portal.

This function allows modification of the authorization configuration that governs access to a particular endpoint, ensuring that only properly authorized users or systems can interact with it. It validates user permissions before applying the changes to maintain security compliance.

Args:
    endpoint (str): The unique name or path of the API endpoint whose authorization configuration is to be updated.
    auth_config (dict): A dictionary representing the new authorization settings to apply to the endpoint, such as roles, scopes, or access rules.
    userauth (object): The user authorization object representing the current user's credentials and permissions, used to verify if the update operation is permitted.

Raises:
    AuthorizationError: If the user does not have sufficient permissions to update the endpoint authorization.
    ValidationError: If the provided authorization configuration is invalid.
    EndpointNotFoundError: If the specified endpoint does not exist.

"""
```

---

## delete_endpoint_authorization_api_endpoint_authorization_delete

```
"""
Delete the authorization configuration for a specific API endpoint within the Ally Portal.

This operation removes any custom authorization settings applied to the given endpoint,
reverting it back to the default authorization configuration. Deleting the authorization
ensures that the endpoint follows the baseline access control policies defined in the system.

Parameters:
    endpoint (str): The unique name of the API endpoint for which the authorization configuration 
                    should be deleted. This name identifies the endpoint within the Ally Portal.
"""
```

---

## execute_evaluation_suite_api_executeEvaluationSuite_post

```
"""
Execute an evaluation suite on a specified endpoint within the Ally Portal.

This function triggers the execution of a predefined test suite against a given API endpoint to evaluate its performance,
functionality, or correctness as configured in the Copilot settings.

Parameters:
    endpoint (str): The name or identifier of the API endpoint to be tested.
    test_suite_name (str): The name of the test suite to be executed for evaluation.

Returns:
    dict: A response object containing detailed results of the evaluation, including success status, errors, and metrics.

Raises:
    NoSuccess: If the specified test suite does not exist, the endpoint is invalid, or the evaluation cannot be executed.
"""
```

---

## get_stored_evaluation_results_api_getStoredEvaluationResults_post

```
"""
Retrieve evaluation results for a specified test suite from a given API endpoint.

This function fetches the stored evaluation results associated with the provided test suite name
from the specified endpoint within the Ally Portal. It is used to obtain detailed performance
and correctness metrics for Copilot configurations that have been previously evaluated.

Parameters:
    endpoint (str): The name of the API endpoint from which to retrieve the evaluation results.
    test_suite_name (str): The name of the test suite whose evaluation results are to be fetched.

Returns:
    dict: A response object containing the evaluation results data.

Raises:
    NoSuccess: If the specified test suite does not exist or if the endpoint is invalid,
              this exception is raised to indicate the failure to retrieve results.
"""
```

---

## get_evaluation_suites_api_getEvaluationSuites_post

```
"""
Retrieve a list of evaluation suite names from AWS based on the specified endpoint.

This function queries AWS to obtain the names of available evaluation suites associated with the given endpoint. Evaluation suites are collections of tests or assessments used to validate Copilot configurations within the Ally Portal.

Parameters:
    endpoint (str): The name of the endpoint for which to retrieve evaluation suites.

Returns:
    dict: A response object containing the list of evaluation suite names.
"""
```

---

## get_evaluation_suite_by_name_api_getEvaluationSuiteContentsByName_post

```
"""
Retrieve the contents of a specific evaluation suite by its name from AWS.

This function fetches the detailed configuration and tests included in the evaluation suite identified by the given test suite name from the specified endpoint within the Ally Portal. It is used to access stored test suites to view or manage their configurations in Copilot.

Parameters:
    endpoint (str): The name of the API endpoint to query for the evaluation suite.
    test_suite_name (str): The exact name of the evaluation test suite whose contents are to be retrieved.

Returns:
    dict: A response object containing the stored test suite details.

Raises:
    NoSuccess: If the specified test suite does not exist or retrieval fails.
"""
```

---

## get_evaluation_suite_history_by_name_api_getEvaluationSuiteHistoryByName_post

```
"""
Retrieve the history of an evaluation suite by its name from AWS.

This function fetches previous versions of the specified evaluation suite associated with a given API endpoint. It provides insight into the historical configurations or iterations of the test suite.

Parameters:
    endpoint (str): The name of the API endpoint associated with the evaluation suite.
    test_suite_name (str): The exact name of the test suite whose history is to be retrieved.

Returns:
    dict: A response object containing a list of previous versions of the specified evaluation suite.

Raises:
    NoSuccess: If the specified test suite does not exist or cannot be found.
"""
```

---

## create_evaluation_suite_api_createEvaluationSuite_post

```
"""
Create a new evaluation suite within the specified AWS endpoint.

This function registers a new test suite by name, which can be used to organize and run evaluations for Copilot configurations managed through the Ally Portal.

Args:
    endpoint (str): The name of the AWS endpoint where the evaluation suite will be created.
    test_suite_name (str): The desired name for the new evaluation test suite. This must be unique and conform to valid naming conventions.

Returns:
    dict: A response object indicating whether the creation was successful or if an error occurred.

Raises:
    NoSuccess: If an evaluation suite with the given test_suite_name already exists at the endpoint.
    ValueError: If the test_suite_name is invalid due to formatting or naming rules.
"""
```

---

## add_test_cases_to_evaluation_suite_api_addTestCasesToEvaluationSuite_post

```
"""
Add or update multiple test cases within a specified evaluation test suite for a given API endpoint in the Ally Portal.

This function enables the management of dialog test cases that are part of an evaluation suite used to assess Copilot configurations. It allows adding new test cases or updating existing ones for a specific endpoint and test suite combination in AWS.

Parameters:
    endpoint (str): The name of the API endpoint associated with the evaluation suite.
    test_suite_name (str): The name of the evaluation test suite to which test cases will be added or updated.
    test_cases (List[DialogTestCase]): A list of dialog test cases to add or update within the specified test suite.

Returns:
    dict: A response object indicating the success or failure of the operation.

Raises:
    NoSuccess: If the specified test suite does not exist or the operation could not be completed successfully.
"""
```

---

## save_evaluation_suite_api_saveEvaluationSuite_post

```
"""
Update or create an evaluation test suite for a specific endpoint in the Ally Portal's AWS configuration.

This function allows you to save or modify an evaluation suite by specifying the target endpoint, the name of the test suite,
and a list of test cases associated with that suite. It is used to manage automated dialog test cases for Copilot configurations,
ensuring that the assistant's behavior is properly validated and maintained.

Parameters:
    endpoint (str): The name of the endpoint that the evaluation suite targets.
    test_suite_name (str): The unique name identifying the test suite for the evaluation.
    test_cases (List[DialogTestCase]): A list of test cases to add or update within the test suite,
        where each test case defines a scenario for dialog evaluation.

Returns:
    dict: A response object indicating whether the operation succeeded or failed.

Raises:
    NoSuccess: If the specified test suite does not exist or could not be modified.
"""
```

---

## get_cost_graph_snapshot_api_getCostGraphSnapshot_post

```
"""
Retrieve a weekly token usage graph snapshot for a specified endpoint.

This function fetches a visual representation of token consumption over a one-week period for a given API endpoint within the Ally Portal. The graph is returned as a base64 encoded string image, which can represent usage in different units such as tokens or euros.

Parameters:
    endpoint (str): The name of the API endpoint for which to retrieve the usage data.
    month (int or None): Optional. The specific month for which to fetch data. If not provided, defaults to the current or relevant period.
    unit (str): The unit of measurement for the usage data (e.g., "tokens" or "euro").

Returns:
    str: A base64 encoded string representing the image of the token usage graph for the specified week and endpoint.
"""
```

---

## get_cost_per_day_api_getCostPerDay_post

```
"""
Retrieve the daily token usage statistics for a specified API endpoint within the Ally Portal.

This function fetches token consumption data per day for a given API endpoint, optionally filtered by a specific month. The usage data is returned in the specified unit of measurement, such as tokens or euros. It is primarily used to monitor and analyze the cost and consumption associated with Copilot configurations managed through the Ally Portal.

Parameters:
    endpoint (str): The name of the API endpoint for which to retrieve usage data.
    month (int or None): The month for which to retrieve data (1-12). If None, data for all available months will be returned.
    unit (str): The unit of measurement for the usage data (e.g., "tokens", "euro"). Must be a supported unit.

Returns:
    dict: A dictionary mapping each date (as a string) to the corresponding token usage value in the specified unit.

Raises:
    InvalidInput: If the provided unit is not supported or the input parameters are invalid.
"""
```

---

## get_permissions_api__resource_type__permissions_get

```
"""
Retrieve all user-manageable permissions associated with a specific resource.

This function fetches a comprehensive list of roles assigned to the given resource,
where each role includes the users associated with it and their corresponding permissions.
Only permissions that can be managed by users are included in the response.

Parameters:
    resource_type (str): The type/category of the resource (e.g., project, file, environment).
    resource_name (str): The unique name or identifier of the resource.

Returns:
    dict: A dictionary containing:
        - success (bool): Indicates if the API call was successful.
        - data (list): A list of roles pertaining to the resource. Each role entry includes
          the users assigned to that role and their user-manageable permissions.

Raises:
    404 Error: If the resource does not have any associated permissions, a 404 error is returned.
"""
```

---

## add_role_api__resource_type__role_post

```
"""
Add a new role to a specified resource within the Ally Portal.

This API endpoint creates a new role associated with the given resource type and resource name.
The newly added role will not have any users assigned or permissions granted initially.
If a role with the specified name already exists for the resource, the operation will fail and return an HTTP 422 error.

Parameters:
    resource_type (str): The type/category of the resource to which the role is being added.
    resource_name (str): The name of the specific resource for which the role is being created.
    role (str): The name of the new role to add to the resource.

Raises:
    HTTPException: 422 if a role with the specified name already exists for the resource.
"""
```

---

## remove_role_api__resource_type__role_delete

```
"""
Remove a specific role from a given resource within the Ally Portal.

This function disassociates the specified role from the resource identified by its type and name.
It is important to note that the 'owner' role is protected and cannot be removed; attempting to do so
will result in an HTTPException with status code 422.

Parameters:
    resource_type (str): The type/category of the resource from which the role will be removed.
    resource_name (str): The unique name/identifier of the resource.
    role (str): The name of the role to be removed from the resource.

Raises:
    HTTPException: If an attempt is made to remove the 'owner' role, an HTTPException with a 422 status code will be raised.
"""
```

---

## grant_permission_api__resource_type__role_permission_post

```
"""
Grant a permission to a specified role on a given resource.

This API endpoint assigns a defined permission to a role associated with a specific type and name of resource within the Ally Portal. It ensures that the role receives the appropriate access rights as identified by the permission ID.

Parameters:
- resource_type (str): The type classification of the resource (e.g., project, folder).
- resource_name (str): The unique name or identifier of the resource to which the permission will be applied.
- role (str): The name of the role that will receive the new permission.
- permission (str): The identifier of the permission to be granted to the role.

Raises:
- HTTPException: Returns a 422 status code if the permission is already granted to the specified role, indicating no changes were made.
"""
```

---

## revoke_permission_api__resource_type__role_permission_delete

```
"""
Revoke a specific permission from a role on a given resource within the Ally Portal.

This function removes the specified permission from the designated role associated with the resource. It is used to manage and update access controls by revoking permissions that were previously granted.

Parameters:
    resource_type (str): The type or category of the resource (e.g., document, project, service).
    resource_name (str): The name of the resource from which the permission will be revoked.
    role (str): The name of the role from which the permission will be removed.
    permission (str): The identifier of the permission to be revoked.

Raises:
    HTTPException (422): If the specified permission is not currently granted to the role, indicating that the revocation cannot proceed.
"""
```

---

## add_user_api__resource_type__role_user_post

```
"""
Add a user to a specified role on a given resource.

This function assigns the specified user to a role within a defined resource type and resource name.
It ensures that the user is added to the role to manage permissions or access control effectively.

Parameters:
    resource_type (str): The type/category of the resource (e.g., project, team, repository).
    resource_name (str): The name identifier of the resource where the role exists.
    role (str): The name of the role to which the user will be added.
    user (str): The username of the user to be added to the role.

Raises:
    HTTPException (422): Raised if the user is already a member of the specified role to prevent duplicates.
"""
```

---

## remove_user_api__resource_type__role_user_delete

```
"""
Remove a user from a specified role on a given resource within the Ally Portal.

This function removes the association of a user with a particular role on a resource. It is used to manage user permissions by revoking their assigned roles. Note that users are not permitted to remove themselves from the owner role to prevent accidental loss of critical permissions.

Parameters:
    resource_type (str): The type/category of the resource (e.g., project, repository).
    resource_name (str): The name identifier of the resource from which the role assignment will be removed.
    role (str): The name of the role from which the user will be removed.
    user (str): The username of the user to be removed from the role.

Raises:
    HTTPException: 
        - Status 422 if the specified user is not currently a member of the given role on the resource.
        - This ensures that removal actions are valid and informs the client of incorrect requests.
"""
```

---

## get_ratings_aws_api_getRatingsAWS_post

```
"""
Fetches ratings data from AWS DynamoDB within an optional specified time range.

This function queries the AWS DynamoDB service to retrieve ratings stored in the database. It supports filtering the results by providing optional start and end date-time parameters to limit the ratings to a specific time window. The endpoint parameter can be used to specify a particular API endpoint or resource context for the request.

Parameters:
    endpoint (str or None): Optional. The specific endpoint or resource name to filter the ratings retrieval. If None, fetches ratings across all endpoints.
    start (str or None): Optional. ISO 8601 formatted date-time string representing the start of the time range for which to fetch ratings. If None, no lower time bound is applied.
    end (str or None): Optional. ISO 8601 formatted date-time string representing the end of the time range for which to fetch ratings. If None, no upper time bound is applied.

Returns:
    list: A list containing the ratings retrieved from AWS DynamoDB matching the specified criteria.

Raises:
    NoSuccess: If the retrieval operation fails due to any error such as network issues, permission errors, or data inconsistencies.
"""
```

---

## get_session_histories_api_getSessionHistories_post

```
"""
Retrieve session histories for a specified endpoint within a given time range.

This function fetches the conversation session histories from the Ally Portal for a particular endpoint, filtered by the provided start and end times. It is used to analyze or review past interactions managed by the Copilot configurations.

Args:
    endpoint (str): The name of the endpoint for which to retrieve session histories.
    start_time (str): The start time of the session interval to filter histories (ISO 8601 format recommended).
    end_time (str): The end time of the session interval to filter histories (ISO 8601 format recommended).

Returns:
    dict: A response object containing a list of Conversation objects that represent the session histories within the specified time frame for the given endpoint.
"""
```

---

## get_available_AI_models_api_getAvailableAIModels_post

```
"""
Retrieve the list of AI models currently available in the model registry.

This function queries the model registry to obtain all AI models that can be utilized within endpoint configurations on the Ally Portal. It does not require any input parameters.

Returns:
    dict: A response object containing a list of available AI models, including their identifiers and metadata suitable for configuring endpoints.
"""
```

---

## get_scopes_api_getScopes_post

```
"""
Fetches all authorization scopes accessible to the current user.

This endpoint retrieves a comprehensive list of permission scopes that the user can utilize within the Ally Portal. Scopes define the level of access granted to the user's configurations and operations in the Copilot management system.

Returns:
    dict: A response object containing a list of available scopes. Each scope represents a specific permission or access right that the user holds.
"""
```

---

## upload_file_to_S3_api_uploadToS3_post

```
"""
Uploads a file to Amazon S3 storage and returns the URI of the uploaded file.

This function facilitates uploading a file to a designated S3 bucket used by the Ally Portal for managing Copilot configurations.
Upon successful upload, it returns the URI where the file can be accessed.

Note:
    It is currently under review whether this endpoint is actively used or required within the application.

Returns:
    dict: A response object containing the key 'uri' with the S3 URI of the uploaded file.
"""
```

---

