"""
Dependencies for multi-agent systems.

This module provides dependency classes for managing state and context
across multiple agents in an orchestrator-specialist architecture.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .openapi_to_tools import OpenAPIToolDependencies


class TimelineEntryType(Enum):
    """Type of entry in the conversation timeline."""
    ORCHESTRATOR_MESSAGE = "orchestrator_message"
    SPECIALIST_RUN = "specialist_run"


@dataclass
class TimelineEntry:
    """
    A single entry in the unified conversation timeline.

    This allows tracking both orchestrator messages and specialist runs
    in chronological order for visualization and debugging.

    Attributes:
        entry_type: The type of entry (orchestrator message or specialist run)
        data: The actual data - either a ModelMessage or SpecialistRun
        displayed: Whether this entry has been shown in the terminal
    """
    entry_type: TimelineEntryType
    data: Any
    displayed: bool = False


@dataclass
class SpecialistRun:
    """
    Record of a single specialist agent run for visualization and debugging.

    Attributes:
        agent_name: Name of the specialist agent that was called
        task: The task/query that was sent to the specialist
        response: The final text response from the specialist
        new_messages: The new messages generated during this specialist run
        all_messages: All messages including history after this run
    """
    agent_name: str
    task: str
    response: str
    new_messages: list[Any] = field(default_factory=list)
    all_messages: list[Any] = field(default_factory=list)


@dataclass
class MultiAgentDependencies(OpenAPIToolDependencies):
    """
    Dependencies for multi-agent systems with conversation tracking.

    Extends OpenAPIToolDependencies to support orchestrator-specialist architectures
    where conversation history needs to be maintained per specialist agent.

    The conversation_timeline provides a unified, chronologically ordered list of
    all events (orchestrator messages and specialist runs) for visualization.

    Attributes:
        auth_manager: Manages authentication for API calls
        geschaeftsbereich: The user's business area (Geschäftsbereich)
        project_number: The project number the user is working with
        endpoint_name: The specific endpoint configuration being discussed
        conversations: Dict mapping agent names to their conversation history
        conversation_timeline: Unified chronological list of all conversation events
    """
    conversations: dict[str, list[Any]] = field(default_factory=dict)
    conversation_timeline: list[TimelineEntry] = field(default_factory=list)

    @classmethod
    def from_openapi_deps(
        cls,
        openapi_deps: OpenAPIToolDependencies
    ) -> "MultiAgentDependencies":
        """
        Create MultiAgentDependencies from existing OpenAPIToolDependencies.

        Args:
            openapi_deps: Existing OpenAPI dependencies to extend

        Returns:
            New MultiAgentDependencies instance with same auth and context
        """
        return cls(
            auth_manager=openapi_deps.auth_manager,
            geschaeftsbereich=openapi_deps.geschaeftsbereich,
            project_number=openapi_deps.project_number,
            endpoint_name=openapi_deps.endpoint_name,
            conversations={},
            conversation_timeline=[],
        )

    def get_conversation(self, agent_name: str) -> list[Any]:
        """
        Get the conversation history for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            List of messages for that agent (empty list if no history)
        """
        return self.conversations.get(agent_name, [])

    def update_conversation(self, agent_name: str, messages: list[Any]) -> None:
        """
        Update the conversation history for a specific agent.

        Args:
            agent_name: Name of the agent
            messages: Full message history to store
        """
        self.conversations[agent_name] = messages

    def add_orchestrator_messages(self, messages: list[Any]) -> None:
        """
        Add orchestrator messages to the timeline.

        Args:
            messages: List of ModelMessages from the orchestrator
        """
        for message in messages:
            entry = TimelineEntry(
                entry_type=TimelineEntryType.ORCHESTRATOR_MESSAGE,
                data=message,
            )
            self.conversation_timeline.append(entry)

    def add_specialist_run(
        self,
        agent_name: str,
        task: str,
        response: str,
        new_messages: list[Any],
        all_messages: list[Any],
    ) -> SpecialistRun:
        """
        Record a specialist agent run to the timeline.

        This should be called from within the specialist tool, BEFORE returning,
        so that the specialist run appears in the timeline before the tool return.

        Args:
            agent_name: Name of the specialist agent
            task: The task that was sent to the specialist
            response: The text response from the specialist
            new_messages: New messages generated in this run
            all_messages: All messages after this run

        Returns:
            The created SpecialistRun for reference
        """
        run = SpecialistRun(
            agent_name=agent_name,
            task=task,
            response=response,
            new_messages=new_messages,
            all_messages=all_messages,
        )
        entry = TimelineEntry(
            entry_type=TimelineEntryType.SPECIALIST_RUN,
            data=run,
        )
        self.conversation_timeline.append(entry)
        return run

    def get_timeline(self) -> list[TimelineEntry]:
        """
        Get the full conversation timeline.

        Returns:
            List of TimelineEntry objects in chronological order
        """
        return self.conversation_timeline.copy()

    def get_undisplayed_entries(self) -> list[TimelineEntry]:
        """
        Get timeline entries that haven't been displayed yet.

        Returns:
            List of TimelineEntry objects that have displayed=False
        """
        return [entry for entry in self.conversation_timeline if not entry.displayed]

    def mark_entries_as_displayed(self) -> int:
        """
        Mark all timeline entries as displayed.

        Returns:
            Number of entries that were marked as displayed
        """
        count = 0
        for entry in self.conversation_timeline:
            if not entry.displayed:
                entry.displayed = True
                count += 1
        return count

    def get_specialist_runs(self) -> list[SpecialistRun]:
        """
        Get all specialist runs from the timeline.

        Returns:
            List of SpecialistRun objects extracted from the timeline
        """
        return [
            entry.data
            for entry in self.conversation_timeline
            if entry.entry_type == TimelineEntryType.SPECIALIST_RUN
        ]

    def clear_timeline(self) -> list[TimelineEntry]:
        """
        Clear and return the conversation timeline.

        Returns:
            List of timeline entries that were cleared
        """
        timeline = self.conversation_timeline.copy()
        self.conversation_timeline = []
        return timeline

    def get_all_conversations(self) -> dict[str, list[Any]]:
        """
        Get all conversation histories.

        Returns:
            Dict mapping agent names to their conversation histories
        """
        return self.conversations.copy()
