"""
Comprehensive evaluation suite example using multiple DatasetManagers from
Data/add_one, Data/analytics, and Data/testing_and_access.

This example demonstrates:
1. Loading multiple DatasetManagers from disk with APITestHookLibrary
   (Data/add_one, Data/analytics, and Data/testing_and_access)
2. Creating an EvaluationSuite with the loaded managers
3. Setting up an agent with tools for evaluation (using mock API by default)
4. Defining multiple evaluators (custom + LLM judges)
5. Running evaluations across all datasets with automatic API resource management
6. Saving and loading evaluation results
7. Analyzing results from saved evaluations

Note: The APITestHookLibrary automatically manages API resources before tests:
- Case 4 tests: Deletes existing sources/collections before running
- Case 5 tests: Ensures sources/collections exist and copilot doesn't before running

Mock API Usage:
- By default, analytics endpoints (get_copilot_ratings, get_copilot_cost_daily, get_copilot_sessions)
  use time-shifted mock data instead of real API calls
- This avoids rate limits and provides reproducible results
- To use real APIs instead, change create_evaluation_agent(use_mock_api=False)
"""

import logging
from pathlib import Path

import logfire
from pydantic_ai.retries import RetryConfig
from pydantic_evals.evaluators import LLMJudge
from tenacity import stop_after_attempt, wait_chain, wait_fixed

from meta_ally.agents import AgentFactory
from meta_ally.agents.agent_presets import (
    create_default_multi_agent_system,
    create_hybrid_assistant,
)
from meta_ally.agents.model_config import create_azure_model_config
from meta_ally.auth.auth_manager import AuthManager
from meta_ally.eval import DatasetManager, EvaluationSuite
from meta_ally.eval.api_test_hooks import APITestHookLibrary
from meta_ally.eval.eval_tasks import (
    create_agent_conversation_task,
    create_multi_agent_conversation_task,
)
from meta_ally.eval.evaluators import ToolCallEvaluator
from meta_ally.mock.analytics_api_mock_service import (
    create_ally_config_mock_tool_replacements,
)
from meta_ally.tools.tool_group_manager import (
    AIKnowledgeToolGroup,
    AllyConfigToolGroup,
)


def create_hybrid_evaluation_agent(use_mock_api: bool = True, use_improved_descriptions: bool = True):
    """
    Create a single hybrid agent with all tools for evaluation.

    Args:
        use_mock_api: If True, use mock API for analytics endpoints (default: True).
                     Set to False to use real API calls.
        use_improved_descriptions: If True, use improved tool descriptions (default: True).

    Returns:
        Tuple of (agent, dependencies, model_config)
    """
    factory = AgentFactory()

    # Create agent with Azure OpenAI model - tools are loaded automatically
    model_config = create_azure_model_config(
        deployment_name="gpt-4.1-mini",
        endpoint="https://ally-frcentral.openai.azure.com/",
    )

    # Optionally use mock API for analytics endpoints
    tool_replacements = None
    if use_mock_api:
        print("\n[Mock API] Creating mock tool replacements for analytics endpoints...")
        try:
            tool_replacements = create_ally_config_mock_tool_replacements()
            print(f"    ✓ Created {len(tool_replacements)} mock replacements:")
            for tool_name in tool_replacements:
                print(f"      • {tool_name}")
            print("    ✓ Analytics endpoints will use time-shifted mock data")
            print("    ✓ Benefits: No rate limits, reproducible results, offline capable")
        except FileNotFoundError as e:
            print(f"    ✗ Warning: Could not load mock data: {e}")
            print("    ✗ Falling back to real API calls")
            print("    [i] Run capture_anonymize_api_data.ipynb to create mock data")
            tool_replacements = None

    # Set up improved descriptions paths if enabled
    ai_knowledge_descriptions_path = None
    ally_config_descriptions_path = None
    if use_improved_descriptions:
        ai_knowledge_descriptions_path = "Data/improved_tool_descriptions/ai_knowledge_improved_descriptions.json"
        ally_config_descriptions_path = "Data/improved_tool_descriptions/ally_config_improved_descriptions.json"
        print("\n[Improved Descriptions] Using enhanced tool descriptions")

    agent = create_hybrid_assistant(
        factory=factory,
        model=model_config,
        ai_knowledge_groups=[AIKnowledgeToolGroup.ALL],
        ally_config_groups=[AllyConfigToolGroup.ALL],
        tool_replacements=tool_replacements,  # Pass mock replacements if available
        ai_knowledge_descriptions_path=ai_knowledge_descriptions_path,
        ally_config_descriptions_path=ally_config_descriptions_path,
    )

    # Create dependencies for the agent
    deps = factory.create_dependencies()

    return agent, deps, model_config


def create_multi_agent_evaluation_orchestrator(use_mock_api: bool = True, use_improved_descriptions: bool = True):
    """
    Create a multi-agent orchestrator with specialist agents for evaluation.

    Args:
        use_mock_api: If True, use mock API for analytics endpoints (default: True).
                     Set to False to use real API calls.
        use_improved_descriptions: If True, use improved tool descriptions (default: True).

    Returns:
        Tuple of (orchestrator, multi_agent_dependencies, model_config)
    """
    factory = AgentFactory()

    # Create model config with Azure OpenAI
    model_config = create_azure_model_config(
        deployment_name="gpt-4.1-mini",
        endpoint="https://ally-frcentral.openai.azure.com/",
    )

    # Optionally use mock API for analytics endpoints
    tool_replacements = None
    if use_mock_api:
        print("\n[Mock API] Creating mock tool replacements for analytics endpoints...")
        try:
            tool_replacements = create_ally_config_mock_tool_replacements()
            print(f"    ✓ Created {len(tool_replacements)} mock replacements:")
            for tool_name in tool_replacements:
                print(f"      • {tool_name}")
            print("    ✓ Analytics endpoints will use time-shifted mock data")
            print("    ✓ Benefits: No rate limits, reproducible results, offline capable")
        except FileNotFoundError as e:
            print(f"    ✗ Warning: Could not load mock data: {e}")
            print("    ✗ Falling back to real API calls")
            print("    [i] Run capture_anonymize_api_data.ipynb to create mock data")
            tool_replacements = None

    # Set up improved descriptions paths if enabled
    ai_knowledge_descriptions_path = None
    ally_config_descriptions_path = None
    if use_improved_descriptions:
        ai_knowledge_descriptions_path = "Data/improved_tool_descriptions/ai_knowledge_improved_descriptions.json"
        ally_config_descriptions_path = "Data/improved_tool_descriptions/ally_config_improved_descriptions.json"
        print("\n[Improved Descriptions] Using enhanced tool descriptions")

    # Create multi-agent orchestrator
    orchestrator = create_default_multi_agent_system(
        factory=factory,
        orchestrator_model=model_config,
        specialist_model=model_config,
        require_human_approval=False,  # No human approval during evaluation
        tool_replacements=tool_replacements,
        ai_knowledge_descriptions_path=ai_knowledge_descriptions_path,
        ally_config_descriptions_path=ally_config_descriptions_path,
    )

    # Create multi-agent dependencies
    deps = factory.create_multi_agent_dependencies()

    return orchestrator, deps, model_config


def setup_evaluators(judge_model):
    """
    Create a list of evaluators for the evaluation.

    Args:
        judge_model: Model to use for LLM judge evaluators

    Returns:
        List of evaluators
    """
    return [
        # Custom evaluator for tool call validation
        ToolCallEvaluator(),

        # LLM judge for overall helpfulness and accuracy
        LLMJudge(
            rubric="Evaluate the overall helpfulness and accuracy of the model's response in its last turn.",
            model=judge_model,
            include_input=True,
            include_expected_output=True,
            score={"evaluation_name": "Helpfulness and accuracy", "include_reason": True}
        ),

        # LLM judge for tool call evaluation
        LLMJudge(
            rubric="Assess the correctness and relevance of the tool calls made by the model in its last turn.",
            model=judge_model,
            include_input=True,
            include_expected_output=True,
            score={"evaluation_name": "Tool Call Evaluation", "include_reason": True}
        ),

    ]


def main():  # noqa: C901, PLR0912, PLR0915, PLR0914
    """
    Main function demonstrating EvaluationSuite usage with mock API support.

    By default, uses mock API for analytics endpoints to avoid rate limits
    and provide reproducible results. Set use_mock_api=False to use real APIs.

    Set use_multi_agent=True to evaluate the multi-agent orchestrator instead of
    the single hybrid agent.
    """
    # ============================================================================
    # Configuration
    # ============================================================================
    use_multi_agent = False  # Set to True to evaluate multi-agent orchestrator
    use_mock_api = True  # Set to False to use real API calls
    use_improved_descriptions = True  # Set to True to use improved tool descriptions

    agent_type = "multi_agent_orchestrator" if use_multi_agent else "single_agent"
    model_name = "gpt-5-mini"

    print("=" * 80)
    print("Multi-Dataset EvaluationSuite Example (ADD*ONE + Analytics + Testing & Access)")
    print("=" * 80)
    agent_mode = 'Multi-Agent Orchestrator with Specialists' if use_multi_agent else 'Single Hybrid Agent'
    api_mode = 'Using mock data for analytics endpoints' if use_mock_api else 'Using real API calls'
    desc_mode = 'Using improved tool descriptions' if use_improved_descriptions else 'Using default tool descriptions'
    print(f"\n[Agent Type] {agent_mode}")
    print(f"[Mock API] {api_mode}")
    print(f"[Descriptions] {desc_mode}")

    # Configure logging with logfire
    logfire.configure(scrubbing=False)
    logfire.instrument_pydantic_ai()
    logging.getLogger("logfire._internal").setLevel(logging.ERROR)
    logging.getLogger("logfire").setLevel(logging.ERROR)

    # Step 1: Load the DatasetManagers from disk with API hooks
    print("\n[1] Loading DatasetManagers from Data/add_one, Data/analytics, and Data/testing_and_access...")

    # Create hook library for loading (required to restore hooks)
    auth_manager = AuthManager()
    hook_library = APITestHookLibrary(auth_manager)
    print(f"    [i] Loaded hook library with {len(hook_library.list_hooks())} hooks")

    # Load add_one dataset manager
    addone_data_dir = Path(__file__).parent.parent / "Data" / "add_one"
    if not addone_data_dir.exists():
        print(f"    ✗ Error: Dataset directory not found: {addone_data_dir}")
        print("    Please run dataset_manager_addone_example.py first to create the dataset.")
        return

    addone_manager = DatasetManager.load(directory=addone_data_dir, hook_library=hook_library)
    addone_dataset_ids = addone_manager.list_dataset_ids()
    print(f"    ✓ Loaded add_one DatasetManager with {len(addone_dataset_ids)} datasets")
    for dataset_id in addone_dataset_ids:
        stats = addone_manager.get_dataset_stats(dataset_id)
        hook_info = " (with hooks)" if stats.get("has_pre_hook") or stats.get("has_post_hook") else ""
        print(f"      • {dataset_id}: {stats['num_variants']} variants, {stats['total_cases']} cases{hook_info}")

    # Load analytics dataset manager
    analytics_data_dir = Path(__file__).parent.parent / "Data" / "analytics"
    if not analytics_data_dir.exists():
        print(f"    ✗ Error: Dataset directory not found: {analytics_data_dir}")
        print("    Please run dataset_manager_analytics_example.py first to create the dataset.")
        return

    analytics_manager = DatasetManager.load(directory=analytics_data_dir, hook_library=hook_library)
    analytics_dataset_ids = analytics_manager.list_dataset_ids()
    print(f"    ✓ Loaded analytics DatasetManager with {len(analytics_dataset_ids)} datasets")
    for dataset_id in analytics_dataset_ids:
        stats = analytics_manager.get_dataset_stats(dataset_id)
        hook_info = " (with hooks)" if stats.get("has_pre_hook") or stats.get("has_post_hook") else ""
        print(f"      • {dataset_id}: {stats['num_variants']} variants, {stats['total_cases']} cases{hook_info}")

    # Load testing_and_access dataset manager
    testing_data_dir = Path(__file__).parent.parent / "Data" / "testing_and_access"
    if not testing_data_dir.exists():
        print(f"    ✗ Error: Dataset directory not found: {testing_data_dir}")
        print("    Please run dataset_manager_testing_and_access_example.py first to create the dataset.")
        return

    testing_manager = DatasetManager.load(directory=testing_data_dir, hook_library=hook_library)
    testing_dataset_ids = testing_manager.list_dataset_ids()
    print(f"    ✓ Loaded testing_and_access DatasetManager with {len(testing_dataset_ids)} datasets")
    for dataset_id in testing_dataset_ids:
        stats = testing_manager.get_dataset_stats(dataset_id)
        hook_info = " (with hooks)" if stats.get("has_pre_hook") or stats.get("has_post_hook") else ""
        print(f"      • {dataset_id}: {stats['num_variants']} variants, {stats['total_cases']} cases{hook_info}")

    # Step 2: Create EvaluationSuite with all loaded managers
    print("\n[2] Creating EvaluationSuite...")
    suite = EvaluationSuite()
    suite.add_dataset_manager(addone_manager, name="add_one")
    suite.add_dataset_manager(analytics_manager, name="analytics")
    suite.add_dataset_manager(testing_manager, name="testing_and_access")
    print(f"    ✓ Suite created with managers: {suite.list_dataset_managers()}")

    # Step 3: Create agent for evaluation
    print("\n[3] Creating evaluation agent...")
    if use_multi_agent:
        agent, deps, _ = create_multi_agent_evaluation_orchestrator(
            use_mock_api=use_mock_api,
            use_improved_descriptions=use_improved_descriptions
        )
        print("    ✓ Multi-agent orchestrator created with AI Knowledge and Ally Config specialists")
    else:
        agent, deps, _ = create_hybrid_evaluation_agent(
            use_mock_api=use_mock_api,
            use_improved_descriptions=use_improved_descriptions
        )
        print("    ✓ Hybrid agent created with AI Knowledge and Ally Config tools")

    # Step 4: Create evaluation task
    print("\n[4] Setting up evaluation task...")
    if use_multi_agent:
        task = create_multi_agent_conversation_task(agent, deps)
        print("    ✓ Multi-agent conversation task created")
    else:
        task = create_agent_conversation_task(agent, deps)
        print("    ✓ Single-agent conversation task created")

    # Step 5: Setup evaluators
    print("\n[5] Setting up evaluators...")
    # Create a separate model config for LLM judges using gpt-4.1-mini
    # This prevents connection pool exhaustion from sharing the same Azure client
    judge_model_config = create_azure_model_config(
        deployment_name="gpt-4.1-mini",
        endpoint="https://ally-frcentral.openai.azure.com/",
    )
    judge_model = judge_model_config.create_model()
    evaluators = setup_evaluators(judge_model)
    print(f"    ✓ Created {len(evaluators)} evaluators (using gpt-4.1-mini for judges):")
    for evaluator in evaluators:
        print(f"      • {type(evaluator).__name__}")

    # Step 6: Configure retry behavior
    print("\n[6] Configuring retry behavior...")
    task_retry_config = RetryConfig(
        stop=stop_after_attempt(3),
        wait=wait_chain(wait_fixed(30), wait_fixed(60), wait_fixed(120)),
        reraise=True,
    )
    evaluator_retry_config = RetryConfig(
        stop=stop_after_attempt(3),
        wait=wait_chain(wait_fixed(30), wait_fixed(60), wait_fixed(120)),
        reraise=True,
    )
    print("    ✓ Retry config: 3 attempts with fixed waits (30s, 60s, 120s)")

    # Step 7: Run evaluation
    print("\n[7] Running evaluation...")
    print("    [i] Hooks will automatically manage API resources before each test:")
    print("      • Case 4: Deletes existing sources/collections")
    print("      • Case 5: Ensures sources/collections exist, copilot doesn't")
    print("-" * 80)

    desc_suffix = 'improved' if use_improved_descriptions else 'no_improved'
    task_name = f"{agent_type}_{desc_suffix}_descriptions_{model_name}"
    desc_with = 'with' if use_improved_descriptions else 'without'
    description = f"Evaluation of {agent_type} on TESTING_AND_ACCESS datasets {desc_with} improved descriptions."

    reports = suite.run_evaluation(
        task=task,
        evaluators=evaluators,
        task_name=task_name,
        dataset_ids=testing_dataset_ids,  # Filter by passing a list of dataset IDs or None for all
        retry_task_config=task_retry_config,
        retry_evaluator_config=evaluator_retry_config,
        max_concurrency=1,  # Run max 1 concurrent test case to keep it sequential
        wrap_with_hooks=True,  # Apply pre/post hooks if defined
        run_metadata={
            "description": description,
            "agent_type": agent_type,
            "model": model_name,
            "use_mock_api": use_mock_api,
            "use_improved_descriptions": use_improved_descriptions,
        }
    )

    print("-" * 80)

    # Step 8: Display results
    print("\n[8] Evaluation Results Summary:")
    print("=" * 80)

    for dataset_id, report in reports.items():
        print(f"\n📊 Dataset: {dataset_id}")
        print("-" * 80)

        # Print the full report using pydantic_evals built-in method
        report.print()

        # Get averages for quick summary
        # averages() returns a ReportCaseAggregate object or None
        averages = report.averages()
        if averages:
            print(f"\n📈 Averages for {dataset_id}:")

            # Print scores (dict[str, float | int])
            if averages.scores:
                print("  Scores:")
                for metric, value in averages.scores.items():
                    print(f"    • {metric}: {value:.3f}")

            # Print labels (dict[str, dict[str, float]]) - shows distribution of categorical labels
            if averages.labels:
                print("  Labels:")
                for label_name, distribution in averages.labels.items():
                    print(f"    • {label_name}:")
                    for value, percentage in distribution.items():
                        print(f"        - {value}: {percentage:.1%}")

            # Print metrics (dict[str, float | int])
            if averages.metrics:
                print("  Metrics:")
                for metric, value in averages.metrics.items():
                    if isinstance(value, (int, float)):
                        print(f"    • {metric}: {value:.3f}")
                    else:
                        print(f"    • {metric}: {value}")

            # Print assertions pass rate (float | None)
            if averages.assertions is not None:
                print(f"  Assertions Pass Rate: {averages.assertions:.1%}")

            # Print durations (float)
            print(f"  Avg Task Duration: {averages.task_duration:.3f}s")
            print(f"  Avg Total Duration: {averages.total_duration:.3f}s")
        else:
            print(f"\n⚠️  No successful evaluations for {dataset_id} - cannot calculate averages")
        print()

    # Step 9: Save evaluation results
    print("\n[9] Saving evaluation results...")
    results_dir = Path(__file__).parent.parent / "evaluation_results"

    save_info = suite.save_results(
        directory=results_dir,
        overwrite=False
    )

    print(f"    ✓ Saved {save_info['num_runs']} evaluation run(s)")
    print(f"    ✓ Results directory: {save_info['results_directory']}")
    print(f"    ✓ Run directories: {len(save_info['run_directories'])}")
    print("    ✓ Each run has its own directory with metadata.json and reports/")

    # Step 10: Demonstrate loading results back
    print("\n[10] Demonstrating result loading...")

    # Create a new suite and load results
    loaded_suite = EvaluationSuite.load(
        directory=results_dir,
        dataset_managers=[addone_manager, analytics_manager, testing_manager]
    )

    print(f"    ✓ Loaded suite with {len(loaded_suite.list_runs())} run(s)")

    # List all runs
    print("\n[11] Listing all evaluation runs:")
    print("-" * 80)
    runs = loaded_suite.list_runs()
    for metadata in runs:
        print(f"  Run ID: {metadata.run_id}")
        print(f"    • Task: {metadata.task_name}")
        print(f"    • Timestamp: {metadata.timestamp}")
        print(f"    • Datasets: {len(metadata.dataset_ids)}")
        print(f"    • Success: {metadata.success}")
        print()

    # Step 12: Access a specific report
    print("\n[12] Accessing specific report from loaded suite:")
    print("-" * 80)

    if runs:
        first_run_id = runs[0].run_id
        # Get first dataset ID from the first run's metadata
        first_dataset_id = runs[0].dataset_ids[0] if runs[0].dataset_ids else None

        report = loaded_suite.get_report(first_run_id, first_dataset_id) if first_dataset_id else None
        if report:
            print(f"  Retrieved report for {first_run_id} / {first_dataset_id}")

            # Loaded reports are now EvaluationReport objects
            print("\n  Sample averages from loaded report:")
            averages = report.averages()
            if averages:
                if averages.scores:
                    print("  Scores:")
                    for metric, value in list(averages.scores.items())[:3]:  # Show first 3
                        print(f"    • {metric}: {value:.3f}")
            else:
                print("    • No averages available")

    # Final summary
    print("\n" + "=" * 80)
    print("✨ Evaluation Suite Example Completed Successfully! ✨")
    print("=" * 80)
    print("\nKey outputs:")
    print(f"  1. Evaluation results: {results_dir}")
    print(f"  2. Metadata: {results_dir / 'metadata.json'}")
    print(f"  3. Reports: {results_dir / 'reports'}/")
    print("\nConfiguration:")
    print(f"  • Agent Type: {agent_type}")
    print(f"  • Model: {model_name}")
    print(f"  • Mock API: {use_mock_api}")
    print(f"  • Improved Descriptions: {use_improved_descriptions}")
    print("\nDatasets Evaluated:")
    print(f"  • ADD*ONE: {len(addone_dataset_ids)} datasets")
    print(f"  • Analytics: {len(analytics_dataset_ids)} datasets")
    print(f"  • Testing & Access: {len(testing_dataset_ids)} datasets")
    print("\nMock API Configuration:")
    print("  • Analytics endpoints used mock data (time-shifted)")
    print("  • Mocked: get_copilot_ratings, get_copilot_cost_daily, get_copilot_sessions")
    print("  • Benefits: No rate limits, reproducible results, offline capable")
    print("  • To use real APIs: edit create_evaluation_agent(use_mock_api=False)")
    print("\nAPI Resource Management:")
    print("  • Hooks automatically cleaned up and set up resources before tests")
    print("  • Case 4: Sources/collections were deleted before creation tests")
    print("  • Case 5: Sources/collections created, copilot deleted before copilot tests")
    print("\nNext steps:")
    print("  • Analyze the reports for insights")
    print("  • Compare performance across datasets")
    print("  • Try different configurations:")
    print("    - Toggle use_multi_agent to compare single vs multi-agent")
    print("    - Toggle use_improved_descriptions to measure impact")
    print("    - Toggle use_mock_api to test with real APIs")
    print("  • Iterate on agent configuration based on results")
    print("=" * 80)


if __name__ == "__main__":
    main()
