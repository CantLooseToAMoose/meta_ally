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
    ENDPOINTS = "endpoints"                # Endpoint management
    CONFIGS = "configs"                    # Configuration management
    EVALUATIONS = "evaluations"            # Evaluation and test suites
    PERMISSIONS = "permissions"            # Permission and role management
    AUDIT = "audit"                        # Audit logs and session histories
    COSTS = "costs"                        # Cost tracking and analysis
    INVENTORY = "inventory"                # Capabilities and model inventory
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
        
    def load_ai_knowledge_tools(
        self, 
        openapi_url: str = "https://backend-api.dev.ai-knowledge.aws.inform-cloud.io/openapi.json",
        models_filename: str = "ai_knowledge_api_models.py",
        regenerate_models: bool = True,
        require_human_approval: bool = False
    ) -> None:
        """Load AI Knowledge API tools and organize them into groups"""
        loader = OpenAPIToolsLoader(
            openapi_url=openapi_url,
            models_filename=models_filename,
            regenerate_models=regenerate_models,
            require_human_approval=require_human_approval
        )
        
        self._ai_knowledge_tools = loader.load_tools()
        self._organize_ai_knowledge_tools()
        
    def load_ally_config_tools(
        self,
        openapi_url: str = "https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        models_filename: str = "ally_config_api_models.py",
        regenerate_models: bool = True,
        require_human_approval: bool = False
    ) -> None:
        """Load Ally Config API tools and organize them into groups"""
        loader = OpenAPIToolsLoader(
            openapi_url=openapi_url,
            models_filename=models_filename,
            regenerate_models=regenerate_models,
            require_human_approval=require_human_approval
        )
        
        self._ally_config_tools = loader.load_tools()
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
        
        # Specific tool mappings (based on notebook analysis)
        audit_tools = [
            "get_aws_logs_api_getAWSLogs_post",
            "get_session_histories_api_getSessionHistories_post", 
            "get_ratings_aws_api_getRatingsAWS_post"
        ]
        
        cost_tools = [
            "get_cost_graph_snapshot_api_getCostGraphSnapshot_post",
            "get_cost_per_day_api_getCostPerDay_post"
        ]
        
        inventory_tools = [
            "get_capabilities_api_capabilities_get",
            "get_available_AI_models_api_getAvailableAIModels_post",
            "get_scopes_api_getScopes_post"
        ]
        
        for tool in self._ally_config_tools:
            name_lower = tool.name.lower()
            
            # Check specific tool mappings first
            if tool.name in audit_tools:
                self._ally_config_groups[AllyConfigToolGroup.AUDIT].append(tool)
            elif tool.name in cost_tools:
                self._ally_config_groups[AllyConfigToolGroup.COSTS].append(tool)
            elif tool.name in inventory_tools:
                self._ally_config_groups[AllyConfigToolGroup.INVENTORY].append(tool)
            # Then check general patterns
            elif 'endpoint' in name_lower:
                self._ally_config_groups[AllyConfigToolGroup.ENDPOINTS].append(tool)
            elif 'config' in name_lower:
                self._ally_config_groups[AllyConfigToolGroup.CONFIGS].append(tool)
            elif 'evaluation' in name_lower or 'suite' in name_lower:
                self._ally_config_groups[AllyConfigToolGroup.EVALUATIONS].append(tool)
            elif 'permission' in name_lower or 'role' in name_lower:
                self._ally_config_groups[AllyConfigToolGroup.PERMISSIONS].append(tool)
                
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
