import datetime
from typing import Optional

from openai import OpenAI
from pinecone import Pinecone
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


async def search(
    query: str,
    top_k: Optional[int] = 16,
    doc_ids: Optional[list[str]] = None,
) -> list:
    """Search for the ESG information."""

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

    id_set = set()
    for doc in docs["matches"]:
        id = doc["metadata"]["rec_id"]
        id_set.add(id)

    xata_response = xata.data().query(
        "ESG",
        {
            "columns": ["company_short_name", "report_title", "publication_date"],
            "filter": {
                "id": {"$any": list(id_set)},
            },
        },
    )

    records = xata_response.get("records", [])
    records_dict = {record["id"]: record for record in records}

    docs_list = []
    for doc in docs["matches"]:
        id = doc.metadata["rec_id"]
        record = records_dict.get(id, {})

        if record:
            date = datetime.datetime.strptime(
                record.get("publication_date"), "%Y-%m-%dT%H:%M:%SZ"
            )
            formatted_date = date.strftime("%Y-%m-%d")
            company_short_name = record.get("company_short_name", "")
            report_title = record.get("report_title", "")

            source_entry = "{}. {}. {}.".format(
                company_short_name,
                report_title,
                formatted_date,
            )
            docs_list.append({"content": doc.metadata["text"], "source": source_entry})

    return docs_list
