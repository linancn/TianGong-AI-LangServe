import datetime

from openai import OpenAI
from pinecone import Pinecone

from src.config.config import (
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL_V3,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE_PATENT,
)


async def search(query: str, top_k: int = 16) -> str:
    """Semantic search in patents vector database."""

    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    pc = Pinecone(api_key=PINECONE_API_KEY)
    idx = pc.Index(PINECONE_INDEX_NAME)

    response = openai_client.embeddings.create(
        input=query, model=OPENAI_EMBEDDING_MODEL_V3
    )
    query_vector = response.data[0].embedding

    docs = idx.query(
        namespace=PINECONE_NAMESPACE_PATENT,
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
    )

    docs_list = []
    for doc in docs["matches"]:

        date = datetime.datetime.fromtimestamp(doc.metadata["publication_date"])
        formatted_date = date.strftime("%Y-%m-%d")
        country = doc.metadata["country"]
        url = doc.metadata["url"]
        title = doc.metadata["title"]
        id = doc["id"]

        source_entry = "[{}. {}. {}. {}.]({})".format(
            id,
            title,
            country,
            formatted_date,
            url,
        )
        docs_list.append({"content": doc.metadata["abstract"], "source": source_entry})

    return docs_list
