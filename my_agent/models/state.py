from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState, add_messages


def add_artifacts(left: List["Artifact"], right: List["Artifact"]) -> List["Artifact"]:
    """
    Reducer function to accumulate artifacts without duplicates.
    """
    if not left:
        return right
    if not right:
        return left

    latest_versions = {}
    for a in left + right:
        if a.get("content"):
            latest_versions[a.get("content")] = a

    result = []
    seen = set()
    for a in left + right:
        content = a.get("content")
        if content and content not in seen:
            result.append(latest_versions[content])
            seen.add(content)
    
    return result


def update_analysis_steps(left: List["AnalysisStep"], right: List["AnalysisStep"]) -> List["AnalysisStep"]:
    """
    Reducer function to update analysis steps.
    """
    if not left:
        return right
    if not right:
        return left

    steps_dict = {step.get("order"): step for step in left}

    for step in right:
        order = step.get("order")
        if order is not None:
            steps_dict[order] = step

    return sorted(steps_dict.values(), key=lambda x: x.get("order", 0))


class RouterDecision(TypedDict, total=False):
    route: str  # "chat", "analysis", "analysis_followup"
    reasoning: str
    analysis_type: Optional[str]
    entity_type: Optional[str]
    requires_chart: Optional[bool]
    requires_simulation: Optional[bool]
    confidence: Optional[float]


class SupervisorDecision(TypedDict, total=False):
    needs_analysis: bool
    reuse_previous_results: bool
    scope_changed: bool
    entity_mismatch: bool
    data_sufficient: bool
    reasoning: str


class Artifact(TypedDict, total=False):
    type: str
    content: str
    description: str
    timestamp: str


class AnalysisStep(TypedDict, total=False):
    description: str
    status: str
    order: int
    result_summary: str


class ExcelAnalysisState(MessagesState):
    excel_file_path: Optional[str]
    data_context: Optional[Dict[str, Any]]
    route_decision: Optional[RouterDecision]
    supervisor_decision: Optional[SupervisorDecision]
    analysis_plan: Optional[str]
    user_query: Optional[str]
    code_iterations: int
    execution_result: Optional[str]
    final_analysis: Optional[str]
    artifacts: Annotated[List[Artifact], add_artifacts]
    analysis_steps: Annotated[List[AnalysisStep], update_analysis_steps]


class CodingSubgraphInput(TypedDict, total=False):
    excel_file_path: str
    data_context: Dict[str, Any]
    analysis_plan: str
    user_query: str
    analysis_steps: List[AnalysisStep]


class CodingSubgraphOutput(TypedDict, total=False):
    messages: List
    artifacts: List[Artifact]
    analysis_steps: List[AnalysisStep]
    final_analysis: str


class CodingSubgraphState(TypedDict, total=False):
    messages: Annotated[List[BaseMessage], add_messages]
    excel_file_path: str
    data_context: Dict[str, Any]
    analysis_plan: str
    user_query: str
    code_iterations: int
    final_analysis: str
    artifacts: Annotated[List[Artifact], add_artifacts]
    analysis_steps: Annotated[List[AnalysisStep], update_analysis_steps]
