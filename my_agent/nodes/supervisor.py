"""Supervisor node — evaluates whether a new analysis run is needed."""

import logging
from typing import Any, cast, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from my_agent.core.config import ModelConfig
from my_agent.core.llm import get_llm
from my_agent.models.schemas import SupervisorOutput
from my_agent.models.state import ExcelAnalysisState
from my_agent.prompts.prompts import SUPERVISOR_SYS_PROMPT, SUPERVISOR_USER_PROMPT

logger = logging.getLogger(__name__)


def _fallback_decision(reason: str) -> Dict[str, Any]:
    return {
        "supervisor_decision": {
            "needs_analysis": True,
            "reuse_previous_results": False,
            "reasoning": reason,
        }
    }


async def supervisor_node(state: ExcelAnalysisState) -> Dict[str, Any]:
    logger.info("🎯 Supervisor: Evaluating if new analysis is needed...")
    try:
        router_output = state.get("route_decision")
        if not router_output: raise ValueError("No router output")

        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        user_query = user_messages[-1].content if user_messages else "Analyze"

        data_context = state.get("data_context") or {}
        dataset_summary = data_context.get("summary", {})

        llm = await get_llm(ModelConfig.SUPERVISOR_MODEL, temperature=0)
        llm_structured = llm.with_structured_output(SupervisorOutput)
        
        response = await llm_structured.ainvoke([
            SystemMessage(content=SUPERVISOR_SYS_PROMPT),
            HumanMessage(content=SUPERVISOR_USER_PROMPT.format(
                user_query=user_query,
                router_output=router_output,
                previous_metadata={},
                dataset_summary=dataset_summary
            ))
        ])

        return {"supervisor_decision": response.model_dump() if hasattr(response, 'model_dump') else response}
    except Exception as exc:
        return _fallback_decision(f"Supervisor error: {exc}")


