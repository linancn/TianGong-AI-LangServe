import base64
import datetime
import json
import os

import pandas as pd
from dotenv import load_dotenv
from xata.client import XataClient
import re
from typing import Optional, Type
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.chains.openai_functions import create_structured_output_chain
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema import SystemMessage

from langchain.tools import BaseTool
from pydantic import BaseModel

load_dotenv()

xata_api_key = os.getenv("XATA_API_KEY")
xata_db_url = os.getenv("XATA_DB_URL")
llm_model = os.getenv("OPENAI_MODEL")
openai_api_key = os.getenv("OPENAI_API_KEY")
langchain_verbose = os.getenv("LANGCHAIN_VERBOSE", "False") == "True"
xata = XataClient(api_key=xata_api_key, db_url=xata_db_url)



class SearchESG(BaseTool):
    name = "search_ESG_tool"
    description = "Search the xata for the ESG information."

    def esg_query_func_calling_chain(self):
        func_calling_json_schema = {
            "title": "get_querys_and_filters_to_search_xata_for_ESG_information",
            "description": "Extract the queries and filters for a Xata database semantic search",
            "type": "object",
            "properties": {
                "query": {
                    "title": "Query",
                    "description": "The queries extracted for a Xata database semantic search",
                    "type": "string",
                },
                "corporate": {
                    "title": "Corporate Filter",
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
                    "title": "Date Filter",
                    "description": 'Date extracted for a Xata database semantic search, in MongoDB\'s query and projection operators, in format like {"$gte": 1609459200.0, "$lte": 1640908800.0}',
                    "type": "string",
                },
            },
            "required": ["query"],
        }

        prompt_func_calling_msgs = [
            SystemMessage(
                content="You are a world class algorithm for extracting the queries and filters for a Xata database semantic search. Make sure to answer in the correct structured format"
            ),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]

        prompt_func_calling = ChatPromptTemplate(messages=prompt_func_calling_msgs)

        llm_func_calling = ChatOpenAI(
            api_key=openai_api_key,
            model_name=llm_model,
            temperature=0,
            streaming=False,
        )

        query_func_calling_chain = create_structured_output_chain(
            output_schema=func_calling_json_schema,
            llm=llm_func_calling,
            prompt=prompt_func_calling,
            verbose=langchain_verbose,
        )

        return query_func_calling_chain

    class InputSchema(BaseModel):
        query: str

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool synchronously."""

        query_response = self.esg_query_func_calling_chain().run(query)
        query = query_response.get("query")

        try:
            created_at = json.loads(query_response.get("created_at", None))
        except TypeError:
            created_at = None

        corporate = query_response.get("corporate", None)

        filters = {}
        if created_at:
            filters["created_at"] = created_at
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
            filters["corporate"] = [item['id'] for item in search_reportid['records']]

        result = xata.data().ask(
            "ESG_Embeddings",  # reference table
            query,  # question to ask
            options={
                "searchType": "vector",
                "vectorSearch": {
                    "column": "vector",
                    "contentColumn": "text",
                    "filter": filters,
                },
            },
        )
        return result

