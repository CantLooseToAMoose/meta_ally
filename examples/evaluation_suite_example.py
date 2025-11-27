"""
Example of using EvaluationSuiteManager to run evaluations across multiple datasets.

This example demonstrates:
1. Creating multiple DatasetManager instances
2. Building datasets with different configurations
3. Using EvaluationSuiteManager to coordinate evaluations
4. Adding global and dataset-specific evaluators
5. Running evaluations across all datasets
"""

import sys
import asyncio
from pathlib import Path
from typing import List, Any

# Import pydantic_evals
import logfire
from pydantic_evals.evaluators import LLMJudge
from tenacity import stop_after_attempt, wait_exponential

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import required modules after path setup
from src.agents import AgentFactory
from src.util.tool_group_manager import AIKnowledgeToolGroup, AllyConfigToolGroup
from src.eval.case_factory import CaseFactory
from src.eval.dataset_manager import DatasetManager
from src.eval.evaluation_suite_manager import EvaluationSuiteManager
from src.eval.evaluators import ToolCallEvaluator
from src.eval.eval_tasks import create_agent_conversation_task
from examples.case_factory_addone_example import example_addone_sales_copilot_creation


def create_evaluation_agent():
    """Create the agent for evaluation with all tools."""
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


def create_dataset1() -> DatasetManager:
    """Create first dataset - original cases only."""
    print("\nCreating Dataset 1: Original cases only...")
    manager = DatasetManager()
    
    # Add cases from the example dataset
    from examples.case_factory_addone_example import example_addone_sales_copilot_creation
    from src.eval.case_factory import MessageHistoryCase
    
    # Get the dataset and convert cases to MessageHistoryCase
    dataset = example_addone_sales_copilot_creation()
    for case in dataset.cases:
        message_history_case = MessageHistoryCase.from_case(case)
        manager.add_case(message_history_case)
    
    # Build dataset without variants
    manager.build_dataset(
        name="AddOne Sales Copilot - Original Cases",
        include_originals=True,
        include_variants=False
    )
    
    return manager


def create_dataset2() -> DatasetManager:
    """Create second dataset - original cases + 2 variants each."""
    print("\nCreating Dataset 2: Original + 2 variants...")
    manager = DatasetManager()
    
    # Add cases from the example dataset
    from examples.case_factory_addone_example import example_addone_sales_copilot_creation
    from src.eval.case_factory import MessageHistoryCase
    
    # Get the dataset and convert cases to MessageHistoryCase
    dataset = example_addone_sales_copilot_creation()
    for case in dataset.cases:
        message_history_case = MessageHistoryCase.from_case(case)
        manager.add_case(message_history_case)
    
    # Create variants
    manager.create_variants(num_variants_per_case=2)
    
    # Build dataset with variants
    manager.build_dataset(
        name="AddOne Sales Copilot - With Variants",
        include_originals=True,
        include_variants=True
    )
    
    return manager


def create_dataset3() -> DatasetManager:
    """Create third dataset - variants only."""
    print("\nCreating Dataset 3: Variants only...")
    manager = DatasetManager()
    
    # Add cases from the example dataset
    from examples.case_factory_addone_example import example_addone_sales_copilot_creation
    from src.eval.case_factory import MessageHistoryCase
    
    # Get the dataset and convert cases to MessageHistoryCase
    dataset = example_addone_sales_copilot_creation()
    for case in dataset.cases:
        message_history_case = MessageHistoryCase.from_case(case)
        manager.add_case(message_history_case)
    
    # Create variants
    manager.create_variants(num_variants_per_case=3)
    
    # Build dataset with variants only
    manager.build_dataset(
        name="AddOne Sales Copilot - Variants Only",
        include_originals=False,
        include_variants=True
    )
    
    return manager


def main():
    """Main function to run the evaluation suite."""
    
    logfire.configure()
    logfire.instrument_pydantic_ai()
    
    # Create the agent and dependencies
    print("Creating evaluation agent...")
    agent, deps = create_evaluation_agent()
    
    # Create the evaluation task
    task = create_agent_conversation_task(agent, deps)
    
    # Create the evaluation suite manager
    print("\nInitializing Evaluation Suite Manager...")
    suite = EvaluationSuiteManager(name="AddOne Sales Copilot Evaluation Suite")
    
    # Create and add multiple datasets
    dataset1 = create_dataset1()
    dataset2 = create_dataset2()
    dataset3 = create_dataset3()
    
    suite.add_dataset_manager("original_only", dataset1)
    suite.add_dataset_manager("with_variants", dataset2)
    suite.add_dataset_manager("variants_only", dataset3)
    
    # Add global evaluators (applied to all datasets)
    print("\nAdding global evaluators...")
    suite.add_global_evaluator(ToolCallEvaluator())
    
    # Add dataset-specific evaluators
    print("Adding dataset-specific evaluators...")
    factory = AgentFactory()
    model_config = factory.create_azure_model_config()
    
    # Add LLMJudge only to the first dataset as an example
    suite.add_evaluator(
        "original_only",
        LLMJudge(
            rubric="Evaluate the overall helpfulness and accuracy of the model's responses.",
            model=model_config.create_model(),
            include_input=True,
            include_expected_output=True,
            score={"evaluation_name": "Helpfulness and Accuracy", "include_reason": True}
        )
    )
    
    # Add a different LLMJudge to the second dataset
    suite.add_evaluator(
        "with_variants",
        LLMJudge(
            rubric="Assess the correctness and relevance of the tool calls made by the model.",
            model=model_config.create_model(),
            include_input=True,
            include_expected_output=True,
            score={"evaluation_name": "Tool Call Evaluation", "include_reason": True}
        )
    )
    
    # Print suite statistics
    suite.print_stats()
    
    # Configure retry settings
    retry_config = {
        'stop': stop_after_attempt(2),
        'wait': wait_exponential(multiplier=2, min=30, max=200),
        'reraise': True,
    }
    
    # Run evaluation across all datasets
    print("\nRunning evaluations across all datasets...")
    results = suite.run_evaluation_sync(
        task=task,
        retry_task=retry_config
    )
    
    # Print all results
    results.print()
    
    # Access individual results
    print("\n" + "="*80)
    print("Accessing individual results:")
    print("="*80)
    original_result = results.get_result("original_only")
    if original_result:
        print(f"\nFound result for '{original_result.dataset_name}'")
    
    # You can also run evaluation on specific datasets only
    print("\n" + "="*80)
    print("Running evaluation on specific datasets only...")
    print("="*80)
    specific_results = suite.run_evaluation_sync(
        task=task,
        dataset_names=["original_only", "variants_only"],
        retry_task=retry_config
    )
    specific_results.print()


if __name__ == "__main__":
    main()
