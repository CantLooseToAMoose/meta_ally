#!/usr/bin/env python3
"""
Tool Group Manager

Manages tool groups and organizes tools from OpenAPI loaders.
Based on the tool categorization patterns found in the AI Knowledge and Ally Config notebooks.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum

from ..lib.auth_manager import AuthManager
from ..lib.openapi_to_tools import OpenAPIToolDependencies, OpenAPIToolsLoader


class AIKnowledgeToolGroup(Enum):
    """Tool groups for AI Knowledge API based on OpenAPI tags"""
    COLLECTIONS = "collections"            # Collection management
    SOURCES = "sources"                    # Source management operations
    STATUS = "status"                      # Status and health checks
    CONNECTIONS = "connections"            # Connection management
    INFO = "info"                         # API information
    DOCUMENTS = "documents"                # Document CRUD operations
    INDEX_RUNS = "index-runs"             # Indexing and index run operations
    PERMISSIONS = "permissions"            # Permission and access control
    ALL = "all"                           # All available tools


class AllyConfigToolGroup(Enum):
    """Tool groups for Ally Config API based on OpenAPI tags"""
    INFO = "info"                         # Portal configuration and capabilities
    COPILOTS = "copilots"                 # Copilot management operations
    CONFIGURATION = "configuration"        # Configuration management
    SERVER_AUTHORIZATION = "server authorization"  # Server authorization
    EVALUATION = "evaluation"              # Test suites and evaluation execution
    LOGS = "logs"                         # Logs and analytics
    PERMISSIONS = "permissions"            # Role-based access control
    DEPRECATED = "DEPRECATED"             # Deprecated operations
    ALL = "all"                           # All available tools


ToolGroupType = AIKnowledgeToolGroup | AllyConfigToolGroup


class ToolGroupManager:
    """Manages tool groups and organizes tools from OpenAPI loaders"""

    def __init__(self, auth_manager: AuthManager):
        """Initialize the ToolGroupManager with an AuthManager instance."""
        self._auth_manager = auth_manager
        self._ai_knowledge_tools: list = []
        self._ally_config_tools: list = []
        self._ai_knowledge_groups: dict[AIKnowledgeToolGroup, list] = {}
        self._ally_config_groups: dict[AllyConfigToolGroup, list] = {}
        self._ai_knowledge_loader: OpenAPIToolsLoader | None = None
        self._ally_config_loader: OpenAPIToolsLoader | None = None

    def load_ai_knowledge_tools(
        self,
        openapi_url: str = "https://backend-api.dev.ai-knowledge.aws.inform-cloud.io/openapi.json",
        models_filename: str = "ai_knowledge_api_models.py",
        regenerate_models: bool = True,
        require_human_approval: bool = False
    ) -> None:
        """Load AI Knowledge API tools and organize them into groups"""
        self._ai_knowledge_loader = OpenAPIToolsLoader(
            openapi_url=openapi_url,
            models_filename=models_filename,
            regenerate_models=regenerate_models,
            require_human_approval=require_human_approval,
            tool_name_prefix="ai_knowledge_"
        )

        self._ai_knowledge_tools = self._ai_knowledge_loader.load_tools()
        self._organize_ai_knowledge_tools()

    def load_ally_config_tools(
        self,
        openapi_url: str = "https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        models_filename: str = "ally_config_api_models.py",
        regenerate_models: bool = True,
        require_human_approval: bool = False
    ) -> None:
        """Load Ally Config API tools and organize them into groups"""
        self._ally_config_loader = OpenAPIToolsLoader(
            openapi_url=openapi_url,
            models_filename=models_filename,
            regenerate_models=regenerate_models,
            require_human_approval=require_human_approval,
            tool_name_prefix="ally_config_"
        )

        self._ally_config_tools = self._ally_config_loader.load_tools()
        self._organize_ally_config_tools()

    def _categorize_by_tag(self, tool, tag_to_group: dict) -> bool:
        """
        Try to categorize a tool by its OpenAPI tags.

        Returns:
            True if the tool was successfully categorized, False otherwise.
        """
        if not self._ai_knowledge_loader:
            return False

        tags = self._ai_knowledge_loader.get_tags_for_tool(tool.name)
        if tags:
            first_tag = tags[0].lower()
            if first_tag in tag_to_group:
                group = tag_to_group[first_tag]
                self._ai_knowledge_groups[group].append(tool)
                return True
        return False

    def _categorize_by_patterns(self, tool, name_lower: str) -> None:
        """Categorize a tool by name patterns as fallback."""
        patterns_map = {
            AIKnowledgeToolGroup.SOURCES: ["source", "sources"],
            AIKnowledgeToolGroup.DOCUMENTS: ["document", "documents", "doc"],
            AIKnowledgeToolGroup.COLLECTIONS: ["collection", "collections"],
            AIKnowledgeToolGroup.PERMISSIONS: ["permission", "permissions", "access", "auth", "role", "acl"],
            AIKnowledgeToolGroup.STATUS: ["status", "health"],
            AIKnowledgeToolGroup.CONNECTIONS: ["connection", "connections"],
            AIKnowledgeToolGroup.INFO: ["info", "models", "test"],
            AIKnowledgeToolGroup.INDEX_RUNS: ["index", "indexing", "reindex", "index-run", "index_run"],
        }

        for group, patterns in patterns_map.items():
            if any(pattern in name_lower for pattern in patterns):
                self._ai_knowledge_groups[group].append(tool)
                break

    def _organize_ai_knowledge_tools(self) -> None:
        """Organize AI Knowledge tools into logical groups based on tags first, then notebook patterns"""
        # Initialize groups
        for group in AIKnowledgeToolGroup:
            if group != AIKnowledgeToolGroup.ALL:
                self._ai_knowledge_groups[group] = []

        # Create tag to group lookup (using enum values as tags)
        tag_to_group = {group.value: group for group in AIKnowledgeToolGroup if group != AIKnowledgeToolGroup.ALL}

        for tool in self._ai_knowledge_tools:
            name_lower = tool.name.lower()

            # First, try to categorize by OpenAPI tags
            categorized = self._categorize_by_tag(tool, tag_to_group)

            # Fallback to pattern matching if not categorized by tags
            if not categorized:
                self._categorize_by_patterns(tool, name_lower)

    def _categorize_ally_tool_by_tag(self, tool, tag_to_group: dict) -> bool:
        """
        Try to categorize an Ally Config tool by its OpenAPI tags.

        Returns:
            True if the tool was successfully categorized, False otherwise.
        """
        if not self._ally_config_loader:
            return False

        tags = self._ally_config_loader.get_tags_for_tool(tool.name)
        if not tags:
            return False

        first_tag = tags[0]  # Keep original case for matching
        if first_tag not in tag_to_group:
            return False

        group = tag_to_group[first_tag]
        self._ally_config_groups[group].append(tool)
        return True

    def _categorize_ally_tool_by_rules(self, tool, categorization_rules: list) -> bool:
        """
        Categorize an Ally Config tool using categorization rules.

        Returns:
            True if the tool was successfully categorized, False otherwise.
        """
        tool_name_without_prefix = tool.name.replace("ally_config_", "")

        for category, identifiers in categorization_rules:
            # Check if tool name exactly matches any identifier (with or without prefix)
            if tool_name_without_prefix in identifiers or tool.name in identifiers:
                self._ally_config_groups[category].append(tool)
                return True

            # Otherwise check if any identifier keyword is in the tool name
            if any(identifier in tool.name.lower() for identifier in identifiers if len(identifier) > 3):
                self._ally_config_groups[category].append(tool)
                return True

        return False

    def _organize_ally_config_tools(self) -> None:
        """Organize Ally Config tools into logical groups based on tags first, then notebook patterns"""
        # Initialize groups
        for group in AllyConfigToolGroup:
            if group != AllyConfigToolGroup.ALL:
                self._ally_config_groups[group] = []

        # Create tag to group lookup (using enum values as tags)
        tag_to_group = {group.value: group for group in AllyConfigToolGroup if group != AllyConfigToolGroup.ALL}

        # Define categorization rules with exact tool name mappings (based on notebook analysis) - used as fallback
        categorization_rules = [
            # Info / Portal info
            (AllyConfigToolGroup.INFO, ["get_portal_config", "list_models", "list_scopes"]),

            # Copilot operations (management, metadata)
            (AllyConfigToolGroup.COPILOTS, [
                "list_copilots", "create_copilot", "delete_copilot",
                "get_copilot_metadata", "update_copilot_metadata",
            ]),

            # Configuration
            (AllyConfigToolGroup.CONFIGURATION, [
                "get_copilot_config", "update_copilot_config", "validate_copilot_config", "get_copilot_config_history",
            ]),

            # Server Authorization
            (AllyConfigToolGroup.SERVER_AUTHORIZATION, [
                "get_copilot_authorization", "update_copilot_authorization", "delete_copilot_authorization"
            ]),

            # Evaluation (suites management + execution)
            (AllyConfigToolGroup.EVALUATION, [
                "list_copilot_evaluation_suites", "get_copilot_evaluation_suite",
                "create_copilot_evaluation_suite", "update_copilot_evaluation_suite",
                "get_copilot_evaluation_suite_history", "add_copilot_evaluation_test_cases",
                "execute_copilot_evaluation_suite", "get_copilot_evaluation_results"
            ]),

            # Logs and analytics operations
            (AllyConfigToolGroup.LOGS, [
                "get_copilot_logs",
                "get_copilot_cost_graph", "get_copilot_cost_daily",
                "get_copilot_ratings",
                "get_copilot_sessions",
                "upload_file_to_s3"
            ]),

            # Permissions (role-based access control)
            (AllyConfigToolGroup.PERMISSIONS, [
                "get_permissions", "add_role", "remove_role",
                "grant_permission", "revoke_permission", "add_user", "remove_user"
            ]),
        ]

        for tool in self._ally_config_tools:
            # First, try to categorize by OpenAPI tags
            categorized = self._categorize_ally_tool_by_tag(tool, tag_to_group)

            # Fallback to pattern matching if not categorized by tags
            if not categorized:
                self._categorize_ally_tool_by_rules(tool, categorization_rules)

            # Tools not matched will remain uncategorized (no default group added)

    def get_tools_for_groups(self, tool_groups: list[ToolGroupType]) -> list:
        """
        Get all tools for the specified tool groups

        Returns:
            List of tools from the specified groups
        """
        all_tools = []

        for group in tool_groups:
            if isinstance(group, AIKnowledgeToolGroup):
                if group == AIKnowledgeToolGroup.ALL:
                    all_tools.extend(self._ai_knowledge_tools)
                else:
                    all_tools.extend(self._ai_knowledge_groups.get(group, []))
            elif isinstance(group, AllyConfigToolGroup):
                if group == AllyConfigToolGroup.ALL:
                    all_tools.extend(self._ally_config_tools)
                else:
                    all_tools.extend(self._ally_config_groups.get(group, []))

        return all_tools

    def create_dependencies(
        self,
        auth_manager: AuthManager | None = None,
    ) -> OpenAPIToolDependencies:
        """
        Create dependencies for API tools

        Returns:
            OpenAPIToolDependencies instance configured with the auth manager
        """
        if auth_manager is None:
            auth_manager = self._auth_manager
        return OpenAPIToolDependencies(auth_manager=auth_manager)

    def get_available_groups(self) -> dict[str, dict[str, list[str]]]:
        """
        Get information about available tool groups and their tools

        Returns:
            Dictionary mapping API names to their groups and associated tool names
        """
        info = {
            "ai_knowledge_groups": {},
            "ally_config_groups": {}
        }

        for group, tools in self._ai_knowledge_groups.items():
            info["ai_knowledge_groups"][group.value] = [tool.name for tool in tools]

        for group, tools in self._ally_config_groups.items():
            info["ally_config_groups"][group.value] = [tool.name for tool in tools]

        return info

    def get_ai_knowledge_tool_by_operation_id(self, operation_id: str):
        """
        Get an AI Knowledge tool by its operation ID

        Returns:
            The tool if found

        Raises:
            ValueError: If AI Knowledge tools are not loaded
        """
        if self._ai_knowledge_loader is None:
            raise ValueError("AI Knowledge tools not loaded. Call load_ai_knowledge_tools() first.")
        return self._ai_knowledge_loader.get_tool_by_operation_id(operation_id)

    def get_ally_config_tool_by_operation_id(self, operation_id: str):
        """
        Get an Ally Config tool by its operation ID

        Returns:
            The tool if found

        Raises:
            ValueError: If Ally Config tools are not loaded
        """
        if self._ally_config_loader is None:
            raise ValueError("Ally Config tools not loaded. Call load_ally_config_tools() first.")
        return self._ally_config_loader.get_tool_by_operation_id(operation_id)

    def get_tool_by_operation_id(self, operation_id: str):
        """
        Get a tool by operation ID from either AI Knowledge or Ally Config APIs

        Args:
            operation_id: The operation ID to search for

        Returns:
            The tool if found, None otherwise

        Note:
            Searches AI Knowledge tools first, then Ally Config tools
        """
        # Try AI Knowledge tools first
        if self._ai_knowledge_loader is not None:
            tool = self._ai_knowledge_loader.get_tool_by_operation_id(operation_id)
            if tool is not None:
                return tool

        # Try Ally Config tools
        if self._ally_config_loader is not None:
            tool = self._ally_config_loader.get_tool_by_operation_id(operation_id)
            if tool is not None:
                return tool

        return None

    def apply_tool_replacements(
        self,
        tool_replacements: dict[str, Callable]
    ) -> None:
        """
        Replace tool functions with mock functions.

        This is useful for testing with mock API services instead of real API calls.
        The replacements are applied in-place to tools that have already been loaded
        and organized into groups.

        Args:
            tool_replacements: Dictionary mapping prefixed tool names to replacement functions.
                              Keys should be full tool names with prefix like "ally_config_get_copilot_ratings"
                              or "ai_knowledge_get_sources".
                              Values should be callable mock functions with the same signature.

        Example:
            ```python
            from meta_ally.util.api_mock_service import create_mock_service

            # Create mock service
            mock_service = create_mock_service()

            # Define replacements with prefixed names
            replacements = {
                "ally_config_get_copilot_ratings": mock_service.get_copilot_ratings,
                "ally_config_get_copilot_cost_daily": mock_service.get_copilot_cost_daily,
                "ally_config_get_copilot_sessions": mock_service.get_copilot_sessions,
            }

            # Apply to tool manager
            tool_manager.apply_tool_replacements(replacements)
            ```

        Note:
            - Tool names MUST include the prefix (ally_config_ or ai_knowledge_)
            - The prefix determines which tool list the replacement is applied to
            - Replacements only affect tools in the matching tool list
        """
        replaced_count = 0

        # Separate replacements by prefix
        ai_knowledge_replacements = {}
        ally_config_replacements = {}
        unknown_replacements = []

        for tool_name, new_function in tool_replacements.items():
            if tool_name.startswith("ai_knowledge_"):
                ai_knowledge_replacements[tool_name] = new_function
            elif tool_name.startswith("ally_config_"):
                ally_config_replacements[tool_name] = new_function
            else:
                unknown_replacements.append(tool_name)

        # Warn about unknown prefixes
        if unknown_replacements:
            print(f"  ⚠️  Warning: {len(unknown_replacements)} tool name(s) without recognized prefix:")
            for tool_name in unknown_replacements:
                print(f"      • {tool_name} (expected 'ai_knowledge_' or 'ally_config_' prefix)")

        # Apply replacements to AI Knowledge tools
        if ai_knowledge_replacements:
            replaced_count += self._replace_in_tool_list(
                self._ai_knowledge_tools, ai_knowledge_replacements, "AI Knowledge"
            )

        # Apply replacements to Ally Config tools
        if ally_config_replacements:
            replaced_count += self._replace_in_tool_list(
                self._ally_config_tools, ally_config_replacements, "Ally Config"
            )

        if replaced_count == 0:
            print("  ⚠️  Warning: No tools were replaced. Check that tool names match loaded tools.")
        else:
            print(f"  ✓ Successfully replaced {replaced_count} tool function(s)")

    def _replace_in_tool_list(
        self,
        tools: list,
        tool_replacements: dict[str, Callable],
        api_name: str,
    ) -> int:
        """
        Replace tools in a tool list with mock functions.

        Args:
            tools: List of tools to search
            tool_replacements: Mapping of prefixed tool names to replacement functions
            api_name: Name of the API for logging

        Returns:
            Number of tools replaced
        """
        replaced_count = 0
        for tool_name, new_function in tool_replacements.items():
            for tool in tools:
                if tool.name == tool_name:
                    tool.function = new_function
                    replaced_count += 1
                    print(f"  ✓ Replaced {api_name} tool: {tool.name}")
                    break  # Move to next replacement after finding match
        return replaced_count

    async def execute_tool_safely(self, operation_id: str, **kwargs):
        """
        Safely execute a tool by operation ID with proper error handling

        Args:
            operation_id: The operation ID of the tool to execute
            **kwargs: Parameters to pass to the tool

        Returns:
            The result of the tool execution, or None if an API error occurred

        Raises:
            ValueError: If the tool with the given operation_id is not found
            ValueError: If dependencies cannot be created for the tool
        """
        tool = self.get_tool_by_operation_id(operation_id)
        if tool is None:
            raise ValueError(f"Tool '{operation_id}' not found in loaded tools")

        # Determine which loader to use for dependencies
        dependencies = None
        if self._ai_knowledge_loader is not None:
            ai_tool = self._ai_knowledge_loader.get_tool_by_operation_id(operation_id)
            if ai_tool is not None:
                dependencies = self._ai_knowledge_loader.create_dependencies(auth_manager=self._auth_manager)

        if dependencies is None and self._ally_config_loader is not None:
            ally_tool = self._ally_config_loader.get_tool_by_operation_id(operation_id)
            if ally_tool is not None:
                dependencies = self._ally_config_loader.create_dependencies(auth_manager=self._auth_manager)

        if dependencies is None:
            raise ValueError(f"Could not create dependencies for tool '{operation_id}'")

        # Create a simple context object with the required attributes
        class SimpleContext:
            def __init__(self, deps):
                self.deps = deps
                self.tool_call_approved = True  # For human approval if needed

        ctx = SimpleContext(dependencies)

        try:
            print(f"🔄 Attempting to call: {tool.name}")
            result = await tool.function(ctx, **kwargs)  # type: ignore
            print(f"✅ Success! Result type: {type(result)}")
            return result

        except Exception as e:
            # API errors are handled gracefully - print warning and return None
            error_msg = str(e) if str(e) else f"{type(e).__name__}: {e!r}"
            print(f"⚠️ Error calling {tool.name}: {error_msg}")
            return None
