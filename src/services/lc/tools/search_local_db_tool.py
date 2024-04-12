from typing import Optional, Type

import weaviate
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools import BaseTool
from pydantic import BaseModel
from weaviate.classes.query import Rerank

from src.config.config import WEAVIATE_COLLECTION_NAME, WEAVIATE_HOST, WEAVIATE_PORT
from src.models.models import VectorSearchRequest


class SearchLocalDb(BaseTool):
    name = "search_local_db_tool"
    description = "Semantic search in local vector database."
    args_schema: Type[BaseModel] = VectorSearchRequest

    def _run(
        self,
        query: str,
        top_k: Optional[int] = 16,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool synchronously."""

        client = weaviate.connect_to_local(host=WEAVIATE_HOST, port=WEAVIATE_PORT)

        tiangong = client.collections.get(WEAVIATE_COLLECTION_NAME)
        docs_list = tiangong.query.near_text(
            query=query,
            limit=top_k,
            target_vector="content",
            rerank=Rerank(prop="content", query=query),
        )

        client.close()

        return str(docs_list)

    async def _arun(
        self,
        query: str,
        top_k: Optional[int] = 16,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""

        client = weaviate.connect_to_local(host=WEAVIATE_HOST, port=WEAVIATE_PORT)

        tiangong = client.collections.get(WEAVIATE_COLLECTION_NAME)
        docs_list = tiangong.query.near_text(
            query=query,
            limit=top_k,
            target_vector="content",
            rerank=Rerank(prop="content", query=query),
        )

        client.close()

        return str(docs_list)
