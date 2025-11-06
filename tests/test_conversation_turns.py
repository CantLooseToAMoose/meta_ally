#!/usr/bin/env python3
"""
Pytest tests for ConversationTurns functionality in the CaseFactory.
"""

import pytest

from src.eval.case_factory import CaseFactory


@pytest.fixture
def case_factory():
    """Fixture to provide a CaseFactory instance for tests."""
    return CaseFactory()


@pytest.fixture
def simple_conversation(case_factory):
    """Fixture to provide a simple conversation for testing."""
    conversation = case_factory.create_conversation_turns(
    )
    conversation.add_user_message("Hello, how are you?")
    conversation.add_model_message("I'm doing well, thank you for asking!")
    conversation.add_user_message("Can you help me with something?")
    return conversation


@pytest.fixture
def tool_conversation(case_factory):
    """Fixture to provide a conversation with tool calls for testing."""
    conversation = case_factory.create_conversation_turns()
    conversation.add_user_message("What's the weather like?")
    conversation.add_model_message("Let me check the weather for you.")
    conversation.add_tool_call(
        tool_call_id="weather_1",
        tool_name="get_weather", 
        args={"location": "current"}
    )
    conversation.add_tool_response(
        tool_call_id="weather_1",
        tool_name="get_weather",
        content="Current weather: 72°F, sunny"
    )
    conversation.add_user_message("Thanks! What about tomorrow?")
    return conversation


class TestConversationTurns:
    """Test suite for ConversationTurns functionality."""
    
    def test_simple_conversation_creation(self, simple_conversation, case_factory):
        """Test creating a simple conversation with user and model messages."""
        conversation = simple_conversation
        
        # Validate conversation structure
        errors = conversation.validate()
        assert not errors, f"Simple conversation should be valid, got errors: {errors}"
        
        # Check message count
        message_count = conversation.get_message_count()
        assert message_count == 3, f"Expected 3 messages, got {message_count}"
        
        # Create test case
        case = case_factory.create_conversation_case(
            name="Simple Conversation Test",
            conversation_turns=conversation,
            expected_final_response="Of course! I'd be happy to help you with whatever you need.",
            description="Test simple conversation flow"
        )
        
        assert case.name == "Simple Conversation Test"
        assert case.description == "Test simple conversation flow"
        assert len(case.input_messages) == 3
    
    def test_conversation_with_tool_calls(self, tool_conversation, case_factory):
        """Test conversation with tool calls and responses."""
        conversation = tool_conversation
        
        # Validate conversation
        errors = conversation.validate()
        assert not errors, f"Tool call conversation should be valid, got errors: {errors}"
        
        # Check message count (should have 4 messages)
        message_count = conversation.get_message_count()
        assert message_count == 4, f"Expected 4 messages, got {message_count}"
        
        # Create test case
        case = case_factory.create_conversation_case(
            name="Tool Call Conversation Test",
            conversation_turns=conversation,
            expected_final_response="Let me check tomorrow's forecast for you.",
            description="Test conversation with tool calls"
        )
        
        assert case.name == "Tool Call Conversation Test"
        assert len(case.input_messages) == 4

    def test_invalid_conversation_start(self, case_factory):
        """Test that conversations starting with model message fail validation."""
        conversation = case_factory.create_conversation_turns()
        
        # Start with model message instead of user message (invalid)
        conversation.add_model_message("I'll start this conversation incorrectly")
        conversation.add_user_message("This won't validate properly")
        
        errors = conversation.validate()
        assert len(errors) > 0, "Invalid conversation should have validation errors"
        assert any("must start with a ModelRequest" in error for error in errors)
    
    def test_invalid_conversation_end(self, case_factory):
        """Test that conversations ending with model message fail validation."""
        conversation = case_factory.create_conversation_turns()
        
        conversation.add_user_message("Hello")
        conversation.add_model_message("Hi there!")
        # Missing final user message (invalid)
        
        errors = conversation.validate()
        assert len(errors) > 0, "Invalid conversation should have validation errors"
        assert any("must end with a ModelRequest" in error for error in errors)
    
    @pytest.mark.parametrize("test_case,expected_error", [
        ("empty_conversation", "must have at least one message"),
        ("start_with_model", "must start with a ModelRequest"),
        ("end_with_model", "must end with a ModelRequest"),
        ("tool_without_response", "Tool calls without responses"),
    ])
    def test_conversation_validation_errors(self, case_factory, test_case, expected_error):
        """Test various conversation validation error scenarios."""
        conversation = case_factory.create_conversation_turns()
        
        if test_case == "empty_conversation":
            # Leave conversation empty
            pass
        elif test_case == "start_with_model":
            conversation.add_model_message("Starting incorrectly")
            conversation.add_user_message("Follow up")
        elif test_case == "end_with_model":
            conversation.add_user_message("Hello")
            conversation.add_model_message("Hi there!")
            # Missing final user message
        elif test_case == "tool_without_response":
            conversation.add_user_message("Search for something")
            conversation.add_tool_call("search_1", "search", {"query": "test"})
            # Missing tool response
        
        errors = conversation.validate()
        assert len(errors) > 0, f"Test case '{test_case}' should have validation errors"
        assert any(expected_error in error for error in errors), f"Expected error '{expected_error}' not found in {errors}"
    
    def test_tool_call_without_response(self, case_factory):
        """Test that tool calls without responses fail validation."""
        conversation = case_factory.create_conversation_turns()
        
        conversation.add_user_message("Search for something")
        conversation.add_tool_call(
            tool_call_id="search_1",
            tool_name="search",
            args={"query": "test"}
        )
        # Missing tool response
        
        errors = conversation.validate()
        assert len(errors) > 0, "Tool call without response should have validation errors"
        assert any("Tool calls without responses" in error for error in errors)
        assert any("search_1" in error for error in errors)
    
    def test_single_tool_call_constraint(self, case_factory):
        """Test that multiple tool calls per response are prevented."""
        conversation = case_factory.create_conversation_turns()
        
        conversation.add_user_message("Do multiple searches")
        conversation.add_tool_call("search_1", "search", {"query": "test1"})
        
        # This should raise a ValueError due to single tool call constraint
        with pytest.raises(ValueError, match="Only one tool call is allowed per model response"):
            conversation.add_tool_call("search_2", "search", {"query": "test2"})
    
    def test_sequential_tool_calls_valid(self, case_factory):
        """Test that sequential tool calls (in separate responses) are valid."""
        conversation = case_factory.create_conversation_turns()
        
        conversation.add_user_message("Do multiple searches")
        
        # First tool call
        conversation.add_tool_call("search_1", "search", {"query": "test1"})
        conversation.add_tool_response("search_1", "search", "Results 1")
        
        # Second tool call in new model response
        conversation.add_model_message("Let me search for more information.")
        conversation.add_tool_call("search_2", "search", {"query": "test2"})
        conversation.add_tool_response("search_2", "search", "Results 2")
        
        conversation.add_user_message("Thanks for the results!")
        
        # Should be valid
        errors = conversation.validate()
        assert not errors, f"Sequential tool calls should be valid, got errors: {errors}"
    
    def test_conversation_turns_to_messages(self, case_factory):
        """Test converting ConversationTurns to ModelMessage list."""
        conversation = case_factory.create_conversation_turns()
        
        conversation.add_user_message("Hello")
        conversation.add_model_message("Hi there!")
        conversation.add_user_message("How are you?")
        
        messages = conversation.to_messages()
        assert len(messages) == 3
        
        # Check message types
        from pydantic_ai.messages import ModelRequest, ModelResponse
        assert isinstance(messages[0], ModelRequest)
        assert isinstance(messages[1], ModelResponse)
        assert isinstance(messages[2], ModelRequest)
    
    def test_preview_messages(self, case_factory):
        """Test the preview_messages debugging functionality."""
        conversation = case_factory.create_conversation_turns()
        
        conversation.add_user_message("Hello")
        conversation.add_model_message("Hi!")
        conversation.add_tool_call("test_call", "test_tool", {"arg": "value"})
        conversation.add_tool_response("test_call", "test_tool", "response")
        conversation.add_user_message("Thanks")
        
        preview = conversation.preview_messages()
        assert len(preview) == 4, f"Expected 4 preview messages, got {len(preview)}"
        
        # Check that preview contains expected content
        preview_text = "\n".join(preview)
        assert "UserPrompt: Hello" in preview_text
        assert "Text: Hi!" in preview_text
        assert "ToolCall[test_tool]" in preview_text
        assert "ToolReturn[test_tool]" in preview_text
    
    def test_dataset_creation(self, case_factory):
        """Test creating a dataset from multiple conversation cases."""
        # Create first conversation
        conversation1 = case_factory.create_conversation_turns()
        conversation1.add_user_message("Hello")
        conversation1.add_model_message("Hi!")
        conversation1.add_user_message("Goodbye")
        
        case_factory.create_conversation_case(
            name="Simple Chat",
            conversation_turns=conversation1,
            description="Simple conversation test"
        )
        
        # Create second conversation with tools
        conversation2 = case_factory.create_conversation_turns()
        conversation2.add_user_message("Search for something")
        conversation2.add_tool_call("search_1", "search", {"query": "test"})
        conversation2.add_tool_response("search_1", "search", "Found results")
        conversation2.add_user_message("Thanks")
        
        case_factory.create_conversation_case(
            name="Tool Search",
            conversation_turns=conversation2,
            description="Tool-based conversation test"
        )
        
        # Build dataset
        dataset = case_factory.build_dataset("Test Dataset")
        
        assert dataset.name == "Test Dataset"
        assert len(dataset.cases) == 2
        
        case_names = [case.name for case in dataset.cases]
        assert "Simple Chat" in case_names
        assert "Tool Search" in case_names
    
    def test_case_factory_integration(self, case_factory):
        """Test that ConversationTurns integrates properly with CaseFactory."""
        conversation = case_factory.create_conversation_turns()
        
        conversation.add_user_message("Test message")
        conversation.add_model_message("Test response")
        conversation.add_user_message("Follow up")
        
        # Should be able to create case without errors
        case = case_factory.create_conversation_case(
            name="Integration Test",
            conversation_turns=conversation,
            expected_final_response="Expected response",
            description="Test integration",
            metadata={"test": True, "complexity": "simple"}
        )
        
        assert case.name == "Integration Test"
        assert case.description == "Test integration"
        assert case.metadata is not None
        assert case.metadata["test"] is True
        assert case.metadata["complexity"] == "simple"
        assert case.expected_output_messages is not None
        assert len(case.expected_output_messages) == 1
    
    def test_empty_conversation_validation(self, case_factory):
        """Test that empty conversations fail validation."""
        conversation = case_factory.create_conversation_turns()
        
        errors = conversation.validate()
        assert len(errors) > 0, "Empty conversation should have validation errors"
        assert any("must have at least one message" in error for error in errors)
