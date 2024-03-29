from typing import List, Optional

from pydantic import BaseModel


class PlainSearchRequest(BaseModel):
    query: str


class VectorSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 16


class SearchResultWithSource(BaseModel):
    content: str
    source: str


class SearchResponse(BaseModel):
    result: List[SearchResultWithSource]


class AgentInput(BaseModel):
    input: str


class AgentOutput(BaseModel):
    output: str


class SubscriptionRequest(BaseModel):
    code: str
    state: str
