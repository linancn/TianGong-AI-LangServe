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
from openai import OpenAI

from langchain.tools import BaseTool
from pydantic import BaseModel
from src.tools.common.function_calling import function_calling

load_dotenv()

xata_api_key = os.getenv("XATA_API_KEY")
xata_db_url = os.getenv("XATA_DB_URL")
llm_model = os.getenv("OPENAI_MODEL")
openai_api_key = os.getenv("OPENAI_API_KEY")
langchain_verbose = os.getenv("LANGCHAIN_VERBOSE", "False") == "True"
xata = XataClient(api_key=xata_api_key, db_url=xata_db_url)
openai_client = OpenAI()



query = "苹果公司2021年的碳减排措施有哪些？"

### langchain bind function
# function_desc = "Extracting the queries and filters for a fulltext search."
# function_para = {
#     "type": "object",
#     "properties": {
#         "query": {
#             "description": "The queries extracted for a fulltext search",
#             "type": "string",
#         },
#         "corporate": {
#             "description": "Corporate Name extracted for a fulltext search, MUST be in short name",
#             "type": "string",
#             "enum": [
#                 "Apple",
#                 "Tesla",
#                 "Toyota",
#                 "BYD",
#             ],
#         },
#     },
#     "required": ["query"],
# }

# prompt = ChatPromptTemplate.from_messages(
#     [
#         # (
#         #     "system",
#         #     "You are a world class algorithm for extracting the queries and filters for a fulltext search. Make sure to answer in the correct structured format",
#         # ),
#         ("human", "You are a world class algorithm for extracting the queries and filters for a fulltext search in its original language. Make sure to answer in the correct structured format. The query: {input}"),
#     ]
# )

# model_name = llm_model


# query_response = function_calling(
#     function_desc, function_para, prompt, model_name, query
# )


#### openai 原生写法
# messages = [
#     {
#         "role": "user",
#         "content": query,
#     }
# ]
# tools = [
#     {
#         "type": "function",
#         "function": {
#             "name": "get_querys_and_filters_to_search_ESG_information",
#             "description": "Extract the query and filters for a fulltext search",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "query": {
#                         "title": "query",
#                         "description": "Extract a query for fulltext search. Value MUST be in English",
#                         "type": "string",
#                     },
#                     "corporate": {
#                         "title": "corporate",
#                         "description": "Extract corporate name for search filter, MUST be in short name and English",
#                         "type": "string",
#                         "enum": [
#                             "Apple",
#                             "Tesla",
#                             "Toyota",
#                             "BYD",
#                         ],
#                     },
#                 },
#                 "required": [
#                     "query",
#                 ],
#             },
#         },
#     }
# ]
# response = openai_client.chat.completions.create(
#     model="gpt-4-1106-preview",
#     messages=messages,
#     tools=tools,
#     temperature=0.0,
#     tool_choice="auto",  # auto is default, but we'll be explicit
# )
# response_message = response.choices[0].message
# response_string = response_message.tool_calls[0].function.arguments
# response_json = json.loads(response_string)


### old functioncalling
def esg_query_func_calling_chain():
    func_calling_json_schema = {
        "title": "get_querys_and_filters_to_search_xata_for_ESG_information",
        "description": "Extract the queries and filters for semantic search",
        "type": "object",
        "properties": {
            "query": {
                "title": "Query",
                "description": "The queries extracted for semantic search",
                "type": "string",
            },
            "corporate": {
                "title": "Corporate Filter",
                "description": "Corporate Name extracted, MUST be in short name",
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
                "description": 'Date extracted for semantic search, in MongoDB\'s query and projection operators, in format like {"$gte": 1609459200.0, "$lte": 1640908800.0}',
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

query_response = esg_query_func_calling_chain().run(query)
query = query_response.get("query")




###
query_response = json.loads(query)
query = query_response.get("query")

corporate = query_response.get("corporate", None)

filters = {}
# if created_at:
#     filters["publicationDate"] = created_at
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
    filters["corporate"] = [item["id"] for item in search_reportid["records"]]


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
print(result)
