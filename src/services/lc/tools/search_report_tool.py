from typing import Optional, Type

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools import BaseTool
from openai import OpenAI
from pinecone import Pinecone
from pydantic import BaseModel

from src.config.config import (
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL_V3,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE_REPORT,
)
from src.models.models import VectorSearchRequestWithIds


class SearchReport(BaseTool):
    name = "search_report_tool"
    description = "Search for the Report information."
    args_schema: Type[BaseModel] = VectorSearchRequestWithIds

    def _run(
        self,
        query: str,
        top_k: Optional[int] = 16,
        doc_ids: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool synchronously."""

        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        pc = Pinecone(api_key=PINECONE_API_KEY)
        idx = pc.Index(PINECONE_INDEX_NAME)

        response = openai_client.embeddings.create(
            input=query, model=OPENAI_EMBEDDING_MODEL_V3
        )
        query_vector = response.data[0].embedding

        filter = None
        if doc_ids:
            filter = {"rec_id": {"$in": doc_ids}}

        response = idx.query(
            namespace=PINECONE_NAMESPACE_REPORT,
            vector=query_vector,
            filter=filter,
            top_k=top_k,
            include_metadata=True,
        )

        result_list = [item["metadata"]["text"] for item in response["matches"]]

        return str(result_list)

    async def _arun(
        self,
        query: str,
        top_k: Optional[int] = 16,
        doc_ids: Optional[list[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""

        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        pc = Pinecone(api_key=PINECONE_API_KEY)
        idx = pc.Index(PINECONE_INDEX_NAME)

        response = openai_client.embeddings.create(
            input=query, model=OPENAI_EMBEDDING_MODEL_V3
        )
        query_vector = response.data[0].embedding

        filter = None
        if doc_ids:
            filter = {"rec_id": {"$in": doc_ids}}

        response = idx.query(
            namespace=PINECONE_NAMESPACE_REPORT,
            vector=query_vector,
            filter=filter,
            top_k=top_k,
            include_metadata=True,
        )

        result_list = [item["metadata"]["text"] for item in response["matches"]]

        return str(result_list)
