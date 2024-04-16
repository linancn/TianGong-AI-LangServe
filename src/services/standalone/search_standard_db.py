from datetime import datetime

from openai import OpenAI
from pinecone import Pinecone
from xata.client import XataClient

from src.config.config import (
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL_V3,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE_STANDARD,
    XATA_API_KEY,
    XATA_DOCS_DB_URL,
)


async def search(query: str, top_k: int = 16) -> str:
    """Semantic search in standard vector database."""

    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    pc = Pinecone(api_key=PINECONE_API_KEY)
    idx = pc.Index(PINECONE_INDEX_NAME)

    xata = XataClient(api_key=XATA_API_KEY, db_url=XATA_DOCS_DB_URL)

    response = openai_client.embeddings.create(
        input=query, model=OPENAI_EMBEDDING_MODEL_V3
    )
    query_vector = response.data[0].embedding

    docs = idx.query(
        namespace=PINECONE_NAMESPACE_STANDARD,
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
    )

    id_set = set()
    for matche in docs["matches"]:
        id = matche["id"].rpartition("_")[0]
        id_set.add(id)

    xata_response = xata.data().query(
        "standards",
        {
            "columns": [
                "standard_number",
                "standard_title",
                "issuing_organization",
                "release_date",
                "url",
            ],
            "filter": {
                "id": {"$any": list(id_set)},
            },
        },
    )

    records = xata_response.get("records", [])
    records_dict = {record["id"]: record for record in records}

    docs_list = []
    for doc in docs["matches"]:
        id = doc["id"].rpartition("_")[0]
        record = records_dict.get(id, {})

        if record:
            date = datetime.strptime(record["release_date"], "%Y-%m-%dT%H:%M:%SZ")
            formatted_date = date.strftime("%Y-%m-%d")
            organizations = ", ".join(record["issuing_organization"])

            source_entry = "[{}. {}. {}. {}.]({})".format(
                record["standard_number"],
                record["standard_title"],
                organizations,
                formatted_date,
                record["url"],
            )
            docs_list.append({"content": doc.metadata["text"], "source": source_entry})

    return docs_list
