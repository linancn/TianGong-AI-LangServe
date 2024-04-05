from typing import Optional, Type

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.prompts import ChatPromptTemplate
from langchain.tools import BaseTool
from openai import OpenAI
from xata.client import XataClient
from pinecone import Pinecone
from pydantic import BaseModel

from src.config.config import (
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL_V3,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE_ESG,
)
from src.models.models import VectorSearchRequest


class SearchESG(BaseTool):
    name = "search_ESG_tool"
    description = "Search for the ESG information."
    args_schema: Type[BaseModel] = VectorSearchRequest

    def _run(
        self, 
        query: str, 
        top_k: Optional[int] = 16,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool synchronously."""

        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        pc = Pinecone(api_key=PINECONE_API_KEY)
        idx = pc.Index(PINECONE_INDEX_NAME)

        response = openai_client.embeddings.create(input=query, model=OPENAI_EMBEDDING_MODEL_V3)
        query_vector = response.data[0].embedding
        
        response = idx.query(
            namespace=PINECONE_NAMESPACE_ESG,
            vector=query_vector,
            filter={
                "rec_id": {"$eq": "rec_cml2mt6s5o8n71hqlle0"}
            },
            top_k=top_k,
            include_metadata=True
        )

        result_list = [item["metadata"]["text"] for item in response["matches"]]

        return result_list
    async def _arun(
        self,
        query: str,
        top_k: Optional[int] = 16,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""

        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        pc = Pinecone(api_key=PINECONE_API_KEY)
        idx = pc.Index(PINECONE_INDEX_NAME)

        response = openai_client.embeddings.create(input=query, model=OPENAI_EMBEDDING_MODEL_V3)
        query_vector = response.data[0].embedding
        
        response = idx.query(
            namespace=PINECONE_NAMESPACE_ESG,
            vector=query_vector,
            filter={
                "rec_id": {"$eq": "rec_cml2mt6s5o8n71hqlle0"}
            },
            top_k=top_k,
            include_metadata=True
        )

        result_list = [item["metadata"]["text"] for item in response["matches"]]

        return result_list        