import datetime
import json
import os
from typing import Optional, Type

from dotenv import load_dotenv
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.chains.openai_functions import create_structured_output_runnable
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema import SystemMessage
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pinecone import Pinecone
from pydantic import BaseModel
from xata.client import XataClient

load_dotenv()


class SearchVectorDB(BaseTool):
    name = "search_vectordb_tool"
    description = "Use original query to semantic search in academic or professional vector database."

    llm_model = os.getenv("OPENAI_MODEL")
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL_v3")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    langchain_verbose = os.getenv("LANGCHAIN_VERBOSE", "False") == "True"
    pinecone_api_key = os.getenv("PINECONE_SERVERLESS_API_KEY")
    pinecone_index = os.getenv("PINECONE_SERVERLESS_INDEX_NAME")

    xata_api_key = os.getenv("XATA_API_KEY")
    xata_db_url = os.getenv("XATA_DOCS_DB_URL")
    xata = XataClient(api_key=xata_api_key, db_url=xata_db_url)

    class InputSchema(BaseModel):
        query: str

    args_schema: Type[BaseModel] = InputSchema

    def vector_database_query_func_calling_chain(self):
        func_calling_json_schema = {
            "title": "get_querys_and_filters_to_search_vector_database",
            "description": "Extract the queries and filters for a vector database semantic search",
            "type": "object",
            "properties": {
                "query": {
                    "title": "Query",
                    "description": "The queries extracted for a vector database semantic search",
                    "type": "string",
                },
                "source": {
                    "title": "Source Filter",
                    "description": "Journal Name or Source extracted for a vector database semantic search, MUST be in upper case",
                    "type": "string",
                    "enum": [
                        "AGRICULTURE, ECOSYSTEMS & ENVIRONMENT",
                        "ANNUAL REVIEW OF ECOLOGY, EVOLUTION, AND SYSTEMATICS",
                        "ANNUAL REVIEW OF ENVIRONMENT AND RESOURCES",
                        "APPLIED CATALYSIS B: ENVIRONMENTAL",
                        "BIOGEOSCIENCES",
                        "BIOLOGICAL CONSERVATION",
                        "BIOTECHNOLOGY ADVANCES",
                        "CONSERVATION BIOLOGY",
                        "CONSERVATION LETTERS",
                        "CRITICAL REVIEWS IN ENVIRONMENTAL SCIENCE AND TECHNOLOGY",
                        "DIVERSITY AND DISTRIBUTIONS",
                        "ECOGRAPHY",
                        "ECOLOGICAL APPLICATIONS",
                        "ECOLOGICAL ECONOMICS",
                        "ECOLOGICAL MONOGRAPHS",
                        "ECOLOGY",
                        "ECOLOGY LETTERS",
                        "ECONOMIC SYSTEMS RESEARCH",
                        "ECOSYSTEM HEALTH AND SUSTAINABILITY",
                        "ECOSYSTEM SERVICES",
                        "ECOSYSTEMS",
                        "ENERGY & ENVIRONMENTAL SCIENCE",
                        "ENVIRONMENT INTERNATIONAL",
                        "ENVIRONMENTAL CHEMISTRY LETTERS",
                        "ENVIRONMENTAL HEALTH PERSPECTIVES",
                        "ENVIRONMENTAL POLLUTION",
                        "ENVIRONMENTAL SCIENCE & TECHNOLOGY",
                        "ENVIRONMENTAL SCIENCE & TECHNOLOGY LETTERS",
                        "ENVIRONMENTAL SCIENCE AND ECOTECHNOLOGY",
                        "ENVIRONMENTAL SCIENCE AND POLLUTION RESEARCH",
                        "EVOLUTION",
                        "FOREST ECOSYSTEMS",
                        "FRONTIERS IN ECOLOGY AND THE ENVIRONMENT",
                        "FRONTIERS OF ENVIRONMENTAL SCIENCE & ENGINEERING",
                        "FUNCTIONAL ECOLOGY",
                        "GLOBAL CHANGE BIOLOGY",
                        "GLOBAL ECOLOGY AND BIOGEOGRAPHY",
                        "GLOBAL ENVIRONMENTAL CHANGE",
                        "INTERNATIONAL SOIL AND WATER CONSERVATION RESEARCH",
                        "JOURNAL OF ANIMAL ECOLOGY",
                        "JOURNAL OF APPLIED ECOLOGY",
                        "JOURNAL OF BIOGEOGRAPHY",
                        "JOURNAL OF CLEANER PRODUCTION",
                        "JOURNAL OF ECOLOGY",
                        "JOURNAL OF ENVIRONMENTAL INFORMATICS",
                        "JOURNAL OF ENVIRONMENTAL MANAGEMENT",
                        "JOURNAL OF HAZARDOUS MATERIALS",
                        "JOURNAL OF INDUSTRIAL ECOLOGY",
                        "JOURNAL OF PLANT ECOLOGY",
                        "LANDSCAPE AND URBAN PLANNING",
                        "LANDSCAPE ECOLOGY",
                        "METHODS IN ECOLOGY AND EVOLUTION",
                        "MICROBIOME",
                        "MOLECULAR ECOLOGY",
                        "NATURE",
                        "NATURE CLIMATE CHANGE",
                        "NATURE COMMUNICATIONS",
                        "NATURE ECOLOGY & EVOLUTION",
                        "NATURE ENERGY",
                        "NATURE REVIEWS EARTH & ENVIRONMENT",
                        "NATURE SUSTAINABILITY",
                        "ONE EARTH",
                        "PEOPLE AND NATURE",
                        "PROCEEDINGS OF THE NATIONAL ACADEMY OF SCIENCES",
                        "PROCEEDINGS OF THE ROYAL SOCIETY B: BIOLOGICAL SCIENCES",
                        "RENEWABLE AND SUSTAINABLE ENERGY REVIEWS",
                        "RESOURCES, CONSERVATION AND RECYCLING",
                        "REVIEWS IN ENVIRONMENTAL SCIENCE AND BIO/TECHNOLOGY",
                        "SCIENCE",
                        "SCIENCE ADVANCES",
                        "SCIENCE OF THE TOTAL ENVIRONMENT",
                        "SCIENTIFIC DATA",
                        "SUSTAINABLE CITIES AND SOCIETY",
                        "SUSTAINABLE MATERIALS AND TECHNOLOGIES",
                        "SUSTAINABLE PRODUCTION AND CONSUMPTION",
                        "THE AMERICAN NATURALIST",
                        "THE INTERNATIONAL JOURNAL OF LIFE CYCLE ASSESSMENT",
                        "THE ISME JOURNAL",
                        "THE LANCET PLANETARY HEALTH",
                        "TRENDS IN ECOLOGY & EVOLUTION",
                        "WASTE MANAGEMENT",
                        "WATER RESEARCH",
                    ],
                },
                "created_at": {
                    "title": "Date Filter",
                    "description": 'Date extracted for a vector database semantic search, in MongoDB\'s query and projection operators, in format like {"$gte": 1609459200.0, "$lte": 1640908800.0}',
                    "type": "string",
                },
            },
            "required": ["query"],
        }

        prompt_func_calling_msgs = [
            SystemMessage(
                content="You are a world class algorithm for extracting the queries and filters for a vector database semantic search. Make sure to answer in the correct structured format"
            ),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]

        prompt_func_calling = ChatPromptTemplate(messages=prompt_func_calling_msgs)

        llm_func_calling = ChatOpenAI(
            api_key=self.openai_api_key,
            model_name=self.llm_model,
            temperature=0,
            streaming=False,
        )

        query_func_calling_chain = create_structured_output_runnable(
            output_schema=func_calling_json_schema,
            llm=llm_func_calling,
            prompt=prompt_func_calling,
        )

        return query_func_calling_chain


    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool synchronously."""

        embeddings = OpenAIEmbeddings(
            api_key=self.openai_api_key, model=self.embedding_model
        )
        pc = Pinecone(api_key=self.pinecone_api_key)
        idx = pc.Index(self.pinecone_index)

        query_response = self.vector_database_query_func_calling_chain().invoke(
            {"input": query}
        )

        query = query_response.get("query")

        try:
            created_at = json.loads(query_response.get("created_at", None))
        except TypeError:
            created_at = None

        source = query_response.get("source", None)

        filters = {}
        if created_at:
            filters["created_at"] = created_at
        if source:
            filters["source"] = source

        query_vector = embeddings.embed_query(query)

        if filters:
            docs = idx.query(
                namespace="sci",
                vector=query_vector,
                top_k=16,
                include_metadata=True,
                filters=filters,
            )
        else:
            docs = idx.query(
                namespace="sci",
                vector=query_vector,
                top_k=16,
                include_metadata=True,
            )

        doi_set = set()
        for matche in docs["matches"]:
            doi = matche["id"].rpartition("_")[0]
            doi_set.add(doi)

        record = self.xata.data().query(
            "journals",
            {
                "columns": ["doi", "title", "authors"],
                "filter": {
                    "doi": {"$any": list(doi_set)},
                },
            },
        )

        docs_list = []
        for doc in docs["matches"]:
            date = datetime.datetime.fromtimestamp(doc.metadata["date"])
            formatted_date = date.strftime("%Y-%m")  # Format date as 'YYYY-MM'
            source_entry = "[{}. {}. {}. {}.]({})".format(
                doc.metadata["source_id"],
                doc.metadata["source"],
                doc.metadata["author"],
                formatted_date,
                doc.metadata["url"],
            )
            docs_list.append({"content": doc.page_content, "source": source_entry})

        return docs_list

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""

        embeddings = OpenAIEmbeddings(api_key=self.openai_api_key)
        pinecone = Pinecone(api_key=os.environ.get("PINECONE_SERVERLESS_API_KEY"))

        vectorstore = PineconeVectorStore.from_existing_index(
            index_name=self.pinecone_index,
            embedding=embeddings,
        )

        query_response = self.vector_database_query_func_calling_chain().run(query)

        query = query_response.get("query")

        try:
            created_at = json.loads(query_response.get("created_at", None))
        except TypeError:
            created_at = None

        source = query_response.get("source", None)

        filters = {}
        if created_at:
            filters["created_at"] = created_at
        if source:
            filters["source"] = source

        if filters:
            docs = vectorstore.similarity_search(query, k=8, filter=filters)
        else:
            docs = vectorstore.similarity_search(query, k=8)

        docs_list = []
        for doc in docs:
            date = datetime.datetime.fromtimestamp(doc.metadata["created_at"])
            formatted_date = date.strftime("%Y-%m")  # Format date as 'YYYY-MM'
            source_entry = "[{}. {}. {}. {}.]({})".format(
                doc.metadata["source_id"],
                doc.metadata["source"],
                doc.metadata["author"],
                formatted_date,
                doc.metadata["url"],
            )
            docs_list.append({"content": doc.page_content, "source": source_entry})

        return docs_list
