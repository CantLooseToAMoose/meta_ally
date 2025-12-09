"""Integration tests for APITestHookLibrary.

These tests execute the registered hooks to verify they work correctly with the API.
Note: These tests will make actual API calls and modify resources.

To inspect API return values, run the inspection tests with -s flag:
    uv run pytest tests/test_api_hooks.py::TestAPITestHookLibraryInspection -v -s

Examples:
    # Run all tests
    uv run pytest tests/test_api_hooks.py -v
    
    # Run only inspection tests with output
    uv run pytest tests/test_api_hooks.py::TestAPITestHookLibraryInspection -v -s
    
    # Run specific inspection test
    uv run pytest tests/test_api_hooks.py::TestAPITestHookLibraryInspection::test_inspect_list_sources_result -v -s
"""

import pytest
from meta_ally.eval.api_test_hooks import APITestHookLibrary
from meta_ally.lib.auth_manager import AuthManager


@pytest.fixture
def hook_library():
    """Create an APITestHookLibrary instance."""
    auth_manager = AuthManager()
    return APITestHookLibrary(auth_manager)


@pytest.fixture
def test_inputs():
    """Mock inputs for hook execution (hooks don't use inputs but signature requires it)."""
    return {}


class TestAPITestHookLibrary:
    """Test suite for APITestHookLibrary."""
    
    def test_hooks_registered(self, hook_library):
        """Test that all expected hooks are registered."""
        hooks = hook_library.list_hooks()
        hook_ids = [h.hook_id for h in hooks]
        
        # Verify all expected hooks are registered
        expected_hooks = [
            "delete_addone_sources_and_collection",
            "delete_addone_copilot",
            "setup_addone_sources_and_collection",
            "cleanup_and_setup_addone_resources"
        ]
        
        for expected_id in expected_hooks:
            assert expected_id in hook_ids, f"Hook '{expected_id}' should be registered"
    
    def test_hook_configs(self, hook_library):
        """Test that hook configs have correct metadata."""
        hooks = hook_library.list_hooks()
        
        for hook in hooks:
            # All hooks should have required fields
            assert hook.hook_id, "Hook should have an ID"
            assert hook.name, "Hook should have a name"
            assert hook.hook_type == "pre", "All API test hooks should be pre-hooks"
    
    @pytest.mark.anyio
    async def test_delete_addone_sources_and_collection_hook(self, hook_library, test_inputs):
        """Test the delete_addone_sources_and_collection hook execution."""
        hook_id = "delete_addone_sources_and_collection"
        hook = hook_library.get_hook(hook_id)
        
        # Execute the hook - should not raise
        await hook(test_inputs)
        print(f"✓ Successfully executed hook: {hook_id}")
    
    @pytest.mark.anyio
    async def test_delete_addone_copilot_hook(self, hook_library, test_inputs):
        """Test the delete_addone_copilot hook execution."""
        hook_id = "delete_addone_copilot"
        hook = hook_library.get_hook(hook_id)
        
        # Execute the hook - should not raise
        await hook(test_inputs)
        print(f"✓ Successfully executed hook: {hook_id}")
    
    @pytest.mark.anyio
    async def test_setup_addone_sources_and_collection_hook(self, hook_library, test_inputs):
        """Test the setup_addone_sources_and_collection hook execution."""
        hook_id = "setup_addone_sources_and_collection"
        hook = hook_library.get_hook(hook_id)
        
        # Execute the hook - should not raise
        # This creates resources, so it should work even if they don't exist
        await hook(test_inputs)
        print(f"✓ Successfully executed hook: {hook_id}")
    
    @pytest.mark.anyio
    async def test_cleanup_and_setup_addone_resources_hook(self, hook_library, test_inputs):
        """Test the cleanup_and_setup_addone_resources hook execution."""
        hook_id = "cleanup_and_setup_addone_resources"
        hook = hook_library.get_hook(hook_id)
        
        # Execute the hook - should not raise
        # This does full cleanup and setup
        await hook(test_inputs)
        print(f"✓ Successfully executed hook: {hook_id}")
    
    @pytest.mark.anyio
    async def test_full_lifecycle(self, hook_library, test_inputs):
        """Test a full lifecycle: cleanup -> setup -> cleanup."""
        # Step 1: Delete everything
        delete_hook = hook_library.get_hook("delete_addone_sources_and_collection")
        await delete_hook(test_inputs)
        print("✓ Step 1: Cleanup completed")
        
        # Step 2: Create resources
        setup_hook = hook_library.get_hook("setup_addone_sources_and_collection")
        await setup_hook(test_inputs)
        print("✓ Step 2: Setup completed")
        
        # Step 3: Cleanup again
        await delete_hook(test_inputs)
        print("✓ Step 3: Final cleanup completed")
    
    def test_get_hook_error(self, hook_library):
        """Test that getting non-existent hook raises KeyError."""
        with pytest.raises(KeyError, match="not found in library"):
            hook_library.get_hook("nonexistent_hook")
    
    def test_get_hook_config_error(self, hook_library):
        """Test that getting non-existent hook config raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            hook_library.get_hook_config("nonexistent_hook")


class TestAPITestHookLibraryInspection:
    """Test suite for inspecting API hook execution results."""
    
    @pytest.mark.anyio
    async def test_inspect_delete_source_result(self):
        """Test and inspect the result of deleting a source."""
        from meta_ally.lib.auth_manager import AuthManager
        from meta_ally.util.tool_group_manager import ToolGroupManager
        
        auth_manager = AuthManager()
        tool_manager = ToolGroupManager(auth_manager)
        tool_manager.load_ai_knowledge_tools()
        
        # Try to delete a source and capture the result
        result = await tool_manager.execute_tool_safely(
            "deleteSource",
            sourceId="test_source_to_delete"
        )
        
        print("\n" + "="*70)
        print("DELETE SOURCE RESULT:")
        print("="*70)
        print(f"Type: {type(result)}")
        print(f"Value: {result}")
        if result is not None:
            print(f"String representation: {str(result)}")
            if hasattr(result, '__dict__'):
                print(f"Attributes: {result.__dict__}")
        print("="*70 + "\n")
    
    @pytest.mark.anyio
    async def test_inspect_create_source_result(self):
        """Test and inspect the result of creating a source."""
        from meta_ally.lib.auth_manager import AuthManager
        from meta_ally.util.tool_group_manager import ToolGroupManager
        
        auth_manager = AuthManager()
        tool_manager = ToolGroupManager(auth_manager)
        tool_manager.load_ai_knowledge_tools()
        
        # Create a test source
        result = await tool_manager.execute_tool_safely(
            "createSource",
            sourceId="test_inspection_source",
            description="Test source for inspection",
            properties={
                "sourceType": "website",
                "urls": ["https://example.com"]
            }
        )
        
        print("\n" + "="*70)
        print("CREATE SOURCE RESULT:")
        print("="*70)
        print(f"Type: {type(result)}")
        print(f"Value: {result}")
        if result is not None:
            print(f"String representation: {str(result)}")
            if hasattr(result, '__dict__'):
                print(f"Attributes: {result.__dict__}")
            if isinstance(result, dict):
                print("Dictionary keys:", list(result.keys()))
                for key, value in result.items():
                    print(f"  {key}: {value}")
        print("="*70 + "\n")
        
        # Cleanup - delete the test source
        await tool_manager.execute_tool_safely(
            "deleteSource",
            sourceId="test_inspection_source"
        )
    
    @pytest.mark.anyio
    async def test_inspect_list_sources_result(self):
        """Test and inspect the result of listing sources."""
        from meta_ally.lib.auth_manager import AuthManager
        from meta_ally.util.tool_group_manager import ToolGroupManager
        
        auth_manager = AuthManager()
        tool_manager = ToolGroupManager(auth_manager)
        tool_manager.load_ai_knowledge_tools()
        
        # List all sources
        result = await tool_manager.execute_tool_safely("listSources")
        
        print("\n" + "="*70)
        print("LIST SOURCES RESULT:")
        print("="*70)
        print(f"Type: {type(result)}")
        if result is not None:
            if isinstance(result, list):
                print(f"Number of sources: {len(result)}")
                if len(result) > 0:
                    print("\nFirst source:")
                    first_source = result[0]
                    print(f"  Type: {type(first_source)}")
                    if hasattr(first_source, '__dict__'):
                        print(f"  Attributes: {first_source.__dict__}")
                    elif isinstance(first_source, dict):
                        for key, value in first_source.items():
                            print(f"  {key}: {value}")
            else:
                print(f"Value: {result}")
        print("="*70 + "\n")
    
    @pytest.mark.anyio
    async def test_inspect_copilot_operations(self):
        """Test and inspect the result of copilot operations."""
        from meta_ally.lib.auth_manager import AuthManager
        from meta_ally.util.tool_group_manager import ToolGroupManager
        
        auth_manager = AuthManager()
        tool_manager = ToolGroupManager(auth_manager)
        tool_manager.load_ally_config_tools()
        
        # List copilots
        result = await tool_manager.execute_tool_safely("list_copilots")
        
        print("\n" + "="*70)
        print("LIST COPILOTS RESULT:")
        print("="*70)
        print(f"Type: {type(result)}")
        if result is not None:
            if isinstance(result, list):
                print(f"Number of copilots: {len(result)}")
                if len(result) > 0:
                    print("\nFirst copilot:")
                    first_copilot = result[0]
                    print(f"  Type: {type(first_copilot)}")
                    if hasattr(first_copilot, '__dict__'):
                        print(f"  Attributes: {first_copilot.__dict__}")
                    elif isinstance(first_copilot, dict):
                        for key, value in first_copilot.items():
                            print(f"  {key}: {value}")
            elif isinstance(result, dict):
                print("Dictionary keys:", list(result.keys()))
                for key, value in result.items():
                    print(f"  {key}: {value}")
            else:
                print(f"Value: {result}")
        print("="*70 + "\n")


class TestAPITestHookLibraryWithoutAuth:
    """Test APITestHookLibrary initialization without auth manager."""
    
    def test_initialization_without_auth(self):
        """Test that library can be initialized without providing AuthManager."""
        library = APITestHookLibrary()
        assert library is not None
        assert library._auth_manager is not None
        
        # Should still have hooks registered
        hooks = library.list_hooks()
        assert len(hooks) > 0
