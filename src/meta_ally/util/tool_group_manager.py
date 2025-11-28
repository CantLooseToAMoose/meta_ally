#!/usr/bin/env python3
"""
Tool Group Manager

Manages tool groups and organizes tools from OpenAPI loaders.
Based on the tool categorization patterns found in the AI Knowledge and Ally Config notebooks.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Dict, Union, Optional

from ..lib.openapi_to_tools import OpenAPIToolsLoader, OpenAPIToolDependencies
from ..lib.auth_manager import AuthManager


class AIKnowledgeToolGroup(Enum):
    """Tool groups for AI Knowledge API based on the ai_knowledge_to_tool_groups notebook"""
    SOURCES = "sources"                    # Source management operations
    DOCUMENTS = "documents"                # Document CRUD operations
    SEARCH = "search"                      # Search and query functionality
    RETRIEVAL = "retrieval"                # RAG and vector retrieval operations
    PROCESSING = "processing"              # Document processing and ingestion
    METADATA = "metadata"                  # Metadata and tagging operations
    COLLECTIONS = "collections"            # Collection management
    INDEXING = "indexing"                  # Indexing and vector operations
    PERMISSIONS = "permissions"            # Permission and access control
    ADMIN = "admin"                        # Administrative operations
    ALL = "all"                           # All available tools


class AllyConfigToolGroup(Enum):
    """Tool groups for Ally Config API based on the ally_config_to_tool_groups notebook"""
    PORTAL_INFO = "portal_info"            # Portal configuration and capabilities
    COPILOT = "copilot"                    # All copilot operations (CRUD, config, metadata, auth)
    EVALUATION = "evaluation"              # Test suites and evaluation execution
    ANALYTICS = "analytics"                # Logs, ratings, costs, sessions
    PERMISSIONS = "permissions"            # Role-based access control
    FILE_OPERATIONS = "file_operations"    # File uploads
    ALL = "all"                           # All available tools


ToolGroupType = Union[AIKnowledgeToolGroup, AllyConfigToolGroup]


class ToolGroupManager:
    """Manages tool groups and organizes tools from OpenAPI loaders"""
    
    def __init__(self, auth_manager: AuthManager):
        self._auth_manager = auth_manager
        self._ai_knowledge_tools: List = []
        self._ally_config_tools: List = []
        self._ai_knowledge_groups: Dict[AIKnowledgeToolGroup, List] = {}
        self._ally_config_groups: Dict[AllyConfigToolGroup, List] = {}
        self._ai_knowledge_loader: Optional[OpenAPIToolsLoader] = None
        self._ally_config_loader: Optional[OpenAPIToolsLoader] = None
        
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
        
    def _organize_ai_knowledge_tools(self) -> None:
        """Organize AI Knowledge tools into logical groups based on notebook patterns"""
        # Initialize groups
        for group in AIKnowledgeToolGroup:
            if group != AIKnowledgeToolGroup.ALL:
                self._ai_knowledge_groups[group] = []
        
        # Define patterns for categorization (based on notebook analysis)
        source_patterns = ["source", "sources"]
        document_patterns = ["document", "documents", "doc"]
        search_patterns = ["search", "query", "find"]
        retrieval_patterns = ["retrieve", "rag", "vector", "embedding"]
        processing_patterns = ["process", "ingest", "parse", "extract"]
        metadata_patterns = ["metadata", "tag", "label", "annotation"]
        collection_patterns = ["collection", "collections"]
        indexing_patterns = ["index", "indexing", "reindex", "vector", "embedding"]
        permission_patterns = ["permission", "permissions", "access", "auth", "role", "acl"]
        admin_patterns = ["admin", "user", "config", "health", "status", "info", "models", "test"]
        
        for tool in self._ai_knowledge_tools:
            name_lower = tool.name.lower()
            
            # Check patterns in order of specificity
            if any(pattern in name_lower for pattern in source_patterns):
                self._ai_knowledge_groups[AIKnowledgeToolGroup.SOURCES].append(tool)
            elif any(pattern in name_lower for pattern in document_patterns):
                self._ai_knowledge_groups[AIKnowledgeToolGroup.DOCUMENTS].append(tool)
            elif any(pattern in name_lower for pattern in search_patterns):
                self._ai_knowledge_groups[AIKnowledgeToolGroup.SEARCH].append(tool)
            elif any(pattern in name_lower for pattern in collection_patterns):
                self._ai_knowledge_groups[AIKnowledgeToolGroup.COLLECTIONS].append(tool)
            elif any(pattern in name_lower for pattern in indexing_patterns):
                self._ai_knowledge_groups[AIKnowledgeToolGroup.INDEXING].append(tool)
            elif any(pattern in name_lower for pattern in permission_patterns):
                self._ai_knowledge_groups[AIKnowledgeToolGroup.PERMISSIONS].append(tool)
            elif any(pattern in name_lower for pattern in retrieval_patterns):
                self._ai_knowledge_groups[AIKnowledgeToolGroup.RETRIEVAL].append(tool)
            elif any(pattern in name_lower for pattern in processing_patterns):
                self._ai_knowledge_groups[AIKnowledgeToolGroup.PROCESSING].append(tool)
            elif any(pattern in name_lower for pattern in metadata_patterns):
                self._ai_knowledge_groups[AIKnowledgeToolGroup.METADATA].append(tool)
            elif any(pattern in name_lower for pattern in admin_patterns):
                self._ai_knowledge_groups[AIKnowledgeToolGroup.ADMIN].append(tool)
                
    def _organize_ally_config_tools(self) -> None:
        """Organize Ally Config tools into logical groups based on notebook patterns"""
        # Initialize groups
        for group in AllyConfigToolGroup:
            if group != AllyConfigToolGroup.ALL:
                self._ally_config_groups[group] = []
        
        # Define categorization rules with exact tool name mappings (based on notebook analysis)
        categorization_rules = [
            # Portal info - highest priority
            (AllyConfigToolGroup.PORTAL_INFO, ["get_portal_config", "list_models", "list_scopes"]),
            
            # Copilot operations (management, metadata, config, authorization)
            (AllyConfigToolGroup.COPILOT, [
                # Management
                "list_copilots", "create_copilot", "delete_copilot",
                # Metadata
                "get_copilot_metadata", "update_copilot_metadata",
                # Configuration
                "get_copilot_config", "update_copilot_config", "validate_copilot_config", "get_copilot_config_history",
                # Authorization
                "get_copilot_authorization", "update_copilot_authorization", "delete_copilot_authorization"
            ]),
            
            # Evaluation (suites management + execution)
            (AllyConfigToolGroup.EVALUATION, [
                "list_copilot_evaluation_suites", "get_copilot_evaluation_suite", 
                "create_copilot_evaluation_suite", "update_copilot_evaluation_suite",
                "get_copilot_evaluation_suite_history", "add_copilot_evaluation_test_cases",
                "execute_copilot_evaluation_suite", "get_copilot_evaluation_results"
            ]),
            
            # Analytics (logs, costs, ratings, sessions)
            (AllyConfigToolGroup.ANALYTICS, [
                "get_copilot_logs",
                "get_copilot_cost_graph", "get_copilot_cost_daily",
                "get_copilot_ratings",
                "get_copilot_sessions"
            ]),
            
            # Permissions (role-based access control)
            (AllyConfigToolGroup.PERMISSIONS, [
                "get_permissions", "add_role", "remove_role", 
                "grant_permission", "revoke_permission", "add_user", "remove_user"
            ]),
            
            # File operations
            (AllyConfigToolGroup.FILE_OPERATIONS, ["upload_file_to_s3"]),
        ]
        
        for tool in self._ally_config_tools:
            categorized = False
            
            # Check exact name matches and keyword matches
            for category, identifiers in categorization_rules:
                # Check if tool name exactly matches any identifier (with or without prefix)
                tool_name_without_prefix = tool.name.replace("ally_config_", "")
                if tool_name_without_prefix in identifiers or tool.name in identifiers:
                    self._ally_config_groups[category].append(tool)
                    categorized = True
                    break
                # Otherwise check if any identifier keyword is in the tool name
                elif any(identifier in tool.name.lower() for identifier in identifiers if len(identifier) > 3):
                    self._ally_config_groups[category].append(tool)
                    categorized = True
                    break
            
            # Tools not matched will remain uncategorized (no default group added)
                
    def get_tools_for_groups(self, tool_groups: List[ToolGroupType]) -> List:
        """Get all tools for the specified tool groups"""
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
        auth_manager: Optional[AuthManager] = None,
    ) -> OpenAPIToolDependencies:
        """Create dependencies for API tools"""
        if auth_manager is None:
            auth_manager = self._auth_manager
        return OpenAPIToolDependencies(auth_manager=auth_manager)
        
    def get_available_groups(self) -> Dict[str, Dict[str, List[str]]]:
        """Get information about available tool groups and their tools"""
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
        """Get an AI Knowledge tool by its operation ID"""
        if self._ai_knowledge_loader is None:
            raise ValueError("AI Knowledge tools not loaded. Call load_ai_knowledge_tools() first.")
        return self._ai_knowledge_loader.get_tool_by_operation_id(operation_id)
    
    def get_ally_config_tool_by_operation_id(self, operation_id: str):
        """Get an Ally Config tool by its operation ID"""
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
    
    async def execute_tool_safely(self, operation_id: str, **kwargs):
        """
        Safely execute a tool by operation ID with proper error handling
        
        Args:
            operation_id: The operation ID of the tool to execute
            **kwargs: Parameters to pass to the tool
            
        Returns:
            The result of the tool execution, or None if an error occurred
        """
        tool = self.get_tool_by_operation_id(operation_id)
        if tool is None:
            print(f"⚠️ Tool '{operation_id}' not found")
            return None
        
        try:
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
                print(f"⚠️ Could not create dependencies for tool '{operation_id}'")
                return None
            
            # Create a simple context object with the required attributes
            class SimpleContext:
                def __init__(self, deps):
                    self.deps = deps
                    self.tool_call_approved = True  # For human approval if needed
            
            ctx = SimpleContext(dependencies)
            
            print(f"🔄 Attempting to call: {tool.name}")
            result = await tool.function(ctx, **kwargs)  # type: ignore
            print(f"✅ Success! Result type: {type(result)}")
            return result
            
        except Exception as e:
            print(f"⚠️ Error calling {tool.name}: {str(e)}")
            return None
