"""
HookLibrary for AI Knowledge and Ally Config API operations.

This module provides pre-configured hooks for managing API resources during test execution,
such as creating and deleting sources, collections, and copilots.
"""

from __future__ import annotations

from typing import Any

from ..auth.auth_manager import AuthManager
from ..tools.tool_group_manager import ToolGroupManager
from .dataset_hooks import HookLibrary


class APITestHookLibrary(HookLibrary):
    """
    HookLibrary for AI Knowledge and Ally Config API test operations.

    This library provides hooks for:
    - Deleting sources and collections (pre-hook for cleanup)
    - Creating sources and collections (pre-hook for setup)
    - Deleting copilots (pre-hook for cleanup)

    Example usage:
        ```python
        from meta_ally.lib.auth_manager import AuthManager
        from meta_ally.eval.api_test_hooks import APITestHookLibrary
        from meta_ally.eval.dataset_manager import DatasetManager

        # Create auth manager and hook library
        auth_manager = AuthManager()
        hooks = APITestHookLibrary(auth_manager)

        # Create dataset manager with hooks
        manager = DatasetManager(hook_library=hooks)

        # Set hooks for specific test cases
        manager.set_dataset_hooks(
            "test_create_sources",
            pre_task_hook_id="delete_addone_sources_and_collection"
        )
        manager.set_dataset_hooks(
            "test_create_copilot",
            pre_task_hook_id="setup_addone_sources_and_collection"
        )
        ```
    """

    def __init__(self, auth_manager: AuthManager | None = None):
        """
        Initialize the API test hook library.

        Args:
            auth_manager: Optional AuthManager instance. If None, a new one is created.
        """
        self._auth_manager: AuthManager = auth_manager or AuthManager()
        self._tool_manager: ToolGroupManager | None = None
        super().__init__()

    def _ensure_tool_manager(self) -> ToolGroupManager:
        """
        Ensure tool manager is initialized and return it.

        Returns:
            The initialized ToolGroupManager instance.
        """
        if self._tool_manager is None:
            self._tool_manager = ToolGroupManager(self._auth_manager)
            # Load both API tools
            self._tool_manager.load_ai_knowledge_tools()
            self._tool_manager.load_ally_config_tools()
        return self._tool_manager

    def register_hooks(self) -> None:
        """Register all API test hooks."""
        # DELETE hooks (pre-task for cleanup)
        self.register_hook(
            "delete_addone_sources_and_collection",
            self._delete_addone_sources_and_collection,
            "Delete ADD*ONE Sources and Collection",
            description="Deletes inform_website, addone_infopapers sources and addone_sales_resources collection",
            hook_type="pre"
        )

        self.register_hook(
            "delete_addone_copilot",
            self._delete_addone_copilot,
            "Delete ADD*ONE Copilot",
            description="Deletes /gb10/addone_sales_copilot endpoint",
            hook_type="pre"
        )

        # CREATE hooks (pre-task for setup)
        self.register_hook(
            "setup_addone_sources_and_collection",
            self._setup_addone_sources_and_collection,
            "Setup ADD*ONE Sources and Collection",
            description="Creates inform_website, addone_infopapers sources and addone_sales_resources collection",
            hook_type="pre"
        )

        # Combined cleanup + setup hooks
        self.register_hook(
            "cleanup_and_setup_addone_resources",
            self._cleanup_and_setup_addone_resources,
            "Cleanup and Setup ADD*ONE Resources",
            description="Deletes copilot, then deletes and recreates sources and collection",
            hook_type="pre"
        )

        self.register_hook(
            "setup_addone_copilot_for_plugin_config",
            self._setup_addone_copilot_for_plugin_config,
            "Setup ADD*ONE Copilot for Plugin Configuration",
            description="Creates full copilot setup (sources, collection, copilot) for plugin configuration tests",
            hook_type="pre"
        )

        # Testing & Access Management hooks
        self.register_hook(
            "empty_evaluation_suite",
            self._empty_evaluation_suite,
            "Empty Evaluation Suite",
            description="Empties the website_test_suite evaluation suite for /gb80/inform_webseite_dummy",
            hook_type="pre"
        )

        self.register_hook(
            "cleanup_role_and_user",
            self._cleanup_role_and_user,
            "Cleanup Role and User",
            description="Removes user from 'Copilot Viewer & User' role and then deletes the role",
            hook_type="pre"
        )

    # ============================================================================
    # Generic API Helper Functions
    # ============================================================================

    async def _delete_source(self, source_id: str) -> None:
        """Generic function to delete a source by ID."""
        tool_manager = self._ensure_tool_manager()
        result = await tool_manager.execute_tool_safely(
            "delete_source",
            source_id=source_id
        )
        print(f"✓ Executed delete_source for '{source_id}'")
        print(f"  API returned: {result}")

    async def _delete_collection(self, collection_id: str) -> None:
        """Generic function to delete a collection by ID."""
        tool_manager = self._ensure_tool_manager()
        result = await tool_manager.execute_tool_safely(
            "delete_collection",
            collection_id=collection_id
        )
        print(f"✓ Executed delete_collection for '{collection_id}'")
        print(f"  API returned: {result}")

    async def _create_source(
        self,
        source_id: str,
        description: str,
        properties: dict
    ) -> None:
        """Generic function to create a source."""
        tool_manager = self._ensure_tool_manager()
        result = await tool_manager.execute_tool_safely(
            "create_source",
            sourceId=source_id,  # camelCase for request body
            description=description,
            properties=properties
        )
        print(f"✓ Executed create_source for '{source_id}'")
        print(f"  API returned: {result}")

    async def _create_collection(
        self,
        collection_id: str,
        description: str,
        sources: list[str]
    ) -> None:
        """Generic function to create a collection."""
        tool_manager = self._ensure_tool_manager()
        result = await tool_manager.execute_tool_safely(
            "create_collection",
            collectionId=collection_id,  # camelCase for request body
            description=description,
            sources=sources
        )
        print(f"✓ Executed create_collection for '{collection_id}'")
        print(f"  API returned: {result}")

    async def _delete_copilot(self, endpoint: str) -> None:
        """Generic function to delete a copilot by endpoint."""
        tool_manager = self._ensure_tool_manager()
        result = await tool_manager.execute_tool_safely(
            "delete_copilot",
            endpoint=endpoint
        )
        print(f"✓ Executed delete_copilot for '{endpoint}'")
        print(f"  API returned: {result}")

    async def _create_copilot(
        self,
        endpoint: str,
        endpoint_attributes: dict,
        endpoint_metadata: dict
    ) -> None:
        """Generic function to create a copilot."""
        tool_manager = self._ensure_tool_manager()
        result = await tool_manager.execute_tool_safely(
            "create_copilot",
            endpoint=endpoint,
            endpoint_attributes=endpoint_attributes,
            endpoint_metadata=endpoint_metadata
        )
        print(f"✓ Executed create_copilot for '{endpoint}'")
        print(f"  API returned: {result}")

    # ============================================================================
    # Specific Hook Implementations for ADD*ONE Example
    # ============================================================================

    async def _delete_addone_sources_and_collection(self, _inputs: Any) -> None:
        """
        Delete ADD*ONE sources and collection.

        Pre-hook for test cases that expect to create these resources.
        Deletes:
        - inform_website source
        - addone_infopapers source
        - addone_sales_resources collection
        """
        print("\n🧹 Cleaning up ADD*ONE sources and collection...")

        # Delete collection first (depends on sources)
        await self._delete_collection("addone_sales_resources")

        # Then delete sources
        await self._delete_source("inform_website")
        await self._delete_source("addone_infopapers")

        print("✓ Cleanup complete\n")

    async def _delete_addone_copilot(self, _inputs: Any) -> None:
        """
        Delete ADD*ONE copilot endpoint.

        Pre-hook for test cases that expect to create the copilot.
        Deletes:
        - /gb10/addone_sales_copilot endpoint
        """
        print("\n🧹 Cleaning up ADD*ONE copilot...")
        await self._delete_copilot("/gb10/addone_sales_copilot")
        print("✓ Cleanup complete\n")

    async def _setup_addone_sources_and_collection(self, _inputs: Any) -> None:
        """
        Create ADD*ONE sources and collection.

        Pre-hook for test cases that expect these resources to exist.
        Creates:
        - inform_website source
        - addone_infopapers source
        - addone_sales_resources collection
        """
        print("\n🔧 Setting up ADD*ONE sources and collection...")

        # Create website source
        await self._create_source(
            source_id="inform_website",
            description="INFORM Webseite über KI-Systeme & Optimierung von Geschäftsprozessen",
            properties={
                "sourceType": "website",
                "urls": ["https://www.inform-software.com/de"]
            }
        )

        # Create SharePoint source
        await self._create_source(
            source_id="addone_infopapers",
            description="SharePoint Ordner mit AddOne-InfoPapers Broschüren",
            properties={
                "sourceType": "sharepoint",
                "sharingUrl": "https://informsoftwaregmbh-my.sharepoint.com/:f:/g/personal/johannes_schillberg_inform-software_com/Erci0wuz2RVEinJQ7drbjT0BwpIOSmGNuDqyiQ9FJax5xA?e=WGtgpM"
            }
        )

        # Create collection with both sources
        await self._create_collection(
            collection_id="addone_sales_resources",
            description="Sales-relevante Ressourcen & Produktinfos für ADD*ONE",
            sources=["inform_website", "addone_infopapers"]
        )

        print("✓ Setup complete\n")

    async def _cleanup_and_setup_addone_resources(self, inputs: Any) -> None:
        """
        Combined cleanup and setup for ADD*ONE resources.

        Pre-hook that:
        1. Deletes the copilot (if it exists)
        2. Deletes sources and collection
        3. Recreates sources and collection

        Useful for copilot creation tests that need clean, pre-existing resources.
        """
        print("\n🔄 Full cleanup and setup for ADD*ONE resources...")

        # Step 1: Delete copilot
        await self._delete_copilot("/gb10/addone_sales_copilot")

        # Step 2: Delete existing resources
        await self._delete_collection("addone_sales_resources")
        await self._delete_source("inform_website")
        await self._delete_source("addone_infopapers")

        # Step 3: Create fresh resources
        await self._setup_addone_sources_and_collection(inputs)

        print("✓ Full cleanup and setup complete\n")

    async def _setup_addone_copilot_for_plugin_config(self, inputs: Any) -> None:
        """
        Setup complete ADD*ONE copilot for plugin configuration tests.

        Pre-hook that:
        1. Deletes the copilot (if it exists)
        2. Deletes and recreates sources and collection
        3. Creates the copilot

        Useful for plugin configuration tests that need the copilot to already exist.
        """
        print("\n🔧 Setting up ADD*ONE copilot for plugin configuration...")

        # Step 1: Clean up existing copilot
        await self._delete_copilot("/gb10/addone_sales_copilot")

        # Step 2: Clean up and recreate sources/collection
        await self._delete_collection("addone_sales_resources")
        await self._delete_source("inform_website")
        await self._delete_source("addone_infopapers")
        await self._setup_addone_sources_and_collection(inputs)

        # Step 3: Create the copilot
        await self._create_copilot(
            endpoint="/gb10/addone_sales_copilot",
            endpoint_attributes={
                "dep_name": "gpt-4.1-mini",
                "instructions": (
                    "Du bist der Sales Assistant für ADD*ONE. Nutze die Quellen "
                    "(INFORM Webseite, AddOne InfoPapers) für überzeugende Antworten."
                ),
                "default_message": (
                    "Hallo! Ich bin Ihr ADD*ONE Sales Assistant. Womit kann ich helfen?"
                )
            },
            endpoint_metadata={
                "display_name": "ADD*ONE Sales Copilot",
                "description": "Sales Assistant für die ADD*ONE Webseite",
                "project_number": "10000"
            }
        )

        print("✓ Copilot setup complete for plugin configuration\n")

    # ============================================================================
    # Testing & Access Management Hooks
    # ============================================================================

    async def _empty_evaluation_suite(self, _inputs: Any) -> None:
        """
        Empty the evaluation suite by updating it with an empty test case list.

        Pre-hook for test cases that create new evaluation suites.
        Uses update_copilot_evaluation_suite with empty test_cases list since
        there is no delete_evaluation_suite API.
        """
        print("\n🧹 Emptying evaluation suite...")

        tool_manager = self._ensure_tool_manager()
        result = await tool_manager.execute_tool_safely(
            "update_copilot_evaluation_suite",
            test_suite_name="website_test_suite",
            endpoint="/gb80/inform_webseite_dummy",
            test_cases=[]
        )
        print(f"✓ Executed update_copilot_evaluation_suite with empty test_cases")
        print(f"  API returned: {result}")
        print("✓ Evaluation suite emptied\n")

    async def _cleanup_role_and_user(self, _inputs: Any) -> None:
        """
        Remove user from role and delete the role.

        Pre-hook for test cases that create new roles with users.
        Steps:
        1. Remove user from 'Copilot Viewer & User' role
        2. Wait a few seconds
        3. Remove the 'Copilot Viewer & User' role
        """
        print("\n🧹 Cleaning up role and user...")
        import asyncio

        tool_manager = self._ensure_tool_manager()

        # Step 1: Remove user from role
        result = await tool_manager.execute_tool_safely(
            "remove_user",
            resource_type="endpoint",
            resource_name="/gb80/inform_webseite_dummy",
            role="Copilot Viewer & User",
            user="colleague@inform-software.com"
        )
        print(f"✓ Executed remove_user for 'colleague@inform-software.com'")
        print(f"  API returned: {result}")

        # Step 2: Wait a few seconds
        print("⏳ Waiting 3 seconds...")
        await asyncio.sleep(3)

        # Step 3: Remove role
        result = await tool_manager.execute_tool_safely(
            "remove_role",
            resource_type="endpoint",
            resource_name="/gb80/inform_webseite_dummy",
            role="Copilot Viewer & User"
        )
        print(f"✓ Executed remove_role for 'Copilot Viewer & User'")
        print(f"  API returned: {result}")
        print("✓ Role and user cleanup complete\n")
