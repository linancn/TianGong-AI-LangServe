import json
import os
from typing import Optional

from dotenv import load_dotenv
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.prompts import ChatPromptTemplate
from langchain.tools import BaseTool
from openai import OpenAI
from xata.client import XataClient

from src.services.lc.tools.common.function_calling import function_calling

load_dotenv()

xata_api_key = os.getenv("XATA_API_KEY")
xata_db_url = os.getenv("XATA_ESG_DB_URL")
llm_model = os.getenv("OPENAI_MODEL")
openai_api_key = os.getenv("OPENAI_API_KEY")
langchain_verbose = os.getenv("LANGCHAIN_VERBOSE", "False") == "True"
xata = XataClient(api_key=xata_api_key, db_url=xata_db_url)

client = OpenAI(api_key=openai_api_key)


class SearchESG(BaseTool):
    name = "search_ESG_tool"
    description = "Search for the ESG information."

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool synchronously."""

        function_desc = "Generate the query and filters for a semantic search"
        function_para = {
            "type": "object",
            "properties": {
                "query": {
                    "description": "The queries extracted for a Xata database semantic search",
                    "type": "string",
                },
                "corporate": {
                    "description": "Corporate Name or Corporate extracted for a Xata database semantic search, MUST be in short name",
                    "type": "string",
                    "enum": [
                        "Apple",
                        "Tesla",
                        "Toyota",
                        "BYD",
                    ],
                },
                "created_at": {
                    "description": 'Date extracted for a Xata database semantic search, in MongoDB\'s query and projection operators, in format like {"$gte": 1609459200.0, "$lte": 1640908800.0}',
                    "type": "string",
                },
            },
            "required": ["query"],
        }

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a world class algorithm for extracting the queries and filters for a Xata database semantic search. Make sure to answer in the correct structured format",
                ),
                ("human", "{input}"),
            ]
        )

        model_name = "gpt-4"

        query_response = function_calling(
            function_desc, function_para, prompt, model_name, query
        )

        query_response = json.loads(query_response)
        query = query_response.get("query")

        try:
            corporate = query_response.get("corporate", None)
        except TypeError:
            corporate = None

        filters = {}

        if corporate:
            search_reportid = xata.data().query(
                "ESG_Reports",
                {
                    "columns": ["id"],
                    "filter": {
                        "companyShortName": corporate,
                    },
                },
            )
            report_ids = [item["id"] for item in search_reportid["records"]]
            filters = {"reportId": {"$any": report_ids}}

        response = client.embeddings.create(input=query, model="text-embedding-ada-002")
        vector = response.data[0].embedding

        result = xata.data().vector_search(
            "ESG_Embeddings",  # reference table
            {
                "queryVector": vector,
                "column": "vector",
                "size": 10,
                "filter": filters,
            },
        )

        result_list = [item["text"] for item in result["records"]]

        return result_list

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""

        function_desc = "Generate the query and filters for a semantic search"
        function_para = {
            "type": "object",
            "properties": {
                "query": {
                    "description": "The queries extracted for a Xata database semantic search",
                    "type": "string",
                },
                "corporate": {
                    "description": "Corporate Name or Corporate extracted for a Xata database semantic search, MUST be in short name",
                    "type": "string",
                    "enum": [
                        "Apple",
                        "Tesla",
                        "Toyota",
                        "BYD",
                    ],
                },
                "created_at": {
                    "description": 'Date extracted for a Xata database semantic search, in MongoDB\'s query and projection operators, in format like {"$gte": 1609459200.0, "$lte": 1640908800.0}',
                    "type": "string",
                },
            },
            "required": ["query"],
        }

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a world class algorithm for extracting the queries and filters for a Xata database semantic search. Make sure to answer in the correct structured format",
                ),
                ("human", "{input}"),
            ]
        )

        model_name = "gpt-4"

        query_response = function_calling(
            function_desc, function_para, prompt, model_name, query
        )

        query_response = json.loads(query_response)
        query = query_response.get("query")

        try:
            corporate = query_response.get("corporate", None)
        except TypeError:
            corporate = None

        filters = {}

        if corporate:
            search_reportid = xata.data().query(
                "ESG_Reports",
                {
                    "columns": ["id"],
                    "filter": {
                        "companyShortName": corporate,
                    },
                },
            )
            report_ids = [item["id"] for item in search_reportid["records"]]
            filters = {"reportId": {"$any": report_ids}}

        response = client.embeddings.create(input=query, model="text-embedding-ada-002")
        vector = response.data[0].embedding

        result = xata.data().vector_search(
            "ESG_Embeddings",  # reference table
            {
                "queryVector": vector,
                "column": "vector",
                "size": 10,
                "filter": filters,
            },
        )

        result_list = [item["text"] for item in result["records"]]

        return result_list
