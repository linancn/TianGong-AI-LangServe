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
    PINECONE_NAMESPACE_ESG,
    XATA_API_KEY,
    XATA_ESG_DB_URL,
)
from src.models.models import VectorSearchRequestWithIds


class SearchESG(BaseTool):
    name = "search_ESG_tool"
    description = "Full text search and semantic search in ESG reports. Query MUST be in Simplified Chinese."
    args_schema: Type[BaseModel] = VectorSearchRequestWithIds

    def _run(
        self,
        query: str,
        top_k: Optional[int] = 8,
        doc_ids: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool synchronously."""

        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        pc = Pinecone(api_key=PINECONE_API_KEY)
        idx = pc.Index(PINECONE_INDEX_NAME)

        xata = XataClient(api_key=XATA_API_KEY, db_url=XATA_ESG_DB_URL)

        response = openai_client.embeddings.create(
            input=query, model=OPENAI_EMBEDDING_MODEL_V3
        )
        query_vector = response.data[0].embedding

        filter = None
        if doc_ids:
            filter = {"rec_id": {"$in": doc_ids}}

        docs = idx.query(
            namespace=PINECONE_NAMESPACE_ESG,
            vector=query_vector,
            filter=filter,
            top_k=top_k,
            include_metadata=True,
        )

        xata_fulltext_response = xata.data().search_table(
            "ESG_Fulltext",
            {
                "query": query,
                "target": ["text"],
                "page": {"size": top_k},
                "filter": {"reportId": {"$any": doc_ids}},
            },
        )

        records = xata_fulltext_response.get("records", [])

        text_set = set()
        unique_docs = []

        # Process docs
        for doc in docs["matches"]:
            text = doc["metadata"]["text"]
            if text not in text_set:
                text_set.add(text)
                unique_docs.append(
                    {
                        "id": doc["metadata"]["rec_id"],
                        "page_number": doc["metadata"]["page_number"],
                        "text": text,
                    }
                )

        # Process records
        for record in records:
            text = record["text"]
            if text not in text_set:
                text_set.add(text)
                unique_docs.append(
                    {
                        "id": record["reportId"],
                        "page_number": record["pageNumber"],
                        "text": text,
                    }
                )

        id_set = set()
        for doc in unique_docs:
            id_set.add(doc["id"])

        xata_meta_response = xata.data().query(
            "ESG",
            {
                "columns": ["company_name", "report_title", "publication_date"],
                "filter": {
                    "id": {"$any": list(id_set)},
                },
            },
        )

        meta_records = xata_meta_response.get("records", [])
        records_dict = {record["id"]: record for record in meta_records}

        docs_list = []
        for doc in unique_docs:
            id = doc["id"]
            record = records_dict.get(id, {})

            if record:
                date = datetime.datetime.strptime(
                    record.get("publication_date"), "%Y-%m-%dT%H:%M:%SZ"
                )
                formatted_date = date.strftime("%Y-%m-%d")
                company_name = record.get("company_name", "")
                report_title = record.get("report_title", "")

                source_entry = "{}. {}. {}. (P{})".format(
                    company_name,
                    report_title,
                    formatted_date,
                    int(doc["page_number"]),
                )
                docs_list.append({"content": doc["text"], "source": source_entry})

        return str(docs_list)

    async def _arun(
        self,
        query: str,
        top_k: Optional[int] = 8,
        doc_ids: Optional[list[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""

        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        pc = Pinecone(api_key=PINECONE_API_KEY)
        idx = pc.Index(PINECONE_INDEX_NAME)

        xata = XataClient(api_key=XATA_API_KEY, db_url=XATA_ESG_DB_URL)

        response = openai_client.embeddings.create(
            input=query, model=OPENAI_EMBEDDING_MODEL_V3
        )
        query_vector = response.data[0].embedding

        filter = None
        if doc_ids:
            filter = {"rec_id": {"$in": doc_ids}}

        docs = idx.query(
            namespace=PINECONE_NAMESPACE_ESG,
            vector=query_vector,
            filter=filter,
            top_k=top_k,
            include_metadata=True,
        )

        xata_fulltext_response = xata.data().search_table(
            "ESG_Fulltext",
            {
                "query": query,
                "target": ["text"],
                "page": {"size": top_k},
                "filter": {"reportId": {"$any": doc_ids}},
            },
        )

        records = xata_fulltext_response.get("records", [])

        text_set = set()
        unique_docs = []

        # Process docs
        for doc in docs["matches"]:
            text = doc["metadata"]["text"]
            if text not in text_set:
                text_set.add(text)
                unique_docs.append(
                    {
                        "id": doc["metadata"]["rec_id"],
                        "page_number": doc["metadata"]["page_number"],
                        "text": text,
                    }
                )

        # Process records
        for record in records:
            text = record["text"]
            if text not in text_set:
                text_set.add(text)
                unique_docs.append(
                    {
                        "id": record["reportId"],
                        "page_number": record["pageNumber"],
                        "text": text,
                    }
                )

        id_set = set()
        for doc in unique_docs:
            id_set.add(doc["id"])

        xata_meta_response = xata.data().query(
            "ESG",
            {
                "columns": ["company_name", "report_title", "publication_date"],
                "filter": {
                    "id": {"$any": list(id_set)},
                },
            },
        )

        meta_records = xata_meta_response.get("records", [])
        records_dict = {record["id"]: record for record in meta_records}

        docs_list = []
        for doc in unique_docs:
            id = doc["id"]
            record = records_dict.get(id, {})

            if record:
                date = datetime.datetime.strptime(
                    record.get("publication_date"), "%Y-%m-%dT%H:%M:%SZ"
                )
                formatted_date = date.strftime("%Y-%m-%d")
                company_name = record.get("company_name", "")
                report_title = record.get("report_title", "")

                source_entry = "{}. {}. {}. (P{})".format(
                    company_name,
                    report_title,
                    formatted_date,
                    int(doc["page_number"]),
                )
                docs_list.append({"content": doc["text"], "source": source_entry})

        return str(docs_list)
