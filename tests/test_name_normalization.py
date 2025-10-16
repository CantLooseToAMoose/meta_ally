"""
Test suite for the OpenAPI to Pydantic-AI Tools converter

Tests the model name normalization function that converts OpenAPI schema names
to Python class names.
"""

import pytest
from lib.openapi_to_tools import OpenAPIToolsLoader


@pytest.fixture
def loader():
    """Create a loader instance for testing"""
    return OpenAPIToolsLoader("https://example.com/openapi.json")


class TestModelNameNormalization:
    """Test cases for the _normalize_model_name method"""
    
    @pytest.mark.unit
    @pytest.mark.parametrize("openapi_name,expected", [
        # Hyphen removal
        ("EngineConfig-Input", "EngineConfigInput"),
        ("EngineConfig-Output", "EngineConfigOutput"),
        
        # Trailing underscore removal
        ("Response_str_", "ResponseStr"),
        ("Response_Evaluation_", "ResponseEvaluation"),
        
        # Double underscore handling
        ("Response_list_str__", "ResponseListStr"),
        ("Response_dict_date__list__", "ResponseDictDateList"),
        ("Response_list_AIModel__", "ResponseListAIModel"),
        
        # Complex cases
        ("Body_upload_file_to_S3_api_uploadToS3_post", "BodyUploadFileToS3ApiUploadToS3Post"),
        ("Response_AWSLogDataDetails_", "ResponseAWSLogDataDetails"),
        ("Response_EndpointMetadata_", "ResponseEndpointMetadata"),
        ("Response_EndpointsResponseEntry_", "ResponseEndpointsResponseEntry"),
        ("Response_LenientConfig_", "ResponseLenientConfig"),
        ("Response_StoredTestSuite_", "ResponseStoredTestSuite"),
        ("Response_list_ConfigHistoryItem__", "ResponseListConfigHistoryItem"),
        ("Response_list_Conversation__", "ResponseListConversation"),
        ("Response_list_Rating__", "ResponseListRating"),
        ("Response_list_StoredTestSuite__", "ResponseListStoredTestSuite"),
    ])
    def test_normalize_model_name(self, loader, openapi_name, expected):
        """Test that OpenAPI names are correctly normalized to Python class names"""
        result = loader._normalize_model_name(openapi_name)
        assert result == expected, (
            f"Failed to normalize '{openapi_name}': "
            f"expected '{expected}', got '{result}'"
        )
    
    @pytest.mark.unit
    def test_normalize_simple_name(self, loader):
        """Test that simple names without special characters pass through correctly"""
        assert loader._normalize_model_name("SimpleModel") == "SimpleModel"
        assert loader._normalize_model_name("User") == "User"
    
    @pytest.mark.unit
    def test_normalize_empty_string(self, loader):
        """Test handling of empty string"""
        assert loader._normalize_model_name("") == ""
    
    @pytest.mark.unit
    def test_normalize_underscore_separated(self, loader):
        """Test that underscore-separated words are capitalized correctly"""
        assert loader._normalize_model_name("my_model_name") == "MyModelName"
        assert loader._normalize_model_name("api_response") == "ApiResponse"


class TestOpenAPIToolsLoader:
    """Additional integration tests for the loader"""
    
    @pytest.mark.unit
    def test_loader_initialization(self):
        """Test that loader can be initialized with a URL"""
        loader = OpenAPIToolsLoader("https://example.com/openapi.json")
        assert loader.openapi_url == "https://example.com/openapi.json"
        assert loader.base_url == "https://example.com"
    
    @pytest.mark.unit
    def test_loader_custom_base_url(self):
        """Test that custom base URL is used when provided"""
        loader = OpenAPIToolsLoader(
            "https://example.com/openapi.json",
            base_url="https://api.example.com"
        )
        assert loader.base_url == "https://api.example.com"


# For backwards compatibility and visual feedback when run directly
if __name__ == "__main__":
    import sys
    
    # Run pytest with verbose output
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
