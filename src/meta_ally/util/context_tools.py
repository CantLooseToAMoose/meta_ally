"""
Context Management Tools for Agents

This module provides base tools that allow agents to track and manage user context
information such as business area (Geschäftsbereich), project number, and endpoint name.

These tools are designed to be automatically included in all agents to maintain
conversation context and provide more personalized assistance.

TODO: Add safety checks to validate inputs (e.g., valid project number formats).
"""

from pydantic_ai import RunContext, Tool

from meta_ally.lib.openapi_to_tools import OpenAPIToolDependencies

# ============================================================================
# Geschäftsbereich (Business Area) Tools
# ============================================================================


def set_geschaeftsbereich(
    ctx: RunContext[OpenAPIToolDependencies],
    geschaeftsbereich: str
) -> str:
    """
    Set the user's business area (Geschäftsbereich).

    Use this tool when the user mentions their business area or department.
    This helps provide context-aware assistance tailored to their specific domain.

    Args:
        ctx: The run context containing dependencies
        geschaeftsbereich: The business area name (e.g., "Logistics", "Manufacturing", "Sales")

    Returns:
        Confirmation message
    """
    ctx.deps.geschaeftsbereich = geschaeftsbereich
    return f"Business area set to: {geschaeftsbereich}"


def get_geschaeftsbereich(
    ctx: RunContext[OpenAPIToolDependencies]
) -> str:
    """
    Get the user's current business area (Geschäftsbereich).

    Use this tool to check if the user's business area is already known.
    If not set, ask the user to provide this information.

    Args:
        ctx: The run context containing dependencies

    Returns:
        The business area if set, or a message prompting for the information
    """
    if ctx.deps.geschaeftsbereich is None:
        return (
            "The business area (Geschäftsbereich) has not been set yet. "
            "Please ask the user: 'What is your business area (Geschäftsbereich)?'"
        )
    return f"Current business area: {ctx.deps.geschaeftsbereich}"


# ============================================================================
# Project Number Tools
# ============================================================================

def set_project_number(
    ctx: RunContext[OpenAPIToolDependencies],
    project_number: str
) -> str:
    """
    Set the user's project number.

    Use this tool when the user mentions their project number.
    This helps filter and retrieve project-specific information.

    Args:
        ctx: The run context containing dependencies
        project_number: The project number (e.g., "80300")

    Returns:
        Confirmation message
    """
    ctx.deps.project_number = project_number
    return f"Project number set to: {project_number}"


def get_project_number(
    ctx: RunContext[OpenAPIToolDependencies]
) -> str:
    """
    Get the user's current project number.

    Use this tool to check if the user's project number is already known.
    If not set, ask the user to provide this information.

    Args:
        ctx: The run context containing dependencies

    Returns:
        The project number if set, or a message prompting for the information
    """
    if ctx.deps.project_number is None:
        return (
            "The project number has not been set yet. "
            "Please ask the user: 'What is your project number?'"
        )
    return f"Current project number: {ctx.deps.project_number}"


# ============================================================================
# Endpoint Name Tools
# ============================================================================

def set_endpoint_name(
    ctx: RunContext[OpenAPIToolDependencies],
    endpoint_name: str
) -> str:
    """
    Set the endpoint configuration name being discussed.

    Use this tool when the user mentions a specific endpoint or configuration they want to work with.
    This helps maintain context about which endpoint configuration is being discussed.

    Args:
        ctx: The run context containing dependencies
        endpoint_name: The endpoint configuration name (e.g., "production-api", "staging-endpoint")

    Returns:
        Confirmation message
    """
    ctx.deps.endpoint_name = endpoint_name
    return f"Endpoint name set to: {endpoint_name}"


def get_endpoint_name(
    ctx: RunContext[OpenAPIToolDependencies]
) -> str:
    """
    Get the current endpoint configuration name.

    Use this tool to check if an endpoint name is already known.
    If not set, ask the user to provide this information.

    Args:
        ctx: The run context containing dependencies

    Returns:
        The endpoint name if set, or a message prompting for the information
    """
    if ctx.deps.endpoint_name is None:
        return (
            "The endpoint configuration name has not been set yet. "
            "Please ask the user: 'Which endpoint configuration are you working with?'"
        )
    return f"Current endpoint name: {ctx.deps.endpoint_name}"


# ============================================================================
# Clear Context Tool
# ============================================================================

def clear_context(
    ctx: RunContext[OpenAPIToolDependencies]
) -> str:
    """
    Clear all stored context information.

    Use this tool when the user wants to start fresh or switch to a different context
    (e.g., different project, business area, or endpoint).

    Args:
        ctx: The run context containing dependencies

    Returns:
        Confirmation message
    """
    ctx.deps.geschaeftsbereich = None
    ctx.deps.project_number = None
    ctx.deps.endpoint_name = None
    return "All context information has been cleared. You can now set new values."


def get_all_context(
    ctx: RunContext[OpenAPIToolDependencies]
) -> str:
    """
    Get all stored context information at once.

    Use this tool to display a summary of all known context about the user.

    Args:
        ctx: The run context containing dependencies

    Returns:
        Summary of all context information
    """
    context_parts = []

    if ctx.deps.geschaeftsbereich:
        context_parts.append(f"Business Area (Geschäftsbereich): {ctx.deps.geschaeftsbereich}")
    else:
        context_parts.append("Business Area (Geschäftsbereich): Not set")

    if ctx.deps.project_number:
        context_parts.append(f"Project Number: {ctx.deps.project_number}")
    else:
        context_parts.append("Project Number: Not set")

    if ctx.deps.endpoint_name:
        context_parts.append(f"Endpoint Name: {ctx.deps.endpoint_name}")
    else:
        context_parts.append("Endpoint Name: Not set")

    return "Current Context:\n" + "\n".join(f"  - {part}" for part in context_parts)


# ============================================================================
# Tool List Export
# ============================================================================

def get_context_tools() -> list[Tool[OpenAPIToolDependencies]]:
    """
    Get all context management tools as a list.

    Returns:
        List of Tool objects for context management
    """
    return [
        Tool(set_geschaeftsbereich, takes_ctx=True),
        Tool(get_geschaeftsbereich, takes_ctx=True),
        Tool(set_project_number, takes_ctx=True),
        Tool(get_project_number, takes_ctx=True),
        Tool(set_endpoint_name, takes_ctx=True),
        Tool(get_endpoint_name, takes_ctx=True),
        Tool(clear_context, takes_ctx=True),
        Tool(get_all_context, takes_ctx=True),
    ]
