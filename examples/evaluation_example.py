"""
Comprehensive evaluation example that combines:
- Case from case_factory_example 
- Agent from create_agent_example
- Evaluation task from eval_tasks.py
- Custom evaluator from evaluators.py
- Two LLMJudge evaluators from pydantic_evals
"""

import sys
import asyncio
from pathlib import Path
from typing import List, Any

# Import pydantic_evals
import logfire
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge
from pydantic_ai.messages import UserPromptPart

from tenacity import stop_after_attempt, wait_exponential



# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import required modules after path setup
from src.agents import AgentFactory
from src.util.tool_group_manager import AIKnowledgeToolGroup, AllyConfigToolGroup
from src.eval.case_factory import CaseFactory, create_tool_call_part
from src.eval.evaluators import ToolCallEvaluator
from src.eval.conversation_turns import ModelMessage
from examples.case_factory_addone_example import example_addone_sales_copilot_creation
from src.eval.eval_tasks import create_agent_conversation_task


def create_evaluation_agent():
    """Create the agent from create_agent_example with all tools."""
    factory = AgentFactory()
    
    # Setup the tools
    print("Setting up AI Knowledge tools...")
    factory.setup_ai_knowledge_tools()
    print("Setting up Ally Config tools...")
    factory.setup_ally_config_tools()

    model_config = factory.create_azure_model_config(deployment_name="gpt-4.1")

    agent = factory.create_hybrid_assistant(
        model=model_config,
        ai_knowledge_groups=[AIKnowledgeToolGroup.ALL],
        ally_config_groups=[AllyConfigToolGroup.ALL],
    )

    # Create dependencies for the agent
    deps = factory.create_dependencies()
    deps.auth_manager._refresh_token()
    
    return agent, deps

def main():
    """Main function to run the evaluation."""
            
    logfire.configure()
    logfire.instrument_pydantic_ai()
    # Create the agent and dependencies
    agent, deps = create_evaluation_agent()
    factory=AgentFactory()
    model_config = factory.create_azure_model_config()

    # Create the evaluation task
    task=create_agent_conversation_task(agent, deps)

    #Create the case factory and dataset
    dataset=example_addone_sales_copilot_creation()
    dataset.add_evaluator(ToolCallEvaluator())

    # Add LLMJudge evaluators
    dataset.add_evaluator(
        LLMJudge(
            rubric="Evaluate the overall helpfulness and accuracy of the model's responses in the conversation.",
            model=model_config.create_model(),
            include_input=True,
            include_expected_output=True,
            score={"evaluation_name": "Helpfulness and accuracy", "include_reason": True}

        )
    )
    dataset.add_evaluator(
        LLMJudge(
            rubric="Assess the correctness and relevance of the tool calls made by the model during the conversation.",
            model=model_config.create_model(),
            include_input=True,
            include_expected_output=True,
            score={"evaluation_name": "Tool Call Evaluation", "include_reason": True}
        )
    )
    # Run the evaluation

    retry_config = {
    'stop': stop_after_attempt(2),  # Stop after 2 attempts
    'wait': wait_exponential(multiplier=2, min=30, max=200),  # Exponential backoff: 30s, 60s
    'reraise': True,  # Re-raise the original exception after exhausting retries
}
    report=dataset.evaluate_sync(task,retry_task=retry_config)
    report.print()

if __name__ == "__main__":
    main()
