import datetime
from typing import Optional, Type

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools import BaseTool
from openai import OpenAI
from pinecone import Pinecone
from pydantic import BaseModel
from xata.client import XataClient

from src.config.config import (
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL_V3,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE_ALI,
    XATA_ALI_DB_URL,
    XATA_API_KEY,
)
from src.models.models import VectorSearchRequestWithIds


class SearchALI(BaseTool):
    name = "search_ali_tool"
    description = "Search for the ali information."
    args_schema: Type[BaseModel] = VectorSearchRequestWithIds

    def _run(
        self,
        query: str,
        top_k: Optional[int] = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool synchronously."""

        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        pc = Pinecone(api_key=PINECONE_API_KEY)
        idx = pc.Index(PINECONE_INDEX_NAME)

        xata = XataClient(api_key=XATA_API_KEY, db_url=XATA_ALI_DB_URL)

        response = openai_client.embeddings.create(
            input=query, model=OPENAI_EMBEDDING_MODEL_V3
        )
        query_vector = response.data[0].embedding

        docs = idx.query(
            namespace=PINECONE_NAMESPACE_ALI,
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
        )

        xata_response = xata.data().search_table(
            "fulltext",
            {
                "query": query,
                "target": ["text"],
            },
        )

        records = xata_response.get("records", [])
        records_dict = {record["text"]: record for record in records}

        docs_list = []
        for doc in docs["matches"]:
            text = doc.metadata["text"]
            if text not in records_dict:
                docs_list.append({"content": text, "source": doc.metadata["title"]})

        docs_dict = {doc["content"]: doc for doc in docs_list}
        for record in records:
            if record["text"] not in docs_dict:
                docs_list.append({"content": record["text"], "source": record["title"]})

        return str(docs_list)

    async def _arun(
        self,
        query: str,
        top_k: Optional[int] = 5,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""

        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        pc = Pinecone(api_key=PINECONE_API_KEY)
        idx = pc.Index(PINECONE_INDEX_NAME)

        xata = XataClient(api_key=XATA_API_KEY, db_url=XATA_ALI_DB_URL)

        response = openai_client.embeddings.create(
            input=query, model=OPENAI_EMBEDDING_MODEL_V3
        )
        query_vector = response.data[0].embedding

        docs = idx.query(
            namespace=PINECONE_NAMESPACE_ALI,
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
        )

        xata_response = xata.data().search_table(
            "fulltext",
            {
                "query": query,
                "target": ["text"],
            },
        )

        records = xata_response.get("records", [])
        records_dict = {record["text"]: record for record in records}

        docs_list = []
        for doc in docs["matches"]:
            text = doc.metadata["text"]
            if text not in records_dict:
                docs_list.append({"content": text, "source": doc.metadata["title"]})

        docs_dict = {doc["content"]: doc for doc in docs_list}
        for record in records:
            if record["text"] not in docs_dict:
                docs_list.append({"content": record["text"], "source": record["title"]})

        return str(docs_list)
