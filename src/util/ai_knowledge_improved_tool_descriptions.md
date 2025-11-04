# Improved AI Knowledge Tool Docstrings

This document contains improved docstrings for tools generated from the AI Knowledge API OpenAPI specification.

---

## list_collections

```
"""
Retrieve a list of document collections with optional filtering, pagination, and sorting.

This function returns collections sorted by their collection ID. You can filter the results based on various criteria such as collection ID, description, business department, project number, and access flags. Additionally, it supports flags to include metadata about the last and next scheduled index runs for each collection. Pagination is supported through limit and nextToken parameters.

Parameters
----------
lastIndexRun : str, optional
    Flag indicating whether to include the last index run information for each collection.
nextIndexRun : str, optional
    Flag indicating whether to include the next scheduled index run information for each collection.
collectionId : str, optional
    Filter collections by their ID(s). Supports multiple values with OR logic and partial matching.
description : str, optional
    Filter collections by description(s). Supports multiple values with OR logic and partial matching.
public : str, optional
    Flag to filter collections that are marked as public.
accessDenied : str, optional
    Filter collections by access denied flags. Supports multiple values with OR logic.
businessDepartment : str, optional
    Filter collections by business department. Supports partial matching.
projectNumber : str, optional
    Filter collections by project number(s). Supports multiple values with OR logic and partial matching.
limit : str, optional, default='1000'
    Maximum number of collections to return in the response.
nextToken : str, optional
    Token to retrieve the next page of results for pagination.

Returns
-------
list
    A list of collections matching the specified filters, each including metadata and sorted by collection ID.
"""
```

---

## create_collection

```
"""
Create a new document collection configuration for AI Knowledge API.

This tool initializes a collection that serves as a container for documents and their associated metadata, embedding indexes, and search configurations. Collections are identified by a unique collectionId and can be customized with various settings including storage backend, vector database type, embedding models, chunking strategies, and plugins to enhance the indexing and summarization processes. It also supports scheduling triggers for automated processing and controlling access permissions.

Parameters
----------
collectionId : str
    A unique identifier for the collection. Must be 8 to 62 characters long, start with a letter or underscore, and contain only alphanumeric characters and underscores.
description : str or None, optional
    Human-readable description of the collection. Defaults to None.
projectNumber : str, optional
    Project number associated with the collection, used for business department classification and cost allocation.
    Must match pattern '^(00000|[1-9]\d{4}|1\d{5})'. Defaults to '00000'.
collectionType : dict
    Configuration defining the type of collection and underlying vector database. Supports:
    - PostgreSQL vector database with options for vector type (e.g., 'vector', 'halfvec', 'bit', 'sparsevec')
    - S3 vector bucket configuration
sources : list of str, optional
    List of source identifiers associated with the collection (max 32).
plugins : list of dict, optional
    Plugins to extend indexing functionality, such as document summarization. Each plugin defines scope, execution mode, language models for summarization and reduction, prompts, and chunk sizes.
trigger : dict or None, optional
    Configuration for scheduling automatic tasks via cron expressions, including timezone specification.
chunking : dict, optional
    Settings for document chunking including chunk type, size, overlap, and minimum length.
embedding : dict or None, optional
    Embedding model configuration specifying provider, model name, and optional embedding dimensions.
searchIndex : dict or None, optional
    Configuration for the search index, including index type, distance function, and parameters for HNSW index construction and search.
metadata : dict, optional
    Additional metadata key-value pairs for the collection.
public : bool, optional
    Whether the collection is publicly accessible. Defaults to False.
allowFileUpload : bool, optional
    Flag to enable or disable file uploads to the collection. Defaults to True.
datetimeCreation : str or None, optional
    Timestamp of the collection creation.

Returns
-------
dict
    Confirmation of collection creation and its configured settings.
"""
```

---

## get_collection_configuration

```
"""
Retrieve the configuration settings of a specified document collection.

Parameters
----------
collection_id : str
    The unique identifier of the collection whose configuration is to be fetched.

Returns
-------
dict
    A dictionary containing the configuration details of the specified collection,
    such as indexing parameters, metadata fields, storage options, and other relevant settings.

Raises
------
ValueError
    If the given collection_id does not correspond to any existing collection.
"""
```

---

## update_collection

```
"""
Update the configuration of an existing document collection.

This function allows modifying various attributes and settings of a collection used in the AI Knowledge API, which manages document collections, their indexing, and semantic search capabilities.

Parameters
----------
collection_id : str
    The unique identifier of the collection to update.
collectionId : str
    A unique identifier for the collection, which must be 8 to 62 characters long,
    start with a letter or underscore, and contain only alphanumeric characters or underscores.
description : str or None, optional
    A textual description of the collection providing additional context. Can be None.
projectNumber : str, optional
    Project number associated with the collection used for deriving business department
    and cost allocation. Must match the pattern '^(00000|[1-9]\d{4}|1\d{5})$'. Default is '00000'.
collectionType : dict
    Specifies the type and configuration of the collection's underlying vector database.
    Supported configurations include PostgreSQL vector database with options for
    vector types ('vector', 'halfvec', 'bit', 'sparsevec') or S3 vector bucket storage.
sources : list of str, optional
    List of source identifiers associated with the collection. Each source identifier must
    be 0 to 255 characters long and match the pattern '^[a-zA-Z0-9-_]+$'. Up to 32 sources allowed.
plugins : list of dict, optional
    Configurations for plugins that enhance indexing features, such as document summary creation.
    Supports up to 10 plugins with detailed settings including summarization models, prompts, and chunk sizes.
trigger : dict or None, optional
    Configuration to schedule automatic operations on the collection using cron expressions and timezones.
chunking : dict, optional
    Defines how documents should be chunked before processing, including chunk type,
    size, overlap, and minimum chunk length. Defaults to character-based chunking.
embedding : dict, optional
    Configuration for the embedding model used to convert documents into vector representations.
    Supports multiple providers such as OpenAI, Bedrock, and mock embeddings with model selection and dimension settings.
searchIndex : dict or None, optional
    Settings for the search index including index type, distance function, and performance parameters
    like number of connections and candidate list sizes for hierarchical navigable small world graphs (HNSW).
metadata : dict, optional
    Additional user-defined metadata entries to associate with the collection.
public : bool, optional
    Flag indicating whether the collection should be publicly accessible. Defaults to False.
allowFileUpload : bool, optional
    Flag indicating whether direct file uploads to the collection are permitted. Defaults to True.
datetimeCreation : str or None, optional
    ISO8601 timestamp indicating when the collection was initially created.

Returns
-------
None
    This function updates the collection configuration in place and does not return a value.

Raises
------
ValueError
    If any of the input parameters fail validation checks on format, length, or allowed values.
"""
```

---

## delete_collection

```
"""
Delete a specific collection from the AI Knowledge API.

This function removes an existing collection identified by its unique collection ID.
Deleting a collection will permanently remove all documents and associated data within it.
Use this operation with caution, as the deletion is irreversible.

Parameters
----------
collection_id : str
    The unique identifier of the collection to be deleted.

Raises
------
ValueError
    If the specified collection_id does not exist or is invalid.
"""
```

---

## index_collection

```
"""
Trigger an indexing process for a specified document collection to update its search index.

Parameters
----------
collection_id : str
    The unique identifier of the document collection to be indexed.
forceRun : bool, optional
    If True, forces the indexing process to re-index all documents in the collection,
    even if they have been indexed before. Default is False.

Raises
------
ValueError
    If the specified collection_id does not exist or is invalid.

Notes
-----
This operation updates the search index to reflect the current state of the documents
within the collection, enabling up-to-date semantic search capabilities.
"""
```

---

## query

```
"""
Query a document collection using semantic search to retrieve relevant documents based on a text input.

This function performs a similarity search against the specified collection using vector embeddings. 
It supports multiple similarity metrics and allows filtering of results by document name.

Parameters
----------
collection_id : str
    Identifier of the collection to query. This specifies which document collection to search.
text : str
    The textual query string to search for in the collection.
limit : int, optional
    Maximum number of results to return. Defaults to 5.
metric : str, optional
    Similarity metric to use for the vector search. Must be one of:
    'L2 distance', '(negative) inner product', 'cosine distance', 'L1 distance', 'Hamming distance', 'Jaccard distance'.
    Defaults to 'cosine distance'.
documentNameContains : str, optional
    Case-insensitive substring filter for document names. Only documents whose names contain the specified string(s) will be included in the results.

Returns
-------
list of dict
    A list of matching documents, each represented as a dictionary with its metadata and relevance score.

Raises
------
ValueError
    If required parameters are missing or if an invalid similarity metric is provided.
"""
```

---

## get_fragment_counts

```
"""
Retrieve the count of fragments within a specified document collection.

This function returns detailed information regarding the number of fragments (i.e., segmented pieces or units of text/data) that exist in the given collection. It is useful for understanding the size or segmentation granularity of the stored data in the AI Knowledge API.

Parameters
----------
collection_id : str
    The unique identifier of the document collection for which the fragment counts are requested.

Returns
-------
dict
    A dictionary containing information about the number of fragments in the specified collection. The structure typically includes total fragment count and may include other relevant metadata related to fragment distribution.
"""
```

---

## get_collection_usage

```
"""
Retrieve usage statistics for a specified document collection within an optional date range.

Parameters
----------
collection_id : str
    The unique identifier of the document collection for which usage data is requested.
startDate : str, optional
    The start date (inclusive) for filtering usage data, in a date string format (e.g., 'YYYY-MM-DD').
    If not provided, usage data will be retrieved from the earliest available date.
endDate : str, optional
    The end date (inclusive) for filtering usage data, in a date string format (e.g., 'YYYY-MM-DD').
    If not provided, usage data will be retrieved up to the latest available date.

Returns
-------
dict
    A dictionary containing usage information about the collection, such as number of queries,
    access frequency, or other relevant usage metrics within the specified date range.
"""
```

---

## list_sources

```
"""
List all document sources with optional filtering and pagination.

This function retrieves a list of document sources, sorted by their source IDs. It allows for filtering based on various criteria such as source ID, description, source type, and access permissions. The filtering supports multiple values with OR logic, enabling flexible queries. Pagination is supported through a next token parameter, and the number of results can be limited to control the output size.

Parameters
----------
sourceId : str, optional
    Filter sources containing any of the specified source ID substrings.
    Multiple values are supported using OR logic.
description : str, optional
    Filter sources containing any of the specified description substrings.
    Multiple values are supported using OR logic.
sourceType : str, optional
    Filter sources by type. Supports multiple values with OR logic.
accessDenied : str or list of str, optional, default=[False]
    Filter sources based on access permissions.
    Can specify flags indicating if access to the source is denied.
    Defaults to only showing accessible sources (accessDenied=False).
limit : str, optional, default='1000'
    Maximum number of sources to return.
nextToken : str, optional
    Token used to retrieve the next page of results for pagination.

Returns
-------
list
    A list of source objects matching the filter criteria, sorted by sourceId.
    The response may include a nextToken if there are additional pages of results.
"""
```

---

## create_source

```
"""
Create a new data source configuration for the AI Knowledge API.

This function registers a new source from which data can be ingested and indexed for semantic search and document management.
The source can be of various types such as website, S3 bucket, GitHub repository, or SharePoint directory, each with its own specific properties.

Parameters
----------
sourceId : str
    A unique identifier for the data source. Must be 8 to 255 characters long, containing only alphanumeric characters, hyphens, or underscores.
description : str or None, optional
    A human-readable description of the data source.
properties : dict
    Properties specific to the data source type. This is a required dictionary with configurations depending on the sourceType:
    
    - Website Source:
        - sourceType : str = 'website'
        - urls : list of str
            List of website URLs to extract information from.
        - includeSitemap : bool, optional
            Whether to automatically extract all URLs from the sitemap for ingestion. Default is False.
        - authentication : dict or None, optional
            Authentication configuration for accessing protected websites, supporting Basic (username/password) or Bearer token.
        - prefix, suffix : list of str, optional
            Filters to include URLs by prefix or suffix.
        - prefixIgnore, suffixIgnore : list of str, optional
            Filters to exclude URLs by prefix or suffix.
    
    - S3 Source:
        - sourceType : str = 's3'
        - bucketName : str
            Name of the S3 bucket.
        - allowFileUpload : bool, optional
            Flag to allow file uploads to this source. Default is False.
        - accessKeyId, secretAccessKey, roleArn : str or None, optional
            AWS credentials or role ARN used to access the bucket.
        - prefix, suffix, prefixIgnore, suffixIgnore : list of str, optional
            Object key filters to include or exclude specific files.
    
    - GitHub Source:
        - sourceType : str = 'github'
        - organization : str
            GitHub organization name.
        - repository : str
            GitHub repository name.
        - branch : str, optional
            Repository branch to extract from. Defaults to 'main'.
        - personalAccessToken : str or None, optional
            Personal access token with read access.
        - prefix, suffix, prefixIgnore, suffixIgnore : list of str, optional
            Filters to include or exclude files in the repository.
    
    - SharePoint Source:
        - sourceType : str = 'sharepoint'
        - sharingUrl : str or None, optional
            The password-protected sharing URL for the SharePoint or OneDrive directory.
        - prefix, suffix, prefixIgnore, suffixIgnore : list of str, optional
            Filters to include or exclude files.
    
metadata : dict, optional
    Additional key-value pairs to store metadata about the source.
public : bool, optional
    Indicates whether the source is publicly accessible. Defaults to False.

Returns
-------
dict
    Confirmation of source creation, typically including the created source details such as the sourceId.

Raises
------
ValueError
    If required parameters are missing or invalid according to the source type schema.

Notes
-----
This configuration enables the AI Knowledge API to connect, extract, and index data from the specified source for efficient semantic search and knowledge management.
"""
```

---

## get_source_configuration

```
"""
Retrieve the configuration details for a specified source within the AI Knowledge API.

This function fetches the settings and parameters associated with a particular source, identified by its unique source ID. The configuration includes details necessary to understand how the source is set up and managed within the system.

Parameters
----------
source_id : str
    The unique identifier of the source for which the configuration should be retrieved.

Returns
-------
dict
    A dictionary containing the configuration settings and attributes of the specified source.

Raises
------
ValueError
    If the source_id is invalid or does not correspond to any existing source.
"""
```

---

## update_source

```
"""
Update the configuration of an existing data source in the AI Knowledge API.

This function allows you to modify the settings of a specified data source by providing its unique identifier 
and updated configuration details. Supported source types include websites, S3 buckets, GitHub repositories, 
and SharePoint directories. Configuration options include filtering rules for included and excluded prefixes 
and suffixes, authentication methods, source-specific properties, and additional metadata.

Parameters
----------
source_id : str
    The unique identifier of the data source to update.
sourceId : str
    A unique identifier string for the data source. Must be 8-255 characters long 
    and match the pattern '^[a-zA-Z0-9-_]+$'.
description : str or None, optional
    A human-readable description of the data source. Can be null.
properties : dict
    Configuration properties specific to the data source type. The dictionary must include a 
    'sourceType' key which specifies the type of source ('website', 's3', 'github', or 'sharepoint'), 
    each having its own required and optional fields:
    
    - Website sources support URLs, sitemap inclusion, and basic or bearer authentication.
    - S3 sources require bucket information and optionally access credentials and upload permissions.
    - GitHub sources require repository details and optionally a personal access token and branch name.
    - SharePoint sources require a sharing URL for access.
    
    Additionally, filtering options such as prefix, suffix, prefixIgnore, and suffixIgnore arrays 
    can be provided to control which objects within the source are indexed or ignored.

metadata : dict, optional
    Additional metadata related to the data source as key-value pairs.
public : bool, optional
    Flag indicating whether the data source is publicly accessible. Defaults to False.

Returns
-------
None

Raises
------
ValueError
    If required fields are missing or the data source configuration is invalid.
"""
```

---

## delete_source

```
"""
Delete the configuration of a specified source from the system.

This tool removes all configuration data associated with a given source,
effectively unregistering it from the document collections and indexing
processes managed by the AI Knowledge API. Use this to permanently delete
a source and its settings.

Parameters
----------
source_id : str
    The unique identifier of the source to be deleted. This ID corresponds
    to the source's configuration record within the system.

Raises
------
KeyError
    If the specified source_id does not exist in the system.
"""
```

---

## health_check

```
"""
Performs a health check on the AI Knowledge API service.

This endpoint is used to verify that the service is running and reachable.
It does not require any parameters and will always return a status code 200
to indicate that the system is operational.

Parameters
----------
None

Returns
-------
dict
    A response object indicating the health status of the service, typically empty 
    but with an HTTP 200 status code to confirm service availability.
"""
```

---

## check_connection_s3

```
"""
Test and verify the connection to an Amazon S3 bucket using the provided source configuration details.

This function attempts to establish a connection to a specified S3 bucket with optional filtering, authentication, and metadata parameters.
It helps validate that the given credentials and bucket information are correct and accessible before ingesting or indexing documents.

Parameters
----------
sourceId : str
    A unique identifier for the data source. Must be 8 to 255 characters long and can contain letters, numbers, hyphens, and underscores.
description : str or None, optional
    An optional description providing more context about the data source.
properties : dict
    A dictionary of source-specific properties to configure the connection and filtering behavior. The content depends on the type of source and may include:
    
    - For S3 sources:
      - bucketName : str
          The name of the S3 bucket to connect to.
      - prefix : list of str, optional
          List of prefixes to filter objects in the bucket.
      - suffix : list of str, optional
          List of suffixes to filter objects in the bucket.
      - prefixIgnore : list of str, optional
          List of prefixes to exclude from processing.
      - suffixIgnore : list of str, optional
          List of suffixes to exclude from processing.
      - allowFileUpload : bool, optional
          A flag to indicate if file uploads are allowed.
      - accessKeyId : str or None, optional
          The access key ID used for authentication.
      - secretAccessKey : str or None, optional
          The secret access key used for authentication.
      - roleArn : str or None, optional
          IAM Role ARN for permission delegation.

    - Supports other source types such as 'website', 'github', and 'sharepoint' with their respective configurations.

metadata : dict, optional
    Additional arbitrary metadata associated with the data source.
public : bool, optional
    Flag indicating whether the source is publicly accessible. Defaults to False.

Raises
------
ConnectionError
    If the connection to the S3 bucket or specified source cannot be established or credentials are invalid.

Returns
-------
bool
    Returns True if the connection test is successful, otherwise raises an exception.
"""
```

---

## check_connection_github

```
"""
Test the connectivity to a GitHub repository using provided credentials and source details.

This function attempts to verify access to a specified GitHub repository, ensuring that the
authentication and repository information are correct and usable for further operations such
as indexing and data retrieval within the AI Knowledge API.

Parameters
----------
sourceId : str
    A unique identifier for the data source (GitHub repository). Must be 8 to 255 characters,
    containing only alphanumeric characters, hyphens or underscores.
description : str or None, optional
    A textual description of the data source. Can be None.
properties : dict
    Configuration properties specific to the GitHub source, including:
        - organization (str): The GitHub organization hosting the repository.
        - repository (str): The name of the repository to connect to.
        - personalAccessToken (str or None): A personal access token with read access to the repository.
        - branch (str, optional): The branch of the repository to connect to (default is 'main').
        - prefix, suffix, prefixIgnore, suffixIgnore (list of str): Filters to include or exclude objects by prefix or suffix.
        - sourceType (str): The type of the source, must be 'github' for this model.
metadata : dict, optional
    Additional metadata for the data source.
public : bool, optional
    Flag indicating if the GitHub source is publicly accessible. Defaults to False.

Returns
-------
dict
    Result of the connection test, indicating success or failure, and any relevant messages or errors.

Raises
------
ValueError
    If the input parameters are invalid or incomplete.
ConnectionError
    If the connection to the GitHub repository cannot be established with the provided credentials.

Notes
-----
This is typically used to validate that the AI Knowledge API can successfully access and authenticate
to the specified GitHub repository before performing operations like indexing or semantic search.
"""
```

---

## check_connection_website

```
"""
Test the connectivity and accessibility of a specified website data source 
using the provided configuration and authentication credentials.

This function performs a validation check on a website as a data source for 
document extraction or indexing. It supports filtering of URLs by prefixes 
and suffixes, optional sitemap inclusion for comprehensive URL discovery, 
and authentication via Basic or Bearer schemes to access protected resources.

Parameters
----------
sourceId : str
    A unique identifier for the data source. Must be 8 to 255 characters long 
    consisting of alphanumeric characters, dashes, or underscores.
description : str or None, optional
    An optional textual description of the data source for documentation or 
    identification purposes.
properties : dict
    Configuration properties specific to the website source which include:
        - urls : list of str
            A list of one or more URLs of websites to connect to and test.
        - prefix : list of str, optional
            List of prefixes to filter which objects (pages/resources) to include.
        - suffix : list of str, optional
            List of suffixes to filter included objects.
        - prefixIgnore : list of str, optional
            List of prefixes to exclude certain objects from the source.
        - suffixIgnore : list of str, optional
            List of suffixes to exclude from the source.
        - sourceType : str, fixed as 'website'
            The type of data source being connected to.
        - includeSitemap : bool, optional
            When True, attempts to locate and use the sitemap.xml of the URLs to 
            extract information from all linked URLs within the sitemap.
        - authentication : dict or None, optional
            Authentication details required to access the website if protected.
            Supports:
                - Basic Authentication (username and password)
                - Bearer token authentication
metadata : dict, optional
    Additional arbitrary metadata related to the data source configuration.
public : bool, optional
    Flag indicating whether the website source is publicly accessible or requires 
    authentication. Defaults to False indicating a private or restricted source.

Returns
-------
bool
    Returns True if the connection to the website was successfully established 
    and credentials (if provided) are valid; False otherwise.

Raises
------
ValueError
    If the sourceId format is invalid or required properties are missing.
ConnectionError
    If the website is unreachable or authentication fails.

Notes
-----
This test is crucial for verifying the accessibility of web-based data sources 
before attempting data extraction or indexing. It ensures that the URLs are 
reachable and that any required authentication credentials are accepted by the 
web server.
"""
```

---

## info

```
"""
Retrieve general information about the AI Knowledge API.

This tool provides metadata and overview details about the API, 
such as version, available endpoints, usage guidelines, and other 
relevant information that helps users understand the capabilities 
and current status of the API.

Parameters
----------
None

Returns
-------
dict
    A dictionary containing comprehensive information about the API, 
    including its version, capabilities, and other descriptive details.
"""
```

---

## delete_document

```
"""
Delete a document from a specified collection by its filename.

This function removes a document that was previously uploaded manually to the collection identified by `collection_id`. 
Use this to permanently delete the document from the collection storage.

Parameters
----------
collection_id : str
    The unique identifier of the collection from which the document will be deleted.
filename : str
    The exact filename of the document to be deleted within the specified collection.

Returns
-------
None

Raises
------
KeyError
    If the specified collection_id does not exist.
FileNotFoundError
    If the specified filename does not exist in the collection.
"""
```

---

## get_presigned_url

```
"""
Generate a presigned URL to securely upload a document to a specified collection.

This function provides a time-limited URL that allows clients to upload a file directly
to the storage associated with the given collection. The presigned URL ensures that
uploads are authorized without exposing permanent credentials.

Parameters
----------
collection_id : str
    The unique identifier of the document collection to which the file will be uploaded.
filename : str
    The name of the file to be uploaded. This will be used to generate the upload URL
    and typically determines the storage path or key.

Returns
-------
str
    A presigned URL that can be used to upload the specified file to the collection securely.
"""
```

---

## get_documents_indexed

```
"""
Retrieve a list of documents indexed within a specific collection.

This function fetches documents that have been indexed in the given collection, supporting filtering, pagination, and limiting the number of results returned. It allows filtering by document ID or by partial document name matching, with document ID filter taking precedence if specified.

Parameters
----------
collection_id : str
    The unique identifier of the collection from which to list indexed documents.
limit : str, optional, default='1000'
    The maximum number of documents to return in the response.
nextToken : str, optional
    A token to specify the starting point for the next set of paginated results.
documentId : str, optional
    The specific ID of a document to filter by. When provided, this filter takes precedence and only this document will be retrieved if indexed.
documentNameContains : str, optional
    A case-sensitive partial string to filter document names. Supports multiple values combined with OR logic.

Returns
-------
list of dict
    A list of document metadata objects representing the indexed documents matching the criteria.

Raises
------
ValueError
    If the required 'collection_id' parameter is missing.
"""
```

---

## get_document_uploaded

```
"""
Retrieve a list of manually uploaded documents within a specified collection.

This function returns documents based on various filtering and pagination options, enabling users to efficiently browse through the documents that have been manually added to a particular collection.

Parameters
----------
collection_id : str
    The unique identifier of the collection from which to retrieve documents.
limit : str, optional
    The maximum number of documents to return. Default is 1000.
nextToken : str, optional
    A token to specify the starting point for the next set of results, used for paginating large result sets.
documentId : str, optional
    Filter to retrieve a specific document by its exact ID. When provided, this filter takes precedence over other filters.
documentNameContains : str, optional
    Filter documents whose names contain the specified substring. Supports multiple values combined with OR logic, is case-sensitive, and allows partial matches.

Returns
-------
list
    A list of documents in the collection matching the specified filters and pagination parameters.
"""
```

---

## get_document_content

```
"""
Retrieve the content of a specific document within a given collection.

Parameters
----------
collection_id : str
    The identifier of the collection that contains the target document.
document_id : str
    The unique identifier of the document whose content is to be retrieved.
limit : int, optional, default=0
    The maximum number of content segments or entries to return. 
    If set to 0, all content will be returned without limitation.
nextToken : int, optional, default=0
    Pagination token used to retrieve the next set of content entries 
    if the content is paginated.

Returns
-------
dict
    A dictionary containing the document content along with metadata such as 
    pagination token if applicable.

Raises
------
KeyError
    If the specified collection_id or document_id does not exist.
"""
```

---

## get_document_fragments

```
"""
Retrieve fragments of a specified document from a given collection.

This function fetches segments or fragments of a document stored within a particular collection. It supports pagination and allows limiting the number of fragments returned to manage large documents efficiently.

Parameters
----------
collection_id : str
    The unique identifier of the collection containing the document.
document_id : str
    The unique identifier of the document whose fragments are to be retrieved.
limit : str, optional
    The maximum number of fragments to return. Defaults to '1000'.
nextToken : str, optional
    A token used for pagination to retrieve the next set of fragments in case the results are split across multiple pages.

Returns
-------
dict
    A dictionary containing the list of document fragments and potentially a token for fetching additional pages if more fragments exist.
"""
```

---

## get_index_runs

```
"""
Retrieve a list of index runs associated with a specific document collection.

This function fetches records of the indexing operations performed on the given collection, allowing filtering by task status and supporting pagination for large result sets.

Parameters
----------
collection_id : str
    The unique identifier of the document collection for which to list the index runs.
taskStatus : str, optional
    Filter to include only index runs matching the specified task status(es). Multiple statuses can be provided in a supported format.
nextToken : str, optional
    A token to specify the starting point for the next set of results, used for paginating through large result sets.
limit : str, optional
    The maximum number of index run records to return in the response, used to control pagination size.

Returns
-------
list
    A list of index run records matching the specified criteria, each representing an indexing operation on the collection.
"""
```

---

## get_index_run_tasks

```
"""
Retrieve a list of tasks associated with a specific index run within a document collection.

This function fetches detailed information about the tasks executed during a particular index run,
allowing for filtering and pagination based on multiple criteria. It is useful for monitoring
and managing the indexing process within a collection.

Parameters
----------
collection_id : str
    The unique identifier of the collection containing the index run.
index_run_id : str
    The unique identifier of the index run whose tasks are to be retrieved.
taskStatus : str, optional
    Filter tasks by their status. Supports multiple status values separated by commas.
nextToken : str, optional
    Token for paginating through the list of tasks. Used to retrieve the next set of results.
limit : str, optional
    Maximum number of tasks to return in the response. Specifies the page size for pagination.
task : str, optional
    Filter by specific task types. Supports multiple task types separated by commas.
datetimeExecution : str, optional
    ISO 8601 formatted datetime string specifying when the index run was executed. Filters tasks executed at this time.
sourceId : str, optional
    Filter tasks by source ID(s). Supports multiple IDs separated by commas.
documentId : str, optional
    Filter tasks by document ID(s). Supports multiple document IDs separated by commas.

Returns
-------
list
    A list of task records matching the specified filters for the given index run within the collection.
"""
```

---

## get_index_run_progress

```
"""
Get the progress of an active index run within a specified document collection.

This function retrieves the current status and progress metrics of an indexing operation,
identified by its unique index run ID, that is running on a given collection. It provides
insight into how far the indexing process has advanced, which can be useful for monitoring
and managing long-running index operations.

Parameters
----------
collection_id : str
    The unique identifier of the document collection where the index run is being executed.
index_run_id : str
    The unique identifier of the active index run whose progress is to be retrieved.

Returns
-------
dict
    A dictionary containing details about the index run's progress, such as completed steps,
    total steps, percentage complete, status message, and any relevant timestamps.

Raises
------
ValueError
    If either `collection_id` or `index_run_id` is invalid or not found.
"""
```

---

## get_permissions

```
"""
Retrieve all user-manageable permissions associated with a specific resource.

This function fetches the list of roles assigned to the given resource, along with the users
under each role and their corresponding permissions. It focuses exclusively on permissions
that can be managed by users. If the specified resource does not have any permissions set,
the function will return a 404 error indicating that no permission data is available.

Parameters
----------
resource_type : str
    The type or category of the resource (e.g., document, collection, index).
resource_name : str
    The unique name or identifier of the resource for which permissions are being retrieved.

Returns
-------
dict
    A dictionary containing:
    - success (bool): True if the API call was successful.
    - data (list): A list of roles associated with the resource, each including the users
      assigned to the role and their respective permissions.

Raises
------
HTTPError
    Raises a 404 error if the resource does not have any permissions assigned.
"""
```

---

## add_role

```
"""
Add a new role to a specified resource.

This function registers a new role for a given resource type and resource name.
The newly added role will initially have no users assigned and no permissions granted.
If a role with the same name already exists for the specified resource, the function
raises an HTTPException with status code 422.

Parameters
----------
resource_type : str
    The type of the resource to which the role will be added (e.g., "collection", "index").
resource_name : str
    The name of the specific resource where the role should be created.
role : str
    The name of the role to be added to the resource.

Raises
------
HTTPException
    If a role with the given name already exists for the specified resource, 
    an HTTPException with status code 422 is raised.
"""
```

---

## remove_role

```
"""
Remove a specific role from a given resource.

This function revokes the specified role from the identified resource. Note that the 'owner' role is protected and cannot be removed using this method. Attempting to remove the 'owner' role will result in an HTTP 422 error.

Parameters
----------
resource_type : str
    The type or category of the resource from which the role will be removed.
resource_name : str
    The unique name or identifier of the resource.
role : str
    The name of the role to be removed from the resource.

Raises
------
HTTPException
    If the role to be removed is the 'owner' role, an HTTPException with status code 422 is raised.
"""
```

---

## grant_permission

```
"""
Grant a permission to a specified role on a resource.

This function assigns a particular permission to a given role for a specific
resource type and resource name within the system. It updates the access control
settings by adding the indicated permission to the role, thereby extending the
capabilities of that role with respect to the resource.

Parameters
----------
resource_type : str
    The type or category of the resource for which the permission is granted.
resource_name : str
    The unique name or identifier of the resource on which the permission is applied.
role : str
    The name of the role that will receive the new permission.
permission : str
    The identifier of the permission (e.g., "read", "write", "delete") to be granted.

Raises
------
HTTPException
    Raised with status code 422 if the permission is already granted to the role,
    indicating a conflict or redundant assignment.
"""
```

---

## revoke_permission

```
"""
Revoke a specific permission from a role on a given resource.

This function removes a previously granted permission from a designated role associated with a particular resource. It ensures that the specified role no longer has the stated permission for accessing or managing the resource.

Parameters
----------
resource_type : str
    The type/category of the resource from which the permission will be revoked (e.g., "collection", "document").
resource_name : str
    The name or identifier of the specific resource instance.
role : str
    The name of the role from which the permission will be revoked.
permission : str
    The identifier of the permission to be removed from the role.

Raises
------
HTTPException
    If the specified permission is not currently granted to the role, a 422 Unprocessable Entity error is raised.
"""
```

---

## add_user

```
"""
Add a user to a specific role on a given resource.

This function assigns the specified user to the given role associated with
the designated resource. It facilitates managing user permissions by updating
role memberships within the system.

Parameters
----------
resource_type : str
    The type of the resource to which the role belongs (e.g., 'document', 'collection').
resource_name : str
    The name or identifier of the resource where the role is defined.
role : str
    The name of the role to which the user will be added.
user : str
    The username of the user to be added to the role.

Raises
------
HTTPException
    If the user is already a member of the specified role, an HTTP 422 error is raised.
"""
```

---

## remove_user

```
"""
Remove a user from a specified role on a given resource.

This function revokes a user's membership from a particular role associated with a resource.
It enforces that a user cannot remove themselves if they hold the owner role to prevent accidental loss of ownership.

Parameters
----------
resource_type : str
    The type of the resource (e.g., 'collection', 'index') from which the user’s role membership should be removed.
resource_name : str
    The exact name of the resource from which the user’s role membership is to be removed.
role : str
    The name of the role from which the user will be removed.
user : str
    The username of the user whose role membership is to be revoked.

Raises
------
HTTPException
    Raised with a 422 status code if the specified user is not currently a member of the specified role,
    or if there is an attempt to remove oneself from the owner role.
"""
```

---

