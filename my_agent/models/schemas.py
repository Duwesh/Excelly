from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RouterOutput(BaseModel):
    route: str = Field(description="Classification: 'chat', 'analysis', or 'analysis_followup'")
    reasoning: str = Field(description="Explanation for this classification")
    analysis_type: Optional[str] = Field(default=None)
    entity_type: Optional[str] = Field(default=None)
    requires_chart: Optional[bool] = Field(default=None)
    requires_simulation: Optional[bool] = Field(default=None)
    confidence: float = Field(default=1.0)


class SupervisorOutput(BaseModel):
    needs_analysis: bool = Field(description="True if new code execution needed")
    reuse_previous_results: bool = Field(description="True if query can reuse results")
    scope_changed: bool = Field(description="True if scope has changed")
    entity_mismatch: bool = Field(description="True if entity not found")
    data_sufficient: bool = Field(description="True if data contains columns")
    reasoning: str = Field(description="Explanation for decision")


class PlanStep(BaseModel):
    description: str = Field(description="What needs to be done")
    order: int = Field(description="Order of execution")


class PlanOutput(BaseModel):
    plan_text: str = Field(description="Human-readable plan")
    steps: List[PlanStep] = Field(description="List of structured steps", max_length=5)
