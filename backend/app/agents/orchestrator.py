import json
import re
from typing import Any, Dict, List, Optional

from app.agents.tools import TOOLS, TOOL_SCHEMAS, ToolResult
from app.core.llm import get_llm_provider, LLMMessage


SYSTEM_PROMPT = """You are an AI investigator for EngageIQ, a client delivery intelligence platform.
Your role is to analyze engagement data, identify risks, and provide evidence-based recommendations.

You have access to the following tools:
{tool_descriptions}

When investigating an engagement, follow this process:
1. Understand the user's question
2. Select and call the appropriate tools to gather data
3. Analyze the results
4. Retrieve relevant knowledge base evidence if needed
5. Provide a structured response with:
   - Executive summary
   - Key findings with evidence
   - Risk assessment
   - Recommendations
   - Supporting data references

Always cite your data sources. Distinguish between:
- Model explanations (SHAP values showing feature contributions)
- Causal explanations (business logic and domain knowledge)
- Retrieved evidence (policy documents, playbooks)

Never invent numerical results. Only use data returned by tools."""


def format_tool_descriptions() -> str:
    desc = []
    for name, schema in TOOL_SCHEMAS.items():
        params = schema["parameters"]["properties"]
        param_desc = ", ".join([f"{k}: {v.get('description', '')}" for k, v in params.items()])
        desc.append(f"- {name}: {schema['description']} ({param_desc})")
    return "\n".join(desc)


async def investigate(question: str, engagement_id: Optional[str] = None) -> Dict[str, Any]:
    llm = get_llm_provider()

    messages = [
        LLMMessage(role="system", content=SYSTEM_PROMPT.format(tool_descriptions=format_tool_descriptions())),
    ]

    if engagement_id:
        messages.append(LLMMessage(role="user", content=f"Engagement context: {engagement_id}"))

    messages.append(LLMMessage(role="user", content=question))

    tool_results = []
    max_iterations = 5

    for _ in range(max_iterations):
        response = await llm.chat(messages)

        tool_calls = extract_tool_calls(response.content)
        if not tool_calls:
            break

        for tool_name, tool_args in tool_calls:
            if tool_name in TOOLS:
                if "engagement_id" in tool_args and engagement_id and not tool_args["engagement_id"]:
                    tool_args["engagement_id"] = engagement_id

                result: ToolResult = TOOLS[tool_name](**tool_args)
                tool_results.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result.data if result.success else None,
                    "error": result.error,
                })

                messages.append(LLMMessage(
                    role="assistant",
                    content=f"Tool {tool_name} executed. Result: {json.dumps(result.data) if result.success else result.error}"
                ))

        messages.append(LLMMessage(role="user", content="Continue analysis or provide final answer."))

    final_response = await llm.chat(messages)

    return {
        "question": question,
        "engagement_id": engagement_id,
        "answer": final_response.content,
        "tool_calls": tool_results,
        "evidence": [r for r in tool_results if r["tool"] == "retrieve_evidence" and r["result"]],
    }


def extract_tool_calls(text: str) -> List[tuple]:
    pattern = r'TOOL_CALL:\s*(\w+)\s*\((.*?)\)'
    calls = []

    for match in re.finditer(pattern, text, re.DOTALL):
        tool_name = match.group(1)
        args_str = match.group(2).strip()

        try:
            args = json.loads(args_str) if args_str else {}
        except json.JSONDecodeError:
            args = {}

        calls.append((tool_name, args))

    return calls