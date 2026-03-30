from typing import List
from pydantic import BaseModel, Field


class ResearchPlan(BaseModel):
    problem_statement: str
    subquestions: List[str]
    search_queries: List[str]
    success_criteria: List[str]


class Finding(BaseModel):
    claim: str
    evidence: str
    source_idx: int = Field(..., description="0-based source index")
    importance: float = Field(..., ge=0.0, le=1.0)


class FindingBatch(BaseModel):
    findings: List[Finding]


class CritiqueResult(BaseModel):
    sufficient: bool
    missing_points: List[str]
    weak_spots: List[str]
    extra_queries: List[str]


class LLMGrade(BaseModel):
    completeness: int = Field(ge=1, le=5)
    citation_quality: int = Field(ge=1, le=5)
    clarity: int = Field(ge=1, le=5)
    practical_value: int = Field(ge=1, le=5)
    feedback: str