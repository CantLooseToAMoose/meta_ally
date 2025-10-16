"""
Tests for authorization functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from lib.auth_manager import AuthManager


class TestAuthManager:
    """Tests for the AuthManager class"""
    
    def test_initialization(self):
        """Test AuthManager initialization with default values"""
        auth_manager = AuthManager()
        
        assert auth_manager.keycloak_url == "https://keycloak.prod.iam-services.aws.inform-cloud.io/"
        assert auth_manager.realm_name == "inform-ai"
        assert auth_manager.client_id == "ally-portal-frontend-acc"
        assert auth_manager.should_open_browser is True
        assert auth_manager._token is None
        assert auth_manager._expiration is None
    
    def test_custom_initialization(self):
        """Test AuthManager initialization with custom values"""
        auth_manager = AuthManager(
            keycloak_url="https://custom.keycloak.com/",
            realm_name="custom-realm",
            client_id="custom-client",
            should_open_browser=False
        )
        
        assert auth_manager.keycloak_url == "https://custom.keycloak.com/"
        assert auth_manager.realm_name == "custom-realm"
        assert auth_manager.client_id == "custom-client"
        assert auth_manager.should_open_browser is False
    
    @patch('lib.auth_manager.get_authorization_token')
    def test_get_token_when_none(self, mock_get_token):
        """Test getting token when none exists"""
        # Setup mock
        mock_token = "test-token-123"
        mock_expiration = datetime.now() + timedelta(hours=1)
        mock_get_token.return_value = (mock_token, mock_expiration)
        
        # Create auth manager and get token
        auth_manager = AuthManager()
        token = auth_manager.get_token()
        
        # Verify
        assert token == mock_token
        assert auth_manager._token == mock_token
        mock_get_token.assert_called_once()
    
    @patch('lib.auth_manager.get_authorization_token')
    def test_get_token_cached(self, mock_get_token):
        """Test that cached token is returned without refresh"""
        # Setup mock
        mock_token = "test-token-123"
        mock_expiration = datetime.now() + timedelta(hours=1)
        mock_get_token.return_value = (mock_token, mock_expiration)
        
        # Create auth manager and get token twice
        auth_manager = AuthManager()
        token1 = auth_manager.get_token()
        token2 = auth_manager.get_token()
        
        # Verify token is cached (only called once)
        assert token1 == token2
        assert mock_get_token.call_count == 1
    
    @patch('lib.auth_manager.get_authorization_token')
    def test_get_token_force_refresh(self, mock_get_token):
        """Test forcing token refresh"""
        # Setup mock
        mock_token1 = "test-token-1"
        mock_token2 = "test-token-2"
        mock_expiration = datetime.now() + timedelta(hours=1)
        mock_get_token.side_effect = [
            (mock_token1, mock_expiration),
            (mock_token2, mock_expiration)
        ]
        
        # Create auth manager and get token, then force refresh
        auth_manager = AuthManager()
        token1 = auth_manager.get_token()
        token2 = auth_manager.get_token(force_refresh=True)
        
        # Verify refresh was forced
        assert token1 == mock_token1
        assert token2 == mock_token2
        assert mock_get_token.call_count == 2
    
    @patch('lib.auth_manager.get_authorization_token')
    def test_get_auth_header(self, mock_get_token):
        """Test getting authorization header"""
        # Setup mock
        mock_token = "test-token-123"
        mock_expiration = datetime.now() + timedelta(hours=1)
        mock_get_token.return_value = (mock_token, mock_expiration)
        
        # Create auth manager and get header
        auth_manager = AuthManager()
        header = auth_manager.get_auth_header()
        
        # Verify
        assert header == {"Authorization": f"Bearer {mock_token}"}
    
    @patch('lib.auth_manager.get_authorization_token')
    def test_token_refresh_on_expiration(self, mock_get_token):
        """Test that token is refreshed when expired"""
        # Setup mock - first token expired, second token valid
        mock_token1 = "expired-token"
        mock_token2 = "fresh-token"
        past_time = datetime.now() - timedelta(hours=1)
        future_time = datetime.now() + timedelta(hours=1)
        
        mock_get_token.side_effect = [
            (mock_token1, past_time),
            (mock_token2, future_time)
        ]
        
        # Create auth manager and get token
        auth_manager = AuthManager()
        token1 = auth_manager.get_token()
        
        # Token should be immediately expired and refresh on next call
        token2 = auth_manager.get_token()
        
        # Verify refresh occurred
        assert token2 == mock_token2
        assert mock_get_token.call_count == 2


class TestOpenAPIToolsLoaderAuth:
    """Tests for authorization in OpenAPIToolsLoader"""
    
    @patch('lib.openapi_to_tools.AuthManager')
    def test_loader_creates_auth_manager(self, mock_auth_manager_class):
        """Test that loader creates AuthManager with correct parameters"""
        from lib.openapi_to_tools import OpenAPIToolsLoader
        
        loader = OpenAPIToolsLoader(
            openapi_url="https://api.example.com/openapi.json",
            keycloak_url="https://test.keycloak.com/",
            realm_name="test-realm",
            client_id="test-client"
        )
        
        # Verify AuthManager was created with correct parameters
        mock_auth_manager_class.assert_called_once_with(
            keycloak_url="https://test.keycloak.com/",
            realm_name="test-realm",
            client_id="test-client"
        )
    
    def test_loader_accepts_custom_auth_manager(self):
        """Test that loader accepts a custom AuthManager"""
        from lib.openapi_to_tools import OpenAPIToolsLoader
        
        custom_auth_manager = Mock()
        loader = OpenAPIToolsLoader(
            openapi_url="https://api.example.com/openapi.json",
            auth_manager=custom_auth_manager
        )
        
        assert loader.auth_manager is custom_auth_manager


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
