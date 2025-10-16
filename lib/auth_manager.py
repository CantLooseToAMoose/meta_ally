"""
Authorization Manager for Ally Config API Tools

This module provides authorization token management for API calls using
the ai_core.authorization module.
"""

from typing import Optional, Tuple, Any
from datetime import datetime
from ai_core.authorization.get_token import get_authorization_token


class AuthManager:
    """Manages authorization tokens for API calls"""
    
    def __init__(
        self,
        keycloak_url: str = "https://keycloak.prod.iam-services.aws.inform-cloud.io/",
        realm_name: str = "inform-ai",
        client_id: str = "ally-portal-frontend-dev",
        should_open_browser: bool = True
    ):
        """
        Initialize the AuthManager
        
        Args:
            keycloak_url: The Keycloak server URL
            realm_name: The Keycloak realm name
            client_id: The client ID for authentication
            should_open_browser: Whether to open browser for authentication
        """
        self.keycloak_url = keycloak_url
        self.realm_name = realm_name
        self.client_id = client_id
        self.should_open_browser = should_open_browser
        
        self._token: Optional[str] = None
        self._expiration: Any = None  # Can be datetime or str depending on ai_core implementation
    
    def get_token(self, force_refresh: bool = False) -> str:
        """
        Get a valid authorization token, refreshing if necessary
        
        Args:
            force_refresh: Force token refresh even if current token is valid
        
        Returns:
            A valid bearer token
        """
        if force_refresh or self._needs_refresh():
            self._refresh_token()
        
        if self._token is None:
            raise RuntimeError("Failed to obtain authorization token")
        
        return self._token
    
    def _needs_refresh(self) -> bool:
        """Check if the token needs to be refreshed"""
        if self._token is None or self._expiration is None:
            return True
        
        # Refresh if token expires within 5 minutes
        now = datetime.now()
        return self._expiration <= now
    
    def _refresh_token(self) -> None:
        """Refresh the authorization token"""
        print("Obtaining authorization token...")
        self._token, self._expiration = get_authorization_token(
            keycloak_url=self.keycloak_url,
            realm_name=self.realm_name,
            client_id=self.client_id,
            should_open_browser=self.should_open_browser
        )
        print(f"Token obtained, expires at: {self._expiration}")
    
    def get_auth_header(self) -> dict[str, str]:
        """
        Get the authorization header for API requests
        
        Returns:
            A dict with the Authorization header
        """
        token = self.get_token()
        return {"Authorization": f"Bearer {token}"}
