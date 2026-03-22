"""Chat node for handling generic non-analysis queries."""

from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from my_agent.core.config import ModelConfig
from my_agent.core.llm import get_llm
from my_agent.models.state import ExcelAnalysisState
from my_agent.prompts.prompts import CHAT_SYS_PROMPT, CHAT_USER_PROMPT


async def chat_node(state: ExcelAnalysisState) -> Dict[str, Any]:
    """Chat Node - Handles generic conversational queries."""
    print("💬 Chat: Handling general query...")

    llm = await get_llm(ModelConfig.CHAT_MODEL, temperature=0.7)

    user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
    user_query = user_messages[-1].content if user_messages else "Hello"

    history_messages = state["messages"][:-1]
    recent_messages = history_messages[-8:] if len(history_messages) > 8 else history_messages
    
    conversation_summary = "\n".join(
        [
            f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {str(msg.content)[:150]}..."
            for msg in recent_messages
        ]
    ) if recent_messages else "No prior conversation."

    system_prompt = SystemMessage(content=CHAT_SYS_PROMPT)
    user_prompt = HumanMessage(
        content=CHAT_USER_PROMPT.format(
            user_query=user_query,
            conversation_summary=conversation_summary
        )
    )

    response = await llm.ainvoke([system_prompt, user_prompt])
    print(f"✅ Chat: Response generated")

    return {
        "messages": [AIMessage(content=str(response.content), name="ChatAssistant")]
    }
