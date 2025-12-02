"""
Comprehensive evaluation example that combines:
- Case from case_factory_example 
- Agent from create_agent_example
- Evaluation task from eval_tasks.py
- Custom evaluator from evaluators.py
- Two LLMJudge evaluators from pydantic_evals
"""

# Import pydantic_evals
import logfire
from pydantic_evals.evaluators import LLMJudge

from tenacity import stop_after_attempt, wait_exponential

# Import required modules
from meta_ally.agents import AgentFactory
from meta_ally.util.tool_group_manager import AIKnowledgeToolGroup, AllyConfigToolGroup
from meta_ally.eval.evaluators import ToolCallEvaluator
from examples.case_factory_addone_example import example_addone_sales_copilot_creation
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
    deps.auth_manager._refresh_token()
    
    return agent, deps

def main():
    """Main function to run the evaluation."""
            
    logfire.configure()
    logfire.instrument_pydantic_ai()
    # Create the agent and dependencies
    agent, deps = create_evaluation_agent()
    factory=AgentFactory()
    
    # Create model config for LLMJudge evaluators
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
    report=dataset.evaluate_sync(task,retry_task=retry_config) # type: ignore
    report.print()

if __name__ == "__main__":
    main()
