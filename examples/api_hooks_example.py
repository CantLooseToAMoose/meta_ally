"""
Example demonstrating how to use all registered hooks in APITestHookLibrary.

This example shows how to:
1. Initialize the APITestHookLibrary
2. List all registered hooks
3. Execute each hook individually
4. Use hooks with DatasetManager

The hooks in APITestHookLibrary are designed for managing API resources
like sources, collections, and copilots during test execution.
"""

import asyncio

from meta_ally.auth.auth_manager import AuthManager
from meta_ally.eval.api_test_hooks import APITestHookLibrary


def list_all_hooks():
    """List all available hooks in the library."""
    print("=" * 80)
    print("📚 ALL REGISTERED HOOKS IN APITestHookLibrary")
    print("=" * 80)

    # Initialize hook library
    auth_manager = AuthManager()
    hooks = APITestHookLibrary(auth_manager)

    # Get all registered hooks
    all_hooks = hooks.list_hooks()

    print(f"\nTotal hooks registered: {len(all_hooks)}\n")

    for hook in all_hooks:
        print(f"🔧 Hook ID: {hook.hook_id}")
        print(f"   Name: {hook.name}")
        print(f"   Type: {hook.hook_type}")
        print(f"   Description: {hook.description}")
        print()


async def execute_individual_hooks():
    """Execute each hook individually to demonstrate their functionality."""
    print("=" * 80)
    print("🚀 EXECUTING INDIVIDUAL HOOKS")
    print("=" * 80)

    # Initialize hook library
    auth_manager = AuthManager()
    hooks = APITestHookLibrary(auth_manager)

    # Example inputs (hooks don't use these, but they're required by the interface)
    dummy_inputs = {"example": "data"}

    print("\n" + "=" * 80)
    print("1️⃣  EXECUTING: delete_addone_sources_and_collection")
    print("=" * 80)
    try:
        hook = hooks.get_hook("delete_addone_sources_and_collection")
        await hook(dummy_inputs)
        print("✅ Hook executed successfully")
    except Exception as e:
        print(f"⚠️  Hook execution completed with note: {e}")

    print("\n" + "=" * 80)
    print("2️⃣  EXECUTING: delete_addone_copilot")
    print("=" * 80)
    try:
        hook = hooks.get_hook("delete_addone_copilot")
        await hook(dummy_inputs)
        print("✅ Hook executed successfully")
    except Exception as e:
        print(f"⚠️  Hook execution completed with note: {e}")

    print("\n" + "=" * 80)
    print("3️⃣  EXECUTING: setup_addone_sources_and_collection")
    print("=" * 80)
    try:
        hook = hooks.get_hook("setup_addone_sources_and_collection")
        await hook(dummy_inputs)
        print("✅ Hook executed successfully")
    except Exception as e:
        print(f"❌ Hook execution failed: {e}")

    print("\n" + "=" * 80)
    print("4️⃣  EXECUTING: cleanup_and_setup_addone_resources")
    print("=" * 80)
    try:
        hook = hooks.get_hook("cleanup_and_setup_addone_resources")
        await hook(dummy_inputs)
        print("✅ Hook executed successfully")
    except Exception as e:
        print(f"❌ Hook execution failed: {e}")

    print("\n" + "=" * 80)
    print("5️⃣  EXECUTING: empty_evaluation_suite")
    print("=" * 80)
    try:
        hook = hooks.get_hook("empty_evaluation_suite")
        await hook(dummy_inputs)
        print("✅ Hook executed successfully")
    except Exception as e:
        print(f"⚠️  Hook execution completed with note: {e}")

    print("\n" + "=" * 80)
    print("6️⃣  EXECUTING: cleanup_role_and_user")
    print("=" * 80)
    try:
        hook = hooks.get_hook("cleanup_role_and_user")
        await hook(dummy_inputs)
        print("✅ Hook executed successfully")
    except Exception as e:
        print(f"⚠️  Hook execution completed with note: {e}")


async def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "API HOOKS LIBRARY - COMPLETE EXAMPLE" + " " * 22 + "║")
    print("╚" + "=" * 78 + "╝")

    # 1. List all available hooks
    list_all_hooks()

    print("\n" + "🔹" * 40 + "\n")

    # 2. Execute individual hooks
    await execute_individual_hooks()


if __name__ == "__main__":
    asyncio.run(main())
