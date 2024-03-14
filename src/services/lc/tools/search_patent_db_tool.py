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

from src.config.config import (
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL_V3,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE_PATENT,
)


class InputSchema(BaseModel):
    query: str
    top_k: Optional[int] = 16


class SearchPatentDb(BaseTool):
    name = "search_patent_db_tool"
    description = "Semantic search in patents vector database."

    args_schema: Type[BaseModel] = InputSchema

    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    pc = Pinecone(api_key=PINECONE_API_KEY)
    idx = pc.Index(PINECONE_INDEX_NAME)

    def _run(
        self,
        query: str,
        top_k: Optional[int] = 16,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool synchronously."""
        response = self.openai_client.embeddings.create(
            input=query, model=OPENAI_EMBEDDING_MODEL_V3
        )
        query_vector = response.data[0].embedding

        docs = self.idx.query(
            namespace=PINECONE_NAMESPACE_PATENT,
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
        )

        docs_list = []
        for doc in docs["matches"]:

            date = datetime.datetime.fromtimestamp(doc.metadata["publication_date"])
            formatted_date = date.strftime("%Y-%m")
            country = doc.metadata["country"]
            url = doc.metadata["country"]
            title = doc.metadata["title"]
            id = doc["id"]

            source_entry = "[{}. {}. {}. {}.]({})".format(
                id,
                title,
                country,
                formatted_date,
                url,
            )
            docs_list.append(
                {"content": doc.metadata["abstract"], "source": source_entry}
            )

        return docs_list

    async def _arun(
        self,
        query: str,
        top_k: Optional[int] = 16,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        response = self.openai_client.embeddings.create(
            input=query, model=OPENAI_EMBEDDING_MODEL_V3
        )
        query_vector = response.data[0].embedding

        docs = self.idx.query(
            namespace=PINECONE_NAMESPACE_PATENT,
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
        )

        docs_list = []
        for doc in docs["matches"]:

            date = datetime.datetime.fromtimestamp(doc.metadata["publication_date"])
            formatted_date = date.strftime("%Y-%m")
            country = doc.metadata["country"]
            url = doc.metadata["country"]
            title = doc.metadata["title"]
            id = doc["id"]

            source_entry = "[{}. {}. {}. {}.]({})".format(
                id,
                title,
                country,
                formatted_date,
                url,
            )
            docs_list.append(
                {"content": doc.metadata["abstract"], "source": source_entry}
            )

        return docs_list
