from typing import List, Optional

from pydantic import BaseModel


class PlainSearchRequest(BaseModel):
    query: str


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 8
    ext_k: Optional[int] = 0


class VectorListSearchRequest(BaseModel):
    query_list: List[str]
    top_k: Optional[int] = 16


class SearchResultWithSource(BaseModel):
    content: str
    source: str


class SearchResponse(BaseModel):
    result: List[SearchResultWithSource]


class SearchAuthorsResult(BaseModel):
    authors: List[str]


class SubscriptionRequest(BaseModel):
    code: str
    state: str


class UploadFileResponse(BaseModel):
    file_path: Optional[str]
    session_id: Optional[str]
    status: str
