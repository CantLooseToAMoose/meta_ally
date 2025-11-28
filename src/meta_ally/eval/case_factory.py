"""Factory for creating test cases with message history inputs and outputs."""

from typing import Any, Optional, List, Dict
from pydantic import BaseModel
from pydantic_evals import Case, Dataset
from pydantic_ai.messages import (
    ModelRequest,
    UserPromptPart,
    SystemPromptPart,
    ToolCallPart,
    ToolReturnPart,
)
from .conversation_turns import ConversationTurns, ModelMessage

from ..agents.variation_agent import ConversationVariant, create_variation_agent
from pydantic_ai import ModelRetry


class ExpectedOutput(BaseModel):
    """Flexible expected output configuration for test cases.

    This class allows specifying different types of expected outputs:
    - Simple text response
    - List of tool calls as ToolCallPart objects
    - Full list of ModelMessage objects for complex scenarios
    """

    output_message: Optional[str] = None
    tool_calls: Optional[List[ToolCallPart]] = None
    model_messages: Optional[List[ModelMessage]] = None


class MessageHistoryCase(BaseModel):
    """A test case that holds message history as input and expected output.

    This is a convenient wrapper around pydantic-eval's Case type specifically
    designed for testing conversational AI systems with message histories.
    """

    name: str
    input_messages: List[ModelMessage]
    expected_output: Optional[ExpectedOutput] = None
    metadata: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

    def to_case(self) -> Case[List[ModelMessage], ExpectedOutput, Dict[str, Any]]:
        """Convert this message history case to a pydantic-eval Case."""
        return Case(
            name=self.name,
            inputs=self.input_messages,
            expected_output=self.expected_output,
            metadata=self.metadata,
        )
    
    @classmethod
    def from_case(cls, case: Case[List[ModelMessage], ExpectedOutput, Dict[str, Any]]) -> "MessageHistoryCase":
        """Create a MessageHistoryCase from a pydantic-eval Case.
        
        This is the reverse operation of to_case().
        
        Args:
            case: A pydantic-eval Case object with message history inputs
            
        Returns:
            MessageHistoryCase constructed from the Case object
        """
        return cls(
            name=case.name or "Unnamed Case",
            input_messages=case.inputs,
            expected_output=case.expected_output,
            metadata=case.metadata,
            description=None,  # Case objects don't have a description field
        )
    


class CaseFactory:
    """Factory for creating test cases with message histories."""

    def __init__(self):
        self._cases: List[MessageHistoryCase] = []

    def create_simple_case(
        self,
        name: str,
        user_input: str,
        expected_response: Optional[str] = None,
        system_prompt: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MessageHistoryCase:
        """Create a simple case with a single user input and optional expected response.

        Args:
            name: Name of the test case
            user_input: The user's input message
            expected_response: Expected response from the agent (optional)
            system_prompt: System prompt to include (optional)
            description: Description of the test case
            metadata: Additional metadata for the case

        Returns:
            MessageHistoryCase ready to be used in evaluations
        """
        # Build input messages
        input_parts = []
        if system_prompt:
            input_parts.append(SystemPromptPart(content=system_prompt))
        input_parts.append(UserPromptPart(content=user_input))

        input_messages = [ModelRequest(parts=input_parts)]

        # Build expected output
        expected_output = None
        if expected_response:
            expected_output = ExpectedOutput(output_message=expected_response)

        case = MessageHistoryCase(
            name=name,
            input_messages=list(input_messages),  # Cast to List[ModelMessage]
            expected_output=expected_output,
            metadata=metadata,
            description=description,
        )

        self._cases.append(case)
        return case

    def create_conversation_case(
        self,
        name: str,
        conversation_turns: ConversationTurns,
        expected_final_response: Optional[str] = None,
        expected_final_tool_calls: Optional[List[ToolCallPart]] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MessageHistoryCase:
        """Create a case with multiple conversation turns, including tool calls.

        Args:
            name: Name of the test case
            conversation_turns: ConversationTurns object containing the conversation
            expected_final_response: Expected final response from the agent
            expected_final_tool_calls: Expected tool calls in the final response
            description: Description of the test case
            metadata: Additional metadata for the case

        Returns:
            MessageHistoryCase with full conversation history including tools
        """
        # Validate the conversation
        validation_errors = conversation_turns.validate()
        if validation_errors:
            raise ValueError(
                f"Invalid conversation turns: {'; '.join(validation_errors)}"
            )

        # Get the input messages
        input_messages = conversation_turns.to_messages()

        # Build expected output
        expected_output = None
        if expected_final_response or expected_final_tool_calls:
            expected_output = ExpectedOutput(
                output_message=expected_final_response,
                tool_calls=expected_final_tool_calls,
            )

        case = MessageHistoryCase(
            name=name,
            input_messages=list(input_messages),  # Cast to List[ModelMessage]
            expected_output=expected_output,
            metadata=metadata,
            description=description,
        )

        self._cases.append(case)
        return case

    def create_conversation_turns(self) -> ConversationTurns:
        """Create a new ConversationTurns object for building conversations.

        Returns:
            ConversationTurns object for building the conversation
        """
        return ConversationTurns()

    def create_custom_case(
        self,
        name: str,
        input_messages: List[ModelMessage],
        expected_output: Optional[ExpectedOutput] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MessageHistoryCase:
        """Create a case with custom message history.

        Args:
            name: Name of the test case
            input_messages: List of ModelMessage objects for input
            expected_output: Expected output configuration (optional)
            description: Description of the test case
            metadata: Additional metadata for the case

        Returns:
            MessageHistoryCase with custom message history
        """
        case = MessageHistoryCase(
            name=name,
            input_messages=input_messages,
            expected_output=expected_output,
            metadata=metadata,
            description=description,
        )

        self._cases.append(case)
        return case

    def build_dataset(self, name: str = "Message History Test Dataset") -> Dataset:
        """Build a pydantic-eval Dataset from all created cases.

        Args:
            name: Name for the dataset

        Returns:
            Dataset containing all created cases
        """
        cases = [case.to_case() for case in self._cases]
        return Dataset(cases=cases, name=name)

    def get_cases(self) -> List[MessageHistoryCase]:
        """Get all created cases."""
        return self._cases.copy()

    def clear_cases(self) -> None:
        """Clear all created cases."""
        self._cases.clear()

    def add_batch_simple_cases(
        self, test_data: List[Dict[str, Any]], system_prompt: Optional[str] = None
    ) -> List[MessageHistoryCase]:
        """Add multiple simple cases from a list of test data.

        Args:
            test_data: List of dicts containing 'name', 'user_input', and optionally
                      'expected_response', 'description', 'metadata'
            system_prompt: Optional system prompt to apply to all cases

        Returns:
            List of created MessageHistoryCase objects
        """
        created_cases = []

        for data in test_data:
            case = self.create_simple_case(
                name=data["name"],
                user_input=data["user_input"],
                expected_response=data.get("expected_response"),
                system_prompt=system_prompt,
                description=data.get("description"),
                metadata=data.get("metadata"),
            )
            created_cases.append(case)

        return created_cases


def create_case_variant(
    existing_case: MessageHistoryCase,
    previous_variants: Optional[List[MessageHistoryCase]] = None
) -> MessageHistoryCase:
    """Create a new case variant from an existing MessageHistoryCase.
    
    Args:
        existing_case: The original case to create a variant from
        previous_variants: Optional list of previously generated variants to avoid duplicates
        
    Returns:
        MessageHistoryCase: A new variant case that differs from the original and all previous variants
    """
    if previous_variants is None:
        previous_variants = []

    variation_agent = create_variation_agent(previous_variants)



    @variation_agent.output_validator
    def validate_variant_output(
        output: ConversationVariant,
    ) -> ConversationVariant:
        """
        Validate that the output is a variant of the existing case's output.

        Args:
            ctx: Unused context parameter
            output: The output messages from the variation agent
        Returns:
            ConversationVariant if valid
        
        Raises:
            ModelRetry: If validation fails

        """
        # First, validate the structure of the generated conversation
        conversation = ConversationTurns()
        conversation._messages = output.messages.copy()
        validation_errors = conversation.validate()
        
        if validation_errors:
            raise ModelRetry(
                "Generated variant has structural issues:\n" +
                "\n".join(f"- {error}" for error in validation_errors)
            )
        
        # Get all existing Messages
        existing_message_history = existing_case.input_messages
        
        # Check if the variant is identical to the original case
        if output.messages == existing_message_history:
            raise ModelRetry(
                "Generated variant is identical to the original case.\n"
                "Please create a variation that differs from the original."
            )
        
        # Get a list of all tool calls and responses in existing and new output
        existing_tool_calls_and_responses = [
            part
            for msg in existing_message_history
            for part in msg.parts
            if isinstance(part, (ToolCallPart, ToolReturnPart))
        ]
        new_tool_calls_and_responses = [
            part
            for msg in output.messages
            for part in msg.parts
            if isinstance(part, (ToolCallPart, ToolReturnPart))
        ]
        
        # Compare the tool calls and responses for equality
        for existing_part, new_part in zip(
            existing_tool_calls_and_responses, new_tool_calls_and_responses
        ):
            if existing_part != new_part:
                raise ModelRetry(
                    f"Tool calls and responses need to match in order and content with original case.\n"
                    f"Failed at part:\n"
                    f"Original: {existing_part}\n"
                    f"Variant: {new_part}"
                )
        
        # Check if this variant is identical to any previous variants
        for idx, prev_variant in enumerate(previous_variants, 1):
            if output.messages == prev_variant.input_messages:
                raise ModelRetry(
                    f"Generated variant is identical to previous variant #{idx}.\n"
                    f"Please create a different variation that is unique from all previous variants."
                )
        
        return output

    case_json=existing_case.json()
    variation_input_history=variation_agent.run_sync(case_json)
    new_case=existing_case.model_copy()
    new_case.input_messages=variation_input_history.output.messages
    return new_case


# Convenience function for quick case creation
def create_simple_case(
    name: str,
    user_input: str,
    expected_response: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> Case:
    """Convenience function to create a simple case without using the factory.

    Returns the pydantic-eval Case directly for immediate use.
    """
    factory = CaseFactory()
    message_case = factory.create_simple_case(
        name=name,
        user_input=user_input,
        expected_response=expected_response,
        system_prompt=system_prompt,
    )
    return message_case.to_case()


def create_expected_output(
    output_message: Optional[str] = None,
    tool_calls: Optional[List[ToolCallPart]] = None,
    model_messages: Optional[List[ModelMessage]] = None,
) -> ExpectedOutput:
    """Create an ExpectedOutput object with the specified configuration.

    Args:
        output_message: Expected text response from the agent
        tool_calls: Expected tool calls as ToolCallPart objects
        model_messages: Full list of expected ModelMessage objects

    Returns:
        ExpectedOutput object ready to be used in test cases
    """
    return ExpectedOutput(
        output_message=output_message,
        tool_calls=tool_calls,
        model_messages=model_messages,
    )


def create_tool_call_part(
    tool_name: str, args: Dict[str, Any], tool_call_id: Optional[str] = None
) -> ToolCallPart:
    """Create a ToolCallPart object for use in expected outputs.

    Args:
        tool_name: Name of the tool being called
        args: Arguments for the tool call
        tool_call_id: Unique ID for the tool call (auto-generated if not provided)

    Returns:
        ToolCallPart object ready to be used in ExpectedOutput
    """
    if tool_call_id is None:
        tool_call_id = f"call_{tool_name}_{hash(str(args)) % 10000}"

    return ToolCallPart(tool_name=tool_name, args=args, tool_call_id=tool_call_id)
