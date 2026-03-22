"""Coding Agent Subgraph - Handles code execution and iteration."""

from langgraph.graph import END, StateGraph

from my_agent.models.state import (
    CodingSubgraphInput,
    CodingSubgraphOutput,
    CodingSubgraphState,
)
from my_agent.nodes.coding_agent import (
    coding_agent_node,
    finalize_analysis_node,
    should_continue_coding,
    tool_execution_node,
)


def create_coding_subgraph():
    """Create the Coding Agent subgraph with properly isolated state."""
    workflow = StateGraph(CodingSubgraphState, input=CodingSubgraphInput, output=CodingSubgraphOutput)

    workflow.add_node("coding_agent", coding_agent_node)
    workflow.add_node("execute_tools", tool_execution_node)
    workflow.add_node("finalize", finalize_analysis_node)

    workflow.set_entry_point("coding_agent")

    workflow.add_conditional_edges(
        "coding_agent",
        should_continue_coding,
        {
            "execute_tools": "execute_tools",
            "finalize": "finalize",
            "continue": "coding_agent",
        },
    )

    workflow.add_edge("execute_tools", "coding_agent")
    workflow.add_edge("finalize", END)

    return workflow.compile()
