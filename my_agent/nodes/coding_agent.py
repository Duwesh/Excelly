"""Coding Agent node for executing Python code to analyze Excel data."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from my_agent.core.config import AgentConfig, ModelConfig
from my_agent.core.execution_var import get_current_session_id
from my_agent.core.llm import get_llm
from my_agent.helpers.sandbox import get_session_plots_dir
from my_agent.models.state import CodingSubgraphState
from my_agent.prompts.prompts import CODING_AGENT_SYS_PROMPT, CODING_AGENT_USER_PROMPT
from my_agent.tools.tools import bash_tool, python_repl_tool, think_tool


async def coding_agent_node(state: CodingSubgraphState) -> Dict[str, Any]:
    code_iterations = state.get("code_iterations", 0)
    print(f"💻 Coding Agent: Iteration {code_iterations + 1}...")

    llm = await get_llm(ModelConfig.CODING_MODEL, temperature=0)
    llm_with_tools = llm.bind_tools([python_repl_tool, bash_tool, think_tool])

    session_id = get_current_session_id()
    session_plots_dir = get_session_plots_dir(session_id)

    if code_iterations == 0:
        user_query = state.get("user_query", "Analyze")
        data_ctx = state.get("data_context", {})
        desc = data_ctx.get("description", "") if isinstance(data_ctx, dict) else data_ctx
        
        prompt = CODING_AGENT_USER_PROMPT.format(
            analysis_plan=state.get("analysis_plan", ""),
            data_context=desc,
            excel_file_path=state.get("excel_file_path", ""),
            plots_dir=str(session_plots_dir),
            plots_url=f"/plots/{session_id}",
            total_rows=data_ctx.get("total_rows", 0) if isinstance(data_ctx, dict) else 0,
            large_file_hints="None"
        )
        messages = [SystemMessage(content=CODING_AGENT_SYS_PROMPT), HumanMessage(content=prompt)]
    else:
        messages = [SystemMessage(content=CODING_AGENT_SYS_PROMPT)] + state["messages"]

    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response], "code_iterations": code_iterations + 1}


async def tool_execution_node(state: CodingSubgraphState) -> Dict[str, Any]:
    last_msg = state["messages"][-1]
    if not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
        return {"messages": []}

    tool_messages = []
    for tc in last_msg.tool_calls:
        t_name = tc["name"]
        print(f"🔧 Executing: {t_name}")
        if t_name == "python_repl_tool": res = await python_repl_tool.ainvoke(tc["args"])
        elif t_name == "bash_tool": res = await bash_tool.ainvoke(tc["args"])
        else: res = await think_tool.ainvoke(tc["args"])
        
        tool_messages.append(ToolMessage(content=json.dumps(res, default=str), tool_call_id=tc["id"], name=t_name))
    return {"messages": tool_messages}


def should_continue_coding(state: CodingSubgraphState) -> str:
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls: return "execute_tools"
    if state.get("code_iterations", 0) >= AgentConfig.CODING_MAX_ITERATIONS: return "finalize"
    return "finalize"


async def finalize_analysis_node(state: CodingSubgraphState) -> Dict[str, Any]:
    print("📝 Finalizing analysis...")
    ai_msgs = [m for m in state["messages"] if isinstance(m, AIMessage)]
    content = ai_msgs[-1].content if ai_msgs else "Analysis complete."
    return {"final_analysis": content, "messages": [AIMessage(content=str(content), name="CodingAgent")]}

