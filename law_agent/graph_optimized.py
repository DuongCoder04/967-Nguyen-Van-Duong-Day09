"""Law Agent LangGraph StateGraph — OPTIMIZED version.

Optimization: merge analyze_law + check_routing into a single LLM call.
This saves 1 sequential LLM call (~30-60s) by asking the LLM to both
analyze the legal question AND decide routing in one prompt.

Graph topology (optimized):
    analyze_and_route → (parallel) call_tax + call_compliance → aggregate → END

vs original:
    analyze_law → check_routing → (parallel) call_tax + call_compliance → aggregate → END
"""

from __future__ import annotations

import json
import logging
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import Send
from langgraph.graph import END, StateGraph

from common.llm import get_llm

logger = logging.getLogger(__name__)

MAX_DELEGATION_DEPTH = 3


def _last_wins(a: str, b: str) -> str:
    return b if b else a


class LawState(TypedDict):
    question: str
    context_id: str
    trace_id: str
    delegation_depth: int
    law_analysis: str
    needs_tax: bool
    needs_compliance: bool
    tax_result: Annotated[str, _last_wins]
    compliance_result: Annotated[str, _last_wins]
    final_answer: str


async def analyze_and_route(state: LawState) -> dict:
    """OPTIMIZED: Single LLM call that both analyzes law AND decides routing.

    Original: 2 sequential LLM calls (analyze_law + check_routing).
    Optimized: 1 LLM call returning analysis + routing flags.
    Savings: ~30-60s per request.
    """
    depth = state.get("delegation_depth", 0)
    if depth >= MAX_DELEGATION_DEPTH:
        logger.info("Max delegation depth reached (%d); skipping sub-agents", depth)
        return {"law_analysis": "", "needs_tax": False, "needs_compliance": False}

    llm = get_llm(tools=True)
    messages = [
        SystemMessage(
            content=(
                "You are a senior corporate litigation attorney. Given a legal question:\n"
                "1. Provide a thorough legal analysis covering contract law, tort law, and business law.\n"
                "2. Decide whether specialist sub-agents are needed.\n\n"
                "You MUST respond in this exact JSON format (no markdown, no extra text):\n"
                "{\n"
                '  "analysis": "<your full legal analysis here>",\n'
                '  "needs_tax": <true|false>,\n'
                '  "needs_compliance": <true|false>\n'
                "}\n\n"
                "needs_tax=true → question involves tax law, IRS, tax evasion, penalties\n"
                "needs_compliance=true → question involves SEC, SOX, AML, FCPA, regulatory compliance"
            )
        ),
        HumanMessage(content=state["question"]),
    ]
    result = await llm.ainvoke(messages)
    raw = result.content.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
        law_analysis = parsed.get("analysis", raw)
        needs_tax = bool(parsed.get("needs_tax", True))
        needs_compliance = bool(parsed.get("needs_compliance", True))
    except json.JSONDecodeError:
        logger.warning("analyze_and_route returned non-JSON — defaulting both=True")
        law_analysis = raw
        needs_tax = True
        needs_compliance = True

    logger.info(
        "analyze_and_route done: needs_tax=%s needs_compliance=%s analysis_len=%d",
        needs_tax, needs_compliance, len(law_analysis),
    )
    return {
        "law_analysis": law_analysis,
        "needs_tax": needs_tax,
        "needs_compliance": needs_compliance,
    }


def route_to_subagents(state: LawState) -> list[Send]:
    sends: list[Send] = []
    if state.get("needs_tax"):
        sends.append(Send("call_tax", state))
    if state.get("needs_compliance"):
        sends.append(Send("call_compliance", state))
    if not sends:
        sends.append(Send("aggregate", state))
    return sends


async def call_tax(state: LawState) -> dict:
    from common.a2a_client import delegate
    from common.registry_client import discover
    try:
        endpoint = await discover("tax_question")
        result = await delegate(
            endpoint=endpoint,
            question=state["question"],
            context_id=state["context_id"],
            trace_id=state["trace_id"],
            depth=state.get("delegation_depth", 0) + 1,
        )
        logger.info("Tax Agent returned %d chars", len(result))
        return {"tax_result": result}
    except Exception as exc:
        logger.exception("call_tax failed: %s", exc)
        return {"tax_result": f"[Tax analysis unavailable: {exc}]"}


async def call_compliance(state: LawState) -> dict:
    from common.a2a_client import delegate
    from common.registry_client import discover
    try:
        endpoint = await discover("compliance_question")
        result = await delegate(
            endpoint=endpoint,
            question=state["question"],
            context_id=state["context_id"],
            trace_id=state["trace_id"],
            depth=state.get("delegation_depth", 0) + 1,
        )
        logger.info("Compliance Agent returned %d chars", len(result))
        return {"compliance_result": result}
    except Exception as exc:
        logger.exception("call_compliance failed: %s", exc)
        return {"compliance_result": f"[Compliance analysis unavailable: {exc}]"}


async def aggregate(state: LawState) -> dict:
    llm = get_llm(tools=True)
    sections: list[str] = []
    if state.get("law_analysis"):
        sections.append(f"## Legal Analysis\n{state['law_analysis']}")
    if state.get("tax_result"):
        sections.append(f"## Tax Analysis\n{state['tax_result']}")
    if state.get("compliance_result"):
        sections.append(f"## Regulatory Compliance Analysis\n{state['compliance_result']}")

    combined = "\n\n---\n\n".join(sections)
    messages = [
        SystemMessage(
            content=(
                "You are a senior legal counsel synthesising specialist analyses into a "
                "comprehensive, well-structured response for the client. Combine the following "
                "analyses into a cohesive answer with clear sections. Avoid redundancy. "
                "End with a brief disclaimer that the analysis is educational and the client "
                "should consult licensed attorneys for their specific situation."
            )
        ),
        HumanMessage(content=combined),
    ]
    result = await llm.ainvoke(messages)
    return {"final_answer": result.content}


def create_graph():
    """Build and compile the OPTIMIZED Law Agent StateGraph.

    Key difference from original graph.py:
    - 1 node 'analyze_and_route' replaces 2 nodes 'analyze_law' + 'check_routing'
    - Saves 1 sequential LLM call per request
    """
    graph = StateGraph(LawState)

    graph.add_node("analyze_and_route", analyze_and_route)
    graph.add_node("call_tax", call_tax)
    graph.add_node("call_compliance", call_compliance)
    graph.add_node("aggregate", aggregate)

    graph.set_entry_point("analyze_and_route")
    graph.add_conditional_edges(
        "analyze_and_route",
        route_to_subagents,
        ["call_tax", "call_compliance", "aggregate"],
    )
    graph.add_edge("call_tax", "aggregate")
    graph.add_edge("call_compliance", "aggregate")
    graph.add_edge("aggregate", END)

    return graph.compile()
