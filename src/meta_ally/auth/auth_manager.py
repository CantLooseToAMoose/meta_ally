"""
Authorization Manager for Ally Config API Tools

This module provides authorization token management for API calls using
the ai_core.authorization module.
"""

import base64
import json
from datetime import datetime
from typing import Any

from ai_core.authorization.get_token import get_authorization_token


class AuthManager:
    """Manages authorization tokens for API calls"""

    def __init__(
        self,
        keycloak_url: str = "https://keycloak.test.iam-services.aws.inform-cloud.io/",
        realm_name: str = "inform-ai",
        client_id: str = "ai-cli-device",
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

        self._token: str | None = None
        self._expiration: Any = None  # Can be datetime, timestamp (float), or str depending on ai_core implementation

    def get_token(self, force_refresh: bool = False) -> str:
        """
        Get a valid authorization token, refreshing if necessary

        Args:
            force_refresh: Force token refresh even if current token is valid

        Returns:
            A valid bearer token

        Raises:
            RuntimeError: If failed to obtain authorization token
        """
        if force_refresh or self._needs_refresh():
            self._refresh_token()

        if self._token is None:
            raise RuntimeError("Failed to obtain authorization token")

        return self._token

    def _needs_refresh(self) -> bool:
        """
        Check if the token needs to be refreshed

        Returns:
            True if the token needs to be refreshed, False otherwise
        """
        if self._token is None or self._expiration is None:
            return True

        # Refresh if token expires within 5 minutes
        now = datetime.now()

        # Handle both timestamp (float) and datetime objects
        if isinstance(self._expiration, (int, float)):
            # Convert timestamp to datetime for comparison
            expiration_dt = datetime.fromtimestamp(self._expiration)
        else:
            # Assume it's already a datetime object
            expiration_dt = self._expiration

        return expiration_dt <= now

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


def main():
    """Demonstrate the AuthManager by obtaining and decoding a JWT token."""
    def decode_jwt(token):
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT token format")
        payload = parts[1]
        # Pad base64 string if necessary
        padding = '=' * (-len(payload) % 4)
        payload += padding
        decoded_bytes = base64.urlsafe_b64decode(payload)
        decoded_str = decoded_bytes.decode('utf-8')
        return json.loads(decoded_str)

    auth_manager = AuthManager()
    token = auth_manager.get_token()
    print(f"Token: {token}")

    decoded_payload = decode_jwt(token)
    print(json.dumps(decoded_payload, indent=2))


if __name__ == "__main__":
    main()
