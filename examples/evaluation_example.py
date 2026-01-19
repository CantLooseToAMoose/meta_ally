"""
Comprehensive evaluation example that combines:
- Dataset loaded from DatasetManager (Data/add_one)
- Agent from create_agent_example
- Evaluation task from eval_tasks.py
- Custom evaluator from evaluators.py
- Two LLMJudge evaluators from pydantic_evals
"""

from pathlib import Path

import logfire
from pydantic_ai.retries import RetryConfig
from pydantic_evals.evaluators import LLMJudge
from tenacity import stop_after_attempt, wait_exponential

from meta_ally.agents import AgentFactory
from meta_ally.agents.model_config import create_azure_model_config
from meta_ally.eval import DatasetManager
from meta_ally.eval.eval_tasks import create_agent_conversation_task
from meta_ally.eval.evaluators import ToolCallEvaluator
from meta_ally.tools.tool_group_manager import (
    AIKnowledgeToolGroup,
    AllyConfigToolGroup,
)


def create_evaluation_agent():
    """
    Create the agent like the agent in the create_agent_example with all tools.

    Returns:
        tuple: A tuple containing (agent, deps, model_config).
    """
    factory = AgentFactory()

    # Create agent with custom model config - tools are loaded automatically!
    model_config = create_azure_model_config(
        deployment_name="gpt-4.1-mini",
        endpoint="https://ally-frcentral.openai.azure.com/",
    )

    agent = factory.create_hybrid_assistant(
        model=model_config,
        ai_knowledge_groups=[AIKnowledgeToolGroup.ALL],
        ally_config_groups=[AllyConfigToolGroup.ALL],
    )

    # Create dependencies for the agent
    deps = factory.create_dependencies()

    return agent, deps, model_config


def main():
    """Main function to run the evaluation."""
    logfire.configure()
    logfire.instrument_pydantic_ai()
    # Create the agent, dependencies, and model config
    agent, deps, _model_config = create_evaluation_agent()

    # Create a SEPARATE model config for LLMJudge evaluators to avoid sharing the same Azure client
    # Sharing the same client can cause connection pool exhaustion and rate limiting issues
    judge_model_config = create_azure_model_config(
        deployment_name="gpt-4.1-mini",
        endpoint="https://ally-frcentral.openai.azure.com/",
    )
    judge_model = judge_model_config.create_model()

    # Create the evaluation task
    task = create_agent_conversation_task(agent, deps)

    # Load dataset from DatasetManager
    data_dir = Path(__file__).parent.parent / "Data" / "add_one"
    manager = DatasetManager.load(directory=data_dir)

    # Define evaluators
    evaluators = [
        ToolCallEvaluator(),
        LLMJudge(
            rubric="Evaluate the overall helpfulness and accuracy of the model's responses in the conversation.",
            model=judge_model,
            include_input=True,
            include_expected_output=True,
            score={"evaluation_name": "Helpfulness and accuracy", "include_reason": True}
        ),
        LLMJudge(
            rubric="Assess the correctness and relevance of the tool calls made by the model during the conversation.",
            model=judge_model,
            include_input=True,
            include_expected_output=True,
            score={"evaluation_name": "Tool Call Evaluation", "include_reason": True}
        )
    ]

    # Configure retry behavior for tasks and evaluators separately
    task_retry_config: RetryConfig = {
        'stop': stop_after_attempt(3),  # Stop after 3 attempts for task
        'wait': wait_exponential(multiplier=5, min=1, max=20),  # Exponential backoff: 5s, 10s, 20s
        'reraise': True,  # Re-raise the original exception after exhausting retries
    }

    evaluator_retry_config: RetryConfig = {
        'stop': stop_after_attempt(2),  # Stop after 2 attempts for evaluators
        'wait': wait_exponential(multiplier=5, min=1, max=100),  # Exponential backoff: 5s, 10s, 20s
        'reraise': True,  # Re-raise the original exception after exhausting retries
    }

    # Run evaluation on a single dataset using the new convenience method
    dataset_id = "addone_case_1"
    report = manager.evaluate_dataset(
        dataset_id=dataset_id,
        task=task,
        evaluators=evaluators,
        retry_task_config=task_retry_config,  # Pass the task retry config
        retry_evaluator_config=evaluator_retry_config,  # Pass the evaluator retry config
        max_concurrency=1,  # Run max 1 concurrent test case to keep it sequential
        wrap_with_hooks=False  # This will apply any pre/post hooks defined for the dataset
    )
    report.print()


if __name__ == "__main__":
    main()
