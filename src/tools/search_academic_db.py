import datetime
import os

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from xata.client import XataClient

load_dotenv()


class SearchSciDb:
    """Semantic search in academic or professional vector database."""

    openai_api_key = os.getenv("OPENAI_API_KEY")
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL_v3")
    openai_client = OpenAI(api_key=openai_api_key)

    pinecone_api_key = os.getenv("PINECONE_SERVERLESS_API_KEY")
    pinecone_index = os.getenv("PINECONE_SERVERLESS_INDEX_NAME")
    pc = Pinecone(api_key=pinecone_api_key)
    idx = pc.Index(pinecone_index)

    xata_api_key = os.getenv("XATA_API_KEY")
    xata_db_url = os.getenv("XATA_DOCS_DB_URL")
    xata = XataClient(api_key=xata_api_key, db_url=xata_db_url)

    async def search(self, query: str, top_k: int = 16) -> str:
        """Use the search tool asynchronously."""

        response = self.openai_client.embeddings.create(
            input=query, model=self.embedding_model
        )
        query_vector = response.data[0].embedding

        docs = self.idx.query(
            namespace="sci",
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
        )

        doi_set = set()
        for matche in docs["matches"]:
            doi = matche["id"].rpartition("_")[0]
            doi_set.add(doi)

        xata_response = self.xata.data().query(
            "journals",
            {
                "columns": ["doi", "title", "authors"],
                "filter": {
                    "doi": {"$any": list(doi_set)},
                },
            },
        )

        records = xata_response.get("records", [])
        records_dict = {record["doi"]: record for record in records}

        docs_list = []
        for doc in docs["matches"]:
            doi = doc["id"].rpartition("_")[0]
            record = records_dict.get(doi, {})

            if record:
                date = datetime.datetime.fromtimestamp(doc.metadata["date"])
                formatted_date = date.strftime("%Y-%m")
                authors = ", ".join(record["authors"])
                url = "https://doi.org/{}".format(doi)

                source_entry = "[{}. {}. {}. {}.]({})".format(
                    record["title"],
                    doc.metadata["journal"],
                    authors,
                    formatted_date,
                    url,
                )
                docs_list.append(
                    {"content": doc.metadata["text"], "source": source_entry}
                )

        return docs_list
