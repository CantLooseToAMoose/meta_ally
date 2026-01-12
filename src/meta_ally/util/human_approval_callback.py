"""
Human approval callback for tool execution.

This module provides a terminal-based approval interface for non-read-only API operations.
Uses Rich Console for formatted display of operation details.
"""

import json

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from ..lib.openapi_to_tools import ApprovalResponse


def create_human_approval_callback(console_width: int = 200) -> callable:
    """
    Create a human approval callback function for tool operations.

    Args:
        console_width: Width of the console display (default: 200)

    Returns:
        A callback function that prompts for human approval

    Example:
        ```python
        from meta_ally.util.human_approval_callback import create_human_approval_callback
        from meta_ally.lib.openapi_to_tools import OpenAPIToolsLoader

        # Create approval callback
        approval_callback = create_human_approval_callback()

        # Use with tool loader
        loader = OpenAPIToolsLoader(
            openapi_url="https://api.example.com/openapi.json",
            require_human_approval=True,
            approval_callback=approval_callback
        )
        ```
    """
    console = Console(width=console_width)

    def approval_callback(operation_id: str, method: str, params: dict) -> ApprovalResponse:
        """
        Prompt user for approval of a tool operation.

        Args:
            operation_id: The operation ID being requested
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            params: Parameters that will be sent with the request

        Returns:
            ApprovalResponse with approval decision and optional reason
        """
        # Format operation details
        operation_text = f"[bold cyan]Operation:[/bold cyan] {operation_id}\n"
        operation_text += f"[bold yellow]Method:[/bold yellow] {method}\n\n"

        if params:
            operation_text += "[bold green]Parameters:[/bold green]\n"
            # Pretty print parameters as JSON
            try:
                params_json = json.dumps(params, indent=2, default=str)
                operation_text += f"[dim]{params_json}[/dim]"
            except Exception:
                operation_text += f"[dim]{params}[/dim]"
        else:
            operation_text += "[dim]No parameters[/dim]"

        # Display operation details in a panel
        panel = Panel(
            operation_text,
            title="[bold red]⚠️  Approval Required[/bold red]",
            border_style="red",
            padding=(1, 2)
        )
        console.print("\n")
        console.print(panel)

        # Prompt for approval
        try:
            approved = Confirm.ask(
                "\n[bold]Do you approve this operation?[/bold]",
                default=False
            )

            if approved:
                console.print("[green]✓ Operation approved[/green]\n")
                return ApprovalResponse(approved=True)
            else:
                # Ask for reason
                reason = Prompt.ask(
                    "[yellow]Reason for denial (optional)[/yellow]",
                    default="User denied approval"
                )
                console.print(f"[red]✗ Operation denied: {reason}[/red]\n")
                return ApprovalResponse(approved=False, reason=reason)

        except (EOFError, KeyboardInterrupt):
            console.print("\n[red]✗ Operation cancelled by user[/red]\n")
            return ApprovalResponse(approved=False, reason="Operation cancelled by user")

    return approval_callback
