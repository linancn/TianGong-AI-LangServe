from typing import List, Optional

from pydantic import BaseModel


class VectorSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 16


class SearchResultWithSource(BaseModel):
    content: str
    source: str


class SearchResponse(BaseModel):
    result: List[SearchResultWithSource]
