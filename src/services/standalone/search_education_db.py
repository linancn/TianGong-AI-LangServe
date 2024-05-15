from openai import OpenAI
from pinecone import Pinecone
from xata.client import XataClient

from src.config.config import (
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL_V3,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE_EDUCATION,
    XATA_API_KEY,
    XATA_DOCS_DB_URL,
)


async def search(query: str, top_k: int = 16, course: str = None) -> str:
    """Semantic search in education vector database."""

    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    pc = Pinecone(api_key=PINECONE_API_KEY)
    idx = pc.Index(PINECONE_INDEX_NAME)

    xata = XataClient(api_key=XATA_API_KEY, db_url=XATA_DOCS_DB_URL)

    response = openai_client.embeddings.create(
        input=query, model=OPENAI_EMBEDDING_MODEL_V3
    )
    query_vector = response.data[0].embedding

    filter = None
    if course:
        filter = {
            "course": {"$eq": course},
        }

    docs = idx.query(
        namespace=PINECONE_NAMESPACE_EDUCATION,
        vector=query_vector,
        top_k=top_k,
        filter=filter,
        include_metadata=True,
    )

    id_set = set()
    for matche in docs["matches"]:
        id = matche["id"].rpartition("_")[0]
        id_set.add(id)

    xata_response = xata.data().query(
        "education",
        {
            "columns": ["name", "chapter_number", "description"],
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
            name = record.get("name", "")
            chapter_number = record.get("chapter_number", "")
            description = record.get("description", "")

            source_entry = "**{} (Ch. {})**. {}.".format(
                name, chapter_number, description
            )
            docs_list.append({"content": doc.metadata["text"], "source": source_entry})

    return docs_list
