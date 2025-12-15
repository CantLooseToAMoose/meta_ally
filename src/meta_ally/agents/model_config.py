"""
Model configuration and Azure authentication utilities for pydantic-ai agents.

This module provides functionality for configuring Azure OpenAI models and authentication
mechanisms, adapted from the patterns in the pydantic_ai_engine.py and azure.py examples.
"""

import logging
import os
from enum import Enum
from typing import Any

import httpx
from azure.identity import (
    AzureCliCredential,
    ChainedTokenCredential,
    EnvironmentCredential,
    ManagedIdentityCredential,
    get_bearer_token_provider,
)
from openai import AsyncAzureOpenAI
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider


class AzureAuthMechanism(Enum):
    """
    Enum class representing different Azure authentication mechanisms.

    Attributes
    ----------
    ACTIVE_DIRECTORY : str
        Use Azure Active Directory for authentication.
    API_KEY : str
        Read API key from AZURE_OPENAI_API_KEY.
    AUTO : str
        Try API key first, then Active Directory.
    """
    ACTIVE_DIRECTORY = "active_directory"
    API_KEY = "api-key"
    AUTO = "auto"


class ModelConfiguration:
    """
    Configuration class for Azure OpenAI models with authentication support.

    This class handles the creation of Azure OpenAI clients and providers
    for use with pydantic-ai agents.
    """

    DEFAULT_API_VERSION = "2024-08-01-preview"

    def __init__(
        self,
        deployment_name: str = "gpt-4.1-mini",
        endpoint: str = "https://ally-frcentral.openai.azure.com/",
        azure_auth_mechanism: AzureAuthMechanism | str = AzureAuthMechanism.AUTO,
        api_version: str | None = None,
        temperature: float = 0.0,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the model configuration.

        Parameters
        ----------
        deployment_name : str
            The name of the model deployment in Azure OpenAI.
        endpoint : str
            The endpoint URL for the Azure OpenAI service.
        azure_auth_mechanism : AzureAuthMechanism | str, optional
            The authentication mechanism to use. Defaults to AUTO.
        api_version : str, optional
            The API version to use. Defaults to DEFAULT_API_VERSION.
        temperature : float, optional
            The temperature setting for the model. Defaults to 0.0.
        logger : logging.Logger, optional
            Logger instance for logging information.
        """
        self.deployment_name = deployment_name
        self.endpoint = endpoint
        self.api_version = api_version or self.DEFAULT_API_VERSION
        self.temperature = temperature
        self.logger = logger or logging.getLogger(__name__)

        # Resolve authentication mechanism
        self._azure_auth_mechanism, self._auth_kwargs = self._prepare_azure_openai_auth(
            azure_auth_mechanism
        )

        # Lazy initialization
        self._azure_client: AsyncAzureOpenAI | None = None
        self._azure_provider: OpenAIProvider | None = None
        self._pydantic_ai_model: OpenAIChatModel | None = None

    def _prepare_azure_openai_auth(
        self, azure_auth_mechanism: AzureAuthMechanism | str
    ) -> tuple[AzureAuthMechanism, dict[str, Any]]:
        """
        Resolve Azure OpenAI authentication mechanism and return kwargs for client initialization.

        Parameters
        ----------
        azure_auth_mechanism : AzureAuthMechanism | str
            Desired mechanism (AUTO, API_KEY, ACTIVE_DIRECTORY).

        Returns
        -------
        tuple[AzureAuthMechanism, dict[str, Any]]
            Resolved mechanism and keyword arguments for Azure client.

        Raises
        ------
        ValueError
            If API key mechanism selected but env var missing, or unknown mechanism provided.
        """
        resolved = AzureAuthMechanism(azure_auth_mechanism)

        if resolved == AzureAuthMechanism.AUTO:
            if os.environ.get("AZURE_OPENAI_API_KEY"):
                resolved = AzureAuthMechanism.API_KEY
            else:
                resolved = AzureAuthMechanism.ACTIVE_DIRECTORY
            self.logger.info("Auto-selected authentication mechanism: %s", resolved)

        auth_kwargs: dict[str, Any] = {}

        if resolved == AzureAuthMechanism.API_KEY:
            api_key = os.environ.get("AZURE_OPENAI_API_KEY")
            if api_key is None:
                raise ValueError("AZURE_OPENAI_API_KEY not set in environment variables")
            auth_kwargs["api_key"] = api_key
            self.logger.info("Using API key authentication")

        elif resolved == AzureAuthMechanism.ACTIVE_DIRECTORY:
            self.logger.info("Using Active Directory for authentication")
            credential = ChainedTokenCredential(
                ManagedIdentityCredential(),
                EnvironmentCredential(),
                AzureCliCredential()
            )
            token_provider = get_bearer_token_provider(
                credential, "https://cognitiveservices.azure.com/.default"
            )
            auth_kwargs["azure_ad_token_provider"] = token_provider

        else:
            raise ValueError(f"Unknown Azure authentication mechanism: {resolved}")

        return resolved, auth_kwargs

    def create_azure_client(self) -> AsyncAzureOpenAI:
        """
        Create Azure OpenAI client with proper authentication support.

        Returns
        -------
        AsyncAzureOpenAI
            The configured Azure OpenAI client.
        """
        if self._azure_client is not None:
            return self._azure_client

        # Configure httpx client with larger connection limits to prevent connection pool exhaustion
        # This is especially important when the same client is used for concurrent requests
        http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=100,  # Maximum number of connections in the pool
                max_keepalive_connections=20,  # Maximum number of idle connections to keep alive
            ),
            timeout=httpx.Timeout(60.0, connect=10.0),  # Generous timeouts
        )

        client_kwargs = {
            "azure_endpoint": self.endpoint,
            "api_version": self.api_version,
            "http_client": http_client,
            **self._auth_kwargs
        }

        self._azure_client = AsyncAzureOpenAI(**client_kwargs)
        self.logger.info("Created Azure OpenAI client for endpoint: %s", self.endpoint)

        return self._azure_client

    def get_azure_provider(self) -> OpenAIProvider:
        """
        Get or create OpenAI provider with Azure client.

        Returns
        -------
        OpenAIProvider
            The configured OpenAI provider with Azure support.
        """
        if self._azure_provider is not None:
            return self._azure_provider

        # Create Azure client with proper authentication
        azure_client = self.create_azure_client()

        # Use OpenAIProvider with AsyncAzureOpenAI client
        # This approach supports Azure AD authentication through the client
        self._azure_provider = OpenAIProvider(openai_client=azure_client)
        self.logger.info("Created Azure OpenAI provider")

        return self._azure_provider

    def create_model(self) -> OpenAIChatModel:
        """
        Create Pydantic AI OpenAI model with Azure provider.

        Returns
        -------
        OpenAIChatModel
            The configured OpenAI chat model.
        """
        if self._pydantic_ai_model is not None:
            return self._pydantic_ai_model

        # Get Azure provider
        azure_provider = self.get_azure_provider()

        # Create settings with temperature
        settings = OpenAIChatModelSettings(temperature=self.temperature)

        # Create OpenAI chat model with Azure provider
        self._pydantic_ai_model = OpenAIChatModel(
            model_name=self.deployment_name,
            provider=azure_provider,
            settings=settings,
        )

        self.logger.info("Created Pydantic AI model: %s", self.deployment_name)

        return self._pydantic_ai_model


def create_azure_model_config(
    deployment_name: str,
    endpoint: str,
    azure_auth_mechanism: AzureAuthMechanism | str = AzureAuthMechanism.AUTO,
    api_version: str | None = None,
    temperature: float = 0.0,
    logger: logging.Logger | None = None,
) -> ModelConfiguration:
    """
    Convenience function to create a ModelConfiguration for Azure OpenAI.

    Parameters
    ----------
    deployment_name : str
        The name of the model deployment in Azure OpenAI.
    endpoint : str
        The endpoint URL for the Azure OpenAI service.
    azure_auth_mechanism : AzureAuthMechanism | str, optional
        The authentication mechanism to use. Defaults to AUTO.
    api_version : str, optional
        The API version to use.
    temperature : float, optional
        The temperature setting for the model. Defaults to 0.0.
    logger : logging.Logger, optional
        Logger instance for logging information.

    Returns
    -------
    ModelConfiguration
        Configured ModelConfiguration instance.
    """
    return ModelConfiguration(
        deployment_name=deployment_name,
        endpoint=endpoint,
        azure_auth_mechanism=azure_auth_mechanism,
        api_version=api_version,
        temperature=temperature,
        logger=logger,
    )


__all__ = [
    "AzureAuthMechanism",
    "ModelConfiguration",
    "create_azure_model_config",
]
