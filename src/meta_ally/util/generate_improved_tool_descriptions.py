"""
Generate improved tool descriptions for OpenAPI-based tools.

This script loads function definitions from OpenAPI specifications and generates
improved tool descriptions that focus on how an agent would use the tools in
the context of operating APIs. The descriptions are generated with full context
of all available tools to ensure coherent and contextually-aware descriptions.

Outputs:
- JSON files: Store new tool descriptions
- HTML files: Side-by-side comparisons of old tool_def vs new descriptions
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic_ai import Agent

from meta_ally.agents.model_config import ModelConfiguration
from meta_ally.lib.openapi_to_tools import OpenAPIToolsLoader

# Configuration for each API to process
API_CONFIGS = [
    {
        "name": "ally_config",
        "url": "https://ally-config-ui.dev.copilot.aws.inform-cloud.io/openapi.json",
        "context": "Ally Config UI - a web application to manage Copilot configurations",
    },
    {
        "name": "ai_knowledge",
        "url": "https://backend-api.dev.ai-knowledge.aws.inform-cloud.io/openapi.json",
        "context": "AI Knowledge API - a document retrieval and knowledge management system",
    },
]


def create_agent() -> Agent:
    """Create an agent configured for generating tool descriptions."""

    model_config = ModelConfiguration(deployment_name="gpt-4.1-mini")
    model = model_config.create_model()

    agent = Agent(
        model=model,
        system_prompt=(
            "You are an expert at writing clear, practical tool descriptions for AI agents. "
            "Your task is to generate tool descriptions that help an AI agent understand when and how "
            "to use each tool in the context of operating an API. "
            "\n\n"
            "IMPORTANT CONTEXT: The tool definitions you receive contain descriptions generated from "
            "docstrings of the original API endpoints. However, the agent that will use these tools "
            "receives a tool that wraps that API under the hood. This means the agent does NOT need to "
            "worry about user authentication, required permissions, or low-level API mechanics - these "
            "are handled automatically by the tool wrapper."
            "\n\n"
            "Focus on:\n"
            "- What the tool does from an agent's perspective\n"
            "- When an agent should use this tool\n"
            "- How it fits into the broader API workflow\n"
            "- Practical usage context rather than technical API route details\n"
            "- Avoid mentioning authentication, permissions, or authorization requirements\n"
            "\n\n"
            "You will be given ALL tool definitions for context, but you should only generate "
            "a description for the ONE tool specifically requested. Use the context of other tools "
            "to ensure your description is coherent with the overall API capabilities.\n"
            "\n\n"
            "IMPORTANT: Only answer with the new tool description text. Do not include any preamble, "
            "explanations, or meta-commentary. Just the description itself."
        ),
    )

    return agent


def format_all_tools_context(tools: list[Any]) -> str:
    """Format all tool definitions into a context string."""
    context_parts = ["=== ALL AVAILABLE TOOLS ===\n"]

    for tool in tools:
        if tool.tool_def is None:
            continue

        context_parts.append(f"Tool: {tool.name}")
        context_parts.append(f"Definition:\n{tool.tool_def}")
        context_parts.append("-" * 80)

    return "\n".join(context_parts)


async def generate_description_for_tool(
    agent: Agent,
    tool: Any,
    all_tools_context: str,
) -> str:
    """Generate an improved description for a single tool with full context."""
    prompt = f"""{all_tools_context}

=== TOOL TO DESCRIBE ===
Tool Name: {tool.name}

Generate a new tool description for: {tool.name}

Tool Definition:
{tool.tool_def}
"""

    result = await agent.run(prompt)
    return result.output.strip()


def generate_html_comparison(
    api_name: str,
    api_context: str,
    tools_data: list[dict[str, Any]],
) -> str:
    """Generate HTML file comparing old tool definitions with new descriptions."""
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "    <meta charset='UTF-8'>",
        "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        f"    <title>{api_name} - Tool Descriptions Comparison</title>",
        "    <style>",
        "        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f5f5f5; }",
        "        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }",
        "        .header h1 { margin: 0 0 10px 0; }",
        "        .header p { margin: 0; opacity: 0.9; }",
        "        .tool-card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
        "        .tool-name { color: #2c3e50; font-size: 1.5em; font-weight: bold; margin-bottom: 10px; border-bottom: 3px solid #3498db; padding-bottom: 5px; }",
        "        .comparison { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 15px; }",
        "        .section { border: 1px solid #e0e0e0; border-radius: 4px; padding: 15px; }",
        "        .section-title { font-weight: bold; color: #34495e; margin-bottom: 10px; padding-bottom: 5px; border-bottom: 2px solid #ecf0f1; }",
        "        .old-def { background: #fff5f5; }",
        "        .new-desc { background: #f0fff4; }",
        "        .content { white-space: pre-wrap; font-family: 'Courier New', monospace; font-size: 0.9em; line-height: 1.5; }",
        "        @media (max-width: 768px) { .comparison { grid-template-columns: 1fr; } }",
        "    </style>",
        "</head>",
        "<body>",
        "    <div class='header'>",
        f"        <h1>{api_name.upper()} - Tool Descriptions Comparison</h1>",
        f"        <p>{api_context}</p>",
        f"        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
        f"        <p>Total Tools: {len(tools_data)}</p>",
        "    </div>",
    ]

    for tool_data in tools_data:
        html_parts.extend([
            "    <div class='tool-card'>",
            f"        <div class='tool-name'>{tool_data['name']}</div>",
            "        <div class='comparison'>",
            "            <div class='section old-def'>",
            "                <div class='section-title'>Original Tool Definition</div>",
            f"                <div class='content'>{html_escape(str(tool_data['original_definition']))}</div>",
            "            </div>",
            "            <div class='section new-desc'>",
            "                <div class='section-title'>New Tool Description</div>",
            f"                <div class='content'>{html_escape(tool_data['new_description'])}</div>",
            "            </div>",
            "        </div>",
            "    </div>",
        ])

    html_parts.extend([
        "</body>",
        "</html>",
    ])

    return "\n".join(html_parts)


def html_escape(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


async def process_api(
    agent: Agent,
    api_config: dict[str, str],
    output_dir: Path,
) -> None:
    """Process a single API and generate descriptions."""
    api_name = api_config["name"]
    api_url = api_config["url"]
    api_context = api_config["context"]

    print(f"\n{'=' * 80}")
    print(f"Processing: {api_name}")
    print(f"URL: {api_url}")
    print(f"{'=' * 80}\n")

    # Load tools from OpenAPI spec
    print("Loading tools from OpenAPI spec...")
    loader = OpenAPIToolsLoader(openapi_url=api_url, regenerate_models=True, models_filename=f"{api_name}_api_models.py")
    tools = loader.load_tools()
    print(f"Loaded {len(tools)} tools\n")

    # Filter out tools without definitions
    valid_tools = [t for t in tools if t.tool_def is not None]
    print(f"Processing {len(valid_tools)} tools with valid definitions\n")

    # Create context string with all tools
    all_tools_context = format_all_tools_context(valid_tools)

    # Generate improved descriptions for each tool
    tools_data = []
    for i, tool in enumerate(valid_tools, 1):
        print(f"[{i}/{len(valid_tools)}] Generating description for: {tool.name}")

        # Retry logic for handling timeouts and transient errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                new_description = await generate_description_for_tool(
                    agent=agent,
                    tool=tool,
                    all_tools_context=all_tools_context,
                )

                tools_data.append({
                    "name": tool.name,
                    "original_definition": str(tool.tool_def),
                    "new_description": new_description,
                })

                # Add a small delay to avoid rate limiting and timeouts
                await asyncio.sleep(1.5)
                break  # Success, exit retry loop

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ⏱️  Error on attempt {attempt + 1}/{max_retries}, retrying: {str(e)[:80]}")
                    await asyncio.sleep(2)  # Brief pause before retry
                else:
                    print(f"  ❌ Failed after {max_retries} attempts: {str(e)[:100]}")
                    break  # Give up after max retries

    print(f"\n✅ Successfully processed {len(tools_data)} tools\n")

    # Save JSON file
    json_file = output_dir / f"{api_name}_improved_descriptions.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "api_name": api_name,
                "api_url": api_url,
                "api_context": api_context,
                "generated_at": datetime.now().isoformat(),
                "tools": tools_data,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"📄 JSON saved: {json_file}")

    # Save HTML file
    html_content = generate_html_comparison(api_name, api_context, tools_data)
    html_file = output_dir / f"{api_name}_improved_descriptions.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"📄 HTML saved: {html_file}")


async def main():
    """Main execution function."""
    print("=" * 80)
    print("Tool Description Generator")
    print("=" * 80)

    # Create output directory
    output_dir = Path(__file__).parent.parent.parent.parent / "Data" / "improved_tool_descriptions"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {output_dir}\n")

    # Create agent
    print("Initializing agent...")
    agent = create_agent()
    print("✅ Agent ready\n")

    # Process each API
    for api_config in API_CONFIGS:
        try:
            await process_api(agent, api_config, output_dir)
        except Exception as e:
            print(f"❌ Error processing {api_config['name']}: {e}\n")
            continue

    print("\n" + "=" * 80)
    print("✅ All processing complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
