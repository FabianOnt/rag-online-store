import json
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from services.rag.config import settings as rag_settings
from services.rag.tools import (
    vector_search,
    product_search_name,
    product_search,
    product_search_reviews,
    product_search_warranty
)


planner_llm = ChatOllama(
    base_url=rag_settings.BASE_URL,
    model=rag_settings.MODEL_NAME,
    reasoning=False,
    top_k=80,
    temperature=0.1,
    num_predict=1000,
    num_ctx=2000
)

fast_llm = ChatOllama(
    base_url=rag_settings.BASE_URL,
    model=rag_settings.MODEL_NAME,
    reasoning=False,
    top_k=40,
    temperature=0.7,
    num_predict=400,
    num_ctx=1000
)

TOOLS_LIST = [
    vector_search,
    product_search_name,
    product_search,
    product_search_reviews,
    product_search_warranty
]
TOOL_MAP: Dict[str, Any] = {tool.name: tool for tool in TOOLS_LIST}

executor_llm = planner_llm.bind_tools(TOOLS_LIST)
fast_llm_with_tools = fast_llm.bind_tools(TOOLS_LIST)


class ExecutionStep(BaseModel):
    step_number: int
    tool_name: str = Field(description="Target tool name or 'none'.")
    objective: str = Field(description="Objective of this specific step.")

class ExecutionPlan(BaseModel):
    plan: List[ExecutionStep]

def parse_json_from_llm(raw_content: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_content.strip(), flags=re.MULTILINE)
    return json.loads(cleaned)



def classify_query(query: str) -> str:
    """Classifies query into 'FAST_PATH' or 'PLAN_PATH'."""
    router_prompt = f"""Analyze the user query for an e-commerce assistant.
Classify it into one of two routing modes:
- "FAST_PATH": Single-step actions, simple questions, direct SKU lookups, or single product searches.
- "PLAN_PATH": Complex multi-step queries, comparisons across multiple products, or multi-stage research requiring sequential dependencies (e.g., finding a product first, then checking its warranty and reviews).

Output ONLY a JSON object with key "mode":
{{"mode": "FAST_PATH"}} or {{"mode": "PLAN_PATH"}}

Query: "{query}"
"""
    try:
        response = planner_llm.invoke([HumanMessage(content=router_prompt)])
        data = parse_json_from_llm(response.content)
        return data.get("mode", "FAST_PATH")
    except Exception:
        return "FAST_PATH"  # Default fallback


def run_fast_path(query: str, max_iterations: int = 3) -> str:
    messages = [
        SystemMessage(content="You are an e-commerce assistant. Use tools when needed to answer directly and concisely. Only if you have access to the data, return the product price and sku, if not, dont include them."),
        HumanMessage(content=query)
    ]

    for _ in range(max_iterations):
        response: AIMessage = fast_llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return response.content

        for tool_call in response.tool_calls:

            t_name = tool_call["name"]
            t_args = tool_call["args"]
            c_id = tool_call["id"]

            if t_name in TOOL_MAP:
                try:
                    res = TOOL_MAP[t_name].invoke(t_args)
                except Exception as e:
                    res = json.dumps({"error": f"Tool error: {str(e)}"})

                messages.append(ToolMessage(content=str(res), tool_call_id=c_id, name=t_name))

    return messages[-1].content


def run_plan_and_execute_path(query: str) -> str:
    """
    'Thinking process': 1. Plan -> 2. Execute -> 3. Synthetise.
    """
    
    # Stage 1
    planner_prompt = f"""You are an e-commerce execution planner.
Create a step-by-step execution plan using these available tools:
- vector_search(query, search_descriptions, search_faqs, search_warranty)
- product_search_name(product_name)
- product_search(product_sku, include_faqs)
- product_search_reviews(product_sku)
- product_search_warranty(product_sku)

Return ONLY valid JSON:
{{
  "plan": [
    {{"step_number": 1, "tool_name": "<tool_name>", "objective": "<objective description>"}}
  ]
}}

User Query: "{query}"
"""
    try:
        planner_resp = planner_llm.invoke([HumanMessage(content=planner_prompt)])
        plan_data = parse_json_from_llm(planner_resp.content)
        execution_plan = [ExecutionStep(**step) for step in plan_data.get("plan", [])]
    except Exception:
        return run_fast_path(query)

    # Stage 2
    accumulated_context = []

    for step in execution_plan:
        step_system_prompt = SystemMessage(
            content=(
                "SYSTEM INSTRUCTION: You are an automated executor step.\n"
                "DO NOT write free text, explanations, greetings, or conversational responses.\n"
                "You MUST call the designated tool function directly using the provided parameters.\n"
                f"Target Tool to invoke: `{step.tool_name}`"
            )
        )
        
        step_user_prompt = HumanMessage(
            content=(
                f"Overall Query: '{query}'\n"
                f"Step {step.step_number} Objective: {step.objective}\n\n"
                f"Prior Step Context:\n{json.dumps(accumulated_context, indent=2) if accumulated_context else 'None'}\n\n"
                f"Invoke tool `{step.tool_name}` now."
            )
        )

        step_response: AIMessage = executor_llm.invoke([step_system_prompt, step_user_prompt])

        step_output_payload = {
            "step": step.step_number,
            "tool_used": step.tool_name,
            "objective": step.objective,
            "result": None
        }

        if step_response.tool_calls:
            for tool_call in step_response.tool_calls:
                t_name = tool_call["name"]
                t_args = tool_call["args"]

                if t_name in TOOL_MAP:
                    try:
                        raw_result = TOOL_MAP[t_name].invoke(t_args)
                        step_output_payload["result"] = raw_result
                    except Exception as e:
                        step_output_payload["result"] = f"Execution error: {str(e)}"
        else:
            step_output_payload["result"] = step_response.content

        accumulated_context.append(step_output_payload)

    # Stage 3
    synthesis_prompt = f"""You are a helpful e-commerce AI assistant.
Synthesize the collected data below into a clear, cohesive response addressing the user's question.
Only if you have access to the data, return the product price and sku, if not, dont include them.

User Query: "{query}"

Gathered Execution Insights:
{json.dumps(accumulated_context, indent=2)}

Provide a direct, complete response for the customer:
"""
    final_resp = planner_llm.invoke([HumanMessage(content=synthesis_prompt)])
    return final_resp.content


def add_context(query: str, last_messages: list[str]) -> str:
    if len(last_messages) == 0:
        return query
    else:
        context_prompt = f"""You are a helpful e-commerce AI assistant.
If necessary, extract useful information from the last messages in addition to the user query to 
produce a more contextualized query. If the user is currently asking for 'the product' you may look
for its SKU in the last messages, or its price, rating, etc. Only if required.

User Query: "{query}"

Lasr Messages:
{json.dumps(last_messages, indent=2)}

Return a direct, complete query based on the original query and the context provided:
"""
        final_resp = planner_llm.invoke([HumanMessage(content=context_prompt)])
        return final_resp.content


def run_rag_agent(query: str, last_messages: list[str]) -> str:
    contextualized_query = add_context(query, last_messages)
    mode = classify_query(contextualized_query)
    
    if mode == "PLAN_PATH":
        answer = run_plan_and_execute_path(contextualized_query)
    else:
        answer = run_fast_path(contextualized_query)

    return {
        "answer": answer,
        "sources": []
    } 