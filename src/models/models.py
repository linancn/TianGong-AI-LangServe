from typing import List, Optional

from pydantic import BaseModel, Field


class PlainSearchRequest(BaseModel):
    query: str


class VectorSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 16


class VectorSearchRequestWithIds(VectorSearchRequest):
    doc_ids: Optional[List[str]] = None


class SearchResultWithSource(BaseModel):
    content: str
    source: str


class SearchResponse(BaseModel):
    result: List[SearchResultWithSource]


class AgentInput(BaseModel):
    system_input: str
    human_input: str


class AgentOutput(BaseModel):
    output: str


class SubscriptionRequest(BaseModel):
    code: str
    state: str


class DataAnalysisRequest(BaseModel):
    file_name: Optional[str]
    file_description: Optional[str]
    file_content: str = Field(..., extra={"widget": {"type": "base64file"}})
