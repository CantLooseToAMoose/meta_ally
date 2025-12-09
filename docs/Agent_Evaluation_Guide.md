# Agent Evaluation Guide

This guide walks you through the complete process of evaluating a new agent in the Meta Ally framework, from creating test cases to analyzing results.

## Table of Contents

1. [Overview](#overview)
2. [Step 1: Create Test Cases](#step-1-create-test-cases)
3. [Step 2: Set Up Dataset Manager](#step-2-set-up-dataset-manager)
4. [Step 3: Run Evaluations](#step-3-run-evaluations)
5. [Step 4: Analyze Results](#step-4-analyze-results)
6. [Best Practices](#best-practices)

---

## Overview

The evaluation process consists of four main steps:

```
Use Case Definition → Create Test Cases → Set Up Datasets → Run Evaluations → Analyze Results
```

Each step builds upon the previous one, allowing you to create comprehensive, reproducible evaluations for your agents.

---

## Step 1: Create Test Cases

**Goal:** Define conversation scenarios that represent your agent's use case.

**See:** `examples/case_factory_addone_example.py`

### Process

1. **Create a CaseFactory instance** to organize your test cases
2. **Define a conversation flow** using `ConversationTurns`
3. **Add conversation turns** representing user messages, model responses, and tool calls
4. **Create test cases** at critical points in the conversation

### Example Structure

```python
from meta_ally.eval.case_factory import CaseFactory, create_tool_call_part

def example_your_agent_creation():
    """Define test cases for your agent's use case."""
    
    factory = CaseFactory()
    convo = factory.create_conversation_turns()
    
    # Case 1: Initial user request
    convo.add_user_message("Your user's initial request...")
    case1_expected = "Expected agent response..."
    factory.create_conversation_case(
        name="Case 1: Initial Request",
        conversation_turns=convo,
        expected_final_response=case1_expected,
        description="Description of what this case tests"
    )
    
    # Continue the conversation with model response
    convo.add_model_message(case1_expected)
    
    # Case 2: User provides additional info, agent makes tool calls
    convo.add_user_message("User provides required information...")
    case2_expected = "Agent response after processing..."
    factory.create_conversation_case(
        name="Case 2: Processing with Tools",
        conversation_turns=convo,
        expected_final_response=case2_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="your_tool_name",
                args={"param": "value"},
                tool_call_id="tool_call_1"
            )
        ],
        description="Tests agent's tool usage"
    )
    
    # Add tool execution results to conversation
    convo.add_tool_call(
        tool_call_id="tool_call_1",
        tool_name="your_tool_name",
        args={"param": "value"}
    )
    convo.add_tool_response(
        tool_call_id="tool_call_1",
        tool_name="your_tool_name",
        content="Tool execution result"
    )
    convo.add_model_message(case2_expected)
    
    # ... Continue building conversation and test cases
    
    return factory.dataset
```

### Key Concepts

- **ConversationTurns**: Represents the entire conversation history, shared across all cases
- **Cases**: Snapshots of the conversation at specific points, with expected outputs
- **Progressive Testing**: Each case tests the agent's behavior at increasingly complex stages
- **Expected Outputs**: Define both expected responses and tool calls for validation

---

## Step 2: Set Up Dataset Manager

**Goal:** Create datasets with test variants and configure API hooks for resource management.

**See:** `examples/dataset_manager_addone_example.py`

### Process

1. **Load your test cases** from Step 1
2. **Create a HookLibrary** for managing backend API state
3. **Initialize a DatasetManager** with the hook library
4. **Create datasets** with multiple variants for each case
5. **Assign hooks** to cases that need API resource management
6. **Save the manager** to disk for later use

### Example Structure

```python
from pathlib import Path
from meta_ally.eval import DatasetManager
from meta_ally.eval.api_test_hooks import APITestHookLibrary
from meta_ally.lib.auth_manager import AuthManager
from meta_ally.eval.case_factory import MessageHistoryCase
from your_case_factory import example_your_agent_creation

def main():
    # Step 1: Load cases
    print("Loading cases...")
    original_dataset = example_your_agent_creation()
    
    # Step 2: Create HookLibrary with API operation hooks
    print("Creating HookLibrary...")
    auth_manager = AuthManager()
    hook_library = APITestHookLibrary(auth_manager)
    
    # Step 3: Create DatasetManager
    print("Creating DatasetManager...")
    manager = DatasetManager(hook_library=hook_library)
    
    # Step 4: Create datasets with variants
    print("Creating datasets with variants...")
    for i, case in enumerate(original_dataset.cases, 1):
        # Convert to MessageHistoryCase
        message_history_case = MessageHistoryCase.from_case(case)
        
        # Create dataset with variants (e.g., 3 variations per case)
        dataset_id = manager.create_dataset_from_case(
            case=message_history_case,
            dataset_id=f"your_use_case_{i}",
            num_variants=3,
            name=case.name,
            description=f"Test case {i} with variants"
        )
        
        # Step 5: Assign hooks where needed
        # Example: Cases that create resources need cleanup
        if i == 4:  # Case that creates API resources
            manager.set_dataset_hooks(
                dataset_id=dataset_id,
                pre_task_hook_id="cleanup_your_resources"
            )
        elif i == 5:  # Case that requires existing resources
            manager.set_dataset_hooks(
                dataset_id=dataset_id,
                pre_task_hook_id="setup_your_resources"
            )
    
    # Step 6: Save to disk
    output_dir = Path("Data") / "your_use_case"
    print(f"Saving manager to {output_dir}...")
    manager.save(
        directory=output_dir,
        save_built_datasets=True,
        overwrite=True
    )
    
    print("✓ Dataset manager saved successfully!")
```

### Why Variants?

Creating multiple variants per case helps:
- Test robustness across similar inputs
- Identify edge cases and inconsistencies
- Improve statistical significance of results

### When to Use Hooks

Use **pre-task hooks** when:
- Your agent creates API resources (sources, collections, copilots)
- Tests require a clean state (delete existing resources)
- Tests need specific resources to exist before running

Common hook patterns:
- **Cleanup hooks**: Delete resources before tests that create them
- **Setup hooks**: Ensure required resources exist, remove ones that shouldn't
- **No hooks needed**: For tests that only query or read data

---

## Step 3: Run Evaluations

**Goal:** Execute your test cases against the agent and collect evaluation metrics.

**See:** `examples/evaluation_suite_example.py`

### Process

1. **Load the DatasetManager** from disk (with hook library)
2. **Create an EvaluationSuite** and add your dataset manager
3. **Set up your agent** with appropriate tools and configuration
4. **Create an evaluation task** (typically conversation-based)
5. **Define evaluators** (custom validators and LLM judges)
6. **Configure retry behavior** for robustness
7. **Run the evaluation** with automatic hook execution
8. **Save results** for later analysis

### Example Structure

```python
from pathlib import Path
from tenacity import stop_after_attempt, wait_exponential
from pydantic_evals.evaluators import LLMJudge

from meta_ally.agents import AgentFactory
from meta_ally.util.tool_group_manager import AIKnowledgeToolGroup, AllyConfigToolGroup
from meta_ally.eval import DatasetManager, EvaluationSuite
from meta_ally.eval.evaluators import ToolCallEvaluator
from meta_ally.eval.eval_tasks import create_agent_conversation_task
from meta_ally.eval.api_test_hooks import APITestHookLibrary
from meta_ally.lib.auth_manager import AuthManager

def main():
    # Step 1: Load DatasetManager from disk
    print("Loading DatasetManager...")
    data_dir = Path("Data") / "your_use_case"
    auth_manager = AuthManager()
    hook_library = APITestHookLibrary(auth_manager)
    manager = DatasetManager.load(directory=data_dir, hook_library=hook_library)
    
    # Step 2: Create EvaluationSuite
    print("Creating EvaluationSuite...")
    suite = EvaluationSuite()
    suite.add_dataset_manager(manager, name="your_use_case")
    
    # Step 3: Set up agent
    print("Creating agent...")
    factory = AgentFactory()
    model_config = factory.create_azure_model_config(deployment_name="gpt-4.1")
    agent = factory.create_hybrid_assistant(
        model=model_config,
        ai_knowledge_groups=[AIKnowledgeToolGroup.ALL],
        ally_config_groups=[AllyConfigToolGroup.ALL],
    )
    deps = factory.create_dependencies()
    
    # Step 4: Create evaluation task
    print("Setting up task...")
    task = create_agent_conversation_task(agent, deps)
    
    # Step 5: Define evaluators
    print("Setting up evaluators...")
    factory_for_judge = AgentFactory()
    judge_model_config = factory_for_judge.create_azure_model_config(
        deployment_name="gpt-4.1-mini"
    )
    judge_model = judge_model_config.create_model()
    
    evaluators = [
        # Custom evaluator for tool call validation
        ToolCallEvaluator(),
        
        # LLM judges for qualitative assessment
        LLMJudge(
            rubric="Evaluate the overall helpfulness and accuracy of responses.",
            model=judge_model,
            include_input=True,
            include_expected_output=True,
            score={"evaluation_name": "Helpfulness and accuracy", "include_reason": True}
        ),
        LLMJudge(
            rubric="Assess the correctness and relevance of tool calls.",
            model=judge_model,
            include_input=True,
            include_expected_output=True,
            score={"evaluation_name": "Tool Call Evaluation", "include_reason": True}
        ),
    ]
    
    # Step 6: Configure retry behavior
    task_retry_config = {
        'stop': stop_after_attempt(2),
        'wait': wait_exponential(multiplier=2, min=30, max=200),
        'reraise': True,
    }
    evaluator_retry_config = {
        'stop': stop_after_attempt(2),
        'wait': wait_exponential(multiplier=2, min=30, max=200),
        'reraise': True,
    }
    
    # Step 7: Run evaluation
    print("Running evaluation...")
    reports = suite.run_evaluation(
        task=task,
        evaluators=evaluators,
        task_name="your_use_case_eval",
        dataset_ids=None,  # Evaluate all datasets, or specify subset
        retry_task_config=task_retry_config,
        retry_evaluator_config=evaluator_retry_config,
        max_concurrency=1,  # Sequential execution
        wrap_with_hooks=True,  # Enable automatic API resource management
        run_metadata={
            "description": "Evaluation of your agent",
            "agent_type": "hybrid_assistant",
            "model": "gpt-4.1"
        }
    )
    
    # Step 8: Save results
    print("Saving results...")
    output_dir = Path("evaluation_results")
    save_info = suite.save_results(
        reports=reports,
        base_dir=output_dir,
        overwrite=False
    )
    
    print(f"✓ Results saved to: {save_info['save_path']}")
    print(f"  Run ID: {save_info['metadata']['run_id']}")
```

### Key Configuration Options

- **max_concurrency**: Controls parallel execution (use 1 for sequential(if you plan an changing things on the backend sequential is probably your way to go), higher for parallel)
- **wrap_with_hooks**: Enables automatic pre/post-task hook execution
- **retry_config**: Handles transient failures (API rate limits, network issues)
- **run_metadata**: Additional context saved with results for later reference

### Understanding Hook Execution

When `wrap_with_hooks=True`:
1. Before each test case: Pre-task hook runs (if configured)
2. Test case executes with the agent
3. After each test case: Post-task hook runs (if configured)

This ensures consistent API state across test runs without manual intervention.

---

## Step 4: Analyze Results

**Goal:** Extract insights from evaluation results and generate reports.

**See:** `examples/analyze_reports_example.py`

### Process

1. **Load saved evaluation results** by run ID
2. **Generate dataset-specific tables** for detailed analysis
3. **Create summary tables** for cross-dataset comparison
4. **Export LaTeX tables** for academic papers or reports

### Example Structure

```python
from meta_ally.util.analyze_reports import (
    load_evaluation_run,
    create_dataset_table,
    create_run_summary_table
)

def main():
    # Step 1: Load evaluation run
    print("Loading evaluation run...")
    run_data = load_evaluation_run(
        base_dir="evaluation_results",
        run_id="your_use_case_eval_20251209_093432"
    )
    
    print(f"✓ Loaded run: {run_data['metadata']['run_id']}")
    print(f"  Task: {run_data['metadata']['task_name']}")
    print(f"  Datasets: {', '.join(run_data['metadata']['dataset_ids'])}")
    
    # Step 2: Generate dataset-specific table
    print("\nDataset Table (case_1):")
    dataset_table = create_dataset_table(
        reports=run_data['reports'],
        dataset_id="your_use_case_1",
        include_metrics=True  # Include token counts and costs
    )
    print(dataset_table)
    
    # Step 3: Generate table with filtered scores
    print("\nDataset Table with Selected Scores:")
    filtered_table = create_dataset_table(
        reports=run_data['reports'],
        dataset_id="your_use_case_2",
        score_names=["ToolCallEvaluator"],  # Only specific evaluators
        include_metrics=False
    )
    print(filtered_table)
    
    # Step 4: Generate run summary table
    print("\nRun Summary Table:")
    summary_table = create_run_summary_table(
        run_data=run_data,
        include_metrics=True
    )
    print(summary_table)
    
    # Step 5: Summary without metrics (cleaner for presentations)
    print("\nRun Summary (Scores Only):")
    summary_simple = create_run_summary_table(
        run_data=run_data,
        score_names=["ToolCallEvaluator", "Helpfulness and accuracy"],
        include_metrics=False
    )
    print(summary_simple)
```

### Output Formats

The analysis tools generate:

- **LaTeX tables**: Ready to include in academic papers
- **Console output**: Quick inspection during development
- **Aggregated metrics**: Mean scores across variants with standard deviations
- **Token/cost statistics**: Usage metrics for budget tracking

### Typical Analysis Workflow

1. **Initial check**: Load results and print summary
2. **Dataset deep-dive**: Examine specific datasets with poor performance
3. **Score filtering**: Focus on specific evaluators (e.g., tool calls only)
4. **Report generation**: Create LaTeX tables for documentation
5. **Iteration**: Identify issues, improve agent, re-evaluate

---

## Best Practices

### Test Case Design

✅ **DO:**
- Start simple, build complexity progressively
- Test both happy paths and edge cases
- Include tool usage in critical cases
- Document what each case tests

❌ **DON'T:**
- Create too many cases initially (start with 3-5)
- Mix multiple concerns in one case
- Forget to add model responses between user messages

### Dataset Management

✅ **DO:**
- Use 3-5 variants per case for good coverage
- Assign hooks to cases that modify API state
- Save datasets with descriptive names
- Version control your dataset configurations

❌ **DON'T:**
- Create variants that are too similar (waste of resources)
- Forget to clean up resources between tests
- Hardcode paths (use `Path` objects)

### Evaluation Execution

✅ **DO:**
- Use separate models for agent and LLM judges (avoid connection pool issues)
- Configure retry logic for robustness
- Start with `max_concurrency=1` for debugging
- Save results with descriptive metadata

❌ **DON'T:**
- Run all evaluations in parallel initially (hard to debug)
- Skip retry configuration (transient failures will break runs)
- Forget to enable `wrap_with_hooks` when using hooks

### Results Analysis

✅ **DO:**
- Compare runs across different agent configurations
- Look for patterns in failures (specific case types)
- Track token usage and costs over time
- Export tables for documentation

❌ **DON'T:**
- Make conclusions from single runs (run multiple times)
- Ignore low-scoring cases (they indicate problems)
- Forget to check individual case outputs (not just aggregate scores)

---

## Quick Reference

| Step | Input | Output | Key Tool |
|------|-------|--------|----------|
| 1. Create Cases | Use case requirements | `CaseFactory.dataset` | `CaseFactory` |
| 2. Setup Datasets | Cases + Hook requirements | Saved dataset manager | `DatasetManager` |
| 3. Run Evaluation | Dataset manager + Agent | Evaluation reports | `EvaluationSuite` |
| 4. Analyze Results | Saved reports | LaTeX tables, insights | `analyze_reports` |

---

## Common Issues and Solutions

### Issue: Hooks not executing
**Solution:** Ensure `wrap_with_hooks=True` in `run_evaluation()` and hooks are properly registered in the `HookLibrary`.

### Issue: Connection pool exhausted
**Solution:** Use separate model instances for agent and LLM judges (different `AgentFactory` instances).

### Issue: Tests failing intermittently
**Solution:** Configure retry logic with exponential backoff in `task_retry_config` and `evaluator_retry_config`.

### Issue: Can't find saved results
**Solution:** Check the run ID format (includes timestamp) and verify the `base_dir` path.

### Issue: Variants too similar
**Solution:** Increase the `num_variants` parameter or manually create more diverse variants.

---

## Next Steps

After completing your first evaluation:

1. **Iterate on your agent**: Use insights to improve prompts, tools, or logic
2. **Expand test coverage**: Add more cases for untested scenarios
3. **Compare configurations**: Run evaluations with different models or parameters
4. **Automate**: Set up CI/CD pipelines for continuous evaluation
5. **Share results**: Generate LaTeX tables for papers or reports

For more examples, see:
- `examples/case_factory_addone_example.py` - Complex multi-turn conversation
- `examples/dataset_manager_addone_example.py` - Hook management patterns
- `examples/evaluation_suite_example.py` - Complete evaluation pipeline
- `examples/analyze_reports_example.py` - Results analysis techniques
