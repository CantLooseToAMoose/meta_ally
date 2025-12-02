"""
Comprehensive evaluation example that combines:
- Dataset loaded from DatasetManager (Data/add_one)
- Agent from create_agent_example
- Evaluation task from eval_tasks.py
- Custom evaluator from evaluators.py
- Two LLMJudge evaluators from pydantic_evals
"""

# Import pydantic_evals
import logfire
from pydantic_evals.evaluators import LLMJudge

from pathlib import Path
from tenacity import stop_after_attempt, wait_exponential

# Import required modules
from meta_ally.agents import AgentFactory
from meta_ally.util.tool_group_manager import AIKnowledgeToolGroup, AllyConfigToolGroup
from meta_ally.eval.evaluators import ToolCallEvaluator
from meta_ally.eval import DatasetManager
from meta_ally.eval.eval_tasks import create_agent_conversation_task


def create_evaluation_agent():
    """Create the agent like the agent in the create_agent_example with all tools."""
    factory = AgentFactory()
    
    # Create agent with custom model config - tools are loaded automatically!
    model_config = factory.create_azure_model_config(deployment_name="gpt-4.1")
    
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
    agent, deps, model_config = create_evaluation_agent()
    
    # Create model for LLMJudge evaluators
    judge_model = model_config.create_model()

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
    
    # Configure retry behavior
    retry_config = {
        'stop': stop_after_attempt(2),  # Stop after 2 attempts
        'wait': wait_exponential(multiplier=2, min=30, max=200),  # Exponential backoff: 30s, 60s
        'reraise': True,  # Re-raise the original exception after exhausting retries
    }
    
    # Run evaluation on a single dataset using the new convenience method
    dataset_id = "addone_case_1"
    report = manager.evaluate_dataset(
        dataset_id=dataset_id,
        task=task,
        evaluators=evaluators,
        retry_config=retry_config,
        wrap_with_hooks=True  # This will apply any pre/post hooks defined for the dataset
    )
    report.print()

if __name__ == "__main__":
    main()
