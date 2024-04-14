from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.pydantic_v1 import BaseModel as LangchainBaseModel
from pydantic import BaseModel


class AgentInput(LangchainBaseModel):
    input: str


class AgentOutput(LangchainBaseModel):
    output: str


class GraphInput(LangchainBaseModel):
    messages: List[HumanMessage]


class Messages(LangchainBaseModel):
    messages: List[BaseMessage]


class GraphOutput(LangchainBaseModel):
    __root__: Dict[str, Messages]


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


class SubscriptionRequest(BaseModel):
    code: str
    state: str


class UploadFileResponse(BaseModel):
    file_path: Optional[str]
    session_id: Optional[str]
    status: str
