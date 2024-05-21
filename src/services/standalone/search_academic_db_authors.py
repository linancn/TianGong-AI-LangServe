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
    PINECONE_NAMESPACE_SCI,
    XATA_API_KEY,
    XATA_DOCS_DB_URL,
)


async def search(
    query_list: list[str],
    top_k: Optional[int] = 16,
) -> list:
    """Semantic search authors in academic vector database."""

    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    pc = Pinecone(api_key=PINECONE_API_KEY)
    idx = pc.Index(PINECONE_INDEX_NAME)

    xata = XataClient(api_key=XATA_API_KEY, db_url=XATA_DOCS_DB_URL)

    response = openai_client.embeddings.create(
        input=query_list, model=OPENAI_EMBEDDING_MODEL_V3
    )
    query_vector_list = [item.embedding for item in response.data]

    doi_set = set()

    for query_vector in query_vector_list:
        docs = idx.query(
            namespace=PINECONE_NAMESPACE_SCI,
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
        )

        for matche in docs["matches"]:
            doi = matche["id"].rpartition("_")[0]
            doi_set.add(doi)

    xata_response = xata.data().query(
        "journals",
        {
            "columns": ["doi", "authors"],
            "filter": {
                "doi": {"$any": list(doi_set)},
            },
        },
    )

    records = xata_response.get("records", [])

    authors_set = set()
    for record in records:
        authors_set.update(record["authors"])

    authors_list = list(authors_set)
    authors_list.sort()

    return authors_list
