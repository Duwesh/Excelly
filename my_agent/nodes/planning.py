"""Planning node for creating detailed analysis plans."""

import json
from typing import Any, Dict, List, cast

from langchain_core.messages import HumanMessage, SystemMessage

from my_agent.core.config import ModelConfig
from my_agent.core.llm import get_llm
from my_agent.models.schemas import PlanOutput
from my_agent.models.state import ExcelAnalysisState
from my_agent.prompts.prompts import PLANNING_SYS_PROMPT, PLANNING_USER_PROMPT


async def planning_node(state: ExcelAnalysisState) -> Dict[str, Any]:
    print("📋 Planning: Creating analysis plan...")
    try:
        user_query = state.get("user_query", "Analyze the data")
        data_context = state.get("data_context")
        if not data_context: raise Exception("No data context")

        dataset_profile = data_context.get("dataset_profile", {})
        summary = data_context.get("summary", {})
        route_decision = state.get("route_decision", {})

        llm = await get_llm(ModelConfig.PLANNING_MODEL, temperature=0)
        llm_with_structure = llm.with_structured_output(PlanOutput)
        
        response = await llm_with_structure.ainvoke([
            SystemMessage(content=PLANNING_SYS_PROMPT),
            HumanMessage(content=PLANNING_USER_PROMPT.format(
                user_query=user_query,
                data_context=json.dumps({
                    "analysis_type": route_decision.get("analysis_type"),
                    "dataset_profile": dataset_profile,
                    "summary": summary
                })
            ))
        ])

        structured_steps = [
            {"description": s.description, "status": "pending", "order": s.order, "result_summary": ""}
            for s in response.steps
        ]
        
        return {"analysis_plan": response.plan_text, "analysis_steps": structured_steps[:5]}
    except Exception as e:
        return {"analysis_plan": "1. Load data\n2. Analyze\n3. Summarize", "analysis_steps": []}
village_planning_node = planning_node

