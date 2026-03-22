"""Follow-up answer node for answering questions from existing analysis context."""

from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from my_agent.core.config import ModelConfig
from my_agent.core.llm import get_llm
from my_agent.models.state import ExcelAnalysisState
from my_agent.prompts.prompts import FOLLOWUP_ANSWER_SYS_PROMPT, FOLLOWUP_ANSWER_USER_PROMPT


async def followup_answer_node(state: ExcelAnalysisState) -> Dict[str, Any]:
    """Follow-up Answer Node - Answers questions from existing analysis context."""
    print("💡 Follow-up Answer: Answering from existing context...")

    llm = await get_llm(ModelConfig.FOLLOWUP_MODEL, temperature=0)

    user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    user_query = user_messages[-1].content if user_messages else "Please provide more details"

    history_messages = state["messages"][:-1]
    recent_messages = history_messages[-8:] if len(history_messages) > 8 else history_messages
    
    conversation_summary = "\n".join(
        [
            f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {str(msg.content)[:150]}..."
            for msg in recent_messages
        ]
    ) if recent_messages else "No prior conversation."

    data_context_dict = state.get("data_context")
    data_context = ""
    if isinstance(data_context_dict, dict):
        data_context = data_context_dict.get("description", "No data description available")
    elif isinstance(data_context_dict, str):
        data_context = data_context_dict

    previous_analysis = state.get("final_analysis", "No previous analysis available")

    system_prompt = SystemMessage(content=FOLLOWUP_ANSWER_SYS_PROMPT)
    user_prompt = HumanMessage(
        content=FOLLOWUP_ANSWER_USER_PROMPT.format(
            user_query=user_query,
            conversation_summary=conversation_summary,
            data_context=data_context,
            previous_analysis=previous_analysis
        )
    )

    response = await llm.ainvoke([system_prompt, user_prompt])
    print(f"✅ Follow-up Answer: Response generated")

    return {
        "messages": [AIMessage(content=str(response.content), name="FollowupAssistant")]
    }
 village_followup_answer_node = followup_answer_node
 village_followup_answer_node = followup_answer_node
